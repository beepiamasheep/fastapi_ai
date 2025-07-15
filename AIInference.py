import cv2
from tflite_runtime import interpreter as tflite
import numpy as np
import subprocess as sp
import time 
import yaml
import re
from pathlib import Path

img_width = 320  
img_height = 320  

def yaml_load(file="data.yaml", append_filename=False):

    assert Path(file).suffix in {".yaml", ".yml"}, f" {file} is not YAML"
    with open(file, errors="ignore", encoding="utf-8") as f:
        s = f.read()  
        
        if not s.isprintable():
            s = re.sub(r"[^\x09\x0A\x0D\x20-\x7E\x85\xA0-\uD7FF\uE000-\uFFFD\U00010000-\U0010ffff]+", "", s)
        
        data = yaml.safe_load(s) or {}  
        if append_filename:
            data["yaml_file"] = str(file)  
        return data

class LetterBox:
    def __init__(
        self, new_shape=(img_width, img_height), auto=False, scaleFill=False, scaleup=True, center=True, stride=32
    ):
        
        self.new_shape = new_shape
        self.auto = auto
        self.scaleFill = scaleFill
        self.scaleup = scaleup
        self.stride = stride
        self.center = center

    def __call__(self, labels=None, image=None):
       
        if labels is None:
            labels = {}
        img = labels.get("img") if image is None else image  
        shape = img.shape[:2]
        
        new_shape = labels.pop("rect_shape", self.new_shape)
        if isinstance(new_shape, int):
            new_shape = (new_shape, new_shape)
        
        r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
        if not self.scaleup:  
            r = min(r, 1.0)

        ratio = r, r  
        new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))  
        dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  
        
        if self.auto:  
            dw, dh = np.mod(dw, self.stride), np.mod(dh, self.stride)
        elif self.scaleFill:  
            dw, dh = 0.0, 0.0
            new_unpad = (new_shape[1], new_shape[0])
            ratio = new_shape[1] / shape[1], new_shape[0] / shape[0]

        if self.center:  
            dw /= 2
            dh /= 2
        
        if shape[::-1] != new_unpad:
            img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)

        top, bottom = int(round(dh - 0.1)) if self.center else 0, int(round(dh + 0.1))
        left, right = int(round(dw - 0.1)) if self.center else 0, int(round(dw + 0.1))
        img = cv2.copyMakeBorder(
            img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(114, 114, 114)
        )  

        if labels.get("ratio_pad"):
            labels["ratio_pad"] = (labels["ratio_pad"], (left, top))

        if len(labels):
            labels = self._update_labels(labels, ratio, dw, dh)
            labels["img"] = img
            labels["resized_shape"] = new_shape
            return labels
        else:
            return img

    def _update_labels(self, labels, ratio, padw, padh):
        
        labels["instances"].convert_bbox(format="xyxy")
        labels["instances"].denormalize(*labels["img"].shape[:2][::-1])
        labels["instances"].scale(*ratio)
        labels["instances"].add_padding(padw, padh)
        return labels

class Yolov8TFLite:
    def __init__(self, tflite_model , confidence_thres, iou_thres, ext_delegate):
        self.img = None
        self.tflite_model = tflite_model
        self.confidence_thres = confidence_thres
        self.iou_thres = iou_thres
        
        self.ext_delegate = ext_delegate
        self.ext_delegate_options = {
            "backend_type": "htp",  
        }

        if ext_delegate is not None:
            print('open ext_delegate: {} setting: {}'.format(ext_delegate, self.ext_delegate_options))
            self.ext_delegate = [tflite.load_delegate(ext_delegate, self.ext_delegate_options)]
        
        #此处设置数据集配置文件
        self.classes = yaml_load("coco8.yaml")["names"]
        self.color_palette = np.random.uniform(0, 255, size=(len(self.classes), 3))

    def draw_detections(self, img, box, score, class_id):
        
        x1, y1, w, h = box
        color = self.color_palette[class_id]
        cv2.rectangle(img, (int(x1), int(y1)), (int(x1 + w), int(y1 + h)), color, 2)
        label = f"{self.classes[class_id]}: {score:.2f}"
        (label_width, label_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        label_x = x1
        label_y = y1 - 10 if y1 - 10 > label_height else y1 + 10
        cv2.rectangle(
            img,
            (int(label_x), int(label_y - label_height)),
            (int(label_x + label_width), int(label_y + label_height)),
            color,
            cv2.FILLED,
        )
        cv2.putText(img, label, (int(label_x), int(label_y)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

    def preprocess(self):

        self.img_height, self.img_width = self.img.shape[:2]

        letterbox = LetterBox(new_shape=[img_width, img_height], auto=False, stride=32)
        image = letterbox(image=self.img)
        image = [image]
        image = np.stack(image)
        image = image[..., ::-1].transpose((0, 3, 1, 2))  
        img = np.ascontiguousarray(image)
        
        image = img.astype(np.float32)
        return image / 255  

    def postprocess(self, input_image, output):

        output = output[0]
        output = output.T
        boxes = output[..., :4]  
        scores = np.max(output[..., 4:], axis=1)  
        class_ids = np.argmax(output[..., 4:], axis=1)

        indices = cv2.dnn.NMSBoxes(boxes, scores, self.confidence_thres, self.iou_thres)
        for i in indices:
            score = scores[i]
            class_id = class_ids[i]
            if score > 0.5:  
                box = boxes[i]
                gain = min(img_width / self.img_width, img_height / self.img_height)
                pad = (
                    round((img_width - self.img_width * gain) / 2 - 0.1),
                    round((img_height - self.img_height * gain) / 2 - 0.1),
                )
                box[0] = (box[0] - box[2] / 2 - pad[0]) / gain
                box[1] = (box[1] - box[3] / 2 - pad[1]) / gain
                box[2] = box[2] / gain
                box[3] = box[3] / gain

                self.draw_detections(input_image, box, score, class_id)
        
        return input_image

    def pre_inference(self):
        self.interpreter = tflite.Interpreter(model_path=self.tflite_model, experimental_delegates=self.ext_delegate)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
    
    def inference(self,frame):
        self.img = frame
        img_data = self.preprocess()
        img_data = img_data.transpose((0, 2, 3, 1))
        
        scale, zero_point = self.input_details[0]["quantization"]
        img_data_int8 = (img_data / scale + zero_point).astype(np.int8)
        self.interpreter.set_tensor(self.input_details[0]["index"], img_data_int8)
        
        startTime = time.time()
        self.interpreter.invoke()
        delta = time.time() - startTime
        # print(delta)
        
        output = self.interpreter.get_tensor(self.output_details[0]["index"])
        scale, zero_point = self.output_details[0]["quantization"]
        output = (output.astype(np.float32) - zero_point) * scale
        output[:, [0, 2]] *= img_width
        output[:, [1, 3]] *= img_height
       
        output_image = self.postprocess(self.img, output)
        return output_image
        


if __name__ == "__main__":
    inference_config = {
        "model_path": "/root/test//yolov8n_full_integer_quant.tflite",
        "conf_thres": 0.5,
        "iou_thres": 0.5,
        "ext_delegate": "/usr/lib/libQnnTFLiteDelegate.so",
    }
    detection = Yolov8TFLite(
        tflite_model=inference_config["model_path"],
        confidence_thres=inference_config["conf_thres"],
        iou_thres=inference_config["iou_thres"],
        ext_delegate=inference_config["ext_delegate"]
    )
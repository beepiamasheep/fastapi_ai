import asyncio
import queue
import os
import time
import threading
import subprocess
import cv2
from fastapi import BackgroundTasks, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict

import uvicorn
from AIInference import Yolov8TFLite
from minio_tool import Bucket
from fastapi import APIRouter, HTTPException, Header, Depends
from fastapi.responses import StreamingResponse
from minio import Minio
from minio.error import S3Error
from typing import Optional

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#这些需要加入MySQL中
stream_tasks: Dict[str, threading.Thread] = {}
stream_stop_flags: Dict[str, bool] = {}
record_stop_flags: Dict[str, bool] = {}
stream_status: Dict[str, dict] = {}
frame_queues: Dict[str, queue.Queue] = {}
record_frame_queues: Dict[str, queue.Queue] = {}

# FastAPI IP地址
# 推理配置
fastapi_ip: str = "192.168.101.10"
inference_config = {
        "model_path": "/root/test//yolov8n_full_integer_quant.tflite",
        "conf_thres": 0.5,
        "iou_thres": 0.5,
        "ext_delegate": "/usr/lib/libQnnTFLiteDelegate.so",
    }
minio_config = {
    "minio_address": "192.168.101.10:9000",
    "minio_admin": "minioadmin",
    "minio_password": "minioadmin",
    }

#输入流配置
class StreamConfig(BaseModel):
    input_stream: str = "rtmp://192.168.0.183:1935/live/stream22"
    width: int = 1280
    height: int = 720
    fps: int = 30
    ai_enabled: bool = True
    record_enabled: bool = False

#录制流配置
class RecordRequest(BaseModel):
    stream_id: str
    input_stream: str 

#帧读取函数
def frame_reader(stream_id: str, input_stream: str, width: int, height: int):
    cap = cv2.VideoCapture(input_stream)
    while cap.isOpened() and not stream_stop_flags.get(stream_id, True):
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.resize(frame, (width, height))
        try:
            frame_queues[stream_id].put(frame, timeout=1)
        except queue.Full:
            continue
    cap.release()

#帧推流函数
def frame_pusher(config: StreamConfig, stream_id: str):
    width, height, fps = config.width, config.height, config.fps
    ai_enabled = config.ai_enabled
    record_enabled = config.record_enabled
    output_stream = f"{config.input_stream}_mask"
    
    detection = Yolov8TFLite(
            tflite_model=inference_config["model_path"],
            confidence_thres=inference_config["conf_thres"],
            iou_thres=inference_config["iou_thres"],
            ext_delegate=inference_config["ext_delegate"]
            )
            
    push_cmd = [
        'ffmpeg', '-y',
        '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{width}x{height}', '-r', str(fps),
        '-i', '-', '-pix_fmt', 'yuv420p',
        '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'zerolatency',
        '-f', 'flv','-g', '30', output_stream
    ]
    
    print(f"[{stream_id}] push: {' '.join(push_cmd)}")
    
    try:
        push_proc = subprocess.Popen(push_cmd, stdin=subprocess.PIPE)
    except Exception as e:
        print(f"[{stream_id}] FFmpeg fail: {e}")
        return

    frame_count = 0
    if ai_enabled:
      detection.pre_inference()
    
    stream_status[stream_id] = {
                "stream_id": stream_id,
                "push_status": "running",
                "ai_status": "stopped",
                "record_status": "stopped",
                "fps": fps,
                "frame_count": frame_count,
                "width": width,
                "height": height,
                "last_update": time.strftime("%H:%M:%S")
            }
    if record_enabled:
                stream_status[stream_id]["record_status"] = "running"    
    while not stream_stop_flags.get(stream_id, True):
        try:
            frame = frame_queues[stream_id].get(timeout=1)
           
            stream_status[stream_id]["stream_id"] = stream_id
            stream_status[stream_id]["push_status"] = "running"
            stream_status[stream_id]["fps"] = fps
            stream_status[stream_id]["frame_count"] = frame_count
            stream_status[stream_id]["width"] = width
            stream_status[stream_id]["height"] = height
            stream_status[stream_id]["last_update"] = time.strftime("%H:%M:%S")
            
            if ai_enabled:
                stream_status[stream_id]["ai_status"] = "running"
                frame = detection.inference(frame)
                push_proc.stdin.write(frame.tobytes())
            
            frame_count += 1

        except queue.Empty:
            continue
        except BrokenPipeError:
            print(f"[{stream_id}] fail: Broken pipe")
            break
        except Exception as e:
            print(f"[{stream_id}] fail: {e}")
            break

    try:
        push_proc.stdin.close()
        push_proc.wait()

    except Exception:
        pass
    
    stream_status[stream_id]["push_status"] = "stopped"
    stream_status[stream_id]["ai_status"] = "stopped"
    stream_status[stream_id]["record_status"] = "stopped"
    print(f"[{stream_id}] push and record over")

#视频流转发函数
def smooth_stream_worker(config: StreamConfig, stream_id: str):
    frame_queues[stream_id] = queue.Queue(maxsize=10)
    stream_stop_flags[stream_id] = False

    def reader_then_push():
        reader_thread = threading.Thread(
            target=frame_reader,
            args=(stream_id, config.input_stream, config.width, config.height),
            daemon=True
        )
        reader_thread.start()

        
        for _ in range(30):
            if frame_queues[stream_id].qsize() >= 5:
                break
            time.sleep(0.1)

        threading.Thread(
            target=frame_pusher,
            args=(config, stream_id),
            daemon=True
        ).start()

    threading.Thread(target=reader_then_push, daemon=True).start()

#录制并上传到 MinIO
def record_and_upload_to_minio(input_stream: str):
    from datetime import datetime
    bucket = Bucket(minio_address=minio_config["minio_address"],
                    minio_admin=minio_config["minio_admin"],
                    minio_password=minio_config["minio_password"])
                    
    stream_id = input_stream.split("/")[-1]
    stream_status[stream_id]["record_status"] = "running"
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{now}.mp4"
    output_path = f"records/{filename}"
    record_process = None
    
    bucket.create_one_bucket('videos')
    os.makedirs("records", exist_ok=True)
    
    while True:
        flag = stream_status[stream_id]["record_status"]
        if flag == "running" and record_process is None:
            
            record_cmd = [
                'ffmpeg',
                '-y',                        
                '-i', input_stream,                   
                '-vf', 'format=yuv420p',
                '-c:v', 'libx264',
                '-preset', 'ultrafast',
                output_path
            ]
            record_process = subprocess.Popen(record_cmd)
            print(f"[{stream_id}] record: {' '.join(record_cmd)}")
        
        elif flag == "stopped" and record_process is not None:
            
            record_process.terminate()
            record_process.wait()
            record_process = None
            break
        
        time.sleep(1)  
        
    
    print(f"[{stream_id}] ?? record over: {output_path}")
    bucket.upload_file_to_bucket('videos', filename, output_path)
    print(f"[{stream_id}] ?? upload over")
    stream_status[stream_id]["record_status"] = "stopped"

#启动视频流                   
@app.post("/start-stream")
def start_stream(config: StreamConfig):
    ai_enabled = config.ai_enabled
    record_enabled = config.record_enabled
    input_stream = config.input_stream
    if ai_enabled:
      stream_id = config.input_stream.split("/")[-1]
      stream_id =f"{stream_id}_mask"
    else :
      stream_id = config.input_stream.split("/")[-1]
    if stream_id in stream_status:
        if stream_status[stream_id]["push_status"] == "running":
            return {"status": "running", "msg": f"{stream_id} running"}
    if stream_id in stream_tasks and stream_tasks[stream_id].is_alive():
        return {"status": "running", "msg": f"{stream_id} running"}
    
    t = threading.Thread(target=smooth_stream_worker, args=(config, stream_id))
    stream_tasks[stream_id] = t
    t.start()
    if record_enabled:
        t2=threading.Thread(target=record_and_upload_to_minio, args=(input_stream))
        t2.start()
    return {"status": "started", "stream": stream_id}

#停止视频流  
@app.post("/stop-stream")
def stop_stream(stream_id: str):
    if stream_id in stream_stop_flags:
        stream_stop_flags[stream_id] = True
        if stream_id in stream_tasks:
            stream_tasks[stream_id].join()
            del stream_tasks[stream_id]
        return {"status": "stopped", "stream": stream_id}
    return {"status": "not_found", "stream": stream_id}

#启动录制
@app.post("/start-record")
def start_record(req: RecordRequest, background_tasks: BackgroundTasks):
    record_stream_id = req.input_stream.split("/")[-1]
    if record_stream_id in stream_status :
        if stream_status[record_stream_id]["record_status"] == "running" or stream_status[record_stream_id]["push_status"] == "stopped":
          return {"status": "recording not started again", "stream_id": record_stream_id}
    else :
        return {"stream_id not found": record_stream_id}
    background_tasks.add_task(
        record_and_upload_to_minio,
        req.input_stream
    )
    return {"status": "recording started", "stream_id": record_stream_id}

#停止录制    
@app.post("/stop-record")
def stop_record(record_stream_id: str):
    if record_stream_id in stream_status:
        if stream_status[record_stream_id]["record_status"] == "running":
          stream_status[record_stream_id]["record_status"] = "stopped"
          return {"status": "recording started", "stream_id": record_stream_id}
    else :
        return {"stream_id not found": record_stream_id}

#从minio中下载指定文件
@app.get("/download/videos/{object_name}")
async def download_file(
    object_name: str,
    bucket_name: str="videos",    
    range: Optional[str] = Header(None)
):
  
    try:
        minio_client = Minio(
            endpoint=minio_config["minio_address"],
            access_key=minio_config["minio_admin"],
            secret_key=minio_config["minio_password"],
            secure=False
        )
        if not minio_client.bucket_exists(bucket_name):
            raise HTTPException(status_code=404, detail="Bucket not found")
        
        try:
            
            obj_stat = minio_client.stat_object(bucket_name, object_name)
        except S3Error as e:
            if e.code == "NoSuchKey":
                raise HTTPException(status_code=404, detail="File not found")
            else:
                raise HTTPException(status_code=500, detail=f"MinIO error: {str(e)}")
        
        
        file_name = os.path.basename(object_name)
        
        if range:
            
            parts = range.replace("bytes=", "").split("-")
            start = int(parts[0])
            end = int(parts[1]) if parts[1] else obj_stat.size - 1
            
            if start >= obj_stat.size or end >= obj_stat.size:
                raise HTTPException(status_code=416, detail="Invalid range")
            
            
            data = minio_client.get_partial_object(
                bucket_name, object_name, start, end - start + 1
            )
            
            
            headers = {
                "Content-Range": f"bytes {start}-{end}/{obj_stat.size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(end - start + 1),
                "Content-Disposition": f'attachment; filename="{file_name}"',
            }
            
            return Response(data, status_code=206, headers=headers)
        
        def iterfile():
            try:
                response = minio_client.get_object(bucket_name, object_name)
                for chunk in response.stream(8192):
                    yield chunk
            finally:
                response.close()
                response.release_conn()
        
        headers = {
            "Content-Disposition": f'attachment; filename="{file_name}"',
            "Content-Length": str(obj_stat.size)
        }
        
        return StreamingResponse(iterfile(), headers=headers)
    
    except Exception as e:
        
        print(f"Error downloading file: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

#视频流状态显示
@app.websocket("/ws/status")
async def status_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_json(stream_status)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass

#minio文件列表显示
@app.websocket("/ws/minio")
async def status_ws(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            bucket = Bucket(minio_address=minio_config["minio_address"],
                        minio_admin=minio_config["minio_admin"],
                        minio_password=minio_config["minio_password"])
            ret = bucket.get_list_objects_from_bucket_pro(bucket_name='videos')
            minio_response = {
                'code': 0,
                'message': 'success',
                'data': {
                    'list': ret,  
                    'pagination': {
                        'total': len(ret),  
                        'page': 1,
                        'page_size': 50
                    }
                }
            }
            await websocket.send_json(minio_response)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass

#根路由展示流状态    
@app.get("/")
def root():
    return stream_status

if __name__ == "__main__":
    uvicorn.run(app=app ,host=fastapi_ip ,port=8000)
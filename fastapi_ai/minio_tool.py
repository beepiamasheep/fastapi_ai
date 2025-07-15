from minio import Minio, InvalidResponseError, S3Error


# MinIO使用bucket（桶）来组织对象。
# bucket类似于文件夹或目录，其中每个bucket可以容纳任意数量的对象。
class Bucket:

    def __init__(self, minio_address, minio_admin, minio_password):
        # 通过ip 账号 密码 连接minio server
        # Http连接 将secure设置为False
        self.minioClient = Minio(endpoint=minio_address,
                                 access_key=minio_admin,
                                 secret_key=minio_password,
                                 secure=False)

    def create_one_bucket(self, bucket_name):
        # 创建桶(调用make_bucket api来创建一个桶)
        """
        桶命名规则：小写字母，句点，连字符和数字 允许使用 长度至少3个字符
        使用大写字母、下划线等会报错
        """
        try:
            # bucket_exists：检查桶是否存在
            if self.minioClient.bucket_exists(bucket_name=bucket_name):
                print("该存储桶已经存在")
            else:
                self.minioClient.make_bucket(bucket_name=bucket_name)
                print(f"{bucket_name}桶创建成功")
        except InvalidResponseError as err:
            print(err)

    def remove_one_bucket(self, bucket_name):
        # 删除桶(调用remove_bucket api来创建一个存储桶)
        try:
            if self.minioClient.bucket_exists(bucket_name=bucket_name):
                self.minioClient.remove_bucket(bucket_name)
                print("删除存储桶成功")
            else:
                print("该存储桶不存在")
        except InvalidResponseError as err:
            print(err)

    def upload_file_to_bucket(self, bucket_name, file_name, file_path):
        """
        将文件上传到bucket
        :param bucket_name: minio桶名称
        :param file_name: 存放到minio桶中的文件名字(相当于对文件进行了重命名，可以与原文件名不同)
                            file_name处可以创建新的目录(文件夹) 例如 /example/file_name
                            相当于在该桶中新建了一个example文件夹 并把文件放在其中
        :param file_path: 本地文件的路径
        """
        # 桶是否存在 不存在则新建
        check_bucket = self.minioClient.bucket_exists(bucket_name)
        if not check_bucket:
            self.minioClient.make_bucket(bucket_name)

        try:
            self.minioClient.fput_object(bucket_name=bucket_name,
                                         object_name=file_name,
                                         file_path=file_path)
        except FileNotFoundError as err:
            print('upload_failed: ' + str(err))
        except S3Error as err:
            print("upload_failed:", err)

    def download_file_from_bucket(self, bucket_name, minio_file_path, download_file_path):
        """
        从bucket下载文件
        :param bucket_name: minio桶名称
        :param minio_file_path: 存放在minio桶中文件名字
                            file_name处可以包含目录(文件夹) 例如 /example/file_name
        :param download_file_path: 文件获取后存放的路径
        """
        # 桶是否存在
        check_bucket = self.minioClient.bucket_exists(bucket_name)
        if check_bucket:
            try:
                self.minioClient.fget_object(bucket_name=bucket_name,
                                             object_name=minio_file_path,
                                             file_path=download_file_path)
            except FileNotFoundError as err:
                print('download_failed: ' + str(err))
            except S3Error as err:
                print("download_failed:", err)

    def remove_object(self, bucket_name, object_name):
        """
        从bucket删除文件
        :param bucket_name: minio桶名称
        :param object_name: 存放在minio桶中的文件名字
                            object_name处可以包含目录(文件夹) 例如 /example/file_name
        """
        # 桶是否存在
        check_bucket = self.minioClient.bucket_exists(bucket_name)
        if check_bucket:
            try:
                self.minioClient.remove_object(bucket_name=bucket_name,
                                               object_name=object_name)
            except FileNotFoundError as err:
                print('upload_failed: ' + str(err))
            except S3Error as err:
                print("upload_failed:", err)

    # 获取所有的桶
    def get_all_bucket(self):
        buckets = self.minioClient.list_buckets()
        ret = []
        for _ in buckets:
            ret.append(_.name)
        return ret

    # 获取一个桶中的所有一级目录和文件
    def get_list_objects_from_bucket(self, bucket_name):
        # 桶是否存在
        check_bucket = self.minioClient.bucket_exists(bucket_name)
        if check_bucket:
            # 获取到该桶中的所有目录和文件
            objects = self.minioClient.list_objects(bucket_name=bucket_name)
            ret = []
            for _ in objects:
                ret.append(_.object_name)
            return ret

    # 获取桶里某个目录下的所有目录和文件
    def get_list_objects_from_bucket_dir(self, bucket_name, dir_name):
        # 桶是否存在
        check_bucket = self.minioClient.bucket_exists(bucket_name)
        if check_bucket:
            # 获取到bucket_name桶中的dir_name下的所有目录和文件
            # prefix 获取的文件路径需包含该前缀
            objects = self.minioClient.list_objects(bucket_name=bucket_name,
                                                    prefix=dir_name,
                                                    recursive=True)
            ret = []
            for _ in objects:
                ret.append(_.object_name)
            return ret
            
    def get_list_objects_from_bucket_pro(self, bucket_name):
        check_bucket = self.minioClient.bucket_exists(bucket_name)
        if check_bucket:
            # 获取到该桶中的所有目录和文件
            objects = self.minioClient.list_objects(bucket_name=bucket_name)
            ret = []
            for obj in objects:
                # 添加文件名和最后修改时间到结果列表
                full_path = f"{bucket_name}/{obj.object_name}"
                ret.append({
                    'fingerprint': 'mock1',
                    'drone': 'Test Drone122',
                    'payload': 'Camera',
                    'is_original': 'true',
                    'file_path': full_path,
                    'file_name': obj.object_name,
                    'create_time': obj.last_modified.strftime('%Y-%m-%d %H:%M:%S'),
                    'file_id': obj.etag
                })
            return ret


if __name__ == "__main__":
    # 本地minio登录IP地址和账号密码
    minio_address = "127.0.0.1:9000"
    minio_admin = "minioadmin"
    minio_password = "minioadmin"

    bucket = Bucket(minio_address=minio_address,
                    minio_admin=minio_admin,
                    minio_password=minio_password)
    # 创建桶测试
    # bucket.create_one_bucket('test1')

    # 删除桶测试
    # bucket.remove_one_bucket('test1')

    # 上传文件测试
    # bucket.upload_file_to_bucket('test1', '1.jpg', './1.jpg')
    # bucket.upload_file_to_bucket('test1', '/example/1.jpg', './1.jpg')

    # 删除文件测试
    # bucket.remove_object('test1', '1.jpg')
    # bucket.remove_object('test', '/example/1.jpg')

    # 下载图像测试
    # bucket.download_file_from_bucket('test1', 'example/1.jpg', './1.jpg')

    # 获取所有的桶
    # ret = bucket.get_all_bucket()
    # print(ret)

    # 获取一个桶中的所有一级目录和文件
    # ret = bucket.get_list_objects_from_bucket(bucket_name='test')
    # print(ret)

    # 获取一个桶中的某目录下的所有文件
    # ret = bucket.get_list_objects_from_bucket_dir('test', 'example/')
    # print(ret)


from django.core.files.storage import Storage
from dailyfresh import settings
from fdfs_client.client import Fdfs_client


class FDFSStorage(Storage):
    """自定义storage类"""

    def __init__(self, Base_conf=None, Base_url=None):
        if Base_conf == None:
            Base_conf = settings.FDFS_BASE_CONF
        self.Base_conf = Base_conf

        if Base_url == None:
            Base_url = settings.FDFS_BASE_URL
        self.Base_url = Base_url

    def _open(self, name, mode='rb'):
        pass

    def _save(self, name, content):
        """重写_save方法进行FDFS上传"""
        # 创建客户端连接对象
        client = Fdfs_client(self.Base_conf)
        # 调用链接对象的二进制上传文件方法
        res = client.upload_by_buffer(content.read())
        # 'Group name': group_name,
        # 'Remote file_id': remote_file_id,
        # 'Status': 'Upload successed.',
        # 'Local file name': '',
        # 'Uploaded size': upload_size,
        # 'Storage IP': storage_ip
        # 判断上传图片是否成功
        if res.get('Status') != 'Upload successed.':
            raise Exception('fdfs客户端上传失败')
        # 成功则返回文件id
        filename = res.get('Remote file_id')
        return filename

    def exists(self, name):
        return False

    def url(self, name):
        return self.Base_url+name
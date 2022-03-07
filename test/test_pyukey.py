# -*- coding: utf-8 -*-
"""
同UKey通信的PyUKey类的相关测试
"""


from ukey_.pyukey import PyUKey


class TestPyUKey:

    def setup(self):
        dll_path = r'D:\Projects\python\LicenseManagementTool\files\UKey\Python-x64\Don_API-x64.dll'
        self.py_ukey = PyUKey(dll_path)

    def test_find(self):  # 获取连接的ukey设备数
        self.py_ukey.find()
        print(f'\n当前连接的设备数为 {self.py_ukey.ukey_pool}')

    def test_open_don(self):  # 同第一个设备建立连接
        don_index = 1  # 连接第一个设备
        self.py_ukey.open_don(don_index)
        assert self.py_ukey.is_open is True

    def test_verify_pin(self):  # 测试PIN码校验
        n_flags = 1
        self.py_ukey.open_don(1)
        ret = self.py_ukey.verify_pin(n_flags)
        assert ret is True
        print('PIN码验证通过')

    def test_read_base_file(self):  # 测试读取基本文件信息
        don_index = 1
        self.py_ukey.open_don(don_index)
        self.py_ukey.read_file(0x1001)
        print(self.py_ukey.base_info)

    def test_get_license(self):
        hid = "2B0030001151363136343732"
        n_flags = 1
        self.py_ukey.open_don(1)
        ret = self.py_ukey.verify_pin(n_flags)
        self.py_ukey.read_file(0x1001)
        self.py_ukey.get_license(hid)
        print('License:')
        for i in self.py_ukey.license:
            print(f'    {i}')

    def teardown(self):
        self.py_ukey.close()


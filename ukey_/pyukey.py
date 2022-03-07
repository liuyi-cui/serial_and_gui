# -*- coding: utf-8 -*-
"""同UKey通信的相关方法"""
import sys
import os
import ctypes
from ctypes import *
from pathlib import Path

from utils.convert_utils import strhextobytes
from utils.utility import padding_hex


dll_path = r'D:\Projects\python\LicenseManagementTool\files\UKey\Python-x64\Don_API-x64.dll'


class PyUKeyException(Exception):
    pass


class BaseInfo:
    """基本文件信息"""

    def __init__(self, base_value):
        """
        根据从ukey读取到的基本信息文件的数据，解析得到对应的基本信息
        解析规则：
            按顺序依次为 tag(一个字节)-length(一个字节)-value(length字节)
            授权license额度
            算法类型
            厂商简称
            UKey编号
            用户ID
            账户ID
            芯片型号

        Args:
            base_value: str, eg: 0104000027100201010305434d494f54040a50726f64756374415f3105045573723106084163636f756e743107074e585031303631
        """
        start_index = 0
        while start_index < len(base_value) - 1:
            tag = base_value[start_index: start_index+2]
            length = int(base_value[start_index+2: start_index+4], 16) * 2
            value = base_value[start_index+4: start_index+4+length]
            if tag == '01':  # 授权的license额度
                self.authorized_license_quota = value
            elif tag == '02':  # 算法类型
                self.algorithm_type = value
            elif tag == '03':  # 厂商简称
                self.manufacturer_code = value
            elif tag == '04':  # UKey编号
                self.ukey_no = value
            elif tag == '05':  # 用户ID
                self.user_id = value
            elif tag == '06':  # 账户ID
                self.account_id = value
            elif tag == '07':  # 芯片型号
                self.chip_model = value
            else:
                raise PyUKeyException(f'基本文件信息解析失败，value：{base_value}')
            interval = 4 + length
            start_index += interval

    def __repr__(self):
        ret = f'\n授权license额度为 {self.authorized_license_quota}\n' \
              f'license加密算法类型为 {self.algorithm_type}\n' \
              f'厂商简称为 {self.manufacturer_code}\n' \
              f'UKey编号为 {self.ukey_no}\n' \
              f'用户ID为 {self.user_id}\n' \
              f'账户ID为 {self.account_id}\n' \
              f'芯片型号为 {self.chip_model}\n'
        return ret


class PyUKey:

    ORI_PID = 'ffffffff'  # 初始化的产品ID
    ORI_USERPIN = '12345678'  # 出厂默认的USERPIN
    ORI_ADMINPIN = 'ffffffffffffffff'  # 出厂默认的ADMINPIN

    def __init__(self, dll_path=dll_path):
        self.is_open = False  # 是否已经同一个UKey建立连接
        self.is_connected = False  # 是否已经通过了PIN码验证
        self.handle = None  # UKey连接句柄
        self.ukey_pool = None  # 当前连接的UKey设备数
        if Path(dll_path).exists():
            self.hinst = ctypes.cdll.LoadLibrary(dll_path)
        else:
            raise PyUKeyException('请传入正确的Don_API.dll路径')
        self.license = []

    def find(self):
        """获取当前连接的UKey设备数"""
        n_count = ctypes.c_int(0)  # int类型
        ret = self.hinst.DON_Find(self.ORI_PID.encode(), ctypes.byref(n_count))
        if ret == 0:
            self.ukey_pool = n_count.value

    def open_don(self, don_index):
        """
        同UKey建立连接
        Args:
            don_index: UKey索引，起始值为1

        Returns:
            连接的句柄

        """
        if self.ukey_pool is None:
            self.find()
        if don_index > self.ukey_pool:
            raise PyUKeyException('要连接的设备序号大于真实连接的设备数')
        handle = ctypes.c_longlong(0)  # int类型
        ret = self.hinst.DON_Open(ctypes.byref(handle), don_index)  # 连接第一个UKey
        if ret == 0:
            self.is_open = True
            self.handle = handle

    def verify_pin(self, n_flags, p_pin=None):
        """
        验证PIN码
        Args:
            n_flags: PIN码类型，0为用户PIN码，1为开发者PIN码
            p_pin: PIN码

        Returns:
            0 已锁死
            1-253 剩余的PIN码验证次数
            255 不限制PIN码验证次数

        """
        if self.is_open:
            n_remain_count = ctypes.c_int(0)  # int类型，PIN码验证剩余重试次数。0表示已锁死，0-253表示剩余次数，255表示不限制重试次数
            if p_pin is None:
                if n_flags == 0:
                    p_pin = self.ORI_USERPIN
                elif n_flags == 1:
                    p_pin = self.ORI_ADMINPIN
                else:
                    raise PyUKeyException('PIN码类型只支持0/1')
            ret = self.hinst.DON_VerifyPIN(self.handle, n_flags, p_pin.encode(), ctypes.byref(n_remain_count))
            if n_remain_count.value == 0:
                raise PyUKeyException('目标设备该类型PIN码验证已锁死')
            self.is_connected = True
            return True
        else:
            raise PyUKeyException('请先同UKey建立连接')

    # 读取加密锁内的数据文件
    def read_file(self, file_id: hex, offset=0):
        """
        读取加密锁内的数据文件
        Args:
            file_id: 文件ID
            offset: 文件偏移。文件读取的起始偏移

        Returns:

        """
        if self.is_open:  # 已经PIN码验证通过
            base_offset, data_length = self._pre_read_file(file_id)  # '0004', '0053'
            base_offset = int(base_offset)
            data_length = int(data_length)
            p_out_data = (c_ubyte*data_length)()
            ret = self.hinst.DON_ReadFile(self.handle, file_id, offset+base_offset, p_out_data, data_length)
            if ret == 0:  # 读取成功
                res = ''
                for i in range(data_length):
                    value = hex(p_out_data[i])[2:]
                    res += padding_hex(value)
                self.base_info = BaseInfo(res)
                print(self.base_info)
            else:
                raise PyUKeyException(f'读取数文件失败，返回码为{ret}')
        else:
            raise PyUKeyException('请先同UKey建立连接')

    def _pre_read_file(self, file_id: hex):
        """
        数据文件读取的需要读两次的第一次读取，从0偏移开始读4个字节，返回数据的起始偏移地址和数据的长度
        Args:
            file_id: 文件ID

        Returns:
            base_addr: hex
            data_size: int
        """
        if self.is_open:
            offset = 0
            p_outdata = (c_ubyte * 4)()
            data_len = 4
            ret = self.hinst.DON_ReadFile(self.handle, file_id, offset, p_outdata, data_len)
            if ret == 0:  # 读取成功
                base_offset = f'{padding_hex(p_outdata[0])}{padding_hex(p_outdata[1])}'  # 偏移量
                data_length = f'{padding_hex(p_outdata[2])}{padding_hex(p_outdata[3])}'  # 数据长度
                return base_offset, data_length
            else:
                raise PyUKeyException(f'读取数文件失败，返回码为{ret}')
        else:
            raise PyUKeyException('请先同UKey建立连接')

    def _parse_license(self, value: str):
        """
        解析UKey返回的license数据
        解析规则
            长度： 2字节
            可执行程序运行结果： 1字节
            license数量： 1字节
            data：
                组件ID-1：2字节
                license-1：128字节
                组件ID-2：2字节
                license-2：128字节
                ...
        Args:
            value:

        Returns:

        """
        # 信息长度
        length_data = value[:4]
        assert int(length_data, 16) == int((len(value) - 4) / 2), f'license长度校验不通过{value}'
        # 程序运行结果
        pro_ret = value[4:6]
        assert pro_ret == '00', f'从license通信结果判断程序运行不成功:{value}'
        # license数量
        counts_license = int(value[6:8], 16)
        data = value[8:]
        for i in range(counts_license):
            component_id = data[:4]
            license = data[4:260]
            self.license.append((component_id, license))
            data = data[260:]

    def get_license(self, hid: str):
        """
        输入HID，根据base_info获取的算法类型，调用对应的算法生成license
        Args:
            hid: str, eg: "2B0030001151363136343732"

        Returns:
            license: str

        """
        if not self.is_open:
            raise PyUKeyException('请先同UKey建立连接')
        if self.is_connected:  # 验证PIN码成功之后才能调用算法
            length_hid = int(len(hid) / 2)
            buf = (c_ubyte*(0x400))()  # 构造内存空间接收值
            nDataLen = c_int(0x400)  # 数据大小同buf大小一致
            pMainRet = (c_int * 1)()  # 接收执行结果
            buf[0] = length_hid
            # 构建传入的hid数据
            hid_bytes = strhextobytes(hid)
            for i in range(1, length_hid+1):
                buf[i] = hid_bytes[i-1]

            # 调用可执行程序生成license
            ret = self.hinst.DON_RunExeFile(self.handle, int(self.base_info.algorithm_type),
                                            buf, nDataLen, pMainRet)
            if ret == 0 and pMainRet[0] == 0:
                res = ''
                length_res = (buf[0]<<8) | buf[1]
                for i in range(length_res + 2):
                    value = hex(buf[i])[2:]
                    res += padding_hex(value)
                self._parse_license(res)
            else:
                raise PyUKeyException(f'调用可执行程序生成license错误,结果码为{ret&0xffffffff}, {pMainRet[0]}')
        else:
            raise PyUKeyException('请先进行PIN码验证')

    def close(self):
        """关闭UKey连接"""
        print('关闭UKey连接')
        if self.is_open:
            self.hinst.DON_Close(self.handle)
            self.is_open = False
            self.is_connected = False
            self.handle = None

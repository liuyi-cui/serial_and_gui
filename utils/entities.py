# -*- coding: utf-8 -*-
"""
实体类
"""
import tkinter as tk
from collections import namedtuple
from enum import Enum


HEAD = slice(0, 2)  # 帧头
PAYLOAD_LENGTH = slice(2, 6)  # payload长度
PAYLOAD_DATA_ = slice(6, -2)  # payload data
COMMAND = slice(6, 10)  # 指令
DATA_LENGTH = slice(10, 14)  # 数据长度
COMPONENT_ID = slice(14, 18)  # 组件id
DATA = slice(18, -2)  # 数据
CHECK_SUM = slice(-2, None, None)  # 校验和
BoardProtocol = namedtuple('BoardProtocol', ['head', 'payload_length', 'payload_data', 'check_sum'])  # 上位机-开发板通信协议
PayloadData = namedtuple('Payload', ['command', 'data_length', 'component_id', 'data'])  # payload组成


class ProtocolCommand(Enum):
    """
    通信协议的cmd指令
    两个字节，无符号16位数
        高八位目前保留，以后扩展用
        低八位中
            高两位为报文类型
                00 request 请求报文，一方发出请求，对端必须根据报文指令返回响应信息.包含数据和结果。一段时间后还未收到相关信息，则标识此次通信失败
                01 non 非响应性报文，一方发出报文，对端根据指令执行响应操作。但不必返回信息
                10 response 应答指令，收到对端request报文后，做出的应答。但不要求对端回复信息
                11 ret 复位报文，当一端发出request报文，如果报文中出现上下文缺失，导致无法处理时，对端将返回一个RST报文
            中间两位保留
            低四位为具体指令
                0001
                    请求hid指令。为上位机发出。具体指令为 请求报文00 + 两位保留00 + 0001。
                    回复hid指令。为设备发出的响应信息。具体指令为 应答指令10 + 两位保留00 + 0001
                0010
                    license烧写指令。为上位机发出。具体指令为 请求报文00 + 两位保留00 + 0010
                    回复license烧写指令。为设备发出的响应信息。具体指令为 应答指令10 + 两位保留00 + 0010
                0011  该条指令为在线方案，等待的是平台侧的回复
                    license申请指令。为设备端发出，会等待响应。具体指令为 请求报文00 + 两位保留00 + 0011
                0100
                    license存储分区擦除指令。为上位机发出，必须含有component ID。具体指令为 请求报文00 + 两位保留00 + 0100
                    回复license擦除指令结果。为设备端发出，含有component ID。具体指令为 应答报文10 + 两位保留00 + 0100
    """
    hid_request = '0001'  # 请求hid指令。上位机发出
    hid_response = '0081'  # 回复hid指令。设备端发出
    license_put_request = '0002'  # license烧写指令。上位机发出
    license_put_response = '0082'  # 回复license烧写指令。设备端发出
    license_get_request = '0003'  # license申请指令。设备端发出  TODO设备端什么情况会发出该条指令
    license_clean_request = '0004'  # license存储分区擦除指令。上位机发出 TODO
    license_clean_response = '0084'  # 回复license擦除指令结果
    reset_response = '00c0'  # 复位 因为某些错误，端侧返回复位命令


class DataError(Enum):
    """
    License的校验信息
    """

    LICENSE_PROCESS_OK = '00'
    LICENSE_READ_HID_FAIL = '01'
    LICENSE_CPID_NOT_MATCH = '02'
    LICENSE_NULL_POINTER = '03'
    LICENSE_LIC_SIZE_INVALID = '04'
    LICENSE_SM4_INIT_FAIL = '05'
    LICENSE_DECRYPT_FAIL = '06'
    LICENSE_BODY_LEN_INVALID = '07'
    LICENSE_HID_VERIFY_FAIL = '08'
    LICENSE_PARA_NOT_ENOUGH = '09'
    LICENSE_CPID_NONE_TABLE = '0A'
    LICENSE_FLASH_PART_INVALID = '0B'
    LICENSE_MAGIC_MALLOC_FAIL = '0C'
    LICENSE_MAGIC_READ_FAIL = '0D'
    LICENSE_MAGIC_WRITE_FAIL = '0E'
    LICENSE_FLASH_ERASE_FAIL = '0F'
    LICENSE_WRITE_FAIL = '10'
    LICENSE_READ_POINTER_NULL = '11'
    LICENSE_READ_FAIL = '12'
    LICENSE_UART_NO_HEADER = '14'
    LICENSE_UART_RECV_TIMEOUT = '15'
    LICENSE_UART_CHECK_SUM_FAIL = '16'
    LICENSE_CMD_ERR = '17'


Error_Data_Map = {i.value: i.name for i in DataError.__members__.values()}


class DisplayInfoEntity:
    """
    记录展示信息
    """

    def __init__(self, operate_type: str):
        self.operate_type = operate_type  # 操作状态(读HID/写License)
        self.port = ''  # 串口号
        self.file_path = ''  # HID存储文件/license记录文件


class ModeEnum(Enum):
    """模式"""
    PRODUCT = 'PRODUCT'  # 生产模式
    DEBUG = 'DEBUG'  # 调试模式


class OperateEnum(Enum):
    """工位"""
    HID = 'HID'  # 读HID
    LICENSE_FILE = 'LICENSE_FILE'  # 通过文件写License
    LICENSE_UKEY = 'LICENSE_UKEY'  # 通过UKey写License


class ConnType:
    """通信方式"""
    def __init__(self):
        self.conn_type = tk.StringVar()
        self.swith_to_port()

    def swith_to_jlink(self):
        self.conn_type.set('J-Link通信')

    def swith_to_port(self):
        self.conn_type.set('串口通信')


class SerialPortConfiguration:
    """串口通信配置项"""

    def __init__(self):
        self.port = ''  # 串口号
        self.baud_rate = '115200'  # 波特率
        self.data_digit = '8'  # 数据位
        self.check_digit = 'None'  # 校验位
        self.stop_digit = '1'  # 停止位
        self.stream_controller = 'None'  # 流控


class JLinkConfiguration:
    """J-Link通信配置项"""

    def __init__(self):
        self.serial_no = ''  # 仿真器序列号
        self.interface_type = 'JTAG'  # JTAG/SWD，默认JTAG
        self.rate = '4000'  # 传输速率，默认4000
        self.mcu = ''  # 芯片名称
        self.hid_addr = ''  # hid存储地址
        self.license_addr = ''  # license存储地址
        self.license_size_stored = ''  # license存储区域大小


class MCUInfo:
    """mcu相关信息"""

    def __init__(self):
        self.manufacturer = ''
        self.device = tk.StringVar()
        self.core = ''
        self.num_cores = 0
        self.flash_size = tk.StringVar()
        self.ram_size = ''

    def get_info(self, info: tuple):
        """

        Args:
            info: ('ST', 'STM32L475VG', 'Cortex-M0', '1', '1024 KB', '96 KB')

        Returns:

        """
        self.manufacturer = info[0]
        self.device.set(info[1])
        self.core = info[2]
        self.num_cores = info[3]
        self.flash_size.set(info[4])
        self.ram_size = info[5]

    def __str__(self):
        print(f'厂家: {self.manufacturer}')
        print(f'device: {self.device.get()}')
        print(f'core: {self.core}')
        print(f'num_cores: {self.num_cores}')
        print(f'flash大小: {self.flash_size.get()}')
        print(f'ram大小: {self.ram_size}')
        return ''


class LogConfiguration:
    """日志配置选项"""

    def __init__(self):
        self.is_open = tk.IntVar()  # 默认不开启日志记录
        self.log_path = tk.StringVar()  # 日志路径
        self.max_size = tk.StringVar()  # 日志大小上限


class UKeyInfo:
    """记录UKey信息"""

    def __init__(self):
        self.is_open = False  # 初始状态为未连接
        self.desc = tk.StringVar()
        self.desc_child = tk.StringVar()
        self.desc.set('未验证，请先使用UKey验证')
        self.desc_child.set('UKey验证')

    def update_connected(self, ukey_name):
        """
        建立连接后更新部分属性
        Args:
            ukey_name: TODO 此处表示ukey的名称还是用户名还是ukey占用的端口号呢

        Returns:

        """
        self.is_open = True
        self.desc = f'{ukey_name}：用户已认证'
        self.desc_child = '切换UKey'

    def close(self):
        self.__init__()


if __name__ == '__main__':
    mcu_info = MCUInfo()
    print(mcu_info)

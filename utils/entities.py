# -*- coding: utf-8 -*-
"""
实体类
"""
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


if __name__ == '__main__':
    pass

# -*- coding: utf-8 -*_
# 同设备通信协议相关的解析方法和组装方法

from utils.entities import *
from log import logger


class ProtocolHeadException(Exception):
    """协议帧头错误"""
    pass


class ProtocolException(Exception):
    """协议数据不符合规范、长度校验失败"""
    pass


class ProtocolSumException(Exception):
    """协议校验和校验失败"""
    pass


class ProtocolCommandException(Exception):
    """协议指令错误"""
    pass


def check_head(head: str) -> bool:
    """校验帧头"""
    if head != '5A':
        return False
    return True


def check_data_length(data_length: str, data: str) -> bool:
    """校验data长度"""
    data_length = int(data_length, 16)
    if data_length != len(data) / 2:
        return False
    return True


def check_check_sum(payload_data, check_sum) -> bool:
    """校验数据和校验和"""
    ret = calc_check_sum(payload_data)
    if ret != check_sum:
        return False
    return True


def parse_protocol(protocol_value: str):
    """
    将一条协议信息，解析为具体的帧头、长度、payload、校验和
    Args:
        protocol_value: 一条数据包

    Returns:
        board_protocol
    """
    logger.info(f'parse protocol: {protocol_value}')
    protocol_value = protocol_value.lower()
    if protocol_value.startswith('0x'):
        protocol_value = protocol_value.strip('0x')

    # 一条信息长度最小为10字节(帧头1长度2指令2长度2组件id2数据0校验和1)
    if len(protocol_value) < 20:
        raise ProtocolException(f'信息长度小于10字节')
    head = protocol_value[HEAD].upper()
    payload_length = protocol_value[PAYLOAD_LENGTH].upper()
    payload_data_ = protocol_value[PAYLOAD_DATA_].upper()
    command = protocol_value[COMMAND].upper()
    data_length = protocol_value[DATA_LENGTH].upper()
    component_id = protocol_value[COMPONENT_ID].upper()
    data = protocol_value[DATA].upper()
    check_sum = protocol_value[CHECK_SUM].upper()

    if not check_head(head):
        raise ProtocolHeadException(f'错误的帧头{head}')
    if not check_data_length(payload_length, payload_data_):
        raise ProtocolException('payload length校验不通过')
    if not check_data_length(data_length, component_id + data):
        raise ProtocolException('payload数据长度校验不通过')
    if not check_check_sum(payload_data_, check_sum):
        print(payload_data_, check_sum)
        raise ProtocolSumException('校验和校验不通过')
    payload_data = PayloadData(command, data_length, component_id, data)
    board_protocol = BoardProtocol(head, payload_length, payload_data, check_sum)
    return board_protocol


def assemble_fixedlength_data(data, length, padding='0'):
    """填充数据为指定长度"""
    data = data.lstrip('0x')
    if len(data) >= length:
        return data
    while len(data) < length:
        data = padding + data
    return data


def calc_check_sum(data: str) -> str:
    """
    计算校验和
    Args:
        data:

    Returns:

    """
    res = 0
    start_idx = 0
    for i in range(2, len(data) + 1, 2):
        res += int(data[start_idx:i], 16)
        start_idx = i

    temp_ret = hex(res)
    ret = temp_ret[-2:].replace('x', '0')
    return ret.upper()


def build_protocol(data, component_id='0000', command=ProtocolCommand.hid_request.value,
                   head='5a') -> bytes:
    """
    根据协议以及关键信息，组装一条数据包
    Args:
        data: 需要传输的数据 eg: 540049001350564846323020
        component_id: 组件id eg: 0000
        command: 指令类型 eg: 0081
        head: 帧头 eg: 5a

    Returns:
        数据包
    """
    data_length = assemble_fixedlength_data(hex(len(component_id+data) // 2), 4)  # 计算数据长度，组装为2个字节
    payload_data = command + data_length + component_id + data
    payload_data_length = assemble_fixedlength_data(hex(len(payload_data) // 2), 4)  # 负载长度，组装为2个字节
    check_num = calc_check_sum(payload_data)
    protocol_package = head + payload_data_length + command + data_length + component_id + data + check_num
    return protocol_package


def check_payload(payload, command_type: str) -> bool:
    """
    验证payload是否正确
    Args:
        payload: PayloadData
        command_type: ProtocolCommand.

    Returns:

    """
    if not hasattr(ProtocolCommand, command_type):
        raise ProtocolCommandException

    excepted_command = getattr(ProtocolCommand, command_type).value
    command = payload.command
    data = payload.data
    if command == excepted_command and data == DataError.LICENSE_PROCESS_OK.value:
        return True
    else:
        return False

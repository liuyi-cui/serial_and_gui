# -*- coding: utf-8 -*-
# 类型转换辅助方法
import base64
import binascii


def strhextob64(inputs):
    '''
    hex-string to base64-string
    Args:
        inputs:

    Returns:

    '''
    tmp = binascii.a2b_hex(inputs)
    result = str(base64.b64encode(tmp),'utf-8')
    return result


def strhextobytes(inputs):
    '''
    hex-string to bytes
    Args:
        inputs:

    Returns:

    '''
    result = binascii.a2b_hex(inputs)
    return result


def bytestostrhex(inputs):
    '''
    bytes to hex-string
    Args:
        inputs:

    Returns:

    '''
    return binascii.b2a_hex(inputs).decode('utf-8')


def bytestob64(inputs):
    '''
    bytes to base64-string
    Args:
        inputs:

    Returns:

    '''
    result = str(base64.b64encode(inputs),'utf-8')
    return result


def b64tobytes(inputs):
    '''
    base64-string to bytes
    Args:
        inputs:

    Returns:

    '''
    tmp = bytes(base64.b64decode(inputs).hex(), encoding = "utf8")
    result = binascii.a2b_hex(tmp)
    return result


def b64tostrhex(inputs):
    '''
    base64-string to hex-string
    Args:
        inputs:

    Returns:

    '''
    tmp = bytes(base64.b64decode(inputs).hex(), encoding="utf8")
    bytes_ = binascii.a2b_hex(tmp)
    result = bytestostrhex(bytes_)
    return result


if __name__ == '__main__':
    ret = b'Z\x00\x12\x00\x81\x00\x0e\x00\x00T\x00I\x00\x13PVHF20 \xf5'
    print(bytestostrhex(ret))
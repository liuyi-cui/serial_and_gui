# -*- coding: utf-8 -*-
# 其它辅助方法

import platform


def win64_or_win32():
    """
    判断当前环境是32位还是64位windows
    Returns:

    """
    system_ = platform.system()
    architecture_ = platform.architecture()
    if system_.upper() == 'WINDOWS' and architecture_[0] == '64bit':
        return 'win_64bit'
    elif system_.upper() == 'WINDOWS' and architecture_[0] == '32bit':
        return 'win_32bit'
    else:
        return None


def is_hex(value: str):
    """判断一个字符串是16进制字符串"""
    if not isinstance(value, str):
        value = str(value)
    standard = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f']
    if value.startswith('0x'):
        value = value[2:]
    for i in value:
        if i.lower() not in standard:
            return False
    return True


def padding_hex(value, pad='0', prefix=False):
    """填充16进制数，使其满足一个字节长度"""
    if isinstance(value, int):
        value = str(value)
    assert len(value) <= 2
    if len(value) == 1:
        if not prefix:
            return f'{pad}{value}'
        else:
            return f'0x{pad}{value}'
    if not prefix:
        return value
    else:
        return f'0x{value}'


if __name__ == '__main__':
    for i in ('0', '4', '53'):
        print(padding_hex(i))

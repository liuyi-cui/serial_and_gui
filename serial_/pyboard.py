# -*- coding: utf-8 -*-
# 串口操作类

import serial.tools.list_ports
import time

from log import logger
from serial_.conserial import ConSerial
from utils.convert_utils import strhextobytes, bytestostrhex
from utils.retry import retry
from utils.protocol_utils import parse_protocol, build_protocol


class PyBoardException(Exception):
    pass


class PyBoard:

    @retry(logger)
    def __init__(self, port: str, baudrate: int):
        self.con_serial = ConSerial()
        print(f'连接到开发板: {port} {baudrate}')
        self.open(port, baudrate)
        print(f'连接到开发板完成')
        self.is_open = False  # TODO 考虑使用场景
        self.__update_state()

    def __update_state(self):
        self.is_open = self.con_serial.is_open

    def open(self, port: str, baudrate: int):
        self.con_serial.open(port, baudrate)
        self.__update_state()

    def close(self):
        self.con_serial.close()
        self.__update_state()

    @retry(logger)
    def get_HID(self) -> str:  # TODO 添加日志
        """
        从端侧获取设备HID
        Returns:

        """
        hid_request = build_protocol('')
        command = strhextobytes(hid_request)
        self.con_serial.write(command)
        time.sleep(1)
        ret = None
        times = 1
        while not ret and times <= 4:
            size = self.con_serial.inWaiting()
            if size:
                ret = self.con_serial.read(size)  # TODO 分段读取
            else:
                print(f'第{times}次没有获取到数据')
                times += 1
                time.sleep(1)
        if ret is not None:
            return bytestostrhex(ret)
        return ret

    @retry(logger)
    def send_license(self, license: str) -> None:  # TODO 添加日志
        """
        将License发送到端侧
        Args:`
            license:

        Returns:

        """
        if license:
            # if len(license) % 2 != 0:
            #     raise PyBoardException('Odd-length string')
            license_byte = strhextobytes(license)  # TODO 奇偶判断
            self.con_serial.write(license_byte)  # 分批次写入

    @retry(logger)
    def confirm_license_correct(self) -> bool:  # TODO 添加日志
        """同端侧确认License校验是否成功"""  # TODO
        pass

    @retry(logger)
    def __record_HID_activated(self):
        """如果端侧License校验成功，则对该设备HID进行本地存储"""  # TODO
        pass

    @classmethod
    def get_list(cls):
        """获取串口列表"""
        port_list = serial.tools.list_ports.comports()
        port_list = [i.name for i in port_list]
        return port_list

    @retry(logger)
    def read_response(self):
        ret = None
        times = 1
        while not ret and times <= 4:
            size = self.con_serial.inWaiting()
            if size:
                ret = self.con_serial.read(size)  # TODO 分段读取
            else:
                print(f'第{times}次没有获取到数据')
                times += 1
                time.sleep(1)
        if ret is not None:
            return bytestostrhex(ret)
        return ret

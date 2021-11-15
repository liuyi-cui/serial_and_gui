# -*- coding: utf-8 -*-
# 串口操作类

import serial.tools.list_ports

from log import logger
from serial_.conserial import ConSerial
from utils.retry import retry


class PyBoardException(Exception):
    pass


class PyBoard:

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
        command = '发送请求HID的命令'.encode('utf-8')  # TODO 端侧对其请求HID的接口
        self.con_serial.write(command)
        ret = None
        while not ret:
            size = self.con_serial.inWaiting()
            if size:
                ret = self.con_serial.read(size)  # TODO 分段读取
        return ret.decode('utf-8')

    @retry(logger)
    def send_license(self, license: str) -> None:  # TODO 添加日志
        """
        将License发送到端侧
        Args:`
            license:

        Returns:

        """
        if license:
            license_byte = license.encode('utf-8')
            self.con_serial.write(license_byte)  # 分批次写入
            self.con_serial.write('\x04')  # 回车？\r\n?

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
        print(port_list)
        port_list = [i.name for i in port_list]
        return port_list

# -*- coding: utf-8 -*-
# 串口操作类

import serial.tools.list_ports
import time
import tkinter as tk

from utils.entities import ProtocolCommand
from log import logger
from serial_.conserial import ConSerial
from utils.convert_utils import strhextobytes, bytestostrhex
from utils.retry import retry
from utils.protocol_utils import parse_protocol, build_protocol


class PyBoardException(Exception):
    pass


class PyBoard:

    def __init__(self):
        self.con_serial = ConSerial()
        self.status = tk.StringVar()
        self.status.set('断开')

    @property
    def is_open(self):
        return self.con_serial.is_open

    @retry(logger)
    def open(self, port: str, baudrate: int, stopbits=1, parity='N',
             bytesize=8, rtscts=False, xonxoff=False):
        """
        连接串口
        Args:
            port: 串口号
            baudrate: 波特率
            stopbits: 停止位
            parity: 校验位
            bytesize: 数据位
            rtscts:
            xonxoff:

        Returns:

        """
        logger.info(f'连接串口 {port} {baudrate}, ')
        self.con_serial.open(port, baudrate, stopbits=stopbits, parity=parity,
                             bytesize=bytesize, rtscts=rtscts, xonxoff=xonxoff)
        self.status.set('已连接')

    def close(self):
        if self.is_open:
            self.con_serial.close()
            self.status.set('断开')

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
                logger.warning(f'第{times}次没有获取到数据')
                times += 1
                time.sleep(1)
        logger.info(f'get response {ret}')
        if ret is not None:
            return bytestostrhex(ret)
        return ret

    @retry(logger)
    def get_license(self):
        license_request = build_protocol('', command=ProtocolCommand.license_read_request.value)
        command = strhextobytes(license_request)
        self.con_serial.write(command)
        time.sleep(1)
        ret = None
        times = 1
        while not ret and times <= 4:
            size = self.con_serial.inWaiting()
            if size:
                ret = self.con_serial.read(size)  # TODO 分段读取
            else:
                logger.warning(f'第{times}次没有获取到数据')
                times += 1
                time.sleep(1)
        logger.info(f'get response {ret}')
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
            if len(license) % 2 != 0:
                logger.error('Odd-length string')
                raise PyBoardException('Odd-length string')
            license_byte = strhextobytes(license)
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
                logger.warning(f'第{times}次没有获取到数据')
                times += 1
                time.sleep(1)
        logger.info(f'get response {ret}')
        if ret is not None:
            return bytestostrhex(ret)
        return ret

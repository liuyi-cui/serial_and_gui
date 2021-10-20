# -*- coding: utf-8 -*-
# 串口操作类


from log import logger
from serial_.conseial import ConSerial
from utils.retry import retry


class PyBoard:

    def __init__(self, port: str, baudrate: int):
        self.con_serial = ConSerial()
        self.open(port, baudrate)
        self.is_open = False
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
        Args:
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

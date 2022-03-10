# -*- coding: utf-8 -*-
import pylink
from pathlib import Path

PROJ_PATH = Path(__file__).parent.parent
# DLL_PATH = r'D:\Projects\python\LicenseManagementTool\files\UKey\Python-x64\Don_API-x64.dll'
DLL_PATH = Path(PROJ_PATH, 'JLink_x64.dll').as_posix()


class JLinkCOMException(Exception):
    pass


class JLinkCOM:

    def __init__(self, logger=None):
        """

        Args:
            logger: str, 日志文件路径
        """
        lib_ = pylink.library.Library(dllpath=DLL_PATH)
        self.jlink = pylink.jlink.JLink(lib=lib_)  # 初始化jlink实例
        self.logger = logger

    @property
    def emulators(self):
        """获取当前连接的仿真器序列号"""
        emulators = self.jlink.connected_emulators()
        return [i.SerialNumber for i in emulators]

    @property
    def is_opened(self):
        return self.jlink.opened()

    @property
    def is_connected(self):
        return self.jlink.connected()

    @property
    def is_target_connected(self):
        return self.jlink.target_connected()

    def set_tif_swd(self):
        """更改接口连接方式为SWD"""
        self.jlink.set_tif(pylink.enums.JLinkInterfaces.SWD)

    def set_tif_jtag(self):
        """更改接口连接方式为JTAG"""
        self.jlink.set_tif(pylink.enums.JLinkInterfaces.JTAG)

    def set_speed(self, speed_value: int):
        """
        设置JTAG与ARM内核的通信速度
        Args:
            speed_value: 5-50000

        Returns:

        """
        try:
            self.jlink.set_speed(speed_value)
        except Exception as e:
            raise JLinkCOMException(e)


    def open(self, emulator: str):
        """连接仿真器"""
        try:
            self.jlink.open(emulator)
        except Exception as e:
            raise JLinkCOMException(e)
        if self.logger is not None:
            self.jlink.set_log_file(self.logger)

    def connect(self, chip_name: str):
        """同一个芯片建立连接"""
        if self.is_connected and self.is_opened:
            try:
                self.jlink.connect(chip_name)
            except Exception as e:
                raise JLinkCOMException(e)
        else:
            raise JLinkCOMException('请先连接仿真器')

    def erase(self):
        """擦除flash"""
        return self.jlink.erase()

    def halt(self):
        return self.jlink.halt()

    def flash_file(self, filepath: str, addr: hex):
        """
        下载文件到指定地址
        Args:
            filepath: 可烧录文件(.bin, .hex, ...)
            addr: 地址

        Returns:

        """
        try:
            self.jlink.flash_file(filepath, addr)
        except Exception as e:
            raise JLinkCOMException(e)

    def flash_write(self, addr: hex, data: list):
        """
        烧写指定数据到指定地址
        Args:
            addr: 指定地址
            data: 一个十进制数的列表，每一个元素表示一个字节，0-255

        Returns:

        """
        try:
            self.jlink.flash_write(addr, data)
        except Exception as e:
            raise JLinkCOMException(e)

    def memory_read(self, addr: hex, read_count: int) -> list:
        """
        指定地址进行读取
        Args:
            addr: 指定地址
            read_count: 读取字节数

        Returns:
            list, 一个十进制数的列表，每一个元素表示一个字节，0-255
        """
        try:
            ret = self.jlink.memory_read(addr, read_count)
        except Exception as e:
            raise JLinkCOMException(e)
        return ret






    def close(self):
        """断开连接"""
        self.jlink.close()


if __name__ == "__main__":
    print(DLL_PATH)

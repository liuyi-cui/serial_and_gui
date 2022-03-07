# -*- coding: utf-8 -*-
from serial import Serial

from log import logger
from utils.retry import retry


class ConSerial:

    def __init__(self):
        self.port = ''
        self.baudrate = 0
        self.con = None
        self.is_open = False

    @retry(logger)
    def __open(self, port, baudrate, stopbits, parity, bytesize, rtscts, xonxoff):
        logger.info(f'connect to {port} {baudrate}')
        con = Serial(baudrate=baudrate,
                     stopbits=stopbits,
                     parity=parity,
                     bytesize=bytesize,
                     rtscts=rtscts,
                     xonxoff=xonxoff,
                     interCharTimeout=1,
                     timeout=2)
        con.port = port
        con.open()
        return con

    def open(self, port: str, baudrate: int, stopbits=1, parity='N',
             bytesize=8, rtscts=False, xonxoff=False):
        self.port = port
        self.baudrate = baudrate
        self.con = self.__open(port, baudrate, stopbits=stopbits, parity=parity,
                               bytesize=bytesize, rtscts=rtscts, xonxoff=xonxoff)
        self.is_open = True

    def close(self):
        if self.is_open:
            self.con.close()

    def inWaiting(self):
        if self.is_open:
            return self.con.inWaiting()

    def read(self, size) -> bytes:
        if self.is_open:
            logger.debug(f'read size {size}')
            data = self.con.read(size)
            logger.debug(f'read data < {data}')
            return data

    def write(self, data: bytes):
        if self.is_open:
            logger.debug(f'write > {data}')
            self.con.write(data)

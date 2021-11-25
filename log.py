# -*- coding; utf-8 -*-

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path

FILE_NAME = 'license management tool.log'
FORMAT = '%(asctime)s %(thread)d %(threadName)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'


def init_log():
    log_dir = Path(Path(__file__).parent, 'log')
    if not log_dir.exists():
        os.mkdir(log_dir)
    return Path(log_dir, FILE_NAME)


class Logger:

    def __init__(self, format=FORMAT, level=logging.INFO):
        file_name = init_log()
        self.logger = logging.getLogger()
        self.logger.addHandler(self.__get_filehandler(file_name, format))
        self.logger.setLevel(level)

    @staticmethod
    def __get_filehandler(file_name, format):
        handler_ = RotatingFileHandler(filename=file_name,
                                       mode='a',
                                       maxBytes=5 * 1024 * 1024,
                                       backupCount=5,
                                       encoding='utf-8')
        formatter = logging.Formatter(format)
        handler_.setFormatter(formatter)
        return handler_

    def __call__(self, *args, **kwargs):
        return self.logger


class OperateLogger():

    def __init__(self):
        self.logger = logging.getLogger()

    def add_hander(self, filename, max_bytes):
        handler_ = RotatingFileHandler(filename=filename,
                                       mode='a',
                                       maxBytes=max_bytes,
                                       backupCount=2,
                                       encoding='utf-8')
        formatter = logging.Formatter(FORMAT)
        handler_.setFormatter(formatter)
        self.logger.addHandler(handler_)
        self.logger.setLevel(logging.INFO)


logger = Logger()()

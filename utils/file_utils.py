# -*- coding: utf-8 -*-
import os
import pandas as pd

from log import logger


def store_HID(hids: list, file_path: str):  # TODO
    """存储批量HID到本地"""
    
    hids_df = pd.DataFrame(columns=['设备标志'], data=hids)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f'{file_path} not exists')
    with pd.ExcelWriter(file_path, mode='w') as exfp:
        hids_df.to_excel(exfp, sheet_name='HID')
    logger.info(f'store {len(hids)} success')


def read_license_by_HID(hid: str) -> list:  # TODO 首先需要将映射文件读到内存中来，否则每一次取一次HID，都需要读一次文件
    """根据HID, 从HID-License map表中获取对应的License,
    返回[HID-组件ID-License, ...]的列表"""
    pass


def record_HID_activated(hid: str) -> None:  # TODO
    """存储HID到指定本地文件"""
    pass

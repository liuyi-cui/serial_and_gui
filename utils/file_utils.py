# -*- coding: utf-8 -*-
import os
import pandas as pd

from log import logger


def store_HID(hids: list, file_path=r'D:\Projects\python\LicenseManagementTool\output\HID.xls'):
    """存储批量HID到本地"""

    hids_df = pd.DataFrame(columns=['设备标志'], data=hids)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f'{file_path} not exists')
    with pd.ExcelWriter(file_path, mode='w') as exfp:
        hids_df.to_excel(exfp, sheet_name='HID')
    logger.info(f'store {len(hids)} success')


def record_HID_activated(hid: str, file_path) -> None:  # TODO
    """存储HID到指定本地文件"""
    pass

# -*- coding: utf-8 -*-
import os
import pandas as pd
from pathlib import Path

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


def check_file_suffix(file_name, suffix_='excel') -> bool:
    """
    校验文件名后缀
    Args:
        file_name: str/Path, 文件名称
        suffix_: 所需要的文件类型

    Returns:
        True: 校验通过，文件后缀合格
        False: 校验失败，文件后缀不合格
    """
    real_suffix = Path(file_name).suffix
    print(f'后缀：{real_suffix}')
    if suffix_ == 'excel':
        if real_suffix in ('.xlsx', '.xls'):
            return True
        return False

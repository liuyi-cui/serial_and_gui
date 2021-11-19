# -*- coding: utf-8 -*-
import os
import pandas as pd
from pathlib import Path

from log import logger


HID_COLUMN_NAME = 'HID'


def store_HID(hids: list, file_path: Path):
    """存储批量HID到本地"""

    hids_df = pd.DataFrame(columns=[HID_COLUMN_NAME], data=hids)

    if file_path.exists():
        df_ed = pd.read_excel(file_path, sheet_name='Sheet1')
        hids_df = df_ed.append(hids_df)
    with pd.ExcelWriter(file_path, mode='w', engine='openpyxl') as writer:
        hids_df.to_excel(writer, index=False, sheet_name='Sheet1')


def record_HID_activated(hid: str, file_path: Path) -> None:  # TODO
    """存储HID到指定本地文件"""
    logger.info(f'记录hid{hid}到{file_path}')
    df = pd.DataFrame({HID_COLUMN_NAME: hid}, index=[0])
    if file_path.exists():
        df_ed = pd.read_excel(file_path, sheet_name='Sheet1')
        df = df_ed.append(df)
    with pd.ExcelWriter(file_path, mode='w', engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')


def read_HID(file_path: str) -> list:
    """
    读取file_path中的HID数据
    Args:
        file_path: str, hid.xlsx文件路径

    Returns:

    """
    df_ed = pd.read_excel(file_path, sheet_name='Sheet1', engine='openpyxl')
    hids = df_ed[HID_COLUMN_NAME].values.tolist()
    return hids


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

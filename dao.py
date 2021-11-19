# -*- coding: utf-8 -*-
import os
import pandas as pd

from utils.file_utils import store_HID


HID_COLUMN_NAME = 'HID(hex string)'
COMPONENT_COLUMN_NAME = 'Component ID(hex string)'
LICENSE_COLUMN_NAME = 'License(base64 string)'


class HIDDao:
    """
    存储HID
    """
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance:
            return cls.__instance
        return super().__new__(cls)

    def __init__(self):
        if not HIDDao.__instance:
            self.hid_list = []
            HIDDao.__instance = self

    def store(self) -> None:
        """
        存储hid到本地
        Returns:
            None
        """
        if self.hid_list:
            store_HID(self.hid_list)

    def add(self, hid):
        """添加hid"""
        self.hid_list.append(hid)

    def clear(self):
        """清空hid"""
        self.hid_list = []


class HID_License_Map:

    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance:
            return cls.__instance
        return super().__new__(cls)

    def __init__(self, file_path: str):
        if not HID_License_Map.__instance:
            self.file_path = file_path  # 映射文件地址
            self.hids = []
            self.hid_license_map = dict()
            self._load()
            HID_License_Map.__instance = self

    def _load(self):
        """
        读取HID-LICENSE映射文件，以{HID1: {组件标志1: license1,组件标志2: license2, ...},
                                 HID2: {组件标志1: license1,组件标志2: license2, ...},
                                 ...}方式存储
        Returns:
            None

        """
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f'{self.file_path} not exists')
        df = pd.read_excel(self.file_path, sheet_name='Sheet1', dtype=str)
        assert sum(sum(pd.isnull(df).values)) == 0, f'{self.file_path}有空值，请检查文件完整性'
        self.hids = df[HID_COLUMN_NAME].tolist()
        for hid in self.hids:
            components = df[df[HID_COLUMN_NAME] == hid][COMPONENT_COLUMN_NAME].tolist()  # 组件标识
            licenses = df[df[HID_COLUMN_NAME] == hid][LICENSE_COLUMN_NAME].tolist()  # licenses号
            self.hid_license_map.update(
                {hid: dict(zip(components, licenses))}
            )

    def get_license(self, hid: str) -> dict:
        """
        根据HID 获取对应的license
        Args:
            hid:

        Returns:
            {组件标志1: license1, 组件标志2: license2, ...}

        """
        licenses = self.hid_license_map.get(hid)
        if licenses:
            return licenses
        else:
            return {}

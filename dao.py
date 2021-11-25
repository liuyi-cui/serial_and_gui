# -*- coding: utf-8 -*-
import os
import pandas as pd

from utils.file_utils import store_HID


HID_COLUMN_NAME = '设备HID'
TIPS_COLUMNS_NAME = '提示'
LICENSE_FILE_SHEET_NAME = '设备license.xls'


class DaoException(Exception):
    pass


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
            self.licenses_counts = 0
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
        df = pd.read_excel(self.file_path, sheet_name=LICENSE_FILE_SHEET_NAME, dtype=str)
        self.hids = df[HID_COLUMN_NAME].tolist()
        components_columns = self._get_components_columns(df)
        self.licenses_counts = self._calc_license_counts(df, components_columns)
        for hid in self.hids:
            component_license_map = dict()
            for component_name in components_columns:
                if component_name.find('/') == -1:
                    raise DaoException('license文件中组件列中组件名和组件id需要用斜杠/分隔')
                component_id = component_name.split('/')[-1]
                license = df[df[HID_COLUMN_NAME] == hid].iloc[0,][component_name]
                component_license_map.update({component_id: license})
            self.hid_license_map.update({hid: component_license_map})

    def _get_components_columns(self, df):
        """获取组件标识列名称"""
        columns = df.columns.tolist()
        components_columns = set(columns) - set([HID_COLUMN_NAME, TIPS_COLUMNS_NAME])
        return components_columns

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

    def _calc_license_counts(self, df, components_columns):
        """计算components_columns列非空值个数，即为license个数"""
        return sum(df[list(components_columns)].notnull().sum())

# -*- coding: utf-8 -*-
import os
import pandas as pd

from utils.file_utils import store_HID


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

    def __init__(self, file_path: str):
        self.file_path = file_path  # 映射文件地址
        print(f'file_path: {file_path}')
        self.hids = []
        self.hid_license_map = dict()
        self._load()

    def _load(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f'{self.file_path} not exists')
        df = pd.read_excel(self.file_path, sheet_name='license表', dtype=str)
        assert sum(sum(pd.isnull(df).values)) == 0, f'{self.file_path}有空值，请检查文件完整性'
        self.hids = df['设备标志'].tolist()
        for hid in self.hids:
            components = df[df['设备标志'] == hid]['服务标志'].tolist()  # 组件标识
            licenses = df[df['设备标志'] == hid]['license号'].tolist()  # licenses号
            self.hid_license_map.update(
                {hid: dict(zip(components, licenses))}
            )


if __name__ == "__main__":
    file_path = r'input\1022 license表.xls'
    print(os.path.exists(file_path))





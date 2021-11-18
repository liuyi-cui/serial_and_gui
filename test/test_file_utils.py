# -*- coding: utf-8 -*-
# utils/file_utils相关方法测试
import os
from pathlib import Path
from utils.file_utils import record_HID_activated, store_HID, read_HID


class TestFileUtils:

    def test_record_hid(self):
        file_path = Path(__file__).parent.parent / 'output' / 'test_hid.xlsx'
        hids = ['35D9C0AE729DB9E1', '35D9C0AE729DB9E2', '35D9C0AE729DB9E3', '35D9C0AE729DB9E4']
        for hid in hids:
            record_HID_activated(hid, file_path)

    def test_store_hid(self):
        file_path = Path(__file__).parent.parent / 'output' / 'test_hid.xlsx'
        hids = ['35D9C0AE729DB9E1', '35D9C0AE729DB9E2', '35D9C0AE729DB9E3', '35D9C0AE729DB9E4']
        store_HID(hids, file_path)

    def test_read_hid(self):
        file_path = Path(__file__).parent.parent / 'output' / 'test_hid.xlsx'
        if file_path.exists():
            os.remove(file_path)
        hids = ['35D9C0AE729DB9E1', '35D9C0AE729DB9E2', '35D9C0AE729DB9E3', '35D9C0AE729DB9E4']
        store_HID(hids, file_path)
        record_hids = read_HID(file_path)
        assert hids == record_hids

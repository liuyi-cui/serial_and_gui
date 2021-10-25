# -*- coding: utf-8 -*-
from dao import HID_License_Map


class TestHidLicenseMap:

    def setup(self, file_path=r'D:\Projects\python\LicenseManagementTool\input\1022 license表.xls'):
        self.hid_licese_map = HID_License_Map(file_path)

    def test_read(self):
        hid_license_map = self.hid_licese_map.hid_license_map
        assert hid_license_map == {
            'cab4afd5-40d4-40f0-a3cf-a004ef29069c': {
                'RTC': '12122eweewee',
            },
            'cab4afd5-40d4-4032320-a3cf-a004ef29069c': {
                'POS': '12122ewe212'
            }
        }

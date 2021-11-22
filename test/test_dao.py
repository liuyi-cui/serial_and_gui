# -*- coding: utf-8 -*-
# dao.py相关测试


from dao import HID_License_Map


hid_license_map_filepath = r'D:\Projects\python\LicenseManagementTool\input\hid-license.xlsx'


class TestDao:

    def setup(self):
        self.hid_license_map = HID_License_Map(hid_license_map_filepath)

    def test_get_license(self):
        hid = '35D9C0AE729DB9E0'
        license = self.hid_license_map.get_license(hid)
        print(license)
        # assert license == {
        #     '03E8': '8jqXWK53tuik3NWhgjR2B5nEIUZzH/JLS+/QiMEiJxgKQYrRefZTQeugseljx04nnCqiHGgvVorDbnmXN0BW9RPYIvkdnQWrJpzDbnmXN0BW9RPYIvkdnQWrJpyR2dBQ',
        #     '03E9': '8jqXWK53tuik3NWhgjR2B5nEIUZzH/JLS+/QiMEiJxgKQYrRefZTQeugseljx04nnCqiHGgvVorDbnmXN0BW9RPYIvkdnQWrJpzDbnmXN0BW9RPYIvkdnQWrJpyR9dBQ'
        # }

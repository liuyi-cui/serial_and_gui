# -*- coding: utf-8 -*-
"""
针对protocol解析和组装的相关方法测试
"""


from utils.protocol_utils import parse_protocol, build_protocol, check_payload


class TestProtocol:

    def test_parse_hid_request(self):
        package_value = '5a000600010002000003'
        board_protocol = parse_protocol(package_value)
        payload_data = board_protocol.payload_data
        assert payload_data.command == '0001'
        assert payload_data.data_length == '0002'
        assert payload_data.component_id == '0000'
        assert payload_data.data == ''
        assert board_protocol.head == '5a'
        assert board_protocol.payload_length == '0006'
        assert board_protocol.check_sum == '03'
        print(f'针对{package_value}解析并校验成功')

    def test_parse_hid_response(self):
        package_value = '5A00120081000E0000540049001350564846323020F5'
        board_protocol = parse_protocol(package_value)
        payload_data = board_protocol.payload_data
        assert payload_data.command == '0081'
        assert payload_data.data_length == '000e'
        assert payload_data.component_id == '0000'
        assert payload_data.data == '540049001350564846323020'
        assert board_protocol.head == '5a'
        assert board_protocol.payload_length == '0012'
        assert board_protocol.check_sum == 'f5'
        print(f'针对{package_value}解析并校验成功')

    def test_build_hid_request(self):
        data = ''
        package_value = build_protocol(data)
        print(f'\npackage_value: {package_value}')
        assert package_value == '5a000600010002000003'

    def test_build_hid_response(self):
        data = '540049001350564846323020'
        command = '0081'
        package_value = build_protocol(data, command=command)
        print(f'\npackage_value: {package_value}')
        assert package_value == '5A00120081000E0000540049001350564846323020F5'.lower()

    def test_parse_protocol(self):
        # data = '5A000e0081000a000035D9C0AE729DB9E0AF'
        # data = '5A000E0081000A0000F3097F67D2B14F2D6C'
        # data = '5A06010203'
        data = '5a000c0084000800000101d2078000e7'
        board_protocol = parse_protocol(data)
        payload_data = board_protocol.payload_data
        print('\n')
        print('command', payload_data.command)
        print('data_length', payload_data.data_length)
        print('component_id', payload_data.component_id)
        print('data', payload_data.data)
        print('head', board_protocol.head)
        print('payload_length', board_protocol.payload_length)
        print('check_sum', board_protocol.check_sum)

    def test_build_license_protocol(self):
        """组装查询设备license烧写情况的通信协议"""
        data = ''
        command = '0004'
        package_value = build_protocol(data, command=command)
        print(package_value)





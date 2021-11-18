# -*- coding: utf-8 -*-
"""
针对protocol解析和组装的相关方法测试
"""


from utils.protocol_utils import parse_protocol, build_protocol


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
        payload_data = board_protocol
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

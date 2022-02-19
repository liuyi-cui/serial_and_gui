# -*- coding: utf-8 -*-
"""GUI操作界面"""
import tkinter as tk
import tkinter.messagebox  # 弹窗
from collections import namedtuple
from datetime import datetime
from tkinter import ttk
from tkinter import filedialog

from serial_.pyboard import PyBoard
from utils.entities import ModeEnum, OperateEnum, ConnEnum  # 操作方式、工位、通信方式
from utils.entities import SerialPortConfiguration, JLinkConfiguration, LogConfiguration, MCUInfo  # 串口配置项，JLink配置项，日志配置项，MCU信息
from utils.utility import is_hex

_font_s = ('微软雅黑', 8)  # 字体
_font_b = ('微软雅黑', 12)  # 字体
_active_color = 'gray'  # 激活状态颜色为浅灰色
SIZE_POPUPS = (400, 280)  # 弹出窗体大小


def center_window(win, width=None, height=None):
    """窗口居中"""
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    if width is None:
        width, height = get_window_size(win)[:2]
    print(f'screen width:{screen_width}, screen height:{screen_height}, '
          f'width: {width}, height: {height}')
    size = '%dx%d+%d+%d' % (width, height, (screen_width - width)/2, (screen_height - height)/3)
    win.geometry(size)
    win.resizable(0, 0)  # 设置窗口大小不可改变


def get_window_size(win, update=True):
    """获取窗体的大小"""
    if update:
        win.update()
    return win.winfo_width(), win.winfo_height(), win.winfo_x(), win.winfo_y()


class OneOsGui:

    def __init__(self):
        self.window_ = tk.Tk()
        center_window(self.window_, 950, 660)
        self.window_.title('OneOS License管理工具')
        self.window_.grab_set()
        self.init_types()  # 初始化对象属性
        self.init_values()  # 初始化对象属性值
        self.body()  # 绘制初始界面
        self.window_.pack_propagate(True)

    def init_types(self):
        """定义属性类型"""
        self.__mode_type = tk.StringVar()  # 模式选择(生产模式/调试模式)
        self.__operate_type = tk.StringVar()  # 操作工位(读HID/写License-从License文件/写License-从UKey)
        self.__conn_type = tk.StringVar()  # 通信方式(串口/J-Link)
        self.temp_mcu_info = ()

    def init_values(self):
        """定义属性初始值"""
        self.__mode_type.set('product')  # 默认模式选择为生产模式
        self.__operate_type.set('hid')  # 默认操作工位为读HID
        self.__conn_type.set('serial_port')  # 默认通信方式为串口通信
        self.__serial_port_configuration = SerialPortConfiguration()  # 串口通信数据
        self.__jlink_configuration = JLinkConfiguration()  # J-Link通信数据
        self.__log_configuration = LogConfiguration()  # 日志配置数据
        self.__mcu_info = MCUInfo()  # mcu相关信息

    def port_configuration_confirm(self, cb_port, cb_baudrate, cb_data, cb_check, cb_stop, cb_stream_controller, parent=None):
        """
        串口配置确定按钮触发方法()
        TODO 此处需要获取各个下拉框的值，因此_draw_serial_port_configuration应该返回各个cb
        针对各个下拉框的值，做合理性校验
        校验成功之后，记录各个下拉框的值(需要在几个地方共享)
        """
        def inner():
            print('串口配置确定按钮触发方法')
            port = cb_port.get()
            # 获取串口号
            if port:
                self.__serial_port_configuration.port = port
            print(f'串口号: {port}')
            # 获取波特率
            baudrate = cb_baudrate.get()
            if (isinstance(baudrate, int) or baudrate.isdigit()) and int(baudrate) > 0:
                self.__serial_port_configuration.baud_rate = baudrate
                print(f'波特率:{baudrate}')
            else:
                tkinter.messagebox.showwarning(title='Warning', message='波特率需要为正整数')
                return
            # 获取数据位
            data_digit = cb_data.get()
            self.__serial_port_configuration.data_digit = data_digit
            print(f'数据位: {data_digit}')
            # 获取校验位
            check_digit = cb_check.get()
            self.__serial_port_configuration.check_digit = check_digit
            print(f'校验位: {check_digit}')
            # 获取停止位
            stop_digit = cb_stop.get()
            self.__serial_port_configuration.stop_digit = stop_digit
            print(f'停止位: {stop_digit}')
            # 获取流控
            stream_controller = cb_stream_controller.get()
            self.__serial_port_configuration.stream_controller = stream_controller
            print(f'流控： {stream_controller}')
            if parent is not None:
                parent.destroy()
        return inner

    def jlink_configuration_confirm(self, cb_serial_no, cb_interface_type, cb_rate, entry_mcu, entry_license_addr,
                                    entry_license_size, parent=None):
        """
        J-Link配置项确定按钮触发方法
        针对各个下拉框的值，做合理性校验
        校验成功之后，记录各个下拉框的值(需要在几个地方共享)
        Args:
            cb_serial_no: 连接端口控件(下拉框)
            cb_interface_type: 接口类型控件(下拉框)
            cb_rate: 传输速率控件(下拉框)
            entry_mcu: 芯片类型控件(Entry)
            entry_license_addr: license存储地址控件(Entry)
            entry_license_size: license最大存储空间(Entry)
            parent: 父界面，有或者没有

        Returns:

        """
        def inner():
            print('J-Link配置确定按钮触发方法')
            # 仿真器序列号
            serial_no = cb_serial_no.get()
            if not serial_no:
                tkinter.messagebox.showwarning(title='连接端口', message='未选择仿真器序列号')
                return
            self.__jlink_configuration.serial_no = serial_no
            # 接口类型
            interface_type = cb_interface_type.get()
            self.__jlink_configuration.interface_type = interface_type
            # 速率
            rate = cb_rate.get()
            if (isinstance(rate, int) or rate.isdigit()) and int(rate) > 0:
                self.__jlink_configuration.rate = rate
            else:
                tkinter.messagebox.showwarning(title='速率(kHZ)', message='传输速率需要为正整数')
                return
            # MCU
            self.__jlink_configuration.mcu = self.__mcu_info.device
            # license存储地址
            license_addr = entry_license_addr.get()  # 16进制的字符
            if not is_hex(license_addr):
                tkinter.messagebox.showwarning(title='License存储地址', message='请输入正确的16进制字符')
                return
            self.__jlink_configuration.license_addr = license_addr
            # license可存储空间大小
            license_size = entry_license_size.get()  # 判断是纯数字就可以
            if (isinstance(license_size, int) or license_size.isdigit()) and int(license_size) > 0:
                self.__jlink_configuration.license_size_stored = license_size
            else:
                tkinter.messagebox.showwarning(title='license存储区域大小', message='需要为正整数')
                return
            if parent is not None:
                parent.destroy()
        return inner

    def mcu_configuration_confirm(self, parent):
        """芯片选择界面确定按钮触发方法
        如果mcu_info有值，则替换掉实例的mcu属性
        关闭界面
        """
        def inner():
            if self.temp_mcu_info:
                # 不需要进行校验，因此直接赋值
                self.__mcu_info.get_info(self.temp_mcu_info)
                self.temp_mcu_info = ()
                print(self.__mcu_info)
            parent.destroy()
        return inner

    def _draw_serial_port_configuration(self, parent):  # 给定界面，绘制串口通信配置项 TODO 还可以添加字体大小、padx、pady等参数
        """给定界面，绘制串口通信配置项"""
        # 串口号
        frame = tk.Frame(parent)
        tk.Label(frame, text='串口号').pack(side=tk.LEFT, padx=10)
        cb_port = ttk.Combobox(frame, value=[self.__serial_port_configuration.port], width=35,
                     state='readonly')
        if self.__serial_port_configuration.port != '':
            cb_port.current(0)
        cb_port.pack(side=tk.LEFT, padx=10)
        frame.pack(pady=6)
        # 波特率
        def update_cb_baudrate(event):
            """波特率下拉框绑定事件"""
            value = cb_baudrate.get()
            if value == 'custom':  # 用户输入
                baudrate_values.append('请手动输入波特率')
                cb_baudrate.configure(state='normal', value=baudrate_values)
                index_ = len(baudrate_values) - 1
                cb_baudrate.current(index_)
            else:
                if '请手动输入波特率' in baudrate_values:
                    baudrate_values.pop(-1)
                cb_baudrate.configure(state='readonly', value=baudrate_values)

        frame = tk.Frame(parent)
        tk.Label(frame, text='波特率').pack(side=tk.LEFT, padx=10)
        baudrate_values = ['9600', '19200', '38400', '57600', '115200', 'custom']
        if self.__serial_port_configuration.baud_rate not in baudrate_values:  # 如果手动输入的波特率不在该列表内后面会报错
            baudrate_values.insert(0, self.__serial_port_configuration.baud_rate)
        cb_baudrate = ttk.Combobox(frame, value=baudrate_values,
                                   width=35, state='readonly')
        cb_baudrate.bind('<<ComboboxSelected>>', update_cb_baudrate)
        cb_baudrate.current(baudrate_values.index(self.__serial_port_configuration.baud_rate))
        cb_baudrate.pack(side=tk.LEFT, padx=10)
        frame.pack(pady=6)
        # 数据位
        frame = tk.Frame(parent)
        tk.Label(frame, text='数据位').pack(side=tk.LEFT, padx=10)
        data_digit_values = ['5', '6', '7', '8']
        cb_data = ttk.Combobox(frame, value=data_digit_values,
                               width=35, state='readonly')
        cb_data.current(data_digit_values.index(self.__serial_port_configuration.data_digit))
        cb_data.pack(side=tk.LEFT, padx=10)
        frame.pack(pady=6)
        # 校验位
        frame = tk.Frame(parent)
        tk.Label(frame, text='校验位').pack(side=tk.LEFT, padx=10)
        check_digit_values = ['None', 'Even', 'Odd', 'Mark', 'Space']
        cb_check = ttk.Combobox(frame, value=check_digit_values,
                                width=35, state='readonly')
        cb_check.current(check_digit_values.index(self.__serial_port_configuration.check_digit))
        cb_check.pack(side=tk.LEFT, padx=10)
        frame.pack(pady=6)
        # 停止位
        frame = tk.Frame(parent)
        tk.Label(frame, text='停止位').pack(side=tk.LEFT, padx=10)
        cb_stop = ttk.Combobox(frame, value=['1', ], width=35, state='readonly')
        cb_stop.current(0)
        cb_stop.pack(side=tk.LEFT, padx=10)
        frame.pack(pady=6)
        # 流控
        frame = tk.Frame(parent)
        tk.Label(frame, text='流   控').pack(side=tk.LEFT, padx=10)
        stream_controller_values = ['None', 'RTS/CTS', 'XON/XOFF']
        cb_stream_controller = ttk.Combobox(frame, value=stream_controller_values,
                                            width=35, state='readonly')
        cb_stream_controller.current(stream_controller_values.index(self.__serial_port_configuration.stream_controller))
        cb_stream_controller.pack(pady=6)
        frame.pack(pady=6)
        return cb_port, cb_baudrate, cb_data, cb_check, cb_stop, cb_stream_controller

    def alter_mcu_win(self, parent):
        """弹出MCU菜单栏"""
        def inner():
            frame = tk.Toplevel()
            frame.transient(parent)
            frame.title('选择芯片')
            center_window(frame, *(650, 400))
            frame_top = tk.Frame(frame)
            frame_bottom = tk.Frame(frame)
            frame_top.pack(side=tk.TOP, fill=tk.X)
            frame_bottom.pack(side=tk.BOTTOM, fill=tk.X)
            columns = ('Manufacturer', 'Device', 'Core', 'NumCores', 'Flash Size', 'RAM Size')  # 定义列名称
            displaycolumns = columns  # 表示哪些列可以显示，以及显示顺序。'#all'表示全部显示

            tree = ttk.Treeview(frame_top, columns=columns, displaycolumns=displaycolumns,
                                show='headings')  # 创建treeview对象
            # 设置表格文字居中，以及表格宽度
            for column in columns:
                tree.column(column, anchor='center', width=100, minwidth=100)

            # 设置表格头部标题
            for column in columns:
                tree.heading(column, text=column)

            # 往表格内添加内容 TODO 该内容需要从本地文件中获取。需要维护本地文件
            # TODO 表格的厂家，需要做成下拉框
            contents = [{'Manufacturer': 'ST', 'Device': 'STM32F030C6', 'Core': 'Cortex-M0', 'NumCores': 1,
                         'Flash Size': '32 KB', 'RAM Size': '4 KB'},
                        {'Manufacturer': 'ST', 'Device': 'STM32F030C8', 'Core': 'Cortex-M0', 'NumCores': 1,
                         'Flash Size': '64 KB', 'RAM Size': '8 KB'},
                        {'Manufacturer': 'ST', 'Device': 'STM32F030F4', 'Core': 'Cortex-M0', 'NumCores': 1,
                         'Flash Size': '16 KB', 'RAM Size': '4 KB'},
                        {'Manufacturer': 'ST', 'Device': 'STM32F030R8', 'Core': 'Cortex-M0', 'NumCores': 1,
                         'Flash Size': '64 KB', 'RAM Size': '8 KB'},
                        {'Manufacturer': 'ST', 'Device': 'STM32F042F4', 'Core': 'Cortex-M0', 'NumCores': 1,
                         'Flash Size': '16 KB', 'RAM Size': '6 KB'},
                        {'Manufacturer': 'ST', 'Device': 'STM32F091VC', 'Core': 'Cortex-M0', 'NumCores': 1,
                         'Flash Size': '256 KB', 'RAM Size': '32 KB'},
                        {'Manufacturer': 'ST', 'Device': 'STM32L475VG', 'Core': 'Cortex-M0', 'NumCores': 1,
                         'Flash Size': '1024 KB', 'RAM Size': '96 KB'},
                        {'Manufacturer': 'ST', 'Device': 'STM32F030C6', 'Core': 'Cortex-M0', 'NumCores': 1,
                         'Flash Size': '32 KB', 'RAM Size': '4 KB'},
                        {'Manufacturer': 'ST', 'Device': 'STM32F030C8', 'Core': 'Cortex-M0', 'NumCores': 1,
                         'Flash Size': '64 KB', 'RAM Size': '8 KB'},
                        {'Manufacturer': 'ST', 'Device': 'STM32F030F4', 'Core': 'Cortex-M0', 'NumCores': 1,
                         'Flash Size': '16 KB', 'RAM Size': '4 KB'},
                        {'Manufacturer': 'ST', 'Device': 'STM32F030R8', 'Core': 'Cortex-M0', 'NumCores': 1,
                         'Flash Size': '64 KB', 'RAM Size': '8 KB'},
                        {'Manufacturer': 'ST', 'Device': 'STM32F042F4', 'Core': 'Cortex-M0', 'NumCores': 1,
                         'Flash Size': '16 KB', 'RAM Size': '6 KB'},
                        {'Manufacturer': 'ST', 'Device': 'STM32F091VC', 'Core': 'Cortex-M0', 'NumCores': 1,
                         'Flash Size': '256 KB', 'RAM Size': '32 KB'},
                        {'Manufacturer': 'ST', 'Device': 'STM32L475VG', 'Core': 'Cortex-M0', 'NumCores': 1,
                         'Flash Size': '1024 KB', 'RAM Size': '96 KB'},
                        {'Manufacturer': 'ST', 'Device': 'STM32F030C6', 'Core': 'Cortex-M0', 'NumCores': 1,
                         'Flash Size': '32 KB', 'RAM Size': '4 KB'},
                        {'Manufacturer': 'ST', 'Device': 'STM32F030C8', 'Core': 'Cortex-M0', 'NumCores': 1,
                         'Flash Size': '64 KB', 'RAM Size': '8 KB'},
                        {'Manufacturer': 'ST', 'Device': 'STM32F030F4', 'Core': 'Cortex-M0', 'NumCores': 1,
                         'Flash Size': '16 KB', 'RAM Size': '4 KB'},
                        {'Manufacturer': 'ST', 'Device': 'STM32F030R8', 'Core': 'Cortex-M0', 'NumCores': 1,
                         'Flash Size': '64 KB', 'RAM Size': '8 KB'},
                        {'Manufacturer': 'ST', 'Device': 'STM32F042F4', 'Core': 'Cortex-M0', 'NumCores': 1,
                         'Flash Size': '16 KB', 'RAM Size': '6 KB'},
                        {'Manufacturer': 'ST', 'Device': 'STM32F091VC', 'Core': 'Cortex-M0', 'NumCores': 1,
                         'Flash Size': '256 KB', 'RAM Size': '32 KB'},
                        {'Manufacturer': 'ST', 'Device': 'STM32L475VG', 'Core': 'Cortex-M0', 'NumCores': 1,
                         'Flash Size': '1024 KB', 'RAM Size': '96 KB'},]
            for idx, content in enumerate(contents):
                tree.insert('', idx, values=tuple(content.values()))
            sb = tk.Scrollbar(frame_top, width=32)
            sb.pack(side=tk.RIGHT, fill=tk.Y)
            sb.config(command=tree.yview)
            tree.pack(side=tk.LEFT, fill=tk.Y)

            # 获取当前点击的行
            def treeviewClick(event):  # 单击
                for item in tree.selection():
                    self.temp_mcu_info = tree.item(item, 'value')

            def cancel():
                frame.destroy()


            # 鼠标左键抬起
            tree.bind('<ButtonRelease-1>', treeviewClick)
            tk.Label(frame_bottom).pack(side=tk.RIGHT, fill=tk.Y, padx=40)
            tk.Label(frame_bottom).pack(side=tk.BOTTOM, fill=tk.X, pady=20)
            tk.Button(frame_bottom, text='取消', bg='silver', padx=20, pady=4,
                      command=cancel).pack(side=tk.RIGHT)
            tk.Label(frame_bottom).pack(side=tk.RIGHT, fill=tk.Y, padx=30)
            tk.Button(frame_bottom, text='确定', bg='silver', padx=20, pady=4,
                      command=self.mcu_configuration_confirm(frame)).pack(side=tk.RIGHT)

        return inner

    def _draw_jlink_configuration(self, parent):  # 给定界面，绘制jlink配置项 TODO 还可以添加字体大小颜色、padx、pady等参数
        """给定界面，绘制jlink通信配置项"""
        # 连接端口
        def get_serial_no():
            return ['79765170989']

        frame = tk.Frame(parent)
        tk.Label(frame, text='连接端口').pack(side=tk.LEFT)
        cb_serial_no = ttk.Combobox(frame, value=get_serial_no, width=30,
                                    state='readonly')  # TODO 通过pylink获取当前接入的jlink仿真器的序列号
        if self.__jlink_configuration.serial_no != '':  # 上一次已经确定过了仿真器序列号
            cb_serial_no.current(0)
        cb_serial_no.pack(side=tk.LEFT, padx=80)
        frame.pack(pady=6, fill=tk.X)
        # 接口模式
        frame = tk.Frame(parent)
        tk.Label(frame, text='接口模式').pack(side=tk.LEFT)
        interface_type_values = ['JTAG', 'SWD']
        cb_interface_type = ttk.Combobox(frame, value=interface_type_values, width=30, state='readonly')
        cb_interface_type.current(interface_type_values.index(self.__jlink_configuration.interface_type))
        cb_interface_type.pack(side=tk.LEFT, padx=80)
        frame.pack(pady=6, fill=tk.X)
        # 速率(kHZ)
        def update_cb_rate(event):
            """速率下拉框绑定事件"""
            nonlocal rate_values
            value = cb_rate.get()
            if value == 'custom':  # 用户手动输入
                rate_values.append('请手动输入传输速率')
                cb_rate.configure(state='normal', value=rate_values)
                index_ = len(rate_values) - 1
                cb_rate.current(index_)
            else:
                if '请手动输入传输速率' in rate_values:
                    rate_values = rate_values[:-1]
                cb_rate.configure(state='readonly', value=rate_values)

        frame = tk.Frame(parent)
        tk.Label(frame, text='速率(kHZ)').pack(side=tk.LEFT)
        rate_values = ['5', '10', '20', '30', '50', '100', '200', '300', '400', '500', '600', '750', '900', '1000',
                       '1334', '1600', '2000', '2667', '3200', '4000', '4800', '5334', '6000', '8000',
                       '9600', '12000', 'custom']
        if self.__jlink_configuration.rate not in rate_values:
            rate_values.insert(0, self.__jlink_configuration.rate)
        cb_rate = ttk.Combobox(frame, value=rate_values, width=30, state='readonly')
        cb_rate.bind('<<ComboboxSelected>>', update_cb_rate)
        cb_rate.current(rate_values.index(self.__jlink_configuration.rate))
        cb_rate.pack(side=tk.LEFT, padx=73)
        frame.pack(pady=6, fill=tk.X)
        # MCU
        frame = tk.Frame(parent)
        tk.Label(frame, text='MCU                        ').pack(side=tk.LEFT, padx=0)
        entry_mcu = tk.Entry(frame, show=None, state='disabled', textvariable=self.__mcu_info.device, width=33)
        entry_mcu.pack(side=tk.LEFT, padx=2)
        button_mcu = tk.Button(frame, text='...', width=3, height=1, command=self.alter_mcu_win(frame))
        button_mcu.pack(side=tk.LEFT)
        frame.pack(pady=6, fill=tk.X)
        # License存储地址
        frame = tk.Frame(parent)
        tk.Label(frame, text='License存储地址').pack(side=tk.LEFT)
        addr_value = tk.StringVar()
        addr_value.set('0x8000000')
        entry_license_addr = tk.Entry(frame, show=None, textvariable=addr_value, width=33)  # TODO 默认值应该时动态获取的
        entry_license_addr.pack(side=tk.LEFT, padx=37)
        frame.pack(pady=6, fill=tk.X)
        # License存储区域大小
        frame = tk.Frame(parent)
        tk.Label(frame, text='License存储区域大小').pack(side=tk.LEFT)
        entry_license_size = tk.Entry(frame, show=None, textvariable=self.__mcu_info.flash_size, width=33)
        entry_license_size.pack(side=tk.LEFT, padx=12)
        frame.pack(pady=6, fill=tk.X)
        return cb_serial_no, cb_interface_type, cb_rate, entry_mcu, entry_license_addr, entry_license_size

    def _draw_log_configuration(self, parent):  # TODO 还可以添加字体大小、padx、pady等参数
        """给定界面，绘制日志配置项"""
        is_open = tk.IntVar()
        log_path = tk.StringVar()
        max_size = tk.StringVar()
        is_open.set(self.__log_configuration.is_open.get())
        log_path.set(self.__log_configuration.log_path.get())
        max_size.set(self.__log_configuration.max_size.get())
        # 是否打开日志记录
        frame = tk.Frame(parent)

        def refresh_if_record_status():
            if is_open.get():  # 开启日志记录
                print('开启日志记录')  # TODO 需要设置其余配置项是否可配置
                entry_log_path.configure(state=tk.NORMAL)
                button_log_path.configure(state=tk.NORMAL)
                entry_log_size.configure(state=tk.NORMAL)
            else:
                entry_log_path.configure(state=tk.DISABLED)
                button_log_path.configure(state=tk.DISABLED)
                entry_log_size.configure(state=tk.DISABLED)
                print('关闭日志记录')

        cb_if_record = tk.Checkbutton(frame, text='记录日志', variable=is_open,
                                      onvalue=1, offvalue=0, command=refresh_if_record_status)
        cb_if_record.pack(side=tk.LEFT)
        frame.pack(fill=tk.X, pady=5)
        # 存储日志
        frame = tk.Frame(parent)

        def path_call_back():
            file_path = filedialog.asksaveasfilename(initialfile=f"{datetime.now().strftime('%Y%m%d%H%M%S')}.log")
            if file_path != '':
                log_path.set(file_path)

        tk.Label(frame, text='存储日志').pack(side=tk.LEFT)
        entry_log_path = tk.Entry(frame, textvariable=log_path, width=35)
        button_log_path = tk.Button(frame, text='打开', width=10, bg='whitesmoke', command=path_call_back)
        if not is_open.get():  # 未开启日志记录
            entry_log_path.configure(state=tk.DISABLED)
            button_log_path.configure(state=tk.DISABLED)
        entry_log_path.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        button_log_path.pack(side=tk.RIGHT, padx=5)
        frame.pack(fill=tk.X, pady=5)
        # 日志大小上限
        frame = tk.Frame(parent)
        tk.Label(frame, text='日志大小上限').pack(side=tk.LEFT)
        entry_log_size = tk.Entry(frame, textvariable=max_size, show=None)
        if not is_open.get():  # 未开启日志记录
            entry_log_size.configure(state=tk.DISABLED)
        entry_log_size.pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Label(frame, text='MB').pack(side=tk.LEFT, padx=15)
        frame.pack(fill=tk.X, pady=5)
        # 确定取消按钮
        frame = tk.Frame(parent)

        def cancel():
            print('日志配置取消按钮')
            parent.destroy()

        def confirm():
            """
            如果开启了日志记录，则校验填入的路径以及日志大小时候正确
            校验成功，则更新__log_configuration的各属性值
            如果没有开启日志记录，同取消按钮
            """
            if is_open.get():  # 开启了日志记录
                log_path_value = log_path.get()
                if not log_path_value:  # 没有选择存储文件
                    tkinter.messagebox.showwarning(title='Warning', message='请选择存储日志文件')
                    return
                max_size_value = max_size.get()
                if max_size_value:
                    if not max_size_value.isdigit():
                        tkinter.messagebox.showwarning(title='Warning', message='日志大小需要为纯数字')
                        entry_log_size.delete(0, tk.END)
                        return
                    if float(max_size_value) <= 0:
                        tkinter.messagebox.showwarning(title='Warning', message='日志大小需要为正整数')
                        entry_log_size.delete(0, tk.END)
                        return
                    self.__log_configuration.is_open.set(1)
                    self.__log_configuration.log_path.set(log_path_value)
                    self.__log_configuration.max_size.set(max_size_value)
                else:
                    tkinter.messagebox.showwarning(title='Warning', message='日志上限不能为空')
                    return
            else:
                self.__log_configuration.is_open.set(0)
            parent.destroy()
            print(f'是否记录日志: {self.__log_configuration.is_open.get()}')
            print(f'日志存储路径: {self.__log_configuration.log_path.get()}')
            print(f'日志大小上限: {self.__log_configuration.max_size.get()}')

            print('日志配置确定按钮')

        tk.Button(frame, text='取消', bg='silver', height=1, width=8, command=cancel).pack(
            side=tk.RIGHT, pady=4, padx=10
        )
        tk.Button(frame, text='确定', bg='silver', height=1, width=8, command=confirm).pack(
            side=tk.RIGHT, pady=4, padx=10
        )
        frame.pack(fill=tk.X, pady=10)

    def body(self):  # 绘制主题  TODO 定义几种frame布局，更改布局时，切换frame。需要一个变量存储当前的布局，如果同当前的模式

        self.draw_menu(self.window_)  # 绘制菜单栏，固定布局
        # 绘制生产模式的界面
        self.frame_product = self.draw_product_frame(self.window_)
        # 绘制调试模式的界面
        self.frame_debug = self.draw_debug_frame(self.window_)
        # 默认展示生产模式的界面
        self.frame_product.pack(expand=True, fill=tk.BOTH)

    # 以下为菜单栏界面代码
    def draw_menu(self, parent):
        """绘制菜单栏"""
        # 创建父菜单对象
        menu_bar = tk.Menu(parent)
        # 绘制子菜单
        self._draw_mode_menu(menu_bar)
        self._draw_config_menu(menu_bar)
        # 在界面上展示菜单
        self.window_.config(menu=menu_bar)

    def _draw_mode_menu(self, parent):
        """绘制模式选择的子菜单"""
        # 创建一个菜单对象
        mode_menu = tk.Menu(parent, tearoff=0)

        # 给菜单对象添加选项
        mode_menu.add_radiobutton(label='生产模式', activebackground=_active_color,
                                  variable=self.__mode_type, value=ModeEnum.PRODUCT.value)
        mode_menu.add_radiobutton(label='调试模式', activebackground=_active_color,
                                  variable=self.__mode_type, value=ModeEnum.DEBUG.value)
        # 将菜单对象放置在父对象上，命名为模式选择
        parent.add_cascade(label='模式选择', menu=mode_menu)

    def _draw_config_menu(self, parent):
        """绘制设置的子菜单"""
        config_menu = tk.Menu(parent, tearoff=0)

        def do_detail_config_port():
            """针对config_value_selected的值，弹出对应的配置窗口"""
            self.alter_win(name='port')  # 根据不同的配置选项，弹出对应的弹出窗口

        def do_detail_config_jlink():
            self.alter_win(name='J-Link')

        def do_detail_config_log():
            self.alter_win(name='log')

        config_menu.add_command(label='串口设置', activebackground=_active_color,
                                    command=do_detail_config_port)
        config_menu.add_command(label='J-Link设置', activebackground=_active_color,
                                    command=do_detail_config_jlink)
        config_menu.add_command(label='日志设置', activebackground=_active_color,
                                    command=do_detail_config_log)
        parent.add_cascade(label='设置', menu=config_menu)

    def alter_win(self, name: str) -> None:
        """
        根据名称，弹出对应的窗口
        Args:
            name: port/J-Link/log

        Returns:

        """
        frame = tk.Toplevel()
        frame.transient(self.window_)  # 随主窗口最小化而最小化，关闭而关闭，处于主窗口前方
        if name == 'port':
            self.alter_port_win(frame)
        elif name == 'J-Link':
            self.alter_jlink_win(frame)
        elif name == 'log':
            self.alter_log_win(frame)

    def alter_port_win(self, parent) -> None:
        """弹出串口配置窗口"""
        parent.title('串口配置')
        center_window(parent, *SIZE_POPUPS)
        tk.Label(parent).pack(side=tk.LEFT, fill=tk.Y, padx=20)  # 左边缘空隙
        tk.Label(parent).pack(side=tk.RIGHT, fill=tk.Y, padx=20)  # 右边缘空隙
        cb_port, cb_baudrate, cb_data, cb_check, cb_stop, cb_stream_controller = \
            self._draw_serial_port_configuration(parent)  # 串口配置项

        def cancel():
            print('串口配置取消按钮')
            parent.destroy()

        frame = tk.Frame(parent)
        tk.Button(frame, text='取消', bg='silver', height=3, width=6,
                  command=cancel).pack(side=tk.RIGHT, pady=4, padx=10)
        tk.Button(frame, text='确定', bg='silver', height=3, width=6,
                  command=self.port_configuration_confirm(cb_port, cb_baudrate,
                                                          cb_data, cb_check, cb_stop,
                                                          cb_stream_controller, parent)).pack(side=tk.RIGHT, pady=4, padx=10)
        frame.pack(pady=10)

    def alter_jlink_win(self, parent) -> None:
        """弹出J-Link配置项窗口"""
        parent.title('J-Link设置')
        center_window(parent, *(500, 300))
        tk.Label(parent, bg='red').pack(side=tk.LEFT, fill=tk.Y, padx=1)  # 左边填充
        tk.Label(parent, bg='red').pack(side=tk.RIGHT, fill=tk.Y, padx=1)  # 右边填充
        # 绘制J-Link配置项界面，并获取连接端口、接口模式、速率、芯片名称、license存储地址、license存储区域大小控件，供确定按钮使用
        cb_serial_no, cb_interface_type, cb_rate, entry_mcu, \
        entry_license_addr, entry_license_size = self._draw_jlink_configuration(parent)

        def cancel():
            """取消按钮绑定方法"""
            print('J-Link配置取消按钮')
            parent.destroy()

        frame = tk.Frame(parent)
        # 确定按钮和取消按钮
        tk.Button(frame, text='取消', bg='silver', height=1, width=6,
                  command=cancel).pack(side=tk.RIGHT, pady=4, padx=20)
        tk.Button(frame, text='确定', bg='silver', height=1, width=6,
                  command=self.jlink_configuration_confirm(cb_serial_no, cb_interface_type, cb_rate,
                                                           entry_mcu, entry_license_addr,
                                                           entry_license_size, parent=parent)).pack(side=tk.RIGHT, pady=4, padx=20)
        frame.pack(pady=10)

    def alter_log_win(self, parent):
        """弹出日志配置界面"""
        parent.title('日志设置')
        center_window(parent, *(400, 180))
        self._draw_log_configuration(parent)  # 日志配置项

    # 以下为生产模式界面代码
    def draw_product_frame(self, parent):
        """绘制生产模式界面"""
        # 主界面
        frame = tk.Frame(parent)
        # 界面top
        frame_top = tk.Frame(frame)
        # 界面top_t
        frame_top_t = tk.Frame(frame_top)
        # 界面top_t_l
        frame_top_t_l = tk.Frame(frame_top_t)
        # 界面top_t_l_t TODO 读ID和写License的选择和展示
        frame_top_t_l_t = tk.Frame(frame_top_t_l)
        self.draw_frame_top_t_l_t_detail(frame_top_t_l_t)
        frame_top_t_l_t.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        # 界面top_t_l_b TODO HID存储文件\Licesen存储文件\UKey状态展示
        frame_top_t_l_b = tk.Frame(frame_top_t_l, bg='turquoise')
        tk.Label(frame_top_t_l_b, text='界面top_t_l_b').pack(side=tk.LEFT)
        frame_top_t_l_b.pack(side=tk.BOTTOM, expand=True, fill=tk.BOTH)
        frame_top_t_l.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        # 界面top_t-r
        frame_top_t_r = tk.Frame(frame_top_t)
        # 界面top_t_r_l  TODO 结果展示(序号-设备id-结果)
        frame_top_t_r_l = tk.Frame(frame_top_t_r, bg='lightseagreen')
        tk.Label(frame_top_t_r_l, text='界面top_t_r_l').pack(side=tk.TOP)
        frame_top_t_r_l.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        # 界面top_t_r_r
        frame_top_t_r_r = tk.Frame(frame_top_t_r)
        # 界面top_t_r_r_t  TODO 开始\停止按钮
        frame_top_t_r_r_t = tk.Frame(frame_top_t_r_r, bg='lightblue')
        tk.Label(frame_top_t_r_r_t, text='界面top_t_r_r_t').pack(side=tk.LEFT)
        frame_top_t_r_r_t.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        # 界面top_t_r_r_b  TODO 状态展示(成功\失败\停止\已完成\空白)
        frame_top_t_r_r_b = tk.Frame(frame_top_t_r_r, bg='paleturquoise')
        tk.Label(frame_top_t_r_r_b, text='界面top_t_r_r_b').pack(side=tk.LEFT)
        frame_top_t_r_r_b.pack(side=tk.BOTTOM, expand=True, fill=tk.BOTH)
        frame_top_t_r_r.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
        frame_top_t_r.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
        frame_top_t.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        # 界面top_b
        frame_top_b = tk.Frame(frame_top)
        # 界面top_b_l  TODO 通信方式(串口\J-Link)选择以及配置项展示
        frame_top_b_l = tk.Frame(frame_top_b, bg='hotpink')
        tk.Label(frame_top_b_l, text='界面top_b_l').pack(side=tk.TOP)
        frame_top_b_l.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        # 界面top_b_r
        frame_top_b_r = tk.Frame(frame_top_b)
        # 界面top_b_r_t  TODO 操作明细日志展示
        frame_top_b_r_t = tk.Frame(frame_top_b_r, bg='lightseagreen')
        tk.Label(frame_top_b_r_t, text='界面top_b_r_t').pack(side=tk.LEFT)
        frame_top_b_r_t.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        # 界面top_b_r_b  TODO 清楚按钮
        frame_top_b_r_b = tk.Frame(frame_top_b_r, bg='turquoise')
        tk.Label(frame_top_b_r_b, text='界面top_b_r_b').pack(side=tk.LEFT)
        frame_top_b_r_b.pack(side=tk.BOTTOM, expand=True, fill=tk.BOTH)
        frame_top_b_r.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        frame_top_b.pack(side=tk.BOTTOM, expand=True, fill=tk.BOTH)
        frame_top.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        # 界面bottom  TODO 各类信息(模式\工位\串口状态\运行状态)展示
        frame_bottom = tk.Frame(frame, bg='blue')
        tk.Label(frame_bottom, text='界面bottom').pack(side=tk.LEFT)
        frame_bottom.pack(side=tk.BOTTOM, fill=tk.X)

        return frame

    def draw_frame_top_t_l_t_detail(self, parent):
        """读ID\写License工位选择以及信息展示
        Menu
        Label
        Label
        """

        def swith_read_id(event):
            print('切换工位到读取设备ID')

        # 创建占位label
        tk.Label(parent, text='           ').pack(side=tk.LEFT)

        # 创建读ID菜单
        read_id_menu_bar = tk.Menubutton(parent, text='读ID')  # 其实如果没有次级菜单的话，没有必要做成Menubutton，直接使用Label或者button不就好了吗..
        read_id_menu_bar.bind('<ButtonRelease-1>', swith_read_id)
        read_id_menu_bar.pack(side=tk.LEFT)

        # 创建写License菜单
        menu_bar = tk.Menubutton(parent, text='写License')
        # 定义写License子菜单
        license_menu = tk.Menu(menu_bar, tearoff=0)  # 默认不下拉
        license_menu.add_radiobutton(label='从License文件', activebackground=_active_color,
                                     variable=self.__operate_type, value=OperateEnum.LICENSE_FILE)
        license_menu.add_radiobutton(label='从UKey', activebackground=_active_color,
                                     variable=self.__operate_type, value=OperateEnum.LICENSE_UKEY)
        menu_bar.config(menu=license_menu)
        menu_bar.pack(side=tk.LEFT)

    # 以下为调试模式界面代码
    def draw_debug_frame(self, parent):
        """绘制调试模式界面"""
        frame = tk.Frame(parent, bg='green')
        return frame

    def run(self):
        self.window_.mainloop()


if __name__ == '__main__':
    oneos_gui = OneOsGui()
    oneos_gui.run()
# -*- coding: utf-8 -*-
"""GUI操作界面"""
import time
import tkinter as tk
import tkinter.messagebox  # 弹窗
from datetime import datetime, timedelta
from threading import Thread
from tkinter import ttk
from tkinter import filedialog
from serial.serialutil import SerialException
from pathlib import Path

from dao import HID_License_Map, DaoException
from serial_.pyboard import PyBoard  # 串口通信对象
from jlink_.pyjlink import JLinkCOM  # JLink通信对象
from ukey_.pyukey import PyUKey  # UKey通信对象
from log import logger, OperateLogger  # 软件记录日志， 操作流程记录日志类
from utils.entities import *
from utils.file_utils import *
from utils.utility import is_hex
from utils.convert_utils import *
from utils.protocol_utils import parse_protocol, check_command, build_protocol, check_payload

_font_s = ('微软雅黑', 8)  # 字体
_font_b = ('微软雅黑', 12)  # 字体
_FONT_B = ('宋体', 10, 'bold')
_BACKGOUND = 'gainsboro'  # 默认背景色
_ACTIVE_COLOR = 'green'  # 默认激活状态颜色
_NORMAL_COLOR = 'black'  # 默认正常状态颜色
SIZE_POPUPS = (400, 280)  # 弹出窗体大小
MAX_RETRY_TIME = 5  # 最大重复操作次数
MAX_INTERVAL_SECOND = timedelta(seconds=15)  # 连续失败的最长持续时间为30s


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


def clear_widget(widget):
    """对Text, Entry等控件，清除控件内信息"""
    def inner():
        widget.delete(1.0, tk.END)
    return inner


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
        self.port_com = PyBoard()  # 串口连接对象
        self.jlink_com = JLinkCOM()  # 初始化jlink对象
        self.ukey_com = PyUKey()  # 初始化ukey对象
        self.__mode_type = tk.StringVar()  # 模式选择(生产模式/调试模式)
        self.__operate_type = tk.StringVar()  # 操作工位(读HID/写License-从License文件/写License-从UKey)
        self.__operate_desc = tk.StringVar()  # 操作工位的描述
        self.__run_state = tk.StringVar()  # 运行状态
        self.__operate_desc_detail = tk.StringVar()  # 操作工位的详细描述
        self.__conn_type = ConnType()
        self.log_shower_product = tk.Text()  # 操作关键信息打印控件(同日志共享记录信息)
        self.statistic_product_label = tk.Label()  # 展示操作结果(成功/失败...)的标签控件
        self.temp_mcu_info = ()
        self.__serial_port_info_product = None  # 生产界面的串口控件
        self.__serial_port_info_debug = None  # 调试界面的串口控件
        self.__jlink_info_product = None  # 生产界面的JLink控件
        self.__jlink_info_debug = None  # 调试界面的JLink控件
        self.entry_mcu_product = None
        self.entry_license_addr_product = None
        self.entry_license_size_product = None
        self.entry_mcu_debug = None
        self.entry_license_addr_debug = None
        self.entry_license_size_debug = None
        self.btn_start = None  # 生产模式下的开始按钮
        self.tree_hid = None  # 生产模式批量读ID操作结果展示列表
        self.tree_license = None  # 生产模式批量写License操作结果展示列表
        self.succ_hid = []  # 记录成功的设备ID
        self.fail_hid = []  # 记录失败的设备ID

    def init_values(self):
        """定义属性初始值"""
        self.__mode_type.set('PRODUCT')  # 默认模式选择为生产模式
        self.__operate_type.set('HID')  # 默认操作工位为读HID
        self.__operate_desc.set('读设备ID')  # 默认操作工位描述
        self.__operate_desc_detail.set('  从设备读取物理识别码，并保存到本地文件')
        self.__run_state.set('停止')  # 初始运行状态为停止
        self.__serial_port_configuration = SerialPortConfiguration()  # 串口通信数据
        self.__jlink_configuration = JLinkConfiguration()  # J-Link通信数据
        self.__log_configuration = LogConfiguration()  # 日志配置数据
        self.__ukey_info = UKeyInfo()  # UKey连接信息
        self.__mcu_info = MCUInfo()  # mcu相关信息
        self.__filepath_hid = tk.StringVar()  # HID存储文件路径
        self.__filepath_license = tk.StringVar()  # License存储文件路径
        self.operate_start_time = datetime.now()  # 生成模式中，操作的开始时间
        self.retry_time = 0  # 失败的持续次数
        self.last_success_hid = ''  # 上一次成功的设备HID
        self.go = True  # 生产模式下，一直运行
        self.frame_product = None
        self.frame_debug = None

    @property
    def is_open(self):
        if self.__conn_type.conn_type.get() == '串口通信':
            return self.port_com.is_open
        else:
            return self.jlink_com.is_open

    def __update_statistic(self, text='', fg='white'):
        """
        更新结果展示
        Args:
            text: 结果文字(成功/失败/停止/已完成/'')
            fg:

        Returns:

        """
        self.statistic_product_label.configure(text=text, fg=fg)

    def __update_serial_port_info(self, port, baudrate, data_digit, check_digit, stop_digit,
                                  stream_controller):
        """
        更新串口控件的展示信息
        Args:
            port:
            baudrate:
            data_digit:
            check_digit:
            stop_digit:
            stream_controller:

        Returns:

        """
        self.__serial_port_info_debug.update(port, baudrate, data_digit, check_digit, stop_digit,
                                             stream_controller)
        self.__serial_port_info_product.update(port, baudrate, data_digit, check_digit, stop_digit,
                                               stream_controller)

    def __update_jlink_info(self, serial_no, interface_type, rate, device,
                            license_addr, license_size):
        """
        更新jlink控件的展示信息
        Args:
            serial_no:
            interface_type:
            rate:
            device:
            license_addr:
            license_size:

        Returns:

        """
        self.__jlink_info_product.update(serial_no, interface_type, rate, device,
                                         license_addr, license_size)
        self.__jlink_info_debug.update(serial_no, interface_type, rate, device,
                                       license_addr, license_size)


    def __verify_file(self):
        """
        生产模式进行正式通讯之前，确保hid记录文件或者license记录文件或者UKey连接已经创建
        Returns:
            message: 通过 None；不通过 str

        """
        message = None
        if self.__operate_type.get() == 'HID':  # 校验是否选择了hid存储文件
            if not self.__filepath_hid.get():
                message = '请选择设备ID存储文件...'
        elif self.__operate_type.get() == 'LICENSE_FILE':  # 校验是否选择了license存储文件
            if not self.__filepath_license.get():
                message = '请选择设备License存储文件...'
        elif self.__operate_type.get() == 'LICENSE_UKEY':  # 校验UKey连接是否创建并且已经过PIN码认证
            if not self.ukey_com.is_connected:
                message = '请连接UKey并进行PIN码验证'
        return message

    def __verify_conn(self):
        """
        生产模式进行正式通讯之前，验证通讯所需参数是否配置齐全
        Returns:
            message: 通过 None；不通过 str
        """
        message = None
        if self.__conn_type.conn_type.get() == 'J-Link通信':  # J-Link通信的相关配置验证
            if self.__mode_type.get == 'PRODUCT':  # 生产模式
                self.__jlink_configuration.mcu = self.entry_mcu_product.get()
                self.__jlink_configuration.license_addr = self.entry_license_addr_product.get()
                self.__jlink_configuration.license_size_stored = self.entry_license_size_product.get()
            elif self.__mode_type.get() == 'DEBUG':  # 调试模式
                self.__jlink_configuration.mcu = self.entry_mcu_debug.get()
                self.__jlink_configuration.license_addr = self.entry_license_addr_debug.get()
                self.__jlink_configuration.license_size_stored = self.entry_license_size_debug.get()
            if not self.__jlink_configuration.serial_no:
                message = '请选择ARM仿真器序列号'
                return message
            if not self.__jlink_configuration.interface_type:
                message = '请选择接口类型: JTAG/SWD'
                return message
            if not self.__jlink_configuration.rate:
                message = '请设置通信速率'
                return message
            if not self.__jlink_configuration.mcu:
                message = '请选择适配的MCU'
                return message
            if not self.__jlink_configuration.license_addr:
                message = '请设置license存储地址'
                return message
            if not self.__jlink_configuration.license_size_stored:
                message = '请设置license存储区域大小'
                return message
        elif self.__conn_type.conn_type.get() == '串口通信':  # 串口通信的相关配置验证
            if not self.__serial_port_configuration.port:
                message = '请选择连接串口号'
                return message
            if not self.__serial_port_configuration.baud_rate and not \
                str(self.__serial_port_configuration.baud_rate).isdigit():
                message = '请选择正确的波特率'
                return message
            if not self.__serial_port_configuration.data_digit:
                message = '请选择数据位'
                return message
            if not self.__serial_port_configuration.check_digit:
                message = '请选择校验位'
                return message
            if not self.__serial_port_configuration.stop_digit:
                message = '请选择停止位'
                return message
            if not self.__serial_port_configuration.stream_controller:
                message = '请选择流控'
                return message
        return message

    def log_shower_insert(self, message, tag=None):
        """
        打印操作记录
        Args:
            message:
            tag:

        Returns:

        """
        if tag is None:
            if self.__mode_type.get() == 'PRODUCT':
                self.log_shower_product.insert(tk.END, message)
            else:
                self.log_shower_debug.insert(tk.END, message)
        else:
            if self.__mode_type.get() == 'PRODUCT':
                self.log_shower_product.insert(tk.END, message, tag)
            else:
                self.log_shower_debug.insert(tk.END, message, tag)

    def tree_insert(self, content, tree):
        """
        往tree内添加一条数据(如果设备ID(-组件ID)已经在tree内展示，则对其进行更新)
        Args:
            content: 一条待插入数据(( '12348', '成功')/('12347', 1004, '失败'))
            tree: 待插入的列表控件对象

        Returns:

        """
        # 首先要判断插入的数据是否已经在tree中存在
        key_word = ''
        if len(content) == 2:  # 读ID的操作结果
            key_word = [content[0]]  # 设备ID
        elif len(content) == 3:  # 写License的操作结果
            key_word = [content[0], content[1]]  # 设备ID，组件ID
        else:
            logger.warning(f'获取到非预期的结果描述: {content}')
        for i in tree.get_children():
            values = [str(i) for i in tree.item(i)['values'][1:len(key_word)+1]]
            idx_ = tree.item(i)['values'][0]
            if key_word == values:  # 是子集
                if content[-1] == '失败':
                    tree.item(i, values=(idx_, *content), tags='tag_failed')
                else:
                    tree.item(i, values=(idx_, *content))
                return

        length = len(tree.get_children())
        content = (length+1, *content)
        # 插入
        if content[-1] == '失败':
            tree.insert('', tk.END, values=content, tag='tag_failed')
        else:
            tree.insert('', tk.END, values=content)

    def port_configuration_confirm(self, cb_port, cb_baudrate, cb_data, cb_check, cb_stop, cb_stream_controller, parent=None):
        """
        串口配置确定按钮触发方法()
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
            self.__conn_type.swith_to_port(self.__mode_type.get())  # 通信方式更新为串口通信
            self.__update_serial_port_info(port, baudrate, data_digit, check_digit, stop_digit,
                                           stream_controller)
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
            self.__conn_type.swith_to_jlink(self.__mode_type.get())  # 通信方式更新为J-Link通信
            self.__update_jlink_info(serial_no, interface_type, rate, self.__mcu_info.device,
                                     license_addr, license_size)
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

    def record_filepath_license(self):
        filepath = filedialog.askopenfilename()
        if filepath != '':
            if check_file_suffix(filepath):
                self.__filepath_license.set(filepath)
                try:
                    self.hid_license_map = HID_License_Map(filepath)  # hid-license映射对象
                except DaoException as e:
                    tkinter.messagebox.showerror(title='Error',
                                                 message=str(e))
                    self.__filepath_license.set('')
                    return
                except Exception as e:
                    tkinter.messagebox.showerror(title='Error',
                                                 message='读取license存储文件失败，请检查文件格式是否正确')
                    self.__filepath_license.set('')
                self.log_shower_insert(f'导入license文件，'
                                       f'共导入HID{len(set(self.hid_license_map.hids))}个, '
                                       f'license{self.hid_license_map.licenses_counts}个\n')

            else:
                tk.messagebox.showwarning(title='Warning',
                                          message='License存储文件为Excel类型文件')

    def _draw_serial_port_configuration(self, parent, width=35, bg='SystemButtonFace'):  # 给定界面，绘制串口通信配置项 TODO 还可以添加字体大小、padx、pady等参数
        """给定界面，绘制串口通信配置项"""
        # 串口号

        def update_portlist(event):
            cb_port.configure(value=self.__serial_port_configuration.port_list)


        frame = tk.Frame(parent, bg=bg)
        tk.Label(frame, text='串口号', bg=bg).pack(side=tk.LEFT, padx=10)
        cb_port = ttk.Combobox(frame, value=self.__serial_port_configuration.port_list, width=width,
                     state='readonly')
        if self.__serial_port_configuration.port in self.__serial_port_configuration.port_list:
            index_ = self.__serial_port_configuration.port_list.index(self.__serial_port_configuration.port)
            cb_port.current(index_)
        cb_port.bind('<Button-1>', update_portlist)
        if bg == 'white':  # 主界面，绑定下拉方法
            cb_port.bind('<<ComboboxSelected>>', self.__serial_port_configuration.update_port(cb_port))
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
            if bg == 'white':
                self.__serial_port_configuration.update_baudrate(cb_baudrate.get())

        frame = tk.Frame(parent, bg=bg)
        tk.Label(frame, text='波特率', bg=bg).pack(side=tk.LEFT, padx=10)
        baudrate_values = ['9600', '19200', '38400', '57600', '115200', 'custom']
        if self.__serial_port_configuration.baud_rate not in baudrate_values:  # 如果手动输入的波特率不在该列表内后面会报错
            baudrate_values.insert(0, self.__serial_port_configuration.baud_rate)
        cb_baudrate = ttk.Combobox(frame, value=baudrate_values,
                                   width=width, state='readonly')
        cb_baudrate.bind('<<ComboboxSelected>>', update_cb_baudrate)
        cb_baudrate.current(baudrate_values.index(self.__serial_port_configuration.baud_rate))
        cb_baudrate.pack(side=tk.LEFT, padx=10)
        frame.pack(pady=6)
        # 数据位
        frame = tk.Frame(parent, bg=bg)
        tk.Label(frame, text='数据位', bg=bg).pack(side=tk.LEFT, padx=10)
        data_digit_values = [5, 6, 7, 8]
        cb_data = ttk.Combobox(frame, value=data_digit_values,
                               width=width, state='readonly')
        cb_data.current(data_digit_values.index(self.__serial_port_configuration.data_digit))
        if bg == 'white':
            cb_data.bind('<<ComboboxSelected>>', self.__serial_port_configuration.update_datadigit(cb_data))
        cb_data.pack(side=tk.LEFT, padx=10)
        frame.pack(pady=6)
        # 校验位
        frame = tk.Frame(parent, bg=bg)
        tk.Label(frame, text='校验位', bg=bg).pack(side=tk.LEFT, padx=10)
        check_digit_values = ['None', 'Even', 'Odd', 'Mark', 'Space']
        cb_check = ttk.Combobox(frame, value=check_digit_values,
                                width=width, state='readonly')
        cb_check.current(check_digit_values.index(self.__serial_port_configuration.check_digit))
        if bg == 'white':
            cb_check.bind('<<ComboboxSelected>>', self.__serial_port_configuration.update_checkdigit(cb_check))
        cb_check.pack(side=tk.LEFT, padx=10)
        frame.pack(pady=6)
        # 停止位
        frame = tk.Frame(parent, bg=bg)
        tk.Label(frame, text='停止位', bg=bg).pack(side=tk.LEFT, padx=10)
        cb_stop = ttk.Combobox(frame, value=['1', ], width=width, state='readonly')
        cb_stop.current(0)
        if bg == 'white':
            cb_stop.bind('<<ComboboxSelected>>',
                         self.__serial_port_configuration.update_stopdigit(cb_stop))
        cb_stop.pack(side=tk.LEFT, padx=10)
        frame.pack(pady=6)
        # 流控
        frame = tk.Frame(parent, bg=bg)
        tk.Label(frame, text='流   控', bg=bg).pack(side=tk.LEFT, padx=10)
        stream_controller_values = ['None', 'RTS/CTS', 'XON/XOFF']
        cb_stream_controller = ttk.Combobox(frame, value=stream_controller_values,
                                            width=width, state='readonly')
        cb_stream_controller.current(stream_controller_values.index(self.__serial_port_configuration.stream_controller))
        if bg == 'white':
            cb_stream_controller.bind('<<ComboboxSelected>>',
                                      self.__serial_port_configuration.update_streamcontroller(cb_stream_controller))
        cb_stream_controller.pack(pady=6, padx=10)
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
            sb = tk.Scrollbar(frame_top, width=32)
            sb.pack(side=tk.RIGHT, fill=tk.Y)
            tree = ttk.Treeview(frame_top, columns=columns, displaycolumns=displaycolumns,
                                show='headings', yscrollcommand=sb.set)  # 创建treeview对象
            sb.config(command=tree.yview)
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

    def alter_ukey_connect(self, parent):
        """弹出UKey连接窗口"""
        def inner(event):
            frame = tk.Toplevel()
            frame.transient(parent)
            frame.title('UKey连接...')
            center_window(frame, *(400, 120))
            # ukey选择
            frame_ukey = tk.Frame(frame)
            ## 具体控件代码
            ### UKey选择
            tk.Label(frame_ukey, text='UKey选择', padx=30, pady=10).pack(side=tk.LEFT, fill=tk.Y)
            cb_ukey = ttk.Combobox(frame_ukey, values=('COM1', 'COM2'), width=30)
            cb_ukey.pack(side=tk.LEFT)
            frame_ukey.pack(side=tk.TOP, fill=tk.X)
            # 输入pin码
            frame_pin = tk.Frame(frame)
            ## 具体控件代码
            ### 输入PIN码
            tk.Label(frame_pin, text='PIN码     ', padx=30).pack(side=tk.LEFT, fill=tk.Y)
            entry_pin = tk.Entry(frame_pin, show='*', width=33)
            entry_pin.pack(side=tk.LEFT)
            frame_pin.pack(side=tk.TOP, expand=True, fill=tk.X)
            # 确定\取消按钮
            frame_confirm = tk.Frame(frame)

            def confirm():
                """UKey界面确定按钮
                获取用户输入，同UKey建立连接
                """
                ukey_name = cb_ukey.get()
                print(f'ukey name: {ukey_name}')  # TODO 尝试建立UKey连接，连接失败的话给出相应警告
                pin_value = entry_pin.get()
                print(f'pin value: {pin_value}')
                frame.destroy()

            def cancel():
                print('取消按钮')
                frame.destroy()

            tk.Label(frame_confirm).pack(side=tk.LEFT, padx=60)
            tk.Button(frame_confirm, text='确定', bg='silver', width=6, height=1,
                      command=confirm).pack(side=tk.LEFT)
            tk.Label(frame_confirm).pack(side=tk.LEFT, padx=35)
            tk.Button(frame_confirm, text='取消', bg='silver', width=6, height=1,
                      command=cancel).pack(side=tk.LEFT)
            ## 具体控件代码
            frame_confirm.pack(side=tk.TOP, fill=tk.X)
        return inner

    def _draw_jlink_configuration(self, parent, width=30, bg='SystemButtonFace', padx=80):  # 给定界面，绘制jlink配置项 TODO 还可以添加字体大小颜色、padx、pady等参数
        """给定界面，绘制jlink通信配置项"""
        # 连接端口

        def update_serial_no(event):
            cb_serial_no.configure(value=self.jlink_com.emulators)

        frame = tk.Frame(parent, bg=bg)
        tk.Label(frame, text='连接端口', bg=bg).pack(side=tk.LEFT)
        cb_serial_no = ttk.Combobox(frame, value=self.jlink_com.emulators, width=width,
                                    state='readonly')
        if self.__jlink_configuration.serial_no in self.jlink_com.emulators:
            index_ = self.jlink_com.emulators.index(self.__jlink_configuration.serial_no)
            cb_serial_no.current(index_)
        cb_serial_no.bind('<Button-1>', update_serial_no)
        if bg == 'white':
            cb_serial_no.bind('<<ComboboxSelected>>',
                              self.__jlink_configuration.update_serial_no(cb_serial_no))
        cb_serial_no.pack(side=tk.LEFT, padx=padx)
        frame.pack(pady=6, fill=tk.X)
        # 接口模式
        frame = tk.Frame(parent, bg=bg)
        tk.Label(frame, text='接口模式', bg=bg).pack(side=tk.LEFT)
        interface_type_values = ['JTAG', 'SWD']
        cb_interface_type = ttk.Combobox(frame, value=interface_type_values, width=width, state='readonly')
        cb_interface_type.current(interface_type_values.index(self.__jlink_configuration.interface_type))
        if bg == 'white':
            cb_interface_type.bind('<<ComboboxSelected>>',
                                   self.__jlink_configuration.update_interface_type(cb_interface_type))
        cb_interface_type.pack(side=tk.LEFT, padx=padx)
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
            if bg == 'white':
                self.__jlink_configuration.update_rate(cb_rate.get())

        frame = tk.Frame(parent, bg=bg)
        tk.Label(frame, text='速率(kHZ)', bg=bg).pack(side=tk.LEFT)
        rate_values = ['5', '10', '20', '30', '50', '100', '200', '300', '400', '500', '600', '750', '900', '1000',
                       '1334', '1600', '2000', '2667', '3200', '4000', '4800', '5334', '6000', '8000',
                       '9600', '12000', 'custom']
        if self.__jlink_configuration.rate not in rate_values:
            rate_values.insert(0, self.__jlink_configuration.rate)
        cb_rate = ttk.Combobox(frame, value=rate_values, width=width, state='readonly')
        cb_rate.bind('<<ComboboxSelected>>', update_cb_rate)
        cb_rate.current(rate_values.index(self.__jlink_configuration.rate))
        cb_rate.pack(side=tk.LEFT, padx=padx-7)
        frame.pack(pady=6, fill=tk.X)
        # MCU
        frame = tk.Frame(parent, bg=bg)
        if bg == 'white':
            tk.Label(frame, text='MCU             ', bg=bg).pack(side=tk.LEFT, padx=0)
        else:
            tk.Label(frame, text='MCU                        ', bg=bg).pack(side=tk.LEFT, padx=0)
        entry_mcu = tk.Entry(frame, show=None, state='disabled', bg=bg,
                             textvariable=self.__mcu_info.device, width=width+3)
        entry_mcu.pack(side=tk.LEFT, padx=2)
        button_mcu = tk.Button(frame, text='...', width=3, height=1, command=self.alter_mcu_win(frame))
        button_mcu.pack(side=tk.LEFT)
        frame.pack(pady=6, fill=tk.X)
        # License存储地址
        frame = tk.Frame(parent, bg=bg)
        if bg == 'white':
            tk.Label(frame, text='存储地址', bg=bg).pack(side=tk.LEFT)
        else:
            tk.Label(frame, text='License存储地址', bg=bg).pack(side=tk.LEFT)
        addr_value = tk.StringVar()
        addr_value.set('0x80000000')
        entry_license_addr = tk.Entry(frame, show=None, textvariable=addr_value, width=width+3)  # TODO 默认值应该时动态获取的
        if bg == 'white':
            entry_license_addr.pack(side=tk.LEFT, padx=37)
        else:
            entry_license_addr.pack(side=tk.LEFT, padx=37)
        frame.pack(pady=6, fill=tk.X)
        # License存储区域大小
        frame = tk.Frame(parent, bg=bg)
        if bg == 'white':
            tk.Label(frame, text='存储区域大小', bg=bg).pack(side=tk.LEFT)
        else:
            tk.Label(frame, text='License存储区域大小', bg=bg).pack(side=tk.LEFT)
        entry_license_size = tk.Entry(frame, show=None, textvariable=self.__mcu_info.flash_size, width=width+3)
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

        def swith_to_product():
            self.disconnect_to_board()  # 每次切换断开所有连接
            if self.frame_debug:
                self.frame_debug.pack_forget()
                self.frame_debug = None
            self.frame_product = self.draw_product_frame(self.window_)
            self.frame_product.pack(expand=True, fill=tk.BOTH)

        def swith_to_debug():
            self.disconnect_to_board()  # 每次切换断开所有连接
            # 绘制调试模式的界面
            if self.frame_product:
                self.frame_product.pack_forget()
                self.frame_product = None
            self.frame_debug = self.draw_debug_frame(self.window_)
            self.frame_debug.pack(expand=True, fill=tk.BOTH)

        # 给菜单对象添加选项
        mode_menu.add_radiobutton(label='生产模式', activebackground='gray',
                                  variable=self.__mode_type, value=ModeEnum.PRODUCT.value,
                                  command=swith_to_product)
        mode_menu.add_radiobutton(label='调试模式', activebackground='gray',
                                  variable=self.__mode_type, value=ModeEnum.DEBUG.value,
                                  command=swith_to_debug)
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

        config_menu.add_command(label='串口设置', activebackground='gray',
                                    command=do_detail_config_port)
        config_menu.add_command(label='J-Link设置', activebackground='gray',
                                    command=do_detail_config_jlink)
        config_menu.add_command(label='日志设置', activebackground='gray',
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
        tk.Label(parent).pack(side=tk.LEFT, fill=tk.Y, padx=1)  # 左边填充
        tk.Label(parent).pack(side=tk.RIGHT, fill=tk.Y, padx=1)  # 右边填充
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
        frame_top = tk.Frame(frame, bg=_BACKGOUND)
        # 界面top_t
        frame_top_t = tk.Frame(frame_top)
        # 界面top_t_l
        frame_top_t_l = tk.Frame(frame_top_t)
        # 界面top_t_l_t
        frame_top_t_l_t = tk.Frame(frame_top_t_l)
        # 界面top_t_l_t_t  TODO 读id和写license的切换按钮
        frame_top_t_l_t_t = tk.Frame(frame_top_t_l_t, width=280, height=30)
        self.draw_frame_top_t_l_t_detail(frame_top_t_l_t_t)
        frame_top_t_l_t_t.pack(side=tk.TOP, fill=tk.X, padx=10)
        frame_top_t_l_t_t.pack_propagate(0)
        # 界面top_t_l_t_b  TODO 读id和写license的状态展示
        frame_top_t_l_t_b = tk.Frame(frame_top_t_l_t, width=280, height=75)
        self.draw_frame_topt_l_t_b_detail(frame_top_t_l_t_b)
        frame_top_t_l_t_b.pack(side=tk.TOP, fill=tk.X, pady=4, padx=10)
        frame_top_t_l_t_b.pack_propagate(0)
        frame_top_t_l_t.pack(side=tk.TOP, fill=tk.X)
        # 界面top_t_l_b TODO HID存储文件\Licesen存储文件\UKey状态展示
        frame_top_t_l_b = tk.Frame(frame_top_t_l, width=280, height=160)
        self.frame_hid_display, self.frame_license_file_display, self.frame_license_ukey_display = self.draw_frame_operate(frame_top_t_l_b)
        frame_top_t_l_b.pack(side=tk.BOTTOM, fill=tk.BOTH, padx=10)
        frame_top_t_l_b.pack_propagate(0)
        frame_top_t_l.pack(side=tk.LEFT, fill=tk.BOTH)
        # 界面top_t-r
        frame_top_t_r = tk.Frame(frame_top_t)
        # 界面top_t_r_l  TODO 结果展示(序号-设备id-结果)
        frame_top_t_r_l = tk.Frame(frame_top_t_r, width=405, height=265)
        self.frame_hid_ret_display, self.frame_license_ret_display = self.draw_frame_ret(frame_top_t_r_l)
        frame_top_t_r_l.pack(side=tk.LEFT, fill=tk.Y)
        frame_top_t_r_l.pack_propagate(0)
        # 界面top_t_r_r
        frame_top_t_r_r = tk.Frame(frame_top_t_r)
        # 界面top_t_r_r_t  TODO 开始\停止按钮
        frame_top_t_r_r_t = tk.Frame(frame_top_t_r_r, width=280, height=125)
        self.draw_start_button(frame_top_t_r_r_t)
        frame_top_t_r_r_t.pack(side=tk.TOP, fill=tk.BOTH)
        frame_top_t_r_r_t.pack_propagate(0)
        # 界面top_t_r_r_b  TODO 状态展示(成功\失败\停止\已完成\空白)
        frame_top_t_r_r_b = tk.Frame(frame_top_t_r_r, bg='white', width=280, height=125)
        self.draw_frame_statistic(frame_top_t_r_r_b)
        frame_top_t_r_r_b.pack(side=tk.BOTTOM, fill=tk.BOTH)
        frame_top_t_r_r_b.pack_propagate(0)
        frame_top_t_r_r.pack(side=tk.RIGHT, fill=tk.BOTH)
        frame_top_t_r.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
        frame_top_t.pack(side=tk.TOP, fill=tk.BOTH)
        # 界面top_b
        frame_top_b = tk.Frame(frame_top)
        # 界面top_b_l  TODO 通信方式(串口\J-Link)选择以及配置项展示
        frame_top_b_l = tk.Frame(frame_top_b, bg='white', width=290, height=320)
        self.draw_frame_connected_type(frame_top_b_l)
        frame_top_b_l.pack(side=tk.LEFT, fill=tk.BOTH, pady=20, padx=10)
        frame_top_b_l.pack_propagate(0)
        # 界面top_b_r
        frame_top_b_r = tk.Frame(frame_top_b)
        # 界面top_b_r_t  TODO 操作明细日志展示
        frame_top_b_r_t = tk.Frame(frame_top_b_r, width=770, height=270)
        self.log_shower_product = self.draw_frame_log_shower(frame_top_b_r_t, width=88, height=20)
        frame_top_b_r_t.pack(side=tk.TOP, fill=tk.BOTH, pady=18, padx=10)
        frame_top_b_r_t.pack_propagate(0)
        # 界面top_b_r_b  TODO 清除按钮
        frame_top_b_r_b = tk.Frame(frame_top_b_r, width=770, height=30)
        tk.Button(frame_top_b_r_b, text='清 除', bg='#D7D7D7', width=8,
                  command=clear_widget(self.log_shower_product)).pack(
            anchor='ne', padx=20, pady=2, ipadx=3, ipady=1)
        frame_top_b_r_b.pack(side=tk.TOP, fill=tk.BOTH)
        frame_top_b_r_b.pack_propagate(0)
        frame_top_b_r.pack(side=tk.LEFT, fill=tk.BOTH)
        frame_top_b.pack(side=tk.BOTTOM, fill=tk.BOTH)
        frame_top.pack(side=tk.TOP, fill=tk.BOTH)
        # 界面bottom  TODO 各类信息(模式\工位\串口状态\运行状态)展示
        frame_bottom = tk.Frame(frame, bg='white')
        self.draw_frame_bottom_statistic_product(frame_bottom)
        frame_bottom.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        return frame

    def draw_frame_top_t_l_t_detail(self, parent):
        """读ID\写License工位选择以及信息展示
        Menu
        Label
        Label
        """

        def swith_read_id(event):
            self.__operate_type.set(OperateEnum.HID.value)
            self.__operate_desc.set('读设备ID')
            self.__operate_desc_detail.set('  从设备读取物理识别码，并保存到本地文件')
            label_read_id.configure(bg='white', fg=_ACTIVE_COLOR)
            menu_bar.configure(bg=_BACKGOUND, fg=_NORMAL_COLOR)
            self.frame_license_file_display.pack_forget()
            self.frame_license_ukey_display.pack_forget()
            self.frame_hid_display.pack(side=tk.TOP, fill=tk.X)
            # 切换统计界面
            self.frame_license_ret_display.pack_forget()
            self.frame_hid_ret_display.pack(side=tk.LEFT, fill=tk.BOTH)

        def swith_to_license_file():
            if self.__operate_desc.get() == '读设备ID':  # 表示从读ID界面切换过来
                self.frame_hid_ret_display.pack_forget()
                self.frame_license_ret_display.pack(side=tk.LEFT, fill=tk.BOTH)
            self.__operate_desc.set('写License-从License文件')
            self.__operate_desc_detail.set('  从本地文件获取License，并写入硬件设备  ')
            label_read_id.configure(bg=_BACKGOUND, fg=_NORMAL_COLOR)
            menu_bar.configure(bg='white', fg=_ACTIVE_COLOR)
            self.frame_hid_display.pack_forget()
            self.frame_license_ukey_display.pack_forget()
            self.frame_license_file_display.pack(side=tk.TOP, fill=tk.X)

        def swith_to_license_ukey():
            if self.__operate_desc.get() == '读设备ID':  # 表示从读ID界面切换过来
                self.frame_hid_ret_display.pack_forget()
                self.frame_license_ret_display.pack(side=tk.LEFT, fill=tk.BOTH)
            self.__operate_desc.set('写License-从UKey')
            self.__operate_desc_detail.set('  从UKey获取License，并写入硬件设备      ')
            label_read_id.configure(bg=_BACKGOUND, fg=_NORMAL_COLOR)
            menu_bar.configure(bg='white', fg=_ACTIVE_COLOR)
            self.frame_hid_display.pack_forget()
            self.frame_license_file_display.pack_forget()
            self.frame_license_ukey_display.pack(side=tk.TOP, fill=tk.X)

        # 创建读ID Button
        label_read_id = tk.Label(parent, text='读ID', bg='white', fg=_ACTIVE_COLOR, width=10, bd=3, padx=3, pady=1)  # TODO 鼠标滑过更改字体
        label_read_id.bind('<ButtonRelease-1>', swith_read_id)
        label_read_id.pack(side=tk.LEFT)

        # 创建写License菜单
        menu_bar = tk.Menubutton(parent, text='写License', bg=_BACKGOUND, fg=_NORMAL_COLOR)
        # 定义写License子菜单
        license_menu = tk.Menu(menu_bar, tearoff=0)  # 默认不下拉
        license_menu.add_radiobutton(label='从License文件', activebackground='gray',
                                     variable=self.__operate_type, value=OperateEnum.LICENSE_FILE.value,
                                     command=swith_to_license_file)
        license_menu.add_radiobutton(label='从UKey', activebackground='gray',
                                     variable=self.__operate_type, value=OperateEnum.LICENSE_UKEY.value,
                                     command=swith_to_license_ukey)
        menu_bar.config(menu=license_menu)
        menu_bar.pack(side=tk.LEFT)

    def draw_frame_topt_l_t_b_detail(self, parent):
        """
        根据当前的工位，展示相应的信息
        """
        # 黑色加粗大字
        frame_top = tk.Frame(parent, bg='white')
        tk.Label(frame_top, textvariable=self.__operate_desc, font=('微软雅黑', 12),
                 padx=15, bg='white').pack(side=tk.LEFT, pady=16)
        frame_top.pack(side=tk.TOP, expand=True, fill=tk.X)
        # 灰色小字
        frame_bottom = tk.Frame(parent, bg='white')
        tk.Label(frame_bottom, textvariable=self.__operate_desc_detail, fg='gray',
                 padx=15, font=('微软雅黑', 9), bg='white').pack(side=tk.LEFT)
        frame_bottom.pack(side=tk.TOP, expand=True, fill=tk.X)
        # 底层占位
        frame_placeholder = tk.Frame(parent, bg='white')
        tk.Label(frame_placeholder, text=' ', bg='white').pack()
        frame_placeholder.pack(side=tk.TOP, expand=True, fill=tk.X)

    def draw_frame_operate(self, parent):
        """绘制读HID配置项、license_file配置项、license_ukey配置项
        创建三个frame，根据operte_type属性进行pack和pack_forget
        """
        # 界面1：读hid的配置项
        frame_hid_display = tk.Frame(parent, bg='white')
        ## 占位
        frame_place_holder_1 = tk.Frame(frame_hid_display, bg='white')
        tk.Label(frame_place_holder_1, pady=20, text=' ', bg='white').pack()
        frame_place_holder_1.pack(side=tk.TOP, expand=True, fill=tk.X)
        ## 描述文字
        frame_1 = tk.Frame(frame_hid_display, bg='white')
        tk.Label(frame_1, text='保存设备ID到文件...', font=('微软雅黑', 12), bg='white',
                 padx=15).pack(anchor='nw')
        frame_1.pack(side=tk.TOP, expand=True, fill=tk.X)
        ## 文本选择框
        frame_2 = tk.Frame(frame_hid_display, bg='white')
        filepath_entry = tk.Entry(frame_2, textvariable=self.__filepath_hid, width=20)
        filepath_entry.pack(side=tk.LEFT, padx=18, pady=18)
        ## 按钮
        def record_filepath_hid():
            """
            点击选择按钮后，触发方法
            1 校验选择文件是否合法
            2 记录选择文件
            """
            filepath = filedialog.askopenfilename()  # 打开一个已经存在的文件
            if filepath != '':
                if check_file_suffix(filepath):  # 属于excel文件
                    self.__filepath_hid.set(filepath)
                    self.succ_hid = read_HID(filepath)  # 将已经存储过的hid读出来
                else:
                    tkinter.messagebox.showwarning(title='Warning',
                                                   message='请选择Excel类型文件')

        tk.Button(frame_2, text='选择', width=5, bg='#D7D7D7', command=record_filepath_hid).pack(side=tk.LEFT,
                                                                                               padx=6)
        ### 填充文本选择框以及按钮
        frame_2.pack(side=tk.TOP, fill=tk.X)
        frame_hid_display.pack(side=tk.TOP, fill=tk.X)

        # 界面2：license_file写license的配置项
        frame_license_file_display = tk.Frame(parent)
        ## 占位
        frame_place_holder_2 = tk.Frame(frame_license_file_display, bg='white')
        tk.Label(frame_place_holder_2, pady=10, text=' ', bg='white').pack()
        frame_place_holder_2.pack(side=tk.TOP, expand=True, fill=tk.X)
        ## 描述文字  TODO 此处命名为frame_1，会覆盖掉读hid界面的frame_1吗？需要测试验证
        frame_1 = tk.Frame(frame_license_file_display, bg='white')
        tk.Label(frame_1, text='选择本地License文件...', font=('微软雅黑', 12), bg='white',
                 pady=5, padx=15).pack(side=tk.LEFT, fill=tk.X)
        frame_1.pack(side=tk.TOP, expand=True, fill=tk.X)
        ## License文件选择框
        frame_2 = tk.Frame(frame_license_file_display, bg='white')
        tk.Label(frame_2, text='    ', bg='white').pack(side=tk.LEFT)
        filepath_entry = tk.Entry(frame_2, textvariable=self.__filepath_license, width=20)
        filepath_entry.pack(side=tk.LEFT)
        ## 按钮
        tk.Label(frame_2, text='  ', bg='white').pack(side=tk.LEFT)
        tk.Button(frame_2, text='选择', width=5, bg='#918B8B', command=self.record_filepath_license).pack(side=tk.LEFT)
        frame_2.pack(side=tk.TOP, fill=tk.X)
        frame_place_holder_2_2 = tk.Frame(frame_license_file_display, bg='white')
        tk.Label(frame_place_holder_2_2, pady=10, text=' ', bg='white').pack(side=tk.TOP)
        tk.Label(frame_place_holder_2_2, pady=10, text=' ', bg='white').pack(side=tk.TOP)
        frame_place_holder_2_2.pack(side=tk.TOP, expand=True, fill=tk.X)

        # 界面3：ukey写license的配置项
        frame_license_ukey_display = tk.Frame(parent)
        ## ukey连接状态信息
        frame_1 = tk.Frame(frame_license_ukey_display, bg='white')
        tk.Label(frame_1, textvariable=self.__ukey_info.desc, font=('微软雅黑', 12),
                 padx=15, pady=18, bg='white').pack(side=tk.LEFT)
        frame_1.pack(side=tk.TOP, expand=True, fill=tk.X)
        ## 灰色小字
        frame_2 = tk.Frame(frame_license_ukey_display, bg='white')
        ## TODO 此处需要添加一个图片(表示USB)
        label_ukey = tk.Label(frame_2, textvariable=self.__ukey_info.desc_child, fg='gray',
                 padx=15, font=('微软雅黑', 9), bg='white')  # TODO 此处需要绑定UKey pin的验证弹窗
        label_ukey.pack(side=tk.LEFT)
        label_ukey.bind('<Button-1>', self.alter_ukey_connect(frame_license_ukey_display))
        frame_2.pack(side=tk.TOP, expand=True, fill=tk.X)
        ## 底层占位
        frame_place_holder_3 = tk.Frame(frame_license_ukey_display, bg='white')
        tk.Label(frame_place_holder_3, text=' ', bg='white').pack()
        frame_place_holder_3.pack(side=tk.TOP, expand=True, fill=tk.X)

        return frame_hid_display, frame_license_file_display, frame_license_ukey_display

    def draw_frame_ret(self, parent):
        """绘制结果展示界面
        创建两个frame，根据operate_type进行pack和pack_forget()
        """
        # hid界面
        frame_hid_ret_display = tk.Frame(parent, bg='white')
        columns_1 = [' ', '设备ID', '结果']  # 定义列名称
        displaycolumns_1 = columns_1  # 表示哪些列可以显示

        ## 设置滚动条
        sb = tk.Scrollbar(frame_hid_ret_display)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_hid = ttk.Treeview(frame_hid_ret_display, columns=columns_1,
                              displaycolumns=displaycolumns_1, show='headings',
                              yscrollcommand=sb.set)
        sb.config(command=self.tree_hid.yview)
        ## 设置结果为失败的行标签对应的字体颜色
        self.tree_hid.tag_configure('tag_failed', foreground='red')
        ## 设置表格文字居中，以及表格宽度
        for column in columns_1:
            self.tree_hid.column(column, anchor='center', width=120, minwidth=120)
        ## 设置表格头部标题
        for column in columns_1:
            self.tree_hid.heading(column, text=column)
        self.tree_hid.pack(side=tk.TOP, fill=tk.BOTH, padx=15, pady=20)

        frame_hid_ret_display.pack(side=tk.LEFT, fill=tk.BOTH)

        # license界面
        frame_license_ret_display = tk.Frame(parent, bg='white')
        columns_2 = [' ', '设备ID', '组件ID', '结果']
        displaycolumns_2 = columns_2

        ## 设置滚动条
        sb_2 = tk.Scrollbar(frame_license_ret_display)
        sb_2.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_license = ttk.Treeview(frame_license_ret_display, columns=columns_2,
                              displaycolumns=displaycolumns_2, show='headings',
                              yscrollcommand=sb_2.set)
        sb_2.config(command=self.tree_license.yview)
        ## 设置结果为失败的行标签对应的字体颜色
        self.tree_license.tag_configure('tag_failed', foreground='red')
        ## 设置表格文字居中，以及表格宽度
        for column in columns_2:
            self.tree_license.column(column, anchor='center', width=90, minwidth=90)
        ## 设置表格头部标题
        for column in columns_2:
            self.tree_license.heading(column, text=column)
        ## 往表格内添加内容  TODO 以二维列表形式存储写license操作的结果[(序号，设备ID，组件ID，结果), ...]
        self.tree_license.pack(side=tk.TOP, fill=tk.BOTH, padx=15, pady=20)
        return frame_hid_ret_display, frame_license_ret_display

    def draw_start_button(self, parent):
        """绘制开始\停止按钮
        TODO 通信逻辑部分从此处开始
        """
        frame = tk.Frame(parent)

        def start():
            """点击开始按钮的业务流程"""
            if self.btn_start.configure().get('text')[-1] == '开  始':  # TODO 继续往下写实际的业务逻辑
                print('开始')
                message_file = self.__verify_file()
                if message_file:
                    tk.messagebox.showwarning(title='WARNING',
                                              message=message_file)
                    return
                message_conn = self.__verify_conn()
                if message_conn:
                    tk.messagebox.showwarning(title='WARNING',
                                              message=message_conn)
                # TODO 具体的通信逻辑
                self.__turn_on()
                try:
                    if self.__mode_type.get() == 'PRODUCT':  # 生产模式，连续操作，加入超时机制
                        if self.__operate_type.get() == 'HID':  # 读HID操作
                            t = Thread(target=self.read_id, daemon=True)
                            t.start()
                        elif self.__operate_type.get() == 'LICENSE_FILE':  # 根据license文件写license操作
                            t = Thread(target=self.write_license_by_file, daemon=True)
                            t.start()
                        elif self.__operate_type.get() == 'LICENSE_UKEY':  # 根据UKey进行写license操作
                            self.write_license_by_ukey()
                except Exception as e:
                    logger.exception(e)
                    self.disconnect_to_board()
                    self.__turn_off()
                # 因为开始按钮只存在于生产模式界面，所以没有其余分支
            else:
                self.disconnect_to_board()
                self.__turn_off()

        self.btn_start = tk.Button(frame, text='开  始', font=('微软雅黑', 12, 'bold'), fg='darkgreen', bg='lightgrey',
                  width=10, height=1, command=start)
        self.btn_start.pack(side=tk.LEFT, pady=20, padx=20)

        frame.pack(side=tk.TOP, fill=tk.X)

    def draw_frame_statistic(self, parent):
        # 执行结果信息展示界面
        # TODO 此处应该使用变量，并且记录该Label，插入时候控制字体颜色
        self.statistic_product_label = tk.Label(parent, font=('微软雅黑', 24), bg='white')
        self.__update_statistic()
        self.statistic_product_label.pack(side=tk.TOP, pady=45)

    # 通信方式(串口\J-Link)展示以及配置界面
    def draw_frame_connected_type(self, parent, type='product'):
        # 两个按钮的frame
        frame_1 = tk.Frame(parent)

        def swith_to_port_conn(event):
            """点击串口按钮"""
            if self.__conn_type.conn_type.get() == '串口通信' and self.__conn_type.mode == self.__mode_type.get():
                return
            frame_3.pack_forget()
            frame_2.pack(side=tk.TOP, fill=tk.BOTH)
            self.__conn_type.swith_to_port(self.__mode_type.get())  # 更新为串口通信
            label_port.configure(fg=_ACTIVE_COLOR, bg='white')
            label_jlink.configure(fg='gray', bg=_BACKGOUND)

        def swith_to_jlink_conn(event):
            """点击J-Link按钮"""
            if self.__conn_type.conn_type.get() == 'J-Link通信' and self.__conn_type.mode == self.__mode_type.get():
                return
            print('更新为jlink通信')
            frame_2.pack_forget()
            frame_3.pack(side=tk.TOP, fill=tk.BOTH)
            self.__conn_type.swith_to_jlink(self.__mode_type.get())
            label_jlink.configure(fg=_ACTIVE_COLOR, bg='white')
            label_port.configure(fg='gray', bg=_BACKGOUND)

        label_port = tk.Label(frame_1, text='串口', bg='white', fg=_ACTIVE_COLOR,
                             width=10, bd=3, padx=3, pady=1)
        label_port.bind('<ButtonRelease-1>', swith_to_port_conn)
        label_port.pack(side=tk.LEFT)

        label_jlink = tk.Label(frame_1, text='J-Link', bg=_BACKGOUND, fg='gray',
                              width=10, bd=3, padx=3, pady=1)
        label_jlink.bind('<ButtonRelease-1>', swith_to_jlink_conn)
        label_jlink.pack(side=tk.LEFT)

        frame_1.pack(side=tk.TOP, fill=tk.X)

        # 展示以及配置项的frame
        frame_2 = tk.Frame(parent, bg='white')
        ## 描述信息
        if type == 'product':  # 生产模式
            tk.Label(frame_2, textvariable=self.__conn_type.conn_type, font=('微软雅黑', 12),
                     bg='white').pack(padx=12, pady=13, anchor='nw')
        elif type == 'debug':  # 调试模式需要添加一个连接的按钮
            frame_2_t = tk.Frame(frame_2, bg='white')
            ### 左边放置描述信息
            frame_2_t_l = tk.Frame(frame_2_t, bg='white')
            tk.Label(frame_2_t_l, textvariable=self.__conn_type.conn_type, font=('微软雅黑', 12),
                     bg='white').pack(padx=12, pady=13, anchor='nw')
            frame_2_t_l.pack(side=tk.LEFT, fill=tk.Y)
            ### 右边放置连接按钮
            frame_2_t_r = tk.Frame(frame_2_t, bg='white')
            self.btn_start_debug = tk.Button(frame_2_t_r, text='串口连接', bg='#D7D7D7', command=self.connect_to_port)
            self.btn_start_debug.pack(side=tk.BOTTOM, padx=50, pady=5)  # TODO 串口连接
            frame_2_t_r.pack(side=tk.RIGHT, fill=tk.Y)
            frame_2_t.pack(side=tk.TOP, fill=tk.X)

        frame_2.pack(side=tk.TOP, fill=tk.BOTH)
        ## 配置信息
        cb_port, cb_baudrate, cb_data, cb_check, cb_stop, cb_stream_controller = \
        self._draw_serial_port_configuration(frame_2, width=22, bg='white')
        if type == 'product':
            self.__serial_port_info_product = SerialPortInfo(cb_port, cb_baudrate, cb_data,
                                                             cb_check, cb_stop, cb_stream_controller)
        elif type == 'debug':
            self.__serial_port_info_debug = SerialPortInfo(cb_port, cb_baudrate, cb_data,
                                                           cb_check, cb_stop, cb_stream_controller)

        # 展示以及配置项的frame
        frame_3 = tk.Frame(parent, bg='white')
        ## 描述信息
        if type == 'product':  # 生产模式
            tk.Label(frame_3, textvariable=self.__conn_type.conn_type, font=('微软雅黑', 12),
                     bg='white').pack(padx=12, pady=13, anchor='nw')
        elif type == 'debug':  # 调试模式需要添加一个连接的按钮
            frame_3_t = tk.Frame(frame_3, bg='white')
            ### 左边放置描述信息
            frame_3_t_l = tk.Frame(frame_3_t, bg='white')
            tk.Label(frame_3_t_l, textvariable=self.__conn_type.conn_type, font=('微软雅黑', 12),
                     bg='white').pack(padx=12, pady=13, anchor='nw')
            frame_3_t_l.pack(side=tk.LEFT, fill=tk.Y)
            ### 右边放置连接按钮
            frame_3_t_r = tk.Frame(frame_3_t, bg='white')
            tk.Button(frame_3_t_r, text='J-Link连 接', bg='#D7D7D7').pack(side=tk.BOTTOM, padx=50, pady=5)  # TODO J-Link连接
            frame_3_t_r.pack(side=tk.RIGHT, fill=tk.Y)
            frame_3_t.pack(side=tk.TOP, fill=tk.X)

        ## 配置信息
        cb_serial_no, cb_interface_type, cb_rate, entry_mcu, entry_license_addr, entry_license_size = \
            self._draw_jlink_configuration(frame_3, bg='white', width=15, padx=37)
        if type == 'product':
            self.__jlink_info_product = JLinkInfo(cb_serial_no, cb_interface_type, cb_rate, entry_mcu,
                                                  entry_license_addr, entry_license_size)
            self.entry_mcu_product, self.entry_license_addr_product, \
            self.entry_license_size_product = entry_mcu, entry_license_addr, entry_license_size
        elif type == 'debug':
            self.__jlink_info_debug = JLinkInfo(cb_serial_no, cb_interface_type, cb_rate, entry_mcu,
                                                entry_license_addr, entry_license_size)
            self.entry_mcu_debug, self.entry_license_addr_debug, \
            self.entry_license_size_debug = entry_mcu, entry_license_addr, entry_license_size

    def draw_frame_log_shower(self, parent, width, height):
        """绘制日志打印控件"""
        # 滚动条和Text控件
        sb = tk.Scrollbar(parent)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        log_shower = tk.Text(parent, width=width, height=height, yscrollcommand=sb.set)
        log_shower.insert(tk.END, '默认关闭操作日志\n')
        log_shower.tag_config('error', foreground='red', font=_FONT_B)
        log_shower.tag_config('confirm', foreground='green', font=_FONT_B)
        log_shower.tag_config('warn', foreground='blue', font=_FONT_B)
        sb.config(command=log_shower.yview)
        log_shower.pack()
        return log_shower

    # 绘制底部状态栏信息
    def draw_frame_bottom_statistic_product(self, parent):
        """
        模式： 生产模式(绿色)
        工位： 读设备ID/写License(绿色)
        串口状态： 断开(黑色)/XXX 已连接(绿色)
        运行状态： 工作中(绿色)/停止(黑色)
        """  # TODO 需要添加占位Label
        # 模式-key
        tk.Label(parent, text='模式：', bg='white').pack(side=tk.LEFT, padx=2)
        # 模式-value
        tk.Label(parent, text='生产模式    ', fg='green', bg='white').pack(side=tk.LEFT)
        tk.Label(parent, text='', bg='white').pack(side=tk.LEFT, padx=25)
        # 工位-key
        tk.Label(parent, text='工位：', bg='white').pack(side=tk.LEFT, padx=2)
        # 工位-value  TODO 更新颜色
        tk.Label(parent, textvariable=self.__operate_desc, bg='white').pack(side=tk.LEFT)
        tk.Label(parent, text='', bg='white').pack(side=tk.LEFT, padx=25)
        # 串口状态-key
        tk.Label(parent, text='串口状态：', bg='white').pack(side=tk.LEFT, padx=2)
        # 串口状态-value
        tk.Label(parent, textvariable=self.port_com.status, bg='white').pack(side=tk.LEFT)
        tk.Label(parent, text='', bg='white').pack(side=tk.LEFT, padx=25)
        # 运行状态-key
        tk.Label(parent, text='运行状态：', bg='white').pack(side=tk.LEFT, padx=2)
        # 运行状态-value  TODO  根据流程是否在进行或者等待状态来显示停止或者工作中
        tk.Label(parent, text='停止', bg='white').pack(side=tk.LEFT)

    # 以下为调试模式界面代码
    def draw_debug_frame(self, parent):
        """绘制调试模式界面"""
        frame = tk.Frame(parent)
        # frame_top
        frame_top = tk.Frame(frame)
        ## frame_top_l
        frame_top_l = tk.Frame(frame_top)
        ### frame_top_l_1 通讯方式配置项展示界面(340*290)
        frame_top_l_1 = tk.Frame(frame_top_l, width=320, height=300, bg='red', bd=1, relief='solid')
        self.draw_frame_connected_type(frame_top_l_1, type='debug')
        frame_top_l_1.pack(side=tk.TOP, fill=tk.X, padx=10, pady=2)
        frame_top_l_1.pack_propagate(0)
        ### frame_top_l_2 操作记录日志(340*270)
        frame_top_l_2 = tk.Frame(frame_top_l, width=320, height=280, bg='white', bd=1, relief='solid')
        self.log_shower_debug = self.draw_frame_log_shower(frame_top_l_2, width=42, height=18)
        #### 清除按钮
        tk.Button(frame_top_l_2, text='清 除', bg='#D7D7D7', height=1, width=5,
                  command=clear_widget(self.log_shower_debug)).pack(side=tk.RIGHT, padx=10, pady=3)
        frame_top_l_2.pack(side=tk.TOP, fill=tk.X, padx=10, pady=2)
        frame_top_l_2.pack_propagate(0)
        frame_top_l.pack(side=tk.LEFT, fill=tk.Y)
        ## frame_top_r
        frame_top_r = tk.Frame(frame_top)
        ### frame_top_r_1(680*260)
        frame_top_r_1 = tk.Frame(frame_top_r, width=700, height=235, bd=1, relief='solid')
        # 读hid，读license，单个写license操作界面
        self.draw_frame_hid_debug(frame_top_r_1)
        frame_top_r_1.pack(side=tk.TOP, fill=tk.X, padx=10, pady=2)
        frame_top_r_1.pack_propagate(0)
        ### frame_top_r_2(680*270)
        frame_top_r_2 = tk.Frame(frame_top_r, width=700, height=270, bd=1, relief='solid')
        #### 批量写license操作界面
        self.draw_frame_license_debug(frame_top_r_2)
        frame_top_r_2.pack(side=tk.TOP, fill=tk.X, padx=10, pady=2)
        frame_top_r_2.pack_propagate(0)
        ### frame_top_r_3(680*30)
        frame_top_r_3 = tk.Frame(frame_top_r, width=700, height=80, bd=1, relief='solid')
        #### 读取设备ID，并选择文件进行存储
        self.draw_frame_record_hid(frame_top_r_3)
        frame_top_r_3.pack(side=tk.TOP, fill=tk.X, padx=10, pady=2)
        frame_top_r_3.pack_propagate(0)
        frame_top_r.pack(side=tk.RIGHT, fill=tk.Y)
        frame_top.pack(side=tk.TOP, fill=tk.X)
        # frame_bottom
        frame_bottom = tk.Frame(frame, width=1040, height=30, bg='white')
        self.draw_frame_bottom_statistic_debug(frame_bottom)
        frame_bottom.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        frame_bottom.pack_propagate(0)
        return frame

    def draw_frame_hid_debug(self, parent):
        """
        在界面上绘制调试模式下的HID相关操作
        1 读取设备HID，展示
        2 读取设备已经写过License信息，并展示
        3 输入组件ID和License，做单次License写入
        4 清除当前展示\输入的所有信息
        """
        # 右侧文字提示以及清除按钮
        frame_r = tk.Frame(parent, bg='white')
        ## 文字提示
        tk.Label(frame_r, text='与设备交\n互，读设备\n信息，写\nLicense等操\n作', bg='white',
                 fg='#707070').pack(padx=10, pady=10)

        def clean_1():
            """
            清除个别控件的展示信息
            Returns:

            """
            # 清空设备ID
            hid.set('')
            # 清空license展示
            for i in tree_1.get_children():
                tree_1.delete(i)
            # 清空组件ID
            etn_component.delete(0, tk.END)
            # 清空License
            etn_license.delete(0, tk.END)


        ## 清除按钮
        tk.Button(frame_r, text='清除', font=('微软雅黑', 8), bg='#D7D7D7', command=clean_1).pack(
            side=tk.BOTTOM, padx=10, pady=10, ipadx=10
        )
        frame_r.pack(side=tk.RIGHT, fill=tk.Y, padx=1)

        # 读hid 文字label,展示entry,执行按钮
        frame_l_t = tk.Frame(parent, bg='white')
        ## 具体细节代码
        hid = tk.StringVar()
        def get_hid():  # 获取设备ID按钮执行方法
            hid_value = self.read_id(if_keep=False)  # 表示调试模式
            hid.set(hid_value)
        ### 文字标签
        tk.Label(frame_l_t, text='设备ID   ', bg='white').pack(side=tk.LEFT, padx=3, ipady=5)
        ### 执行按钮
        tk.Button(frame_l_t, text='读取设备ID ', bg='#D7D7D7', command=get_hid
                  ).pack(side=tk.RIGHT, padx=3, pady=3, ipadx=4)
        ### 输入/展示文字框
        ety_hid = tk.Entry(frame_l_t, textvariable=hid, width=45)
        ety_hid.pack(side=tk.LEFT, padx=3, pady=3)
        frame_l_t.pack(side=tk.TOP, fill=tk.X, padx=1)

        # 读license 文字label,展示treeview,执行按钮
        frame_l_m = tk.Frame(parent, bg='white')
        ## 具体细节代码
        ### 文字标签
        tk.Label(frame_l_m, text='License\n详情', bg='white').pack(side=tk.LEFT, padx=3, ipady=5)
        ### 执行按钮
        tk.Button(frame_l_m, text='读取License', bg='#D7D7D7'
                  ).pack(side=tk.RIGHT, padx=3, pady=3, ipadx=3)  # TODO 绑定读取License方法
        ### 展示表格
        frame_inner = tk.Frame(frame_l_m)
        columns = ['组件ID', 'License']
        sb_1 = tk.Scrollbar(frame_inner)
        sb_1.pack(side=tk.RIGHT, fill=tk.Y)
        tree_1 = ttk.Treeview(frame_inner, columns=columns, displaycolumns=columns,
                              show='headings', yscrollcommand=sb_1.set, height=5)  # 创建表格对象
        sb_1.config(command=tree_1.yview)
        frame_inner.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=10)
        #### 设置表格文字居中，以及表格宽度
        tree_1.column('组件ID', anchor='center', width=50, minwidth=50)
        tree_1.column('License', anchor='center', width=260, minwidth=260)
        #### 设置头部标题
        for column in columns:
            tree_1.heading(column, text=column)
        #### 往表格里添加数据  TODO 真实的添加逻辑
        contents = [(1002, 'l7JnPeubhXy0LDrsaftMOI='),
                    (1003, 'l8JnPeubhXy0LDrsaftMOI='),
                    (1004, 'l9JnPeubhXy0LDrsaftMOI=')]

        for idx, content in enumerate(contents):
            tree_1.insert('', idx, values=content)
        tree_1.pack(side=tk.LEFT, fill=tk.X)

        frame_l_m.pack(side=tk.TOP, fill=tk.X, padx=1)
        # 写license 文字label,输入entry,执行按钮
        frame_l_b = tk.Frame(parent, bg='white')
        ## 具体细节代码
        frame_1 = tk.Frame(frame_l_b, bg='white')
        ### 文字
        tk.Label(frame_1, text='组件ID', bg='white').pack(side=tk.LEFT, pady=6, padx=3)
        ### 输入框(输入组件ID)
        etn_component = tk.Entry(frame_1, width=45)
        etn_component.pack(side=tk.LEFT, padx=15)
        frame_1.pack(side=tk.TOP, fill=tk.X)
        frame_2 = tk.Frame(frame_l_b, bg='white')
        ### 文字
        tk.Label(frame_2, text='License', bg='white').pack(side=tk.LEFT, pady=6, padx=3)
        ### 输入框(输入要写入的license)
        etn_license = tk.Entry(frame_2, width=45)
        etn_license.pack(side=tk.LEFT, padx=10)
        ### 执行按钮
        tk.Button(frame_2, text='写License', bg='#D7D7D7', command=self.write_license(etn_component, etn_license),
                  ).pack(side=tk.RIGHT, padx=3, pady=3, ipadx=8, ipady=3)
        frame_2.pack(side=tk.TOP, fill=tk.BOTH)
        frame_l_b.pack(side=tk.TOP, fill=tk.BOTH, padx=1, pady=2)

    # 批量写license界面
    def draw_frame_license_debug(self, parent):
        # 右侧文字提示以及清除按钮
        frame_r = tk.Frame(parent, bg='white')
        ## 文字提示
        tk.Label(frame_r, text='与设备交\n互，可批量\n写license操\n作', bg='white',
                 fg='#707070').pack(padx=2, pady=10)

        def clean_2():
            """清除一些控件的信息展示"""
            # 清除设备ID
            ety_hid.delete(0, tk.END)
            # 清除获取到的license信息
            for i in tree.get_children():
                tree.delete(i)

        ## 清除按钮
        tk.Button(frame_r, text='清除', font=('微软雅黑', 8), bg='#D7D7D7', command=clean_2).pack(
            side=tk.BOTTOM, padx=10, pady=10, ipadx=10
        )
        frame_r.pack(side=tk.RIGHT, fill=tk.Y, padx=1)
        ## 选择license来源以及展示界面
        frame_l_t = tk.Frame(parent)
        license_source = tk.StringVar()
        license_source.set('license_file')

        def swith_to_file_license():
            """选择license来源为本地license文件
            1 右侧状态展示栏为查找license file的输入框
            """
            print(license_source.get())
            frame_l_t_r_license_ukey.pack_forget()
            frame_l_t_r_license_file.pack(side=tk.TOP, expand=True, fill=tk.BOTH)

        def swith_to_ukey_license():
            """选择license来源为UKey
            1 右侧状态展示栏为连接UKey/UKey状态展示界面
            """
            print(license_source.get())
            frame_l_t_r_license_file.pack_forget()
            frame_l_t_r_license_ukey.pack(side=tk.TOP, expand=True, fill=tk.BOTH)

        ### 选择license来源界面
        frame_l_t_l = tk.Frame(frame_l_t, bg='white', width=250, height=94)
        #### TODO 具体细节代码
        ##### 文字标签
        tk.Label(frame_l_t_l, text='请选择License来源：', bg='white').pack(anchor='nw', pady=8)
        ##### 来源的单选框
        tk.Radiobutton(frame_l_t_l, text='从文件获取License  ', variable=license_source,
                       value='license_file', bg='white',
                       command=swith_to_file_license).pack(side=tk.TOP)
        tk.Radiobutton(frame_l_t_l, text='从UKey获取License', variable=license_source,
                       value='license_ukey', bg='white',
                       command=swith_to_ukey_license).pack(side=tk.TOP)
        frame_l_t_l.pack(side=tk.LEFT)
        frame_l_t_l.pack_propagate(0)
        ### license来源详情界面(文件/UKey)
        frame_l_t_r = tk.Frame(frame_l_t, padx=1, pady=2, width=265, height=100)
        #### TODO 具体细节代码
        frame_l_t_r_license_file = tk.Frame(frame_l_t_r, bg='white')  # 当来源为license-file时候展示
        tk.Label(frame_l_t_r_license_file, text='选择本地License文件...', bg='white').pack(anchor='nw', pady=10)
        ety_license_file = tk.Entry(frame_l_t_r_license_file, textvariable=self.__filepath_license, width=25)
        ety_license_file.pack(side=tk.LEFT, padx=15)
        tk.Button(frame_l_t_r_license_file, text='选择', bg='#D7D7D7', width=5,
                  command=self.record_filepath_license).pack(side=tk.RIGHT, pady=2, padx=4)

        frame_l_t_r_license_ukey = tk.Frame(frame_l_t_r)  # 当来源为license-ukey时候展示

        ## ukey连接状态信息
        frame_1 = tk.Frame(frame_l_t_r_license_ukey, bg='white')
        tk.Label(frame_1, textvariable=self.__ukey_info.desc, font=('微软雅黑', 12),
                 padx=15, pady=18, bg='white').pack(side=tk.LEFT)
        frame_1.pack(side=tk.TOP, expand=True, fill=tk.X)
        ## 灰色小字
        frame_2 = tk.Frame(frame_l_t_r_license_ukey, bg='white')
        ## TODO 此处需要添加一个图片(表示USB)
        label_ukey = tk.Label(frame_2, textvariable=self.__ukey_info.desc_child, fg='gray',
                              padx=15, font=('微软雅黑', 12), bg='white')  # TODO 此处需要绑定UKey pin的验证弹窗
        label_ukey.pack(side=tk.BOTTOM)
        label_ukey.bind('<Button-1>', self.alter_ukey_connect(frame_l_t_r_license_ukey))
        frame_2.pack(side=tk.TOP, expand=True, fill=tk.X)

        frame_l_t_r_license_file.pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=1, pady=2)
        frame_l_t_r.pack(side=tk.LEFT, fill=tk.Y)
        frame_l_t_r.pack_propagate(0)
        frame_l_t.pack(side=tk.TOP, fill=tk.X)
        ## 输入设备ID查找license界面
        frame_l_m = tk.Frame(parent, bg='white')

        def get_license():
            """根据用户输入的设备ID，通过本地license文件/UKey查找相应的license"""
            hid = ety_hid.get()
            if not hid:
                tk.messagebox.showwarning(title='Warning',
                                          message='请输入查找License的组件ID')
                return
            if not self.__filepath_license.get():
                tk.messagebox.showwarning(title='Warning',
                                          message='请先选择本地license文件')
                return

            component_license_map = self.hid_license_map.hid_license_map.get(hid)
            if not component_license_map:
                self.log_shower_insert(f'设备ID{hid}本地license文件没有查找到对应的license\n', 'error')
                return
            # 先清空展示信息
            for i in tree.get_children():
                tree.delete(i)
            for component_id, license_ in component_license_map.items():
                tree.insert('', tk.END, values=(component_id, license_))
            self.log_shower_insert(f'设备ID{hid}从本地获取License完成\n')

        tk.Label(frame_l_m, text='设备ID', bg='white').pack(side=tk.LEFT, pady=10, padx=2)
        ety_hid = tk.Entry(frame_l_m, width=30)
        ety_hid.pack(side=tk.LEFT, pady=10)
        tk.Button(frame_l_m, text='获取License', bg='#D7D7D7',
                  command=get_license).pack(side=tk.LEFT, pady=10, padx=30, ipadx=2)
        frame_l_m.pack(side=tk.TOP, fill=tk.X)
        ## 展示查找到的组件-license和批量写界面
        frame_l_b = tk.Frame(parent, bg='white')
        ### treeview展示查找到的组件-license信息，以及执行写入按钮
        #### 执行按钮
        frame_l_b_r = tk.Frame(frame_l_b, width=100, height=170, bg='white')
        frame_l_b_r.pack(side=tk.RIGHT)
        frame_l_b_r.pack_propagate(0)
        #### 展示license的treeview
        frame_l_b_l = tk.Frame(frame_l_b, width=320, height=170, bg='white')
        columns = ['组件ID', 'License']
        sb = tk.Scrollbar(frame_l_b_l)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        tree = ttk.Treeview(frame_l_b_l, columns=columns, displaycolumns=columns,
                            show='headings', yscrollcommand=sb.set, height=4)
        tk.Button(frame_l_b_r, text='批量写license', bg='#D7D7D7', command=self.write_license_tree(tree)).pack(anchor='nw', padx=5)

        sb.config(command=tree.yview)
        frame_l_b_l.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=10)
        ##### 设置文字居中，以及表格宽度
        tree.column('组件ID', anchor='center', width=50, minwidth=50)
        tree.column('License', anchor='center', width=230, minwidth=230)
        #####  设置头部标题
        for column in columns:
            tree.heading(column, text=column)
        tree.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
        frame_l_b_l.pack_propagate(0)
        frame_l_b.pack(side=tk.TOP, fill=tk.X)

    def draw_frame_record_hid(self, parent):
        """读取设备ID，并选择文件进行存储
        1 可选择文件
        2 设备ID支持手动输入。并且跟顶部的读取设备ID按钮保持同步
        """
        # 右侧文字提示以及清除按钮
        frame_r = tk.Frame(parent, bg='white')
        ## 文字提示
        tk.Label(frame_r, text='将设备ID记\n录到本地文\n件', bg='white',
                 fg='#707070').pack(padx=2, pady=10)
        frame_r.pack(side=tk.RIGHT, fill=tk.Y, padx=1)

        frame_l_t = tk.Frame(parent, bg='white')
        tk.Label(frame_l_t, text='记录文件', bg='white').pack(side=tk.LEFT, pady=8)
        ety_hid_filepath = tk.Entry(frame_l_t, width=45)
        ety_hid_filepath.pack(side=tk.LEFT, padx=10, pady=8)
        tk.Button(frame_l_t, text='选 择', bg='#D7D7D7').pack(side=tk.LEFT, pady=10, ipadx=10)
        frame_l_t.pack(side=tk.TOP, fill=tk.X)

        frame_l_b = tk.Frame(parent, bg='white')
        tk.Label(frame_l_b, text='设备ID   ', bg='white').pack(side=tk.LEFT)
        ety_hid = tk.Entry(frame_l_b, width=45)
        ety_hid.pack(side=tk.LEFT, padx=10)
        tk.Button(frame_l_b, text='保 存', bg='#D7D7D7').pack(side=tk.LEFT, ipadx=10)
        frame_l_b.pack(side=tk.BOTTOM, fill=tk.X)

    def draw_frame_bottom_statistic_debug(self, parent):
        """调试界面的底部状态栏
        模式：调试模式(绿色)
        串口状态：XXX已连接(绿色)/断开(黑色)
        """
        # 模式-key
        tk.Label(parent, text='模式：', bg='white').pack(side=tk.LEFT, padx=2)
        # 模式-value
        tk.Label(parent, text='调试模式', bg='white', fg='green').pack(side=tk.LEFT)
        tk.Label(parent, text='', bg='white').pack(side=tk.LEFT, padx=120)
        # 串口状态-key
        tk.Label(parent, text='串口状态：', bg='white').pack(side=tk.LEFT, padx=2)
        # 串口状态-vaule
        self.label_port_status = tk.Label(parent, text='断开', bg='white')
        self.label_port_status.pack(side=tk.LEFT)

    def __turn_on(self):
        """连接到串口/Jlink时，更新状态信息"""
        self.btn_start.configure(text='停  止', fg='red')
        if not self.go:
            self.go = True

    def __turn_off(self):
        """断开串口/Jlink连接时，更新状态信息"""
        self.btn_start.configure(text='开  始', fg='darkgreen')
        if self.go:
            self.go = False

    #### 以上为界面代码，以下为动态逻辑代码
    def connect_to_port(self):
        """同串口建立连接"""
        if not self.__serial_port_configuration.port:
            tk.messagebox.showerror(title='Error',
                                    message='请选择连接串口号')
            return
        logger.info(f'连接串口 {self.__serial_port_configuration.port}')
        rtscts = False
        xonxoff = False
        if self.__serial_port_configuration.stream_controller == 'RTS/CTS':
            rtscts = True
        elif self.__serial_port_configuration.stream_controller == 'XON/XOFF':
            xonxoff = True
        if self.__mode_type.get() == 'DEBUG':  # 调试模式下，需要判断是连接还是断开
            if self.btn_start_debug.configure().get('text')[-1] == '断 开':
                self.disconnect_to_board()
                self.btn_start_debug.configure(text='串口连接', fg='green')
                self.label_port_status.configure(text='断开', fg='black')
                self.log_shower_insert(f'串口 {self.__serial_port_configuration.port}断开连接\n',
                                       tag='error')
                return

        self.port_com.open(self.__serial_port_configuration.port,
                           int(self.__serial_port_configuration.baud_rate),
                           stopbits=int(self.__serial_port_configuration.stop_digit),
                           parity=self.__serial_port_configuration.check_digit[0],
                           bytesize=int(self.__serial_port_configuration.data_digit),
                           rtscts=rtscts,
                           xonxoff=xonxoff,
                           )
        if self.port_com.is_open:  # 已连接
            self.__turn_on()  # 改变状态栏
            if self.__mode_type.get() == 'DEBUG':
                self.btn_start_debug.configure(text='断 开', fg='red')
                self.label_port_status.configure(text=f'{self.__serial_port_configuration.port}已连接', fg='green')
            self.log_shower_insert(f'串口 {self.__serial_port_configuration.port}连接成功\n',
                                   tag='confirm')
            return True
        self.log_shower_insert(f'串口 {self.__serial_port_configuration.port}连接失败\n',
                               tag='warn')

    def disconnect_to_board(self):
        self.port_com.close()
        self.jlink_com.close()

    def read_id(self, if_keep=True):
        """
        读设备ID操作
        if_keep:  是否是持续操作
        Returns:

        """
        if self.__conn_type.conn_type.get() == '串口通信':
            if if_keep:
                self.retry_time = 0
                self.operate_start_time = datetime.now()
                while self.go:
                    self.__update_statistic()
                    time.sleep(1)
                    if self.retry_time >= MAX_RETRY_TIME:
                        self.log_shower_insert('连接未操作时间过长，自动断开连接\n\n', tag='warn')
                        self.__update_statistic('停 止', 'blue')
                        self.__turn_off()
                        break
                    if (datetime.now() - self.operate_start_time) > MAX_INTERVAL_SECOND:
                        self.log_shower_insert('持续失败时间超时，自动断开连接\n\n', tag='warn')
                        self.__update_statistic('停 止', 'blue')
                        self.__turn_off()
                        break
                    hid_value = self.read_id_port()
                    if hid_value:
                        self.record_hid(hid_value)
                    self.disconnect_to_board()
                    time.sleep(1)
            else:
                hid_value = self.read_id_port()  # 进行一次操作
                self.log_shower_insert(f'设备ID获取成功:{hid_value}\n')
                return hid_value
        elif self.__conn_type.conn_type.get() == 'J-Link通信':
            if if_keep:
                pass
            else:
                hid_value = self.read_id_jlink()  # 只进行一次操作
                return hid_value

    def read_id_port(self):
        """
        串口通信方式读取设备ID
        Returns:

        """
        if_port_connected = self.connect_to_port()
        if if_port_connected:  # 已经连接
            try:
                hid_response = self.port_com.get_HID()
            except SerialException as e:
                logger.warning('串口访问异常', exc_info=e)
                self.__update_statistic('失 败', fg='red')
                self.log_shower_insert(f'设备ID读取失败，稍后将重试或更换设备\n', tag='error')
                self.disconnect_to_board()
                return
            except Exception as e:
                logger.warning('串口访问异常', e)
                self.__update_statistic('失 败', fg='red')
                self.log_shower_insert(f'设备ID读取失败，稍后将重试或更换设备\n', tag='error')
                self.disconnect_to_board()
                return
            else:
                if hid_response is None:
                    self.__update_statistic('失 败', fg='red')
                    self.log_shower_insert(f'设备HID读取失败，稍后将重试或更换设备\n', tag='error')
                    self.disconnect_to_board()
                    return
            # 以上，已经成功接收到hid返回，以下为写入本地hid文件代码
            try:
                board_protocol = parse_protocol(hid_response)
            except Exception as e:
                self.__update_statistic('失 败', fg='red')
                self.log_shower_insert(f'解析及校验HID response失败\n', tag='error')
                self.disconnect_to_board()
                return
             # 指令校验
            if not check_command(board_protocol.payload_data.command, 'hid_response'):  # 校验失败
                logger.warning(f'指令校验失败, 预期为0081，收到{board_protocol.payload_data.command}',
                               f'数据为{board_protocol.payload_data.data}')
                error_type = Error_Data_Map.get(board_protocol.payload_data.data)
                if error_type is not None:
                    logger.info(f'hid读取失败，指令{board_protocol.payload_data.command}，')
                    self.log_shower_insert(f'hid读取错误, '
                                                f'指令{board_protocol.payload_data.command} 错误类型{error_type}\n')
                else:
                    logger.info(f'hid读取失败，指令{board_protocol.payload_data.command}，')
                    self.log_shower_insert(f'hid读取错误, '
                                                f'指令{board_protocol.payload_data.command}数据{board_protocol.payload_data.data}\n')
                self.__update_statistic('失 败', fg='red')
                self.log_shower_insert(f'解析及校验 ID response失败\n', tag='error')
                self.disconnect_to_board()
                time.sleep(1)
                return

            hid_value = board_protocol.payload_data.data
            return hid_value
        else:
            tk.messagebox.showwarning(title='Warning',
                                      massage='请先连接串口')
            return

    def record_hid(self, hid_value):
        self.log_shower_insert(f'设备ID读取成功\n')
        logger.info(f'添加ID： {hid_value}')
        self.log_shower_insert(f'记录设备{hid_value}到表格\n')
        if hid_value in self.succ_hid:
            self.tree_insert((str(hid_value), '成功'), self.tree_hid)
            self.retry_time += 1
            self.__update_statistic('已完成', fg='green')
            self.log_shower_insert(f'设备ID已经存储完成，请更换设备...\n', tag='confirm')
            time.sleep(3)
            return
        try:
            record_HID_activated(hid_value, Path(self.__filepath_hid.get()))
        except Exception as e:
            if hid_value not in self.fail_hid:
                self.fail_hid.append(hid_value)
                self.tree_insert((hid_value, '失败'), self.tree_hid)
            logger.exception(e)
            self.__update_statistic('失 败', fg='red')
            self.log_shower_insert(f'设备ID存储失败\n', tag='error')
            self.disconnect_to_board()
        else:
            self.operate_start_time = datetime.now()
            self.succ_hid.append(hid_value)
            self.tree_insert((hid_value, '成功'), self.tree_hid)
            self.__update_statistic('成 功', fg='green')
            self.log_shower_insert(f'设备ID存储完成，请更换设备...\n', tag='confirm')
            self.disconnect_to_board()

    def read_id_jlink(self):
        """
        JLink方式的读取设备ID流程
        Returns:

        """
        pass

    def write_license_by_file(self, if_keep=True):
        """
        根据License文件写License操作
        Args:
            if_keep: 是否是持续操作

        Returns:

        """
        if self.__conn_type.conn_type.get() == '串口通信':
            if if_keep:
                self.retry_time = 0
                self.operate_start_time = datetime.now()
                while self.go:
                    self.__update_statistic()
                    time.sleep(1)
                    print(f'时间间隔: {datetime.now() - self.operate_start_time}')
                    if self.retry_time >= MAX_RETRY_TIME:
                        self.log_shower_insert('连接未操作时间过长，自动断开连接\n\n', tag='warn')
                        self.__update_statistic('停 止', 'blue')
                        self.__turn_off()
                        break
                    if (datetime.now() - self.operate_start_time) > MAX_INTERVAL_SECOND:
                        self.log_shower_insert('持续失败时间超时，自动断开连接\n\n', tag='warn')
                        self.__update_statistic('停 止', 'blue')
                        self.__turn_off()
                        break
                    self.write_license_by_file_port()
                    self.disconnect_to_board()
                    time.sleep(1)
            else:
                self.write_license_by_file_port()
        elif self.__conn_type.conn_type.get() == 'J-Link通信':
            if if_keep:
                pass  # 持续地写license操作
            else:
                self.write_license_by_file_jlink()

    def write_license_by_file_port(self):
        """
        串口通讯方式写License
        Returns:

        """
        if_port_connected = self.connect_to_port()
        if if_port_connected:  # 串口已经连接
            try:
                hid_response = self.port_com.get_HID()
            except Exception as e:
                return
            else:
                if hid_response is None:
                    self.log_shower_insert(f'获取设备HID失败\n', tag='error')
                    self.__update_statistic('失 败', fg='red')
                    return
            logger.info('get hid response')
            try:
                board_protocol = parse_protocol(hid_response)
            except Exception as e:
                return

            if not check_command(board_protocol.payload_data.command, 'hid_response'):  # 指令校验失败
                logger.warning(f'指令校验失败，预期为0081，收到{board_protocol.payload_data.command}, '
                               f'数据{board_protocol.payload_data.data}')
                error_type = Error_Data_Map.get(board_protocol.payload_data.data)
                logger.info(f'hid读取失败，指令{board_protocol.payload_data.command}')
                if error_type is not None:
                    self.log_shower_insert(f'hid读取错误, '
                                           f'指令{board_protocol.payload_data.command} 错误类型{error_type}\n')
                else:
                    self.log_shower_insert(f'hid读取错误, '
                                           f'指令{board_protocol.payload_data.command}数据{board_protocol.payload_data.data}\n')

                self.log_shower_insert(f'设备写入license失败：读取hid失败\n', tag='error')
                self.__update_statistic('失 败', fg='red')
                return
            logger.info('parse hid success')
            hid_value = board_protocol.payload_data.data
            self.log_shower_insert(f'获取设备HID成功，HID {hid_value}\n')
            if hid_value != self.last_success_hid:  # 仅判断当前设备ID是否和刚刚写的设备ID重复
                self.retry_time = 0
                hid_license = self.hid_license_map.get_license(hid_value)
                if not hid_license:  # 没有获取到该HID对应的license
                    logger.warning(f'{hid_value} 没有获取到license')
                    self.log_shower_insert('license写入失败: license文件中没有找到该设备ID\n')
                    self.__update_statistic('失 败', fg='red')
                    return
                self.log_shower_insert(f'对设备{hid_value}，写入license\n')
                if_success = True
                for component_id, license_ in hid_license.items():
                    try:
                        license_ = b64tostrhex(license_)
                    except Exception as e:
                        self.tree_insert((hid_value, component_id, '失败'), self.tree_license)
                        logger.error(f'license {license_}转码错误')
                        self.log_shower_insert(f'{component_id}写入license{str(license_)[:20]}...失败，'
                                               f'license转码错误\n', tag='warn')
                        if_success = False
                        continue
                    protocol = build_protocol(license_, component_id=component_id,
                                              command=ProtocolCommand.license_put_request.value)
                    if not self.send_license(self.port_com, protocol):  # 写license方法
                        if_success = False
                        self.tree_insert((hid_value, component_id, '失败'), self.tree_license)
                        self.log_shower_insert(f'{component_id}写入license{license_[:20]}...失败\n', tag='warn')
                        continue
                    self.tree_insert((hid_value, component_id, '成功'), self.tree_license)
                    self.log_shower_insert(f'{component_id}写入license{license_}成功\n', tag='warn')
                if if_success:
                    self.operate_start_time = datetime.now()
                    self.log_shower_insert(f'设备{hid_value}写入license成功\n', tag='confirm')
                    self.__update_statistic('成 功', fg='green')
                else:  # 组件的license并没有全部写入成功
                    self.log_shower_insert(f'设备{hid_value}写入license失败\n', tag='error')
                    self.__update_statistic('失 败', fg='red')
            else:
                self.retry_time += 1
                self.__update_statistic('已完成', fg='green')
                self.log_shower_insert(f'设备{hid_value}已经写入过license，请更换设备...\n', tag='warn')
                time.sleep(2)

    def send_license(self, serial_obj, protocol):
        """
        写license流程
        Args:
            serial_obj: 串口连接对象
            protocol: 写license协议

        Returns:

        """
        logger.info(f'send license start：{protocol}')
        try:
            serial_obj.send_license(protocol)
        except SerialException as e:
            logger.warning('串口无法访问')
            self.log_shower_insert('串口无法通信\n')
            return
        except Exception as e:
            logger.exception(e)
            self.log_shower_insert('写入license失败\n')
            return

        try:
            resp = serial_obj.read_response()
        except SerialException as e:
            logger.warning('未获取到license写入结果')
            self.log_shower_insert('未获取到license写入结果\n')
            return
        except Exception as e:
            logger.exception(e)
            self.log_shower_insert('获取license写入结果失败\n')
            return
        logger.info(f'get response: {resp}')
        if resp is not None:
            try:
                board_protocol = parse_protocol(resp)
            except Exception as e:
                logger.exception(e)
                return
            payload_data = board_protocol.payload_data
            if check_payload(payload_data, 'license_put_response'):
                logger.info('license写入成功')
                self.log_shower_insert('license写入成功\n', tag='confirm')
                return True
            error_type = Error_Data_Map.get(payload_data.data)
            logger.info(f'license写入失败，指令{payload_data.command}')
            if error_type is not None:
                self.log_shower_insert(f'license写入错误, '
                                       f'指令{payload_data.command} 错误类型{error_type}\n')
            else:
                self.log_shower_insert(f'license写入错误, '
                                       f'指令{payload_data.command}数据{payload_data.data}\n')
        else:  # 没有正确获取到返回
            self.log_shower_insert('license写入失败\n', tag='error')

    def write_license(self, etn_component, etn_license):
        """
        一次写license操作
        Args:
            etn_component: 用于用户输入组件ID的Entry控件
            component_id: 用于用户输入License的Entry控件

        Returns:

        """
        def inner():
            component_id = etn_component.get()
            print(f'组件id：{component_id}')
            license_ = etn_license.get()
            license_ = b64tostrhex(license_)
            print(f'license: {license_}')
            logger.info(f'component id: {component_id}\nlicense: {license_}')

            if not self.is_open:
                tk.messagebox.showerror(title='Error',
                                        message='请先同设备建立串口连接/J-Link连接')
                return
            if not component_id or not license_:
                tk.messagebox.showerror(title='Error',
                                        message='请输入组件ID和License')
                return

            protocol = build_protocol(license_, component_id=component_id,
                                      command=ProtocolCommand.license_put_request.value)
            if self.__conn_type.conn_type.get() == '串口通信':
                if not self.send_license(self.port_com, protocol):  # 写license方法
                    self.log_shower_insert(f'{component_id}写入license{license_[:20]}...失败\n', tag='warn')
                    return
                self.log_shower_insert(f'{component_id}写入license{license_}成功\n', tag='warn')
            else:
                pass  # TODO J-Link方式的一次写license方法

        return inner

    def write_license_tree(self, tree):
        """
        批量写license
        Args:
            tree:

        Returns:

        """
        def inner():
            for i in tree.get_children():
                component_id, license_ = tree.item(i).get('values')
                print(f'组件id：{component_id}')
                license_ = b64tostrhex(license_)
                print(f'license: {license_}')
                logger.info(f'component id: {component_id}\nlicense: {license_}')

                if not self.is_open:
                    tk.messagebox.showerror(title='Error',
                                            message='请先同设备建立串口连接/J-Link连接')
                    return

                protocol = build_protocol(license_, component_id=component_id,
                                          command=ProtocolCommand.license_put_request.value)
                if self.__conn_type.conn_type.get() == '串口通信':
                    if not self.send_license(self.port_com, protocol):  # 写license方法
                        self.log_shower_insert(f'{component_id}写入license{license_[:20]}...失败\n', tag='warn')
                        return
                    self.log_shower_insert(f'{component_id}写入license{license_}成功\n', tag='warn')
                else:
                    pass  # TODO J-Link方式的一次写license方法

        return inner


    def run(self):
        self.window_.mainloop()


if __name__ == '__main__':
    oneos_gui = OneOsGui()
    oneos_gui.run()

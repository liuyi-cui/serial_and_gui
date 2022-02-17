# -*- coding: utf-8 -*-
"""GUI操作界面"""
import tkinter as tk
from collections import namedtuple
from tkinter import ttk
from tkinter import filedialog

from serial_.pyboard import PyBoard
from utils.entities import ModeEnum, OperateEnum, ConnEnum, SerialPortConfiguration   # 操作方式、工位、通信方式、串口配置项

_font_s = ('微软雅黑', 8)  # 字体
_font_b = ('微软雅黑', 12)  # 字体
_active_color = 'gray'  # 激活状态颜色为浅灰色
SIZE_POPUPS = (400, 250)  # 弹出窗体大小


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
        center_window(self.window_, 600, 450)
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

    def init_values(self):
        """定义属性初始值"""
        self.__mode_type.set('product')  # 默认模式选择为生产模式
        self.__operate_type.set('hid')  # 默认操作工位为读HID
        self.__conn_type.set('serial_port')  # 默认通信方式为串口通信
        self.__serial_port_configuration = SerialPortConfiguration()  # 串口通信数据

    def _draw_serial_port_configuration(self, parent):  # 给定界面，绘制串口通信配置项 TODO 还可以添加字体大小，padx, pady等
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
                print(index_)
                cb_baudrate.current(index_)
            else:
                if '请手动输入波特率' in baudrate_values:
                    baudrate_values.pop(-1)
                cb_baudrate.configure(state='readonly', value=baudrate_values)

        frame = tk.Frame(parent)
        tk.Label(frame, text='波特率').pack(side=tk.LEFT, padx=10)
        baudrate_values = [9600, 19200, 38400, 57600, 115200, 'custom']
        cb_baudrate = ttk.Combobox(frame, value=baudrate_values,
                                   width=35, state='readonly')  # TODO 此处需要绑定一个选择后的方法。当波特率选择custom时，变更为可编辑
        cb_baudrate.bind('<<ComboboxSelected>>', update_cb_baudrate)
        cb_baudrate.current(baudrate_values.index(self.__serial_port_configuration.baud_rate))
        cb_baudrate.pack(side=tk.LEFT, padx=10)
        frame.pack(pady=6)
        # 数据位
        frame = tk.Frame(parent)
        tk.Label(frame, text='数据位').pack(side=tk.LEFT, padx=10)
        data_digit_values = [5, 6, 7, 8]
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
        cb_stop = ttk.Combobox(frame, value=[1, ], width=35, state='readonly')
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

    def body(self):  # 绘制主题  TODO 定义几种frame布局，更改布局时，切换frame。需要一个变量存储当前的布局，如果同当前的模式

        self.draw_menu(self.window_)  # 绘制菜单栏，固定布局

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
            pass
        elif name == 'log':
            pass

    def alter_port_win(self, parent) -> None:
        """弹出串口配置窗口"""
        parent.title('串口配置')
        center_window(parent, *SIZE_POPUPS)
        tk.Label(parent).pack(side=tk.LEFT, fill=tk.Y, padx=20)  # 左边缘空隙
        tk.Label(parent).pack(side=tk.RIGHT, fill=tk.Y, padx=20)  # 右边缘空隙
        cb_port, cb_baudrate, cb_data, cb_check, cb_stop, cb_stream_controller = \
            self._draw_serial_port_configuration(parent)  # 串口配置项

        def confirm():
            """
            确定按钮触发方法
            TODO 此处需要获取各个下拉框的值，因此_draw_serial_port_configuration应该返回各个cb
            针对各个下拉框的值，做合理性校验
            校验成功之后，记录各个下拉框的值
            """
            self.__serial_port_configuration.port = cb_port.get()
            print(f'串口号: {self.__serial_port_configuration.port}')

            print('确定按钮')


        frame = tk.Frame(parent)
        tk.Button(frame, text='取消', bg='silver', height=3, width=6,
                  command=cancel).pack(side=tk.RIGHT, pady=4, padx=10)
        tk.Button(frame, text='确定', bg='silver', height=3, width=6,
                  command=confirm).pack(side=tk.RIGHT, pady=4, padx=10)


    def run(self):
        self.window_.mainloop()


if __name__ == '__main__':
    oneos_gui = OneOsGui()
    oneos_gui.run()

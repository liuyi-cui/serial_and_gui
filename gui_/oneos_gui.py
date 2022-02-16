# -*- coding: utf-8 -*-
"""GUI操作界面"""
import tkinter as tk
from collections import namedtuple
from tkinter import ttk
from tkinter import filedialog

from utils.entities import ModeEnum, OperateEnum, ConnEnum   # 操作方式、工位、通信方式

_font_s = ('微软雅黑', 8)  # 字体
_font_b = ('微软雅黑', 12)  # 字体
_active_color = 'gray'  # 激活状态颜色为浅灰色
SIZE_POPUPS = (400, 250)  # 弹出窗体大小
Port_Config_Item = namedtuple('Port_Config_Item', ['name', 'value'])  # 串口配置项 TODO 考虑更为合适的编写方式


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
        self.init()  # 初始化对象属性
        self._init()  # 初始化对象属性值
        self.body()  # 绘制初始界面
        self.window_.pack_propagate(True)

    def init(self):
        """定义属性类型"""
        self.__mode_type = tk.StringVar()  # 模式选择(生产模式/调试模式)
        self.__operate_type = tk.StringVar()  # 操作工位(读HID/写License-从License文件/写License-从UKey)
        self.__conn_type = tk.StringVar()  # 通信方式(串口/J-Link)

    def _init(self):
        """定义属性初始值"""
        self.__mode_type.set('product')  # 默认模式选择为生产模式
        self.__operate_type.set('hid')  # 默认操作工位为读HID
        self.__conn_type.set('serial_port')  # 默认通信方式为串口通信

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

        port_config_items = {
            '串口号': Port_Config_Item(name='port_cb_port_config', value=['COM1', 'COM2', 'COM100']),  # TODO 调用串口获取当前串口号
            '波特率': Port_Config_Item(name='baudrate_cb_port_config', value=[115200, 9600, 19200, 38400, 57600, 'custom']),
            '数据位': Port_Config_Item(name='data_digit_port_config', value=[8, 5, 6, 7]),
            '校验位': Port_Config_Item(name='check_digit_port_config', value=['None', 'Even', 'Odd', 'Mark', 'Space']),
            '停止位': Port_Config_Item(name='stop_digit_port_config', value=[1, ]),
            '流控   ': Port_Config_Item(name='stream_controller', value=['None', 'RTS/CTS', 'XON/XOFF']),
        }
        for _k, _v in port_config_items.items():
            self.__build_port_config_combobox(parent, _k, _v).pack(pady=6)  # TODO 这里考虑是否有必要写成方法，直接

    def __build_port_config_combobox(self, parent, k_name, k_value):
        """日志配置界面，批量生成lable和对应的下拉框"""
        frame = tk.Frame(parent)
        tk.Label(frame, text=k_name).pack(side=tk.LEFT, padx=10)
        setattr(self, k_value.name, ttk.Combobox(frame, value=k_value.value, width=35, state='readonly'))
        # TODO 对串口号的下拉框做额外的配置
        cb = getattr(self, k_value.name)  # TODO 设置为实例属性，是为了将组件对象储存起来，方便随时获取到下拉框的值。否则，只能在生成组件的地方获取。
        cb.current(0)
        cb.pack(side=tk.LEFT, padx=5)
        return frame

    def run(self):
        self.window_.mainloop()


if __name__ == '__main__':
    oneos_gui = OneOsGui()
    oneos_gui.run()

# -*- coding: utf-8 -*-
"""GUI操作界面"""
import tkinter as tk
from enum import Enum
from tkinter import ttk
from tkinter import filedialog

from log import logger

_font_s = ('微软雅黑', 8)  # 字体
_font_b = ('微软雅黑', 12)  # 字体


def center_window(win, width=None, height=None):
    """窗口居中"""
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    if width is None:
        width, height = get_window_size(win)[:2]
    size = '%dx%d+%d+%d' % (width, height, (screen_width - width)/2, (screen_height - height)/3)
    win.geometry(size)


def get_window_size(win, update=True):
    """获取窗体的大小"""
    if update:
        win.update()
    return win.winfo_width(), win.winfo_height(), win.winfo_x(), win.winfo_y()


class StatusEnum(Enum):

    HID = 'HID'
    License = 'License'


class StatusEnumException(Exception):
    pass


class OneOsGui:

    def __init__(self):
        self.window_ = tk.Tk()
        center_window(self.window_, 800, 450)
        self.window_.title('OneOS License管理工具 -1.0.0')
        self.window_.grab_set()
        self.init_var()  # 初始化相关变量
        self.refresh_var()  # 刷新变量值
        self.body()
        self.window_.pack_propagate(True)

    def init_var(self):
        self.operate_desc = tk.StringVar()  # 记录文件/license文件(main_top栏)
        self.work_status = tk.StringVar()  # 工位
        self.curr_port = tk.StringVar()  # 串口号
        self.if_connected = tk.StringVar()  # 连接状态
        self.record_desc = tk.StringVar()  # 记录文件(bottom栏)
        self.record_filepath = tk.StringVar()  # 记录文件路径

        self.port_cb = ttk.Combobox()  # 串口下拉菜单
        self.filepath_entry = tk.Entry()  # 文件选择控件

    def refresh_var(self, status=StatusEnum.HID.value):
        logger.info(f'refresh status to {status}')
        self.status = status
        if status == 'HID':
            self.operate_desc.set('记录文件')
            self.work_status.set('读HID')
            self.curr_port.set('')  # 切换工位时，初始化为''
            self.if_connected.set('断开')  # 切换工位时，初始化为''
            self.record_desc.set('记录文件')
            self.record_filepath.set('')  # 切换模式后，初始化该控件信息(bottom栏)
            self.filepath_entry.delete(0, tk.END)  # 切换模式后，初始化该控件信息(top栏)
        elif status == 'License':
            self.operate_desc.set('license文件')
            self.work_status.set('写license')
            self.curr_port.set('')  # 切换工位时，初始化为''
            self.if_connected.set('断开')  # 切换工位时，初始化为''
            self.record_desc.set('license文件')
            self.record_filepath.set('')  # 切换模式后，初始化该控件信息(bottom栏)
            self.filepath_entry.delete(0, tk.END)  # 切换模式后，初始化该控件信息(top栏)
        else:
            raise StatusEnumException(f'unexpected status {status}')

    def change_status_to_hid(self):
        self.refresh_var(StatusEnum.HID.value)

    def change_status_to_license(self):
        self.refresh_var(StatusEnum.License.value)

    def body(self):  # 绘制主题
        self.window_.config(menu=self.top(self.window_))  # 让菜单栏显示出来

        # main_top
        self.main_top(self.window_).pack(expand=True, fill=tk.BOTH)

        # main_text
        self.main_text(self.window_).pack(expand=True, fill=tk.BOTH)

        # main_bottom
        self.main_bottom(self.window_).pack(expand=True, fill=tk.X)

    def top(self, parent):

        menu_bar = tk.Menu(parent)  # 创建一个菜单栏
        self.__top_1(menu_bar)
        self.__top_2(menu_bar)

        return menu_bar

    def __top_1(self, parent):  # 工位选择菜单栏

        # 创建一个 工位选择 菜单栏(默认不下拉，下拉选项包括 读HID，写License)
        operate_menu = tk.Menu(parent, bd=10, relief='sunken', tearoff=0)
        # 放置operate
        parent.add_cascade(label='工位选择', menu=operate_menu)
        # 放入选项
        operate_menu.add_command(label='读HID', command=self.change_status_to_hid)
        operate_menu.add_command(label='写License', command=self.change_status_to_license)

    def __top_2(self, parent):

        def change_operate(chioce):  # TODO 配置弹窗
            def inner_func():
                if chioce == 1:
                    print('选择串口配置')
                    frame = tk.Toplevel()
                    self.top_port_config(frame)  # 串口配置窗口
                elif chioce == 2:
                    print('选择日志配置')
                    frame = tk.Toplevel(self.window_)
                    frame.transient(self.window_)  # 随主窗口最小化而最小化，关闭而关闭，在主窗口前面
                    self.top_log_config(frame)  # 日志配置窗口
            return inner_func

        # 创建一个 工位选择 菜单栏(默认不下拉，下拉选项包括 读HID，写License)
        operate_menu = tk.Menu(parent, bd=10, relief='sunken', tearoff=0)
        # 放置operate
        parent.add_cascade(label='配置', menu=operate_menu)
        # 放入选项
        operate_menu.add_command(label='串口配置', command=change_operate(chioce=1))
        operate_menu.add_command(label='日志配置', command=change_operate(chioce=2))

    def top_port_config(self, parent):  # 串口配置界面
        """

        Args:
            parent: tk.Toplevel()

        Returns:

        """
        parent.title('串口配置')
        center_window(parent, 400, 250)
        tk.Label(parent, bg='lightgreen').pack(side=tk.LEFT, fill=tk.Y, padx=20)  # 左边缘空隙
        tk.Label(parent, bg='lightgreen').pack(side=tk.RIGHT, fill=tk.Y, padx=20)  # 右边缘空隙
        self.__top_port_config_1(parent).pack(pady=5)
        self.__top_port_config_2(parent).pack(pady=5)
        self.__top_port_config_3(parent).pack(pady=5)
        self.__top_port_config_4(parent).pack(pady=5)
        self.__top_port_config_5(parent).pack(pady=5)
        self.__top_port_config_6(parent).pack(pady=5)
        self.__top_port_config_7(parent).pack(pady=10)

    def __top_port_config_1(self, parent):
        frame = tk.Frame(parent)
        tk.Label(frame, text='串口号').pack(side=tk.LEFT, padx=10)
        port_list = ['COM1', 'com2', 'com3', 'com4']
        ttk.Combobox(frame, value=port_list, width=35, state='readonly').pack(side=tk.LEFT, padx=5)
        return frame

    def __top_port_config_2(self, parent):
        frame = tk.Frame(parent)
        tk.Label(frame, text='波特率').pack(side=tk.LEFT, padx=10)
        baudrate_list = [115200, ]
        baudrate_cb = ttk.Combobox(frame, value=baudrate_list, width=35, state='readonly')
        baudrate_cb.current(0)
        baudrate_cb.pack(side=tk.LEFT, padx=5)
        return frame

    def __top_port_config_3(self, parent):  # 数据位默认值8/校验位默认none/停止位1/流控none
        frame = tk.Frame(parent)
        tk.Label(frame, text='数据位').pack(side=tk.LEFT, padx=10)
        datadigit_list = [8, ]
        datadigit_cb = ttk.Combobox(frame, value=datadigit_list, width=35, state='readonly')
        datadigit_cb.current(0)
        datadigit_cb.pack(side=tk.LEFT, padx=5)
        return frame

    def __top_port_config_4(self, parent):
        frame = tk.Frame(parent)
        tk.Label(frame, text='校验位').pack(side=tk.LEFT, padx=10)
        checkdigit_list = ['none', ]
        checkdigit_cb = ttk.Combobox(frame, value=checkdigit_list, width=35, state='readonly')
        checkdigit_cb.current(0)
        checkdigit_cb.pack(side=tk.LEFT, padx=5)
        return frame

    def __top_port_config_5(self, parent):
        frame = tk.Frame(parent)
        tk.Label(frame, text='停止位').pack(side=tk.LEFT, padx=10)
        stopdigit_list = [1, ]
        stopdigit_cb = ttk.Combobox(frame, value=stopdigit_list, width=35, state='readonly')
        stopdigit_cb.current(0)
        stopdigit_cb.pack(side=tk.LEFT, padx=5)
        return frame

    def __top_port_config_6(self, parent):
        frame = tk.Frame(parent)
        tk.Label(frame, text='流控   ').pack(side=tk.LEFT, padx=10)
        streamcontrol_list = ['none', ]
        streamcontrol_cb = ttk.Combobox(frame, value=streamcontrol_list, width=35, state='readonly')
        streamcontrol_cb.current(0)
        streamcontrol_cb.pack(side=tk.LEFT, padx=5)
        return frame

    def __top_port_config_7(self, parent):  # 确定/取消按钮
        frame = tk.Frame(parent)
        tk.Button(frame, text='取消', font=_font_s, bg='silver', height=3, width=6).pack(
            side=tk.RIGHT, pady=4, padx=10
        )
        tk.Button(frame, text='确定', font=_font_s, bg='silver', height=3, width=6).pack(
            side=tk.RIGHT, pady=4, padx=10
        )
        return frame

    def top_log_config(self, parent):
        """
        日志配置弹窗
        Args:
            parent: tk.Toplevel()

        Returns:

        """
        parent.title('日志配置')
        center_window(parent, 400, 250)
        tk.Label(parent, bg='lightgreen').pack(side=tk.LEFT, fill=tk.Y, padx=20)  # 左边缘空隙
        tk.Label(parent, bg='lightgreen').pack(side=tk.RIGHT, fill=tk.Y, padx=20)  # 右边缘空隙
        tk.Label(parent, bg='lightgreen').pack(pady=10, fill=tk.X)
        self.__top_log_config_1(parent).pack(fill=tk.X, pady=5)  # 是否保存日志单选框
        self.__top_log_config_2(parent).pack(fill=tk.X, pady=5)  # 存盘日志路径
        self.__top_log_config_3(parent).pack(fill=tk.X, pady=5)
        self.__top_log_config_4(parent).pack(fill=tk.X, pady=10)

    def __top_log_config_1(self, parent):
        frame = tk.Frame(parent)

        def refresh_if_record_status():
            if if_record_log.get() == 0:
                print('不开启日志记录')
            elif if_record_log.get() == 1:
                print('开启日志记录')
            else:
                print('未知状态的日志记录')

        if_record_log = tk.IntVar()
        record_log_cb = tk.Checkbutton(frame, text='记录日志', variable=if_record_log,
                                       onvalue=1, offvalue=0, command=refresh_if_record_status)
        record_log_cb.pack(side=tk.LEFT)
        return frame

    def __top_log_config_2(self, parent):
        frame = tk.Frame(parent)
        self.__top_log_config_2_1(frame).pack(side=tk.LEFT)  # 存储日志标签
        log_path_entry, choice_btn = self.__top_log_config_2_2(frame)
        log_path_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        choice_btn.pack(side=tk.RIGHT, padx=5)
        return frame

    def __top_log_config_2_1(self, parent):
        l = tk.Label(parent, text='存储日志', font=_font_s)
        return l

    def __top_log_config_2_2(self, parent):

        log_filepath = tk.StringVar()  # 接收日志路径

        def path_call_back():
            file_path = filedialog.askopenfilename()
            if file_path != '':
                log_filepath.set(file_path)  # TODO 此处的日志路径需要传递给后台使用

        btn = tk.Button(parent, text='打开', font=_font_s,
                        width=10, bg='whitesmoke', command=path_call_back)
        log_path_entry = tk.Entry(parent, textvariable=log_filepath)

        return log_path_entry, btn

    def __top_log_config_3(self, parent):
        frame = tk.Frame(parent)
        self.__top_log_config_3_1(frame).pack(side=tk.LEFT)
        self.__top_log_config_3_2(frame).pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.__top_log_config_3_3(frame).pack(side=tk.LEFT, padx=15)
        return frame

    def __top_log_config_3_1(self, parent):
        l = tk.Label(parent, text='日志大小上限')
        return l

    def __top_log_config_3_2(self, parent):
        e = tk.Entry(parent, show=None)  # 明文形式显示 TODO 确定按钮时需要接收输入框中值，并且要做纯数字的判断
        return e

    def __top_log_config_3_3(self, parent):
        l = tk.Label(parent, text='MB')
        return l

    def __top_log_config_4(self, parent):
        frame = tk.Frame(parent)
        tk.Button(frame, text='取消', font=_font_s, bg='silver',
                  height=2, width=8).pack(side=tk.RIGHT, pady=4, padx=10)
        tk.Button(frame, text='确定', font=_font_s, bg='silver',
                  height=2, width=8).pack(side=tk.RIGHT, pady=4, padx=10)
        return frame

    def main_top(self, parent):
        frame = tk.Frame(parent, bg='red', bd=3, highlightcolor='silver', highlightthickness=1)

        self.__main_top_1(frame).pack(side=tk.RIGHT, fill=tk.Y, padx=10)
        self.__main_top_2(frame).pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=10)
        self.__main_top_3(frame).pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=10)

        return frame

    def __main_top_1(self, parent):

        frame = tk.Frame(parent)

        def start():  # TODO 开始逻辑(获取HID/写license)
            print('触发开始')

        btn = tk.Button(frame, text='开始', bg='gray', font=_font_b, command=start)
        btn.pack(side=tk.LEFT, padx=20)
        return frame

    def __main_top_2(self, parent):
        frame = tk.Frame(parent)
        self.__main_top_2_1(frame).pack(side=tk.LEFT, padx=5)  # 串口号标签
        self.__main_top_2_2(frame).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)  # 串口下拉菜单
        self.__main_top_2_3(frame).pack(side=tk.RIGHT, padx=15)
        return frame

    def __main_top_2_1(self, parent):
        l = tk.Label(parent, text='串口号', font=_font_b, padx=10)
        return l

    def __main_top_2_2(self, parent):
        port_list = ['COM1', 'COM2', 'COM3', 'COM4', 'COM5']  # TODO 实际的串口列表
        self.port_cb = ttk.Combobox(parent, value=port_list, width=25)
        return self.port_cb

    def __main_top_2_3(self, parent):

        if_connected = False
        def test_connect():  # 连接测试
            print('当前选中的串口：', self.port_cb.get())  # TODO 对选中的串口进行连接测试
            self.curr_port.set(self.port_cb.get())
            if_connected = True
            if if_connected:
                self.if_connected.set('连接')

        b = tk.Button(parent, text='连接测试', font=_font_s,
                      width=10, bg='whitesmoke',
                      command=test_connect)
        return b

    def __main_top_3(self, parent):
        frame = tk.Frame(parent)
        self.__main_top_3_1(frame).pack(side=tk.LEFT, padx=5)  # 串口号标签
        filepath_entry, open_btn = self.__main_top_3_2(frame)
        filepath_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)  # 串口下拉菜单
        open_btn.pack(side=tk.RIGHT, padx=15)
        return frame

    def __main_top_3_1(self, parent):
        print(self.operate_desc.get())
        l = tk.Label(parent, textvariable=self.operate_desc, font=_font_b)
        return l

    def __main_top_3_2(self, parent):

        record_hid_filepath = tk.StringVar()  # 接收文件路径

        def path_call_back():
            file_path = filedialog.askopenfilename()
            if file_path != '':
                record_hid_filepath.set(file_path)  # file_path还要传递给状态栏的记录文件
                self.record_filepath.set(file_path)

        btn = tk.Button(parent, text='打开', font=_font_s,
                      width=10, bg='whitesmoke',
                      command=path_call_back)
        self.filepath_entry = tk.Entry(parent, textvariable=record_hid_filepath)

        return self.filepath_entry, btn

    def main_text(self, parent):
        frame = tk.Frame(parent, bg='orange')

        self.__main_text_left(frame).pack(side=tk.LEFT, padx=10, expand=True, fill=tk.BOTH)
        self.__main_text_right(frame).pack(side=tk.RIGHT, padx=10, expand=True, fill=tk.BOTH)

        return frame

    def __main_text_left(self, parent):  # 日志打印text控件，清除日志按钮
        frame_left = tk.Frame(parent)
        self.__main_text_left_1(frame_left).pack(expand=True, fill=tk.BOTH)  # 日志打印text控件
        self.__main_text_left_2(frame_left).pack(side=tk.RIGHT)

        return frame_left

    def __main_text_left_1(self, parent):  # 日志打印Text
        self.log_shower = tk.Text(parent, width=50, height=15)
        self.log_shower.tag_config('warn', foreground='red')
        self.log_shower.tag_config('confirm', foreground='green')
        return self.log_shower

    def __main_text_left_2(self, parent):  # 清除日志按钮

        def clean_log():
            self.log_shower.delete(1.0, tk.END)  # 清除text中文本

        b = tk.Button(parent, text='清除日志', font=_font_s, height=2, width=5,
                      padx=1, pady=1, command=clean_log)
        return b

    def __main_text_right(self, parent):  # 操作统计Text控件，清除统计按钮
        frame_right = tk.Frame(parent, bg='lightcyan')
        self.__main_text_right_1(frame_right).pack(expand=True, fill=tk.BOTH)  # 日志打印text控件
        self.__main_text_right_2(frame_right).pack(side=tk.RIGHT)

        return frame_right

    def __main_text_right_1(self, parent):  # 日志打印Text
        self.operate_shower = tk.Text(parent, width=30, height=15)
        self.operate_shower.tag_config('warn', foreground='red')
        self.operate_shower.tag_config('confirm', foreground='green')
        return self.operate_shower

    def __main_text_right_2(self, parent):  # 清除日志按钮

        def clean_log():
            self.operate_shower.delete(1.0, tk.END)  # 清除text中文本

        b = tk.Button(parent, text='清除统计', font=_font_s, height=2, width=5,
                      padx=1, pady=1, command=clean_log)
        return b

    def main_bottom(self, parent):
        frame = tk.Frame(parent, bg='yellow')

        self.__main_bottom_1(frame).pack(side=tk.LEFT, padx=5, fill=tk.X)
        self.__main_bottom_1_value(frame).pack(side=tk.LEFT, fill=tk.X)
        tk.Label(frame).pack(side=tk.LEFT, padx=15)  # 空白占位控件

        self.__main_bottom_2(frame).pack(side=tk.LEFT, padx=5, fill=tk.X)
        self.__main_bottom_2_value(frame).pack(side=tk.LEFT)
        tk.Label(frame).pack(side=tk.LEFT, padx=15)  # 空白占位控件
        self.__main_bottom_3(frame).pack(side=tk.LEFT, padx=5, fill=tk.X)
        self.__main_bottom_3_value(frame).pack(side=tk.LEFT, fill=tk.X)
        tk.Label(frame).pack(side=tk.LEFT, padx=15)  # 空白占位控件

        self.__main_bottom_4(frame).pack(side=tk.LEFT, padx=10, fill=tk.X)
        self.__main_bottom_5(frame).pack(side=tk.LEFT, fill=tk.X)

        return frame

    def __main_bottom_1(self, parent):
        l = tk.Label(parent, text='工位：')
        return l

    def __main_bottom_1_value(self, parent):  # 工位的值
        l = tk.Label(parent, textvariable=self.work_status)
        return l

    def __main_bottom_2(self, parent):
        l = tk.Label(parent, text='串口号:')
        return l

    def __main_bottom_2_value(self, parent):
        l = tk.Label(parent, textvariable=self.curr_port)
        return l

    def __main_bottom_3(self, parent):
        l = tk.Label(parent, text='串口状态:')
        return l

    def __main_bottom_3_value(self, parent):
        l = tk.Label(parent, textvariable=self.if_connected)
        return l

    def __main_bottom_4(self, parent):
        l = tk.Label(parent, text='记录文件:')
        return l

    def __main_bottom_5(self, parent):
        l = tk.Label(parent, textvariable=self.record_filepath)
        return l

    def run(self):
        self.window_.mainloop()


if __name__ == '__main__':
    oneos_gui = OneOsGui()
    oneos_gui.run()

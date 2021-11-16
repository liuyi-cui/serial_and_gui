# -*- coding: utf-8 -*-
"""GUI操作界面"""
import tkinter as tk
import tkinter.messagebox
from collections import namedtuple
from enum import Enum
from tkinter import ttk
from tkinter import filedialog

from log import logger
from serial_.pyboard import PyBoard, PyBoardException
from utils.file_utils import check_file_suffix

# 字体
_FONT_S = ('微软雅黑', 8)  # 小号字体
_FONT_L = ('微软雅黑', 12)  # 大号字体字体
# 标题
TITLE_MAIN = 'OneOS License管理工具 -1.0.0'
TITLE_PORT_CONFIG = '串口配置'
TITLE_LOG_CONFIG = '日志配置'
# 窗体大小
SIZE_MAIN = (800, 450)
SIZE_POPUPS = (400, 250)
# 串口配置项
Port_Config_Item = namedtuple('Port_Config_Item', ['name', 'value'])


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
    """两种工位状态：读HID/写License"""

    HID = 'HID'
    License = 'License'


class StatusEnumException(Exception):
    pass


class OneOsGui:

    def __init__(self):
        self.window_ = tk.Tk()
        center_window(self.window_, *SIZE_MAIN)
        self.window_.title(TITLE_MAIN)
        self.window_.grab_set()  # 窗口显示在最前方
        self.init_var()  # 初始化相关变量
        self.refresh_var()  # 刷新变量值
        self.body()
        self.window_.pack_propagate(True)
        self.conn = None  # 串口连接对象

    def init_var(self):
        self.if_record_log = False  # 日志配置弹窗复选框，是否存储日志
        self.log_filepath = ''  # 日志存储路径
        self.operate_desc = tk.StringVar()  # 记录文件/license文件(main_top栏)
        self.work_type = tk.StringVar()  # 工位
        self.curr_port = tk.StringVar()  # 串口号
        self.if_connected = tk.StringVar()  # 连接状态
        self.record_desc = tk.StringVar()  # 记录文件(bottom栏)
        self.record_filepath = tk.StringVar()  # 记录文件路径
        self.hid_filepath = ''  # HID存储文件，当work_type为读HID时，等同于record_filepath的值
        self.license_filepath = ''  # 存储license文件，当work_type为写license时，接收record_filepath的值
        self.port_list = []  # 串口列表，main_top串口下拉框展示
        self.curr_baudrate = 0  # 波特率
        self.data_digit = 8  # 数据位
        self.check_digit = None  # 校验位
        self.stop_digit = 1  # 停止位
        self.stream_controller = None  # 流控

        self.port_cb = ttk.Combobox()  # 串口下拉菜单
        self.log_path_entry = tk.Entry()  # 菜单栏日志配置弹窗的日志文件路径
        self.port_cb_port_config = ttk.Combobox()  # 菜单栏串口配置弹窗的串口下拉菜单
        self.baudrate_cb_port_config = ttk.Combobox()  # 菜单栏串口配置弹窗的波特率下拉菜单
        self.data_digit_port_config = ttk.Combobox()  # 菜单栏串口配置弹窗的数据位下拉菜单
        self.check_digit_port_config = ttk.Combobox()  # 菜单栏串口配置弹窗的校验位下拉菜单
        self.stop_digit_port_config = ttk.Combobox()  # 菜单栏串口配置弹窗的停止位下拉菜单
        self.stream_controller_port_config = ttk.Combobox()  # 菜单栏串口配置弹窗的流控下拉菜单
        self.filepath_entry = tk.Entry()  # main_top的文件选择控件
        self.log_shower = tk.Text()  # main_text左边的操作关键信息打印控件
        self.operate_shower = tk.Text()  # main_text右边的操作统计信息打印控件
        self.port_test_desc = tk.StringVar()  # main_top开始测试按钮的显示文字(开始测试/停止测试)

    def refresh_var(self, status=StatusEnum.HID.value):  # TODO 两个text 控件也需要刷新
        """
        切换工位时，刷新面板展示
        Args:
            status: HID/License

        Returns:

        """
        logger.info(f'refresh status to {status}')
        self.curr_port.set('')
        self.if_connected.set('断开')
        self.port_test_desc.set('开始测试')
        self.filepath_entry.delete(0, tk.END)  # 清空记录文件输入框内容
        self.log_shower.delete(1.0, tk.END)
        self.operate_shower.delete(1.0, tk.END)
        if status == 'HID':
            self._refresh_var_hid()
        elif status == 'License':
            self._refresh_var_license()
        else:
            raise StatusEnumException(f'unexpected status {status}')

    def _refresh_var_hid(self):  # TODO 校验位停止位等暂时固定。切换工位不影响
        """切换到读hid时更新属性"""
        self.operate_desc.set('记录文件')
        self.work_type.set('读HID')
        self.record_desc.set('记录文件：')

    def _refresh_var_license(self):
        """切换到写license时更新属性"""
        self.operate_desc.set('license文件')
        self.work_type.set('写license')
        self.record_desc.set('license文件：')

    def change_status_to_hid(self):
        self.refresh_var(StatusEnum.HID.value)

    def change_status_to_license(self):
        self.refresh_var(StatusEnum.License.value)

    def body(self):  # 绘制主题
        self.window_.config(menu=self.top(self.window_))  # 菜单栏

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
        operate_menu = tk.Menu(parent, tearoff=0)
        # 放置operate
        parent.add_cascade(label='工位选择', menu=operate_menu)
        # 放入选项
        operate_menu.add_command(label='读HID', command=self.change_status_to_hid)
        operate_menu.add_command(label='写License', command=self.change_status_to_license)

    def __top_2(self, parent):

        def change_operate(chioce):
            def inner_func():
                if chioce == 1:
                    print('选择串口配置')
                    frame = tk.Toplevel()
                    frame.transient(self.window_)  # 随主窗口最小化而最小化，关闭而关闭，在主窗口前面
                    self.top_port_config(frame)  # 串口配置窗口
                elif chioce == 2:
                    print('选择日志配置')
                    frame = tk.Toplevel(self.window_)
                    frame.transient(self.window_)  # 随主窗口最小化而最小化，关闭而关闭，在主窗口前面
                    self.top_log_config(frame)  # 日志配置窗口
            return inner_func

        # 创建一个 工位选择 菜单栏(默认不下拉，下拉选项包括 读HID，写License)
        operate_menu = tk.Menu(parent, tearoff=0)
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
        parent.title(TITLE_PORT_CONFIG)
        center_window(parent, *SIZE_POPUPS)
        tk.Label(parent).pack(side=tk.LEFT, fill=tk.Y, padx=20)  # 左边缘空隙
        tk.Label(parent).pack(side=tk.RIGHT, fill=tk.Y, padx=20)  # 右边缘空隙

        port_config_items = {
            '串口号': Port_Config_Item(name='port_cb_port_config', value=['COM1', 'COM2', 'COM19', 'COM21']),  # TODO 调用串口获取当前串口号
            '波特率': Port_Config_Item(name='baudrate_cb_port_config', value=[115200, ]),
            '数据位': Port_Config_Item(name='data_digit_port_config', value=[8]),
            '校验位': Port_Config_Item(name='check_digit_port_config', value=['None',]),
            '停止位': Port_Config_Item(name='stop_digit_port_config', value=[1, ]),
            '流控   ': Port_Config_Item(name='stream_controller', value=['None', ]),
        }
        for k, v in port_config_items.items():
            self.__build_top_config_combobox(parent, k, v).pack(pady=5)
        self.__top_port_config_confirm(parent).pack(pady=10)

    def __build_top_config_combobox(self, parent, k_name, k_value):
        frame = tk.Frame(parent)
        tk.Label(frame, text=k_name).pack(side=tk.LEFT, padx=10)
        setattr(self, k_value.name, ttk.Combobox(frame, value=k_value.value, width=35, state='readonly'))
        cb = getattr(self, k_value.name)
        cb.current(0)
        cb.pack(side=tk.LEFT, padx=5)
        return frame

    def __top_port_config_confirm(self, parent):  # 确定/取消按钮

        def confirm():
            print(f'串口号:', self.port_cb_port_config.get())
            print(f'波特率:', self.baudrate_cb_port_config.get())
            print(f'数据位:', self.data_digit_port_config.get())
            print(f'校验位:', self.check_digit_port_config.get())
            print(f'停止位:', self.stop_digit_port_config.get())
            print(f'流控:', self.stream_controller_port_config.get())
            parent.destroy()

        def cancel():
            parent.destroy()

        frame = tk.Frame(parent)
        tk.Button(frame, text='取消', font=_FONT_S, bg='silver', height=3, width=6, command=cancel).pack(
            side=tk.RIGHT, pady=4, padx=10
        )
        tk.Button(frame, text='确定', font=_FONT_S, bg='silver', height=3, width=6, command=confirm).pack(
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
        parent.title(TITLE_LOG_CONFIG)
        center_window(parent, *SIZE_POPUPS)
        tk.Label(parent).pack(side=tk.LEFT, fill=tk.Y, padx=20)  # 左边缘空隙
        tk.Label(parent).pack(side=tk.RIGHT, fill=tk.Y, padx=20)  # 右边缘空隙
        tk.Label(parent).pack(pady=10, fill=tk.X)
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
                self.if_record_log = True
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
        l = tk.Label(parent, text='存储日志', font=_FONT_S)
        return l

    def __top_log_config_2_2(self, parent):

        log_filepath = tk.StringVar()  # 接收日志路径

        def path_call_back():
            file_path = filedialog.askopenfilename()
            if file_path != '':
                log_filepath.set(file_path)  # TODO 此处的日志路径需要传递给后台使用

        btn = tk.Button(parent, text='打开', font=_FONT_S,
                        width=10, bg='whitesmoke', command=path_call_back)
        self.log_path_entry = tk.Entry(parent, textvariable=log_filepath)

        return self.log_path_entry, btn

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

        def cancel():
            parent.destroy()

        def confirm():  # 确定时，需要获取是否需要存储日志，日志存储路径和日志的大小
            print('是否需要存储日志', self.if_record_log)  # 是否需要存储日志
            print('日志存储路径', self.record_filepath)  # 日志存储路径
            print()

            pass


        tk.Button(frame, text='取消', font=_FONT_S, bg='silver',
                  height=2, width=8).pack(side=tk.RIGHT, pady=4, padx=10)
        tk.Button(frame, text='确定', font=_FONT_S, bg='silver',
                  height=2, width=8).pack(side=tk.RIGHT, pady=4, padx=10)
        return frame

    def main_top(self, parent):
        frame = tk.Frame(parent, bd=3, highlightcolor='silver', highlightthickness=1)

        self.__main_top_1(frame).pack(side=tk.RIGHT, fill=tk.Y, padx=10)
        self.__main_top_2(frame).pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=10)
        self.__main_top_3(frame).pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=10)

        return frame

    def __main_top_1(self, parent):

        frame = tk.Frame(parent)

        def start():  # TODO 开始逻辑(获取HID/写license)
            print('触发开始')

        btn = tk.Button(frame, text='开始', bg='gray', font=_FONT_L, command=start)
        btn.pack(side=tk.LEFT, padx=20)
        return frame

    def __main_top_2(self, parent):
        frame = tk.Frame(parent)
        self.__main_top_2_1(frame).pack(side=tk.LEFT, padx=5)  # 串口号标签
        self.__main_top_2_2(frame).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)  # 串口下拉菜单
        self.__main_top_2_3(frame).pack(side=tk.RIGHT, padx=15)
        return frame

    def __main_top_2_1(self, parent):
        l = tk.Label(parent, text='串口号', font=_FONT_L, padx=10)
        return l

    def get_port_list(self, *args):
        """获取当前可用的串口列表"""
        self.port_list = PyBoard.get_list()
        self.port_cb['value'] = self.port_list
        if self.port_list:
            self.log_shower.insert('end', '检测到串口')
            for port_ in self.port_list:
                self.log_shower.insert('end', port_)
            self.log_shower.insert('end', '\n')
        else:
            self.log_shower.insert('end', '未检测到串口\n')

    def __main_top_2_2(self, parent):
        self.port_cb = ttk.Combobox(parent, value=self.port_list, width=25)
        self.port_cb.bind('<Button-1>', self.get_port_list)
        return self.port_cb

    def __main_top_2_3(self, parent):

        def test_connect():  # 连接测试
            if self.port_test_desc.get() == '开始测试':
                temp_port = self.port_cb.get()
                if temp_port:  # 当前选择了串口号
                    self.curr_port.set(temp_port)
                    try:
                        print(f'当前选择串口：{temp_port}')
                        print(f'当前串口属性：{self.curr_port.get()}')
                        # self.connect_to_board()  # TODO 连接开发板
                        self.port_test_desc.set('停止测试')
                    except Exception as e:
                        print(e)
                        tkinter.messagebox.showerror(title='ERROR', message=str(e))
                    print(f'更新串口号：{temp_port}')
                    self.if_connected.set('连接')
                else:
                    tkinter.messagebox.showwarning(title='Warning',
                                                   message='未选中串口号')
            elif self.port_test_desc.get() == '停止测试':
                if self.conn is not None:
                    self.conn.close()
                self.port_test_desc.set('开始测试')
            else:
                print(f'unexcept dest: {self.port_test_desc.get()}')

        self.port_test_desc.set('开始测试')
        b = tk.Button(parent, textvariable=self.port_test_desc, font=_FONT_S,
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
        l = tk.Label(parent, textvariable=self.operate_desc, font=_FONT_L)
        return l

    def __main_top_3_2(self, parent):

        def path_call_back():
            file_path = filedialog.askopenfilename()
            if file_path != '':
                if check_file_suffix(file_path):
                    self.record_filepath.set(file_path)
                else:
                    tkinter.messagebox.showwarning(title='Warning',
                                                   message='请选择Excel类型文件')

        btn = tk.Button(parent, text='打开', font=_FONT_S,
                        width=10, bg='whitesmoke',
                        command=path_call_back)
        self.filepath_entry = tk.Entry(parent, textvariable=self.record_filepath)

        return self.filepath_entry, btn

    def main_text(self, parent):
        frame = tk.Frame(parent)

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
            self.log_shower.insert(1.0, '清除日志...\n')
        b = tk.Button(parent, text='清除日志', font=_FONT_S, height=2, width=5,
                      padx=1, pady=1, command=clean_log)
        return b

    def __main_text_right(self, parent):  # 操作统计Text控件，清除统计按钮
        frame_right = tk.Frame(parent)
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

        b = tk.Button(parent, text='清除统计', font=_FONT_S, height=2, width=5,
                      padx=1, pady=1, command=clean_log)
        return b

    def main_bottom(self, parent):
        frame = tk.Frame(parent)

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
        l = tk.Label(parent, textvariable=self.work_type)
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
        l = tk.Label(parent, textvariable=self.record_desc)
        return l

    def __main_bottom_5(self, parent):
        l = tk.Label(parent, textvariable=self.record_filepath)
        return l

    def run(self):
        self.window_.mainloop()

    # 以上为界面代码，一下为逻辑代码
    def connect_to_board(self):
        print(f'当前串口：{self.curr_port.get()}')
        self.conn = PyBoard(self.curr_port.get(), self.curr_baudrate)


if __name__ == '__main__':
    oneos_gui = OneOsGui()
    oneos_gui.run()

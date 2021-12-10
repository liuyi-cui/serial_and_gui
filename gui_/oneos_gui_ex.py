# -*- coding: utf-8 -*-
"""GUI操作界面"""
from threading import Thread
import time
import tkinter as tk
import tkinter.messagebox
from collections import namedtuple
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from tkinter import ttk
from tkinter import filedialog
from serial.serialutil import SerialException

from dao import HID_License_Map, DaoException
from log import logger, OperateLogger
from serial_.pyboard import PyBoard, PyBoardException
from setting import TITLE_MAIN
from utils.convert_utils import b64tostrhex
from utils.entities import BoardProtocol, PayloadData, ProtocolCommand, DataError, Error_Data_Map
from utils.file_utils import check_file_suffix, record_HID_activated, read_HID
from utils.protocol_utils import parse_protocol, build_protocol, check_payload

# 字体
_FONT_S = ('微软雅黑', 8)  # 小号字体
_FONT_L = ('微软雅黑', 12)  # 大号字体字体
_FONT_B = ('宋体', 10, 'bold')
# 标题
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

    MAX_WAIT_TIME = 5  # 成功后不更换设备，重复该次数后，停止读HID/写license
    MAX_INTERVAL_SECOND = timedelta(seconds=30)  # 持续失败的最大间隔时间

    def __init__(self):
        self.window_ = tk.Tk()
        center_window(self.window_, *SIZE_MAIN)
        self.window_.title(TITLE_MAIN)
        self.window_.grab_set()  # 窗口显示在最前方
        self.operate_logger = OperateLogger()  # 记录操作日志
        self.init_var()  # 初始化相关变量
        self.refresh_var()  # 刷新变量值
        self.body()
        self.window_.pack_propagate(True)
        self.conn = None  # 串口连接对象
        self.wait_time = 0  # 等待时间。
        self.run_start_time = datetime.now()  # 启动开始时间

    def init_var(self):
        self.if_record_log = False  # 日志配置弹窗复选框，是否存储日志
        self.last_if_record_log = False  # 日志配置弹窗上一次确认按钮时，是否存储日志
        self.if_record_log_var = tk.IntVar()
        self.operate_log_size = tk.StringVar()  # 日志配置弹窗日志上限大小
        self.log_filepath = tk.StringVar()  # 日志存储路径
        self.operate_desc = tk.StringVar()  # 记录文件/license文件(main_top栏)
        self.work_type = tk.StringVar()  # 工位
        self.curr_port = tk.StringVar()  # 串口号
        self.if_connected = tk.StringVar()  # 连接状态
        self.run_status = tk.StringVar()  # 运行状态
        self.record_desc = tk.StringVar()  # 记录文件(bottom栏)
        self.record_filepath = tk.StringVar()  # 记录文件路径
        self.hid_filepath = ''  # HID存储文件，当work_type为读HID时，等同于record_filepath的值
        self.license_filepath = ''  # 存储license文件，当work_type为写license时，接收record_filepath的值
        self.port_list = []  # 串口列表，main_top串口下拉框展示
        self.curr_baudrate = 115200  # 波特率
        self.data_digit = 8  # 数据位
        self.check_digit = None  # 校验位
        self.stop_digit = 1  # 停止位
        self.stream_controller = None  # 流控
        self.record_hids = []  # 已经存储过的HID
        self.new_add_hids = []  # 一次开始流程中，新增的HID。停止按钮时清零
        self.new_success_hids = []  # 一次开始流程中，成功记录HID的数量(包括重复的)。停止按钮时清零
        self.new_failed_hids = []  # 一次HID开始流程中，失败的数量。停止按钮时清零
        self.hid_license_map = None  # HID_License_Map
        self.if_keep_reading = False  # 是否一直读取HID
        self.activated_hids = []  # 发送过license的HID
        self.success_license = []  # 成功激活的license
        self.failed_license = []  # 激活失败的license

        self.main_menu_bar = tk.Menu()  # 标题栏菜单
        self.port_cb = ttk.Combobox()  # 串口下拉菜单
        self.log_path_entry = tk.Entry()  # 菜单栏日志配置弹窗的日志文件路径
        self.log_path_entry_start_button = tk.Button()  # 菜单栏日志配置弹窗的打开按钮
        self.operate_log_size_entry = tk.Entry()  # 菜单栏日志配置弹窗地日志大小控件
        self.port_cb_port_config = ttk.Combobox()  # 菜单栏串口配置弹窗的串口下拉菜单
        self.baudrate_cb_port_config = ttk.Combobox()  # 菜单栏串口配置弹窗的波特率下拉菜单
        self.data_digit_port_config = ttk.Combobox()  # 菜单栏串口配置弹窗的数据位下拉菜单
        self.check_digit_port_config = ttk.Combobox()  # 菜单栏串口配置弹窗的校验位下拉菜单
        self.stop_digit_port_config = ttk.Combobox()  # 菜单栏串口配置弹窗的停止位下拉菜单
        self.stream_controller_port_config = ttk.Combobox()  # 菜单栏串口配置弹窗的流控下拉菜单
        self.filepath_entry = tk.Entry()  # main_top的文件选择控件
        self.log_shower = tk.Text()  # main_text左边的操作关键信息打印控件
        self.operate_shower = tk.Text()  # main_text右边的操作统计信息打印控件
        self.statistic_shower = tk.Text()  # main_text右边的操作结果打印控件
        self.port_test_desc = tk.StringVar()  # main_top开始测试按钮的显示文字(开始测试/停止测试)
        self.port_test_button = tk.Button()  # main_top的开始测试按钮
        self.start_btn_desc = tk.StringVar()  # main_top开始按钮的文字信息
        self.start_btn_desc.set('开  始')
        self.start_btn = tk.Button()  # main_top中的开始按钮
        self.port_status_label = tk.Label()  # main_bottom中的串口状态label
        self.run_status_label = tk.Label()  # main_bottom中的运行状态label
        self.other_com_entry = None

    def __reset_wait_time(self):
        self.wait_time = 0

    def refresh_var(self, status=StatusEnum.HID.value):  # TODO 两个text 控件也需要刷新
        """
        切换工位时，刷新面板展示
        Args:
            status: HID/License

        Returns:

        """
        logger.info(f'refresh status to {status}')
        # self.curr_port.set('')  # 切换工位时，保留串口选择
        self.if_connected.set('断开')
        self.run_status.set('停  止')
        self.port_test_desc.set('开始测试')
        self.filepath_entry.delete(0, tk.END)  # 清空记录文件输入框内容
        self.log_shower.delete(1.0, tk.END)
        self.operate_shower.delete(1.0, tk.END)
        self.statistic_shower.delete(1.0, tk.END)
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

    def __refresh_statistics_hid(self):
        """读hid过程中，刷新统计栏信息"""
        self.operate_shower.delete(1.0, tk.END)
        self.operate_shower.insert(tk.END, '本轮操作统计\n', 'head')
        self.operate_shower.insert(tk.END, f'新增HID{len(self.new_add_hids)}个\n'
                                           f'成功{len(self.new_success_hids)}个\n'
                                           f'失败{len(set(self.new_failed_hids))}个\n', 'content')
        self.operate_shower.insert(tk.END, f'文件记录HID总共{len(self.record_hids)}个\n', 'tail')

    def __refresh_statistics_license(self):
        """写license过程中，刷新统计栏信息"""
        self.operate_shower.delete(1.0, tk.END)
        self.operate_shower.insert(tk.END, '本轮操作统计\n', 'head')
        self.operate_shower.insert(tk.END, f'完成HID {len(set(self.activated_hids))} 个\n'
                                           f'成功license {len(set(self.success_license))} 个\n'
                                           f'失败license {len(set(self.failed_license))} 个\n',
                                   'content')
        self.operate_shower.insert(tk.END, f'导入HID {len(set(self.hid_license_map.hids))} 个 '
                                           f'license {self.hid_license_map.licenses_counts} 个',
                                   'tail')

    def __refresh_statistic_log_shower(self, status):
        """刷新结果栏信息"""
        self.statistic_shower.delete(1.0, tk.END)
        if status == 'success':
            self.statistic_shower.insert(1.0, '成 功', 'success')
        elif status == 'confirm':
            self.statistic_shower.insert(1.0, '已 完 成', 'confirm')
        elif status == 'fail':
            self.statistic_shower.insert(1.0, '失 败', 'fail')
        elif status == 'stop':
            self.statistic_shower.insert(1.0, '停 止', 'stop')

    def __refresh_run_start_time(self):  # 重置开始时间
        self.run_start_time = datetime.now()
        logger.info(f'重置开始时间： {self.run_start_time}')

    def __do_log_shower_insert(self, content, start=tk.END, tag=None):
        if tag is None:
            self.log_shower.insert(start, content)
            self.operate_logger.logger.info(content.strip())
        else:
            self.log_shower.insert(start, content, tag)
            self.operate_logger.logger.info(f'{tag}-{content.strip()}')

    def __disable_widgets(self, button_name):
        """当点击连接测试，开始按钮时，其余按钮禁止点击"""
        if button_name == '开始测试':
            self.start_btn.config(state=tk.DISABLED)  # 禁用开始按钮
        elif button_name == '开始':
            self.port_test_button.config(state=tk.DISABLED)  # 禁用连接测试按钮

        self.main_menu_bar.entryconfig('工位选择', state=tk.DISABLED)  # 禁用菜单栏工位选择
        self.main_menu_bar.entryconfig('配置', state=tk.DISABLED)  # 禁用菜单栏配置

    def __able_widgets(self, button_name):
        """当点击停止测试，停止按钮时，其余按钮恢复点击"""
        if button_name == '开始测试':
            self.start_btn.config(state=tk.NORMAL)  # 启用开始按钮
        elif button_name == '开始':
            self.port_test_button.config(state=tk.NORMAL)  # 启用连接测试按钮
        self.main_menu_bar.entryconfig('工位选择', state=tk.NORMAL)  # 启用菜单栏工位选择
        self.main_menu_bar.entryconfig('配置', state=tk.NORMAL)  # 启用菜单栏配置

    def __close_log_config(self):
        """日志配置弹窗中，当关闭日志记录时，其余日志配置选项不可配置"""
        self.log_path_entry.config(state=tk.DISABLED)
        self.log_path_entry_start_button.config(state=tk.DISABLED)
        self.operate_log_size_entry.config(state=tk.DISABLED)

    def __open_log_config(self):
        """日志配置弹窗中，当开启日志记录时，打开其余日志配置选项"""
        self.log_path_entry.config(state=tk.NORMAL)
        self.log_path_entry_start_button.config(state=tk.NORMAL)
        self.operate_log_size_entry.config(state=tk.NORMAL)

    def change_status_to_hid(self):
        self.refresh_var(StatusEnum.HID.value)

    def change_status_to_license(self):
        self.refresh_var(StatusEnum.License.value)

    def ori_other_com_entry(self, parent):
        self.other_com_entry = tk.Entry(parent)
        return self.other_com_entry

    def ori_other_com_handler(self, parent, port_cb):

        def handler(event):
            value = port_cb.get()
            if self.other_com_entry is None:
                self.ori_other_com_entry(parent)
            if value == 'other com':
                print('pack')
                self.other_com_entry.pack(side=tk.RIGHT, padx=10, pady=5)
            else:
                self.curr_port.set(value)
                print('destory')
                self.other_com_entry.destroy()
                self.other_com_entry = None
        return handler

    def body(self):  # 绘制主题
        self.window_.config(menu=self.top(self.window_))  # 菜单栏

        # main_top
        self.main_top(self.window_).pack(expand=True, fill=tk.BOTH)

        # main_text
        self.main_text(self.window_).pack(expand=True, fill=tk.BOTH)

        # main_bottom
        self.main_bottom(self.window_).pack(expand=True, fill=tk.X)

    def top(self, parent):

        self.main_menu_bar = tk.Menu(parent)  # 创建一个菜单栏
        self.__top_1(self.main_menu_bar)
        self.__top_2(self.main_menu_bar)

        return self.main_menu_bar

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
            '串口号': Port_Config_Item(name='port_cb_port_config', value=self.port_list),  # TODO 调用串口获取当前串口号
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
        if k_name == '串口号':
            self.get_port_list(cb)()
            if self.curr_port.get() in PyBoard.get_list():
                cb.current(PyBoard.get_list().index(self.curr_port.get()))
            else:
                cb.current(0)
        else:
            cb.current(0)
        cb.pack(side=tk.LEFT, padx=5)
        return frame

    def __top_port_config_confirm(self, parent):  # 确定/取消按钮

        def confirm():
            self.curr_port.set(self.port_cb_port_config.get())
            self.port_cb.set(self.curr_port.get())
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
            if self.if_record_log_var.get() == 0:
                self.if_record_log = False
                logger.info('关闭操作过程日志记录')
                self.__close_log_config()  # 关闭日志配置选项
            elif self.if_record_log_var.get() == 1:
                self.if_record_log = True
                logger.info('开启操作过程日志记录')
                self.__open_log_config()  # 开启日志配置选项
            else:
                logger.warning('未知状态的日志记录', self.if_record_log_var.get())

        record_log_cb = tk.Checkbutton(frame, text='记录日志', variable=self.if_record_log_var,
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

        def path_call_back():
            file_path = filedialog.asksaveasfilename(initialfile=f"{datetime.now().strftime('%Y%m%d%H%M%S')}.log")
            if file_path != '':
                self.log_filepath.set(file_path)

        self.log_path_entry_start_button = tk.Button(parent, text='打开', font=_FONT_S,
                        width=10, bg='whitesmoke', command=path_call_back)
        self.log_path_entry = tk.Entry(parent, textvariable=self.log_filepath)

        return self.log_path_entry, self.log_path_entry_start_button

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
        self.operate_log_size_entry = tk.Entry(parent, textvariable=self.operate_log_size, show=None)  # 明文形式显示
        return self.operate_log_size_entry

    def __top_log_config_3_3(self, parent):
        l = tk.Label(parent, text='MB')
        return l

    def __top_log_config_4(self, parent):
        frame = tk.Frame(parent)

        def cancel():
            parent.destroy()

        def confirm():  # 确定时，需要获取是否需要存储日志，日志存储路径和日志的大小
            if self.if_record_log:
                operate_log_file_path = self.log_filepath.get()
                if not operate_log_file_path:
                    tkinter.messagebox.showwarning(title='Warning', message='请选择存储日志文件')
                    return
                operate_log_size = self.operate_log_size_entry.get()
                if operate_log_size:
                    try:
                        operate_log_size = float(operate_log_size)
                    except Exception as e:
                        tkinter.messagebox.showwarning(title='Warning', message='日志大小需要为纯数字')
                        self.operate_log_size_entry.delete(0, tk.END)
                        return
                    else:
                        if operate_log_size <= 0:
                            tkinter.messagebox.showwarning(title='Warning', message='日志大小需要为正数')
                            self.operate_log_size_entry.delete(0, tk.END)
                            return
                        self.operate_log_size.set(operate_log_size)
                        max_bytes = (min(operate_log_size, 1024/2)) * 1024 * 1024  # 日志最大容量为1024
                        self.operate_logger.add_hander(operate_log_file_path, max_bytes)
                        logger.info(f'开启日志记录：{operate_log_file_path}')
                        if not self.last_if_record_log:
                            self.log_shower.insert(tk.END, f'开启操作日志记录{operate_log_file_path}\n')
                            self.last_if_record_log = True
                else:
                    tkinter.messagebox.showwarning(title='Warning', message='日志上限不能为空')
                    return
            else:
                if self.last_if_record_log:
                    self.log_shower.insert(tk.END, '关闭操作日志记录')
                    self.last_if_record_log = False

            parent.destroy()

        tk.Button(frame, text='取消', font=_FONT_S, bg='silver',
                  height=2, width=8, command=cancel).pack(side=tk.RIGHT, pady=4, padx=10)
        tk.Button(frame, text='确定', font=_FONT_S, bg='silver',
                  height=2, width=8, command=confirm).pack(side=tk.RIGHT, pady=4, padx=10)
        return frame

    def main_top(self, parent):
        frame = tk.Frame(parent, bd=3, highlightcolor='silver', highlightthickness=1)

        self.__main_top_1(frame).pack(side=tk.RIGHT, fill=tk.Y, padx=10)
        self.__main_top_2(frame).pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=10)
        self.__main_top_3(frame).pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=10)

        return frame

    def __main_top_1(self, parent):

        frame = tk.Frame(parent)

        def start():
            if self.start_btn_desc.get() == '开  始':
                self.__reset_wait_time()
                temp_port = self.port_cb.get()
                file_path = self.record_filepath.get()
                if not temp_port:
                    tkinter.messagebox.showwarning(title='Warning',
                                                   message='未选中串口号')
                elif not file_path:
                    tkinter.messagebox.showwarning(title='Warning',
                                                   message='未选择HID记录文件/license存储文件')
                else:
                    if temp_port == 'other com':
                        temp_port = self.other_com_entry.get()
                    if temp_port not in PyBoard.get_list():
                        tkinter.messagebox.showwarning(title='WARNNING',
                                                       message='无法连接的串口号，请确认串口号合法并且该串口可连接')
                        return
                    self.__refresh_run_start_time()
                    self.port_cb.set(temp_port)
                    self.__disable_widgets('开始')
                    self.start_btn_desc.set('停  止')
                    self.start_btn.config(fg='red')
                    try:
                        self.curr_port.set(temp_port)
                        self.if_keep_reading = True
                        work_type = self.work_type.get()
                        if work_type == '读HID':
                            t = Thread(target=self.do_hid_line, daemon=True)
                            t.start()
                        elif work_type == '写license':
                            t = Thread(target=self.do_license_line, daemon=True)
                            t.start()
                        else:
                            print(f'错误的工作状态: {work_type}')
                    except Exception as e:
                        self.start_btn_desc.set('开  始')
                        self.start_btn.config(fg='green')
                        self.__turn_off()
            elif self.start_btn_desc.get() == '停  止':
                self.__able_widgets('开始')
                self.__reset_wait_time()
                self.if_keep_reading = False
                self.start_btn_desc.set('开  始')
                self.start_btn.config(fg='green')
                self.__turn_off()

        self.start_btn = tk.Button(frame, textvariable=self.start_btn_desc, height=1, width=8,
                                   fg='green', bg='#918B8B', font=_FONT_L, command=start)
        self.start_btn.pack(side=tk.LEFT, padx=20)
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

    def __main_top_2_2(self, parent):

        self.port_cb = ttk.Combobox(parent, value=self.port_list, width=25)
        self.port_cb.bind('<Button-1>', self.get_port_list(self.port_cb))
        self.port_cb.bind('<<ComboboxSelected>>', self.ori_other_com_handler(parent, self.port_cb))
        return self.port_cb

    def __main_top_2_3(self, parent):

        def _test_connect():  # 连接测试
            if self.port_test_desc.get() == '开始测试':
                temp_port = self.port_cb.get()
                if temp_port:  # 当前选择了串口号
                    if temp_port == 'other com':
                        temp_port = self.other_com_entry.get()
                    if temp_port not in PyBoard.get_list():
                        tkinter.messagebox.showwarning(title='WARNNING',
                                                       message='无法连接的串口号，请确认串口号合法并且该串口可连接')
                        return
                    self.curr_port.set(temp_port)
                    self.port_cb.set(temp_port)
                    try:
                        self.if_keep_reading = True
                        self.port_test_desc.set('停止测试')
                        self.__disable_widgets('开始测试')
                        self.connect_to_board(type_='test')
                    except Exception as e:
                        print(e)
                        tkinter.messagebox.showerror(title='ERROR', message=str(e))
                else:
                    tkinter.messagebox.showwarning(title='Warning',
                                                   message='未选中串口号')
            elif self.port_test_desc.get() == '停止测试':
                if self.conn is not None:
                    self.disconnect_to_board()
                self.if_keep_reading = False
                self.port_test_desc.set('开始测试')
                self.__able_widgets('开始测试')
                self.__turn_off()
            else:
                print(f'unexcept dest: {self.port_test_desc.get()}')

        self.port_test_desc.set('开始测试')
        self.port_test_button = tk.Button(parent, textvariable=self.port_test_desc, font=_FONT_S,
                      width=10, bg='#918B8B',
                      command=_test_connect)
        return self.port_test_button

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
                    print('work type:', self.work_type.get())
                    if self.work_type.get() == '读HID':
                        self.hid_filepath = file_path
                        self.record_hids = read_HID(file_path)
                    elif self.work_type.get() == '写license':
                        self.license_filepath = file_path
                        try:
                            self.hid_license_map = HID_License_Map(file_path)  # hid_license映射对象
                        except DaoException as e:
                            tkinter.messagebox.showerror(title='Error',
                                                         message=str(e))
                            self.record_filepath.set('')
                            return
                        except Exception as e:
                            tkinter.messagebox.showerror(title='Error',
                                                         message='读取license存储文件失败，请检查文件格式是否正确')
                            self.record_filepath.set('')
                            return
                        self.__do_log_shower_insert(f'导入license文件，'
                                                    f'共导入HID{len(set(self.hid_license_map.hids))}个, '
                                                    f'license{self.hid_license_map.licenses_counts}个\n')
                        print('写license路径', self.hid_license_map)
                else:
                    tkinter.messagebox.showwarning(title='Warning',
                                                   message='请选择Excel类型文件')

        btn = tk.Button(parent, text='打开', font=_FONT_S,
                        width=10, bg='#918B8B',
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
        sb = tk.Scrollbar(parent)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_shower = tk.Text(parent, width=50, height=15, yscrollcommand=sb.set)
        self.log_shower.insert(tk.END, '默认关闭操作日志\n')
        self.log_shower.tag_config('error', foreground='red', font=_FONT_B)
        self.log_shower.tag_config('confirm', foreground='green', font=_FONT_B)
        self.log_shower.tag_config('warn', foreground='blue', font=_FONT_B)
        sb.config(command=self.log_shower.yview)
        return self.log_shower

    def __main_text_left_2(self, parent):  # 清除日志按钮

        def clean_log():
            self.log_shower.delete(1.0, tk.END)  # 清除text中文本
            # self.__do_log_shower_insert('清除日志...\n', start=1.0)
        b = tk.Button(parent, text='清除日志', font=_FONT_S, height=1, width=8,
                      bg='#918B8B', padx=1, pady=1, command=clean_log)
        return b

    def __main_text_right(self, parent):  # 操作统计Text控件，清除统计按钮
        frame_right = tk.Frame(parent)
        self.__main_text_right_1(frame_right).pack(expand=True, fill=tk.BOTH)  # 日志打印text控件
        self.__main_text_right_2(frame_right).pack(expand=True, fill=tk.X)
        self.__main_text_right_3(frame_right).pack(side=tk.RIGHT)

        return frame_right

    def __main_text_right_1(self, parent):  # 日志打印Text
        self.operate_shower = tk.Text(parent, width=30, height=10, font=_FONT_L)
        self.operate_shower.tag_config('head', lmargin1=25, rmargin=10, spacing1=15, spacing3=15)
        self.operate_shower.tag_config('content', lmargin1=25, rmargin=10, spacing1=5)
        self.operate_shower.tag_config('tail', lmargin1=25, rmargin=10, spacing1=20)
        return self.operate_shower

    def __main_text_right_2(self, parent):
        self.statistic_shower = tk.Text(parent, width=10, height=2, font=('微软雅黑', 24))
        self.statistic_shower.tag_config('success', foreground='green', justify='center', spacing1=20)
        self.statistic_shower.tag_config('confirm', foreground='seagreen', justify='center', spacing1=20)
        self.statistic_shower.tag_config('fail', foreground='red', justify='center', spacing1=20)
        self.statistic_shower.tag_config('stop', foreground='blue', justify='center', spacing1=20)
        return self.statistic_shower

    def __main_text_right_3(self, parent):  # 清除日志按钮

        def clean_log():
            self.operate_shower.delete(1.0, tk.END)  # 清除text中文本

        b = tk.Button(parent, text='清除统计', font=_FONT_S, height=1, width=8,
                      bg='#918B8B', padx=1, pady=1, command=clean_log)
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
        l = tk.Label(parent, textvariable=self.work_type, fg='green')
        return l

    def __main_bottom_2(self, parent):
        l = tk.Label(parent, text='串口状态:')
        return l

    def __main_bottom_2_value(self, parent):
        self.port_status_label = tk.Label(parent, textvariable=self.if_connected)
        return self.port_status_label

    def __main_bottom_3(self, parent):
        l = tk.Label(parent, text='运行状态:')
        return l

    def __main_bottom_3_value(self, parent):
        self.run_status_label = tk.Label(parent, textvariable=self.run_status)
        return self.run_status_label

    def __main_bottom_4(self, parent):
        self.record_filepath_label = tk.Label(parent, textvariable=self.record_desc)
        return self.record_filepath_label

    def __main_bottom_5(self, parent):
        l = tk.Label(parent, textvariable=self.record_filepath, fg='green')
        return l

    def run(self):
        self.window_.mainloop()
        logger.info('----------------------Process Start-----------------------')

    def __turn_on(self, type_='start'):  # 连接上串口时，更新属性
        self.if_connected.set(f'{self.curr_port.get()}已连接')
        if type_ == 'start':
            self.run_status.set('工作中')
            self.run_status_label.config(fg='green')
        self.port_status_label.config(fg='green')
        self.__do_log_shower_insert(f'串口{self.curr_port.get()}连接成功\n')

    def __turn_off(self):  # 断开串口连接时，更新属性
        self.if_connected.set(f'断开')
        self.run_status.set('停  止')
        self.port_status_label.config(fg='black')
        self.run_status_label.config(fg='black')
        self.new_add_hids = []
        self.new_success_hids = []
        self.new_failed_hids = []

    # 以上为界面代码，以下为逻辑代码
    def connect_to_board(self, type_='start'):
        """连接串口"""
        logger.info(f'连接串口 {self.curr_port.get()}')
        if self.curr_port.get():
            self.conn = PyBoard(self.curr_port.get(), self.curr_baudrate)
            if self.conn.is_open:  # 已连接
                self.__turn_on(type_=type_)
                return True
            else:
                self.__do_log_shower_insert(f'串口{self.curr_port.get()}连接失败\n', tag='warn')
                return False

    def disconnect_to_board(self, if_print=True):
        """断开串口连接"""
        logger.info(f'断开串口连接 {self.curr_port.get()}')
        if self.conn.is_open:
            self.conn.close()
            if if_print:
                self.__do_log_shower_insert(f'串口{self.curr_port.get()}断开连接\n\n')

    def get_port_list(self, cb):
        """获取当前可用的串口列表"""
        def _get_port_list(*args):
            self.port_list = PyBoard.get_list()
            if cb is self.port_cb:
                self.port_list.append('other com')
            cb['value'] = self.port_list
            if self.port_list and self.port_list != ['other com']:
                self.__do_log_shower_insert('检测到串口')
                for port_ in self.port_list:
                    if port_ == 'other com':
                        continue
                    self.__do_log_shower_insert(f' {port_}')
                self.log_shower.insert('end', '\n')
            else:
                self.__do_log_shower_insert('未检测到串口\n')
        return _get_port_list

    def do_hid_line(self):
        """开始读HID流程"""
        while self.if_keep_reading:
            if self.wait_time >= self.MAX_WAIT_TIME:
                self.disconnect_to_board(if_print=False)
                self.__do_log_shower_insert('连接未操作时间过长，自动断开连接\n\n', tag='warn')
                self.__able_widgets('开始')
                self.__refresh_statistic_log_shower('stop')
                self.if_keep_reading = False
                self.start_btn_desc.set('开  始')
                self.start_btn.config(fg='green')
                self.__turn_off()
                return

            if (datetime.now() - self.run_start_time) > self.MAX_INTERVAL_SECOND:
                self.disconnect_to_board(if_print=False)
                self.__do_log_shower_insert('持续失败时间超时，自动断开连接\n\n', tag='warn')
                self.__able_widgets('开始')
                self.__refresh_statistic_log_shower('stop')
                self.if_keep_reading = False
                self.start_btn_desc.set('开  始')
                self.start_btn.config(fg='green')
                self.__turn_off()
                return

            if_connected = self.connect_to_board()  # 同串口建立连接
            if if_connected:
                self.get_hid(self.conn)  # 串口通信获取HID

    def get_hid(self, serial_obj):
        """
        同串口通信，获取设备HID
        Args:
            serial_obj: 串口连接对象

        Returns:

        """
        logger.info('get hid start')
        self.__refresh_statistic_log_shower('reset')
        self.__do_log_shower_insert(f'开始读设备HID...\n')
        try:
            hid_response = serial_obj.get_HID()
        except SerialException as e:
            logger.warning('串口访问异常', e)
            self.__do_log_shower_insert(f'设备HID读取失败，稍后将重试或更换设备\n', tag='error')
            self.__refresh_statistic_log_shower('fail')
            self.disconnect_to_board()
            return
        except Exception as e:
            logger.warning('串口访问异常', e)
            self.__do_log_shower_insert(f'设备HID读取失败，稍后将重试或更换设备\n', tag='error')
            self.__refresh_statistic_log_shower('fail')
            self.disconnect_to_board()
            return
        else:
            if hid_response is None:
                self.__do_log_shower_insert(f'设备HID读取失败，稍后将重试或更换设备\n', tag='error')
                self.__refresh_statistic_log_shower('fail')
                self.disconnect_to_board()
                return
        try:
            board_protocol = parse_protocol(hid_response)
        except Exception as e:
            self.__do_log_shower_insert(f'解析及校验HID response失败\n', tag='error')
            self.__refresh_statistic_log_shower('fail')
            self.disconnect_to_board()
            return
        hid_value = board_protocol.payload_data.data
        self.__do_log_shower_insert(f'设备HID读取成功, HID {hid_value}\n')
        if hid_value not in self.record_hids:
            self.__reset_wait_time()  # 重置等待时间
            logger.info(f'添加hid：{hid_value}')
            self.__do_log_shower_insert(f'记录设备{hid_value}到表格\n')
            if Path(self.hid_filepath).exists():

                try:
                    record_HID_activated(hid_value, Path(self.hid_filepath))
                except Exception as e:
                    self.new_failed_hids.append(hid_value)
                    self.__refresh_statistics_hid()
                    logger.exception(e)
                    self.__do_log_shower_insert(f'设备{hid_value}HID存储失败\n', tag='error')
                    self.__refresh_statistic_log_shower('fail')
                    self.disconnect_to_board()
                else:
                    self.__refresh_run_start_time()
                    self.record_hids.append(hid_value)
                    self.new_success_hids.append(hid_value)
                    self.new_add_hids.append(hid_value)
                    self.__refresh_statistics_hid()
                    self.__do_log_shower_insert(f'设备{hid_value}HID存储完成，请更换设备...\n', tag='confirm')
                    self.__refresh_statistic_log_shower('success')
                    self.disconnect_to_board()
                    time.sleep(3)
        else:
            if hid_value not in self.new_success_hids:
                self.new_success_hids.append(hid_value)
            self.__refresh_statistics_hid()
            self.wait_time += 1
            self.__do_log_shower_insert(f'设备{hid_value}已完成，请更换设备...\n', tag='warn')
            self.__refresh_statistic_log_shower('confirm')
            self.disconnect_to_board()
            time.sleep(3)

    def do_license_line(self):
        """开始写license流程"""
        logger.info('write license start')
        self.__do_log_shower_insert('开始写license流程\n')
        self.__refresh_statistic_log_shower('reset')
        while self.if_keep_reading:
            if self.wait_time >= self.MAX_WAIT_TIME:
                self.__do_log_shower_insert('连接未操作时间过长，自动断开连接\n\n', tag='warn')
                self.disconnect_to_board()
                self.if_keep_reading = False
                self.__refresh_statistic_log_shower('stop')
                self.start_btn_desc.set('开  始')
                self.start_btn.config(fg='green')
                self.__able_widgets('开始')
                self.__turn_off()
                return

            if (datetime.now() - self.run_start_time) > self.MAX_INTERVAL_SECOND:
                self.disconnect_to_board(if_print=False)
                self.__do_log_shower_insert('持续失败时间超时，自动断开连接\n\n', tag='warn')
                self.__refresh_statistic_log_shower('stop')
                self.if_keep_reading = False
                self.start_btn_desc.set('开  始')
                self.start_btn.config(fg='green')
                self.__able_widgets('开始')
                self.__turn_off()
                return

            if_connected = self.connect_to_board()
            logger.info(f'connected to {self.curr_port.get()}')
            if_success = True
            if if_connected:
                try:
                    hid_response = self.conn.get_HID()
                except Exception as e:
                    self.disconnect_to_board()
                    time.sleep(1)  # 可能有板子的插拔动作
                    continue
                else:
                    if hid_response is None:
                        self.__do_log_shower_insert(f'获取设备HID失败\n', tag='error')
                        self.__refresh_statistic_log_shower('fail')
                        self.disconnect_to_board()
                        time.sleep(1)
                        continue
                logger.info(f'get hid response')

                try:
                    board_protocol = parse_protocol(hid_response)
                except Exception as e:
                    self.disconnect_to_board()
                    time.sleep(1)  # 可能有板子的插拔动作
                    continue
                logger.info('parse hid success')
                hid_value = board_protocol.payload_data.data
                self.__do_log_shower_insert(f'获取设备HID成功，HID {hid_value}\n')
                if hid_value not in self.activated_hids:
                    self.__reset_wait_time()
                    hid_licenses = self.hid_license_map.get_license(hid_value)
                    if not hid_licenses:  # 该hid没有获取到相应的license
                        logger.warning(f'{hid_value} 没有获取到license\n')
                        self.__do_log_shower_insert('license写入失败: license文件中没有找到该hid\n')
                        self.__refresh_statistics_license()
                        self.__refresh_statistic_log_shower('fail')
                        self.disconnect_to_board()
                        time.sleep(1)
                        continue
                    self.__do_log_shower_insert(f'对设备{hid_value}，写入license\n')
                    for component_id, license_ in hid_licenses.items():
                        try:
                            license_ = b64tostrhex(license_)
                        except Exception as e:
                            logger.error(f'license {license_}转码错误')
                            self.__do_log_shower_insert(f'{component_id}写入license{str(license_)[:20]}...失败，'
                                                        f'license转码错误\n', tag='warn')
                            self.failed_license.append(license_)
                            self.__refresh_statistics_license()
                            if_success = False
                            time.sleep(1)
                            continue
                        protocol = build_protocol(license_, component_id=component_id,
                                                  command=ProtocolCommand.license_put_request.value,
                                                  )
                        if not self.send_license(self.conn, protocol):
                            self.__do_log_shower_insert(f'{component_id}写入license{license_[:20]}...失败\n', tag='warn')
                            self.failed_license.append(license_)
                            self.__refresh_statistics_license()
                            if_success = False
                        else:
                            self.__do_log_shower_insert(f'{component_id}写入license{license_}成功\n', tag='warn')
                            self.success_license.append(license_)
                            self.__refresh_statistics_license()
                    if if_success:
                        self.__refresh_run_start_time()
                        self.__do_log_shower_insert(f'设备{hid_value}写入license成功\n', tag='confirm')
                        self.__refresh_statistic_log_shower('success')
                        self.activated_hids.append(hid_value)
                        self.__refresh_statistics_license()
                    else:
                        self.__refresh_statistic_log_shower('fail')
                        self.__do_log_shower_insert(f'设备{hid_value}写入license失败\n', tag='error')
                else:
                    self.wait_time += 1
                    self.__refresh_statistic_log_shower('confirm')
                    self.__do_log_shower_insert(f'设备{hid_value}已经写入过license，请更换设备...\n', tag='warn')
            self.disconnect_to_board()
            time.sleep(3)

    def send_license(self, serial_obj, protocol):
        logger.info(f'send license start：{protocol}')
        try:
            serial_obj.send_license(protocol)
        except SerialException as e:
            logger.warning('串口无法访问')
            self.__do_log_shower_insert('串口无法通信\n')
            return
        except Exception as e:
            logger.exception(e)
            self.__do_log_shower_insert('写入license失败\n')
            return

        try:
            resp = serial_obj.read_response()
        except SerialException as e:
            logger.warning('未获取到license写入结果')
            self.__do_log_shower_insert('未获取到license写入结果\n')
            return
        except Exception as e:
            logger.exception(e)
            self.__do_log_shower_insert('获取license写入结果失败\n')
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
                self.__do_log_shower_insert('license写入成功\n', tag='confirm')
                return True
            else:
                error_type = Error_Data_Map.get(payload_data.data)
                if error_type is not None:
                    logger.info(f'license写入失败，指令{payload_data.command}，')
                    self.__do_log_shower_insert(f'license写入错误, '
                                                f'指令{payload_data.command} 错误类型{error_type}\n')
                else:
                    logger.info(f'license写入失败，指令{payload_data.command}，')
                    self.__do_log_shower_insert(f'license写入错误, '
                                                f'指令{payload_data.command}数据{payload_data.data}\n')
        else:  # 没有正确获取到返回
            self.__do_log_shower_insert('license写入失败\n', tag='error')


if __name__ == '__main__':
    oneos_gui = OneOsGui()
    oneos_gui.run()

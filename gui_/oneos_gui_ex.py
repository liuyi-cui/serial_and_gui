# -*- coding: utf-8 -*-
"""GUI操作界面"""
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

_font_s = ('微软雅黑', 8)  # 字体
_font_b = ('微软雅黑', 12)  # 字体


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


def get_window_size(win, update=True):
    """获取窗体的大小"""
    if update:
        win.update()
    return win.winfo_width(), win.winfo_height(), win.winfo_x(), win.winfo_y()


class OneOsGui:

    def __init__(self):
        self.window_ = tk.Tk()
        center_window(self.window_, 600, 450)
        self.window_.title('OneOS License管理工具 -1.0.0')
        self.window_.grab_set()
        self.body()
        self.window_.pack_propagate(True)

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

        def change_operate(chioce):
            if chioce == 1:
                print('选择了读HID')
            elif chioce == 2:
                print('选择了写License')

        # 创建一个 工位选择 菜单栏(默认不下拉，下拉选项包括 读HID，写License)
        operate_menu = tk.Menu(parent, bd=10, relief='sunken', tearoff=0)
        # 放置operate
        parent.add_cascade(label='工位选择', menu=operate_menu)
        # 放入选项
        operate_menu.add_command(label='读HID', command=change_operate(chioce=1))
        operate_menu.add_separator()  # 添加一条分割线
        operate_menu.add_command(label='写License', command=change_operate(chioce=2))

    def __top_2(self, parent):

        def change_operate(chioce):
            if chioce == 1:
                print('选择串口配置')
            elif chioce == 2:
                print('选择日志配置')

        # 创建一个 工位选择 菜单栏(默认不下拉，下拉选项包括 读HID，写License)
        operate_menu = tk.Menu(parent, bd=10, relief='sunken', tearoff=0)
        # 放置operate
        parent.add_cascade(label='配置', menu=operate_menu)
        # 放入选项
        operate_menu.add_command(label='串口配置', command=change_operate(chioce=1))
        operate_menu.add_separator()  # 添加一条分割线
        operate_menu.add_command(label='日志配置', command=change_operate(chioce=2))

    def main_top(self, parent):
        frame = tk.Frame(parent, bg='red', bd=3, highlightcolor='silver', highlightthickness=1)

        self.__main_top_1(frame).pack(side=tk.RIGHT, fill=tk.Y, padx=10)
        self.__main_top_2(frame).pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=10)
        self.__main_top_3(frame).pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=10)

        return frame

    def __main_top_1(self, parent):

        frame = tk.Frame(parent)
        def start():
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
        port_list = ['COM1', 'COM2', 'COM3', 'COM4', 'COM5']
        port_cb = ttk.Combobox(parent, value=port_list, width=25)
        return port_cb

    def __main_top_2_3(self, parent):
        def test_connect():  # 连接测试
            print('进行连接测试')

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
        l = tk.Label(parent, text='记录文件', font=_font_b)
        return l

    def __main_top_3_2(self, parent):

        record_hid_filepath = tk.StringVar()  # 接收文件路径

        def path_call_back():
            file_path = filedialog.askopenfilename()
            if file_path != '':
                record_hid_filepath.set(file_path)

        btn = tk.Button(parent, text='打开', font=_font_s,
                      width=10, bg='whitesmoke',
                      command=path_call_back)
        filepath_entry = tk.Entry(parent, textvariable=record_hid_filepath)

        return filepath_entry, btn

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

        self.__main_bottom_1(parent).pack(side=tk.LEFT, padx=20, fill=tk.X)
        self.__main_bottom_2(parent).pack(side=tk.LEFT, padx=20, fill=tk.X)
        self.__main_bottom_3(parent).pack(side=tk.LEFT, padx=20, fill=tk.X)
        self.__main_bottom_4(parent).pack(side=tk.LEFT, padx=20, fill=tk.X)

        return frame

    def __main_bottom_1(self, parent):
        l = tk.Label(parent, text='工位：读HID')
        return l

    def __main_bottom_2(self, parent):
        l = tk.Label(parent, text='串口号：COM21')
        return l

    def __main_bottom_3(self, parent):
        l = tk.Label(parent, text='串口状态：断开')
        return l

    def __main_bottom_4(self, parent):
        l = tk.Label(parent, text='记录文件：filepath')
        return l

    def run(self):
        self.window_.mainloop()


if __name__ == '__main__':
    oneos_gui = OneOsGui()
    oneos_gui.run()

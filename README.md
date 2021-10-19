### 概述

设备`license`管理辅助工具，负责`license`申请的部分前置操作以及下发`license`至设备。

### 目录

```shell
# 仅呈现License相关文件/文件夹
├── HIDs  # 记录从设备直接读取的HID信息
├── input  # 存放从U盘复制得到的License Map文件
|   |-- HIDs-License
├── output  
|   |-- HIDs_used  # 记录已成功使用License的设备HID
├── log  # 日志
|   |--  XXX
├── gui_  # gui界面相关
|   |--  XXX
├── main.py  # 程序入口
├── python  # python环境
|   |--  XXX
├── serial_  # 串口连接相关
|   |--  XXX
├── utility  # 其它
|   |--  XXX
```

### License相关操作流程

![License操作流程图](image\License操作流程图.png)

### 其它


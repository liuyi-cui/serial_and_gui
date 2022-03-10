# -*- coding: utf-8 -*-
from pathlib import Path

# gui工具标题
TITLE_MAIN = 'OneOS License管理工具 -v0.0.3'

# UKey配套的dll路径
PROJ_PATH = Path(__file__).parent
# DLL_PATH = r'D:\Projects\python\LicenseManagementTool\files\UKey\Python-x64\Don_API-x64.dll'
DLL_PATH = Path(PROJ_PATH, 'Don_API-x64.dll').as_posix()

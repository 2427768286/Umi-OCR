import json
from enum import Enum
import tkinter as tk
import tkinter.messagebox
from locale import getdefaultlocale


# 项目属性
class Umi:
    name = None
    ver = None
    website = None
    about = None
    test = None  # 开发使用


class RunModeFlag(Enum):
    '''进程管理模式标志'''
    short = 0  # 按需关闭（减少空闲时内存占用）
    long = 1  # 后台常驻（大幅加快任务启动速度）


# 配置文件路径
ConfigJsonFile = "Umi-OCR_config.json"

# 配置项
ConfigDict = {
    # 计划任务设置
    "isOpenExplorer": False,  # T时任务完成后打开资源管理器到输出目录。isOutputFile为T时才管用
    "isOpenOutputFile": False,  # T时任务完成后打开输出文件。isOutputFile为T时才管用
    "isOkMission": False,  # T时本次任务完成后执行指定计划任务。
    "okMissionName": "",  # 当前选择的计划任务的name。
    "okMission": {  # 计划任务事件，code为cmd代码
        "关机":  # 取消：shutdown /a
        {"code": r'msg %username% /time:25 "Umi-OCR任务完成，将在30s后关机" & echo 关闭本窗口可取消关机 & choice /t 30 /d y /n >nul & shutdown /f /s /t 0'},
        "休眠":  # 用choice实现延时
        {"code": r'msg %username% /time:25 "Umi-OCR任务完成，将在30s后休眠" & echo 关闭本窗口可取消休眠 & choice /t 30 /d y /n >nul & shutdown /f /h'},
    },

    # 读取剪贴板设置
    "isGlobalHotkey": False,  # T时绑定全局快捷键
    "isNeedCopy": False,  # T时识别完成后自动复制文字
    "globalHotkey": "",  # 全局快捷键

    # 忽略区域设置
    "ignoreArea": None,  # 忽略区域
    # "ignoreAreaPreset": [],  # 忽略区域预设列表

    # 输入文件设置
    "isRecursiveSearch": False,  # T时导入文件夹将递归查找子文件夹中所有图片

    # 输出文件设置
    "isOutputFile": True,  # T时输出内容写入本地文件
    "outputFilePath": "",  # 输出文件目录
    "outputFileName": "",  # 输出文件名称

    # 输出格式设置
    "isOutputDebug": False,  # T时输出调试信息
    "isIgnoreNoText": True,  # T时忽略(不输出)没有文字的图片信息
    "outputStyle": 1,  # 1：纯文本，2：Markdown

    # 引擎设置
    "ocrToolPath": "PaddleOCR-json/PaddleOCR_json.exe",  # 引擎路径
    "ocrRunModeName": "",  # 当前选择的进程管理策略
    "ocrRunMode": {
        "后台常驻（大幅加快任务启动速度）": RunModeFlag.long,
        "按需关闭（减少空闲时内存占用）": RunModeFlag.short,
    },
    "ocrProcessStatus": "未启动",  # 进程运行状态字符串，由引擎单例传到tk窗口
    "ocrConfigName": "",  # 当前选择的配置文件的name。
    "ocrConfig": {  # 配置文件信息
        "简体中文": {
            "path": "PaddleOCR_json_config_ch.txt"
        }
    },
    "argsStr": "",  # 启动参数字符串
    "imageSuffix": ".jpg .jpe .jpeg .jfif .png .webp .bmp .tif .tiff"  # 图片后缀
}

#  需要保存的设置项
SaveItem = [
    "isOpenExplorer",
    "isOpenOutputFile",
    "okMission",
    "okMissionName",
    "isGlobalHotkey",
    "isNeedCopy",
    "globalHotkey",
    "isRecursiveSearch",
    "isOutputFile",
    "isOutputDebug",
    "isIgnoreNoText",
    "outputStyle",
    "ocrToolPath",
    "ocrRunModeName",
    "ocrConfigName",
    "ocrConfig",
    "argsStr",
    "imageSuffix",
]


class ConfigModule:
    sysEncoding = 'cp936'  # 系统编码。初始化时获取
    # ↓ 在这些编码下能使用全部功能，其它编码不保证能使用如拖入含中文路径的图片等功能。
    # ↓ 但识图功能是可以正常使用的。
    sysEncodingSalf = ['cp936', 'cp65001']

    def __init__(self):
        self.optVar = {}

    def initValue(self, optVar, tkUpdate):
        """初始化配置。传入并设置tk变量字典，主窗刷新接口。"""
        self.optVar = optVar
        self.tkUpdate = tkUpdate

        def setSysEncoding():  # 获取系统编码
            """初始化编码"""
            # https://docs.python.org/zh-cn/3.8/library/locale.html#locale.getdefaultlocale
            # https://docs.python.org/zh-cn/3.8/library/codecs.html#standard-encodings
            self.sysEncoding = getdefaultlocale()[1]
            print(f'获取系统编码：{self.sysEncoding}')
        setSysEncoding()  # 初始化编码

        def load():
            """从本地json文件读取配置"""
            try:
                with open(ConfigJsonFile, "r", encoding="utf8")as fp:
                    jsonData = json.load(fp)  # 读取json文件
                    for key in jsonData:
                        if key in ConfigDict:
                            ConfigDict[key] = jsonData[key]
            except json.JSONDecodeError:  # 反序列化json错误
                if tk.messagebox.askyesno(
                    "遇到了一点小问题",
                        f"载入配置文件 {ConfigJsonFile} 时，反序列化json失败。\n\n选 “是” 重置该文件。\n选 “否” 将退出程序。"):
                    self.save()
                else:
                    exit(0)
            except FileNotFoundError:  # 无配置文件
                self.save()
                # 当成是首次启动软件，提示
                if self.sysEncoding not in self.sysEncodingSalf:  # 不安全的地区
                    tk.messagebox.showwarning(
                        '警告',
                        f'您的系统地区编码为[{self.sysEncoding}]，可能导致拖入图片的功能异常，建议使用浏览按钮导入图片。其它功能应该能正常使用。')
        load()  # 加载配置文件

        if not self.sysEncoding:  # 无法获取地区，赋默认值
            self.sysEncoding = 'utf-8'

        for key in optVar:
            if key in ConfigDict:
                optVar[key].set(ConfigDict[key])

    def isSaveItem(self, key):
        return key in SaveItem

    def save(self):
        """保存配置到本地json文件"""
        saveDict = {}  # 提取需要保存的项
        for key in SaveItem:
            saveDict[key] = ConfigDict[key]
        with open(ConfigJsonFile, "w", encoding="utf8")as fp:
            fp.write(json.dumps(saveDict, indent=4, ensure_ascii=False))

    def update(self, key):
        """更新某个值，从tk变量读取到配置项"""
        ConfigDict[key] = self.optVar[key].get()

    def get(self, key):
        """获取一个配置项的值"""
        return ConfigDict[key]

    def set(self, key, value, isUpdateTK=False):
        """设置一个配置项的值"""
        if key in self.optVar:
            self.optVar[key].set(value)
            if isUpdateTK:
                self.tkUpdate()
        else:
            ConfigDict[key] = value


Config = ConfigModule()  # 设置模块 单例
import os
import logging
import time
import datetime
import yaml
from typing import Any, Dict, Optional, Literal, Callable, Union
from logging.handlers import RotatingFileHandler
from rich.logging import RichHandler
from rich.console import Console


class CustomFormatter(logging.Formatter):
    """自定义格式化器，用于调整日志格式"""

    # fmt: off
    __MAX_LENGTH_FILENAME  = 10     # 文件名最大长度
    __MAX_LENGTH_LINENO    = 4      # 行号长度
    __MAX_LENGTH_LEVELNAME = 8      # 等级长度
    __MAX_LENGTH_MODULE    = 10     # 模块名最大长度
    __MAX_LENGTH_FUNCTION  = 10     # 函数名最大长度
    __MAX_LENGTH_THRED     = 10     # 线程名最大长度
    # fmt: on
    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        style: Literal['%', '{', '$'] = "%",
        config: Optional[Dict[str, int]] = None,
        validate: bool = True,
        centering: bool = False,
    ) -> None:
        super().__init__(fmt, datefmt, style, validate)
        self.centering = centering
        self._set_maxlength(config)

    def format(self, record: logging.LogRecord) -> str:
        if self.centering:
            return self._format_centering(record)
        else:
            return self._format_non_centering(record)

    def _set_maxlength(self, config: Optional[Dict[str, int]]) -> None:
        if not config:
            return

        self.__MAX_LENGTH_FILENAME = config.get(
            'MAX_LENGTH_FILENAME', self.__MAX_LENGTH_FILENAME
        )
        self.__MAX_LENGTH_LINENO = config.get(
            'MAX_LENGTH_LINENO', self.__MAX_LENGTH_LINENO
        )
        self.__MAX_LENGTH_LEVELNAME = config.get(
            'MAX_LENGTH_LEVELNAME', self.__MAX_LENGTH_LEVELNAME
        )
        # self.__MAX_LENGTH_MODULE = config.get(
        #     'MAX_LENGTH_MODULE', self.__MAX_LENGTH_MODULE
        # )
        # self.__MAX_LENGTH_FUNCTION = config.get(
        #     'MAX_LENGTH_FUNCTION', self.__MAX_LENGTH_FUNCTION
        # )
        # self.__MAX_LENGTH_THRED = config.get(
        #     'MAX_LENGTH_THRED', self.__MAX_LENGTH_THRED
        # )

    def _format_key(
        self, pattern: str, max_length: int, fmt_func: Callable[[str], str]
    ):
        if len(pattern) > max_length:
            left = max_length // 2
            right = max_length - max_length // 2
            pattern = f"{pattern[:left-1]}*{pattern[-right:]}"
        else:
            pattern = fmt_func(pattern, max_length)

        return pattern

    def _format_centering(self, record: logging.LogRecord) -> str:

        # fmt: off
        lineno     = f"{record.lineno}".center(self.__MAX_LENGTH_LINENO)
        levelname  = f"{record.levelname}".center(self.__MAX_LENGTH_LEVELNAME)
        asctime    = self.formatTime(record, self.datefmt)
        filename   = self._format_key(record.filename, self.__MAX_LENGTH_FILENAME, str.rjust)
        # module     = self._format_key(record.module, self.__MAX_LENGTH_MODULE, str.rjust)
        # funcname   = self._format_key(record.funcName, self.__MAX_LENGTH_FUNCTION, str.ljust)
        # threadname = self._format_key(record.threadName, self.__MAX_LENGTH_THRED, str.ljust)
        # fmt: on

        # 使用字符串格式化直接创建对齐后的日志
        formatted_msg = (
            f"{asctime} | {filename}:{lineno} | {levelname} | {record.getMessage()}"
        )
        return formatted_msg

    def _format_non_centering(self, record: logging.LogRecord) -> str:
        # 格式化时间
        # fmt: off
        asctime    = self.formatTime(record, self.datefmt)
        filename   = record.filename
        lineno     = record.lineno
        levelname  = record.levelname
        # module     = record.module
        # funcName   = record.funcName
        # threadName = record.threadName
        # fmt: on
        # 使用字符串格式化直接创建对齐后的日志
        formatted_msg = (
            f"{asctime} | {filename}:{lineno} | {levelname} | {record.getMessage()}"
        )
        return formatted_msg


class CustomRichHandler(RichHandler):
    """自定义 RichHandler，用于格式化日志输出"""

    def __init__(self, config: Dict[str, str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.console = Console()
        self.config = config

    def emit(self, record: logging.LogRecord):
        try:
            # 格式化日志记录
            log_entry = self.format(record)
            # 根据日志级别设置样式
            self.console.print(log_entry, style=self._get_style(record))
        except Exception:
            self.handleError(record)

    def _get_style(self, record: logging.LogRecord) -> str:
        levelname = record.levelname
        return self.config.get(levelname, "green")  # 默认样式为绿色


class LoggerSingleton(object):
    """单例日志类, 允许输出到指定文件"""

    _instance = None
    __logger: Optional[logging.Logger] = None
    __log_root_dir: Optional[str] = None

    def __new__(cls, *args: Any, **kwargs: Dict[Any, Any]):
        if not cls._instance:
            cls._instance = super(LoggerSingleton, cls).__new__(cls)
            cls._init_logger(cls)
        return cls._instance

    def _init_logger(self):
        # 读取配置
        with open('log_config.yaml', 'r', encoding='utf-8') as file:
            self.config: Dict[str : Union[int, str]] = yaml.safe_load(file)

        self.__logger = logging.getLogger("logger")
        self.__log_root_dir = f"logs/{datetime.datetime.today().date()}"

        if not os.path.exists(self.__log_root_dir):
            os.makedirs(self.__log_root_dir)

        # 使用 CustomRichHandler 进行终端输出
        console_handler = CustomRichHandler(
            config=self.config['style'],
            console=Console(),
            rich_tracebacks=True,
            markup=True,  # 启用富文本格式化
        )
        # 添加格式化器
        console_handler.setFormatter(
            CustomFormatter(
                fmt="%(asctime)s | %(filename)s:%(lineno)s | %(levelname)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
                centering=True,
                config=self.config['format'],
            )
        )
        self.__logger.addHandler(console_handler)

        # 文件日志处理, 日志文件达到大小后进行轮转
        file_handler = RotatingFileHandler(
            filename=f'{self.__log_root_dir}/{time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())}.log',
            maxBytes=self.config['rotation'].get(
                'logfile_max_size', 10 * 1024 * 1024
            ),  # 默认为10MB,
            backupCount=self.config['rotation'].get(
                'backup_count', 100
            ),  # 默认最多保留100个副本
            encoding='utf-8',
        )
        file_handler.setFormatter(
            CustomFormatter(
                fmt="%(asctime)s | %(filename)s:%(lineno)s | %(levelname)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
                centering=False,
            )
        )
        self.__logger.addHandler(file_handler)

    @property
    def logger(self) -> logging.Logger:
        return self.__logger


if __name__ == "__main__":
    logger_1 = LoggerSingleton().logger
    logger_1.setLevel("DEBUG")

    logger_1.debug("This is a debug message. 数字效果 12345")
    logger_1.info("This is an info message. 布尔值效果 False True")
    logger_1.warning(
        "This is a warning message. 关键字效果 None, is, import, raise, try, if"
    )
    logger_1.error("This is an error message. 日期效果 2024-04-01")
    logger_1.critical("This is a critical message")

    logger_2 = LoggerSingleton().logger
    print(logger_1 is logger_2)

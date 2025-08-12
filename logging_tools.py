import sys

from loguru import logger

class Logger():
    def __init__(self):
        self.my_logger = logger
        # 清空所有设置
        self.my_logger.remove()
        # 添加控制台输出的格式,sys.stdout为输出到屏幕
        if sys.stdout is not None:
            self.my_logger.add(sys.stdout, level='DEBUG',
                               format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "  # 颜色>时间
                                      "<level>{level}</level>: "  # 等级
                                      "<level>{message}</level>",  # 日志内容
                               )

            # 添加文件输出
            self.my_logger.add("logs.log", level='DEBUG',
                               format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")

    def get_logger(self):
        return self.my_logger

loggers = Logger().get_logger()
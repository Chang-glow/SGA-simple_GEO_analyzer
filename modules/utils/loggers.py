# 日志管理器
import os
import sys
import logging
import inspect
from datetime import datetime


def get_logger(project_name: str = "SGA", log_dir: str = "error_logs"):
    """日志管理总线配置和获取

    Args:
        project_name:项目名称
        log_dir:存储error.log的文件夹名称，默认为log
    """
    # 通过检测调用帧判断是否为主函数
    caller_frame = inspect.stack()[1]  # 通过调用栈截取调用帧
    caller_module = inspect.getmodule(caller_frame[0])  # 提取调用帧中的调用模块

    # 在调用模块中寻找__name__，若无则默认为主函数
    module_name = getattr(caller_module, "__name__", "__main__")

    # 获取脚本名
    script_name = sys.argv[0]  # 脚本名绝对路径
    obj_name = os.path.basename(script_name)  # 相对路径
    pure_name = os.path.splitext(obj_name)[0]  # 去除后缀名
 
    # 判断是否为主函数
    if module_name == "__main__":
        name = pure_name
    else:
        name = f"{project_name}.{pure_name}"
    
    # 如有logger则直接返回
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel("DEBUG")

    # 获取项目根目录路径
    utils_path = os.path.abspath(__file__)
    module_root = os.path.dirname(os.path.dirname(utils_path))
    project_root = os.path.dirname(module_root)
    
    log_dir_path = os.path.join(project_root, log_dir)
    
    # 如不存在log文件夹则创建
    if not os.path.exists(log_dir_path):
        os.makedirs(log_dir_path)

    # 生成含时间戳的文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{timestamp}_{name}_error.log"
    full_path_name = os.path.join(log_dir_path, file_name)

    # 设置格式
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y/%m/%d-%H:%M:%S"
    )

    # 控制台版本
    if "hydra" not in sys.modules:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(fmt="[%(levelname)s] %(message)s")
        console_handler.setFormatter(console_formatter)
        # 将handler放入总线
        logger.addHandler(console_handler)

    # 文件版本
    file_handler = logging.FileHandler(full_path_name, encoding="utf-8", delay=True)
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(formatter)

    # 将handler放入总线
    logger.addHandler(file_handler)

    return logger

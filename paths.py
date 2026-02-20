import os

# 路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
RESULT_DIR = os.path.join(BASE_DIR, "res")
FIGURE_DIR = os.path.join(RESULT_DIR, "figures")
CONFIG_DIR = os.path.join(BASE_DIR, "conf")
LOGGER_DIR = os.path.join(BASE_DIR, "error_logs")


def dirs_init():
    for d in [BASE_DIR, DATA_DIR, RESULT_DIR, RESULT_DIR, CONFIG_DIR, LOGGER_DIR]:
        os.makedirs(d, exist_ok=True)

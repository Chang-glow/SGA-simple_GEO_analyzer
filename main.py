import hydra
import logging
import time

from paths import FIGURE_DIR
from modules.data_loader import DataLoader
from modules.correlation_calculater import DataAnalyzer
from modules.fig_plotter import DataPlotter

from modules.utils import loggers
from modules.utils.config_manager import Config, DataHandler


@hydra.main(version_base=None, config_name="Config")
def main(cfg: Config):
    # 初始化
    logging.getLogger().setLevel(logging.INFO)
    logger = loggers.get_logger()
    logger.info("---欢迎使用本项目---")
    logger.info("初始化中...")
    data = DataHandler()
    logger.info("初始化完成")
    time.sleep(3)

    # 数据获取与清洗
    logger.info("开始获取数据并清洗")
    loader = DataLoader(cfg)
    data.bundle = loader.loader()
    logger.info("数据获取完成")
    time.sleep(3)

    # 相关性计算
    logger.info("开始计算相关性")
    calculater = DataAnalyzer(cfg, data)
    data.res_df = calculater.calculate()
    logger.info("相关性计算完成")

    # 绘图
    logger.info("开始绘图")
    plotter = DataPlotter(cfg, data)
    plotter.plotter()
    logger.info(f"绘图结果保存在{FIGURE_DIR}")


if __name__ == '__main__':
    main()

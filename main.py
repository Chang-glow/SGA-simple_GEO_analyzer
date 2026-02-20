import os

import hydra
import logging
import time

from paths import FIGURE_DIR, dirs_init
from modules.data_loader import DataLoader
from modules.correlation_calculater import DataAnalyzer, FileAnalyzer
from modules.fig_plotter import DataPlotter, FilePlotter

from modules.utils import loggers
from modules.utils.config_manager import Config, DataHandler


@hydra.main(version_base=None, config_name="Config")
def main(cfg: Config):
    # 初始化
    dirs_init()
    logging.getLogger().setLevel(logging.INFO)
    logger = loggers.get_logger()
    logger.info("---欢迎使用本项目---")
    logger.info("初始化中...")
    data = DataHandler()
    data_dir = os.path.join(cfg.data_dir, cfg.gse_id)
    logger.info("初始化完成")
    time.sleep(3)

    # 数据获取与清洗
    bundle_path = os.path.join(data_dir, "pkl", f"{cfg.gse_id}_processed_bundle.pkl")

    # 判断是否存在缓存
    is_bundle = False
    if os.path.exists(bundle_path) and not cfg.debug:
        logger.info(f"发现数据包：{bundle_path}，跳过下载与清洗")
        is_bundle = True
    else:
        logger.info("开始获取数据并清洗")
        loader = DataLoader(cfg)
        data.bundle = loader.loader()
        logger.info("数据获取完成")
    time.sleep(3)

    # 相关性分析
    res_df_path = os.path.join(data_dir, "pkl", f"{cfg.gse_id}_correlation_summary.pkl")

    # 判断是否存在缓存
    is_res_df = False
    if os.path.exists(res_df_path):
        logger.info(f"发现现存分析结果：{res_df_path}，跳过相关性分析")
        is_res_df = True
    else:
        logger.info("开始计算相关性")
        if is_bundle:
            calculater = FileAnalyzer(cfg)
        else:
            calculater = DataAnalyzer(cfg, data)
        data.res_df = calculater.calculate()
        logger.info("相关性分析完成")
    time.sleep(3)

    # 绘图
    logger.info("开始绘图")
    if is_bundle and is_res_df:
        plotter = FilePlotter(cfg)
    elif (is_bundle and not is_res_df) or (is_res_df and not  is_bundle):
        logger.warning("数据缺失，分析可能出错")
        plotter = FilePlotter(cfg)
    else:
        plotter = DataPlotter(cfg, data)
    plotter.plotter()
    logger.info(f"绘图结果保存在{FIGURE_DIR}")


if __name__ == '__main__':
    main()

import os
from abc import ABC, abstractmethod
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from modules.correlation_calculater import fetch_gene_vector
from modules.utils.config_manager import Config, DataHandler
from modules.utils import loggers


class FigurePlotter(ABC):
    """绘图类，用于将基因相关性分析结果汇成含拟合线与误差线的散点图

    Attributes:
        cfg: 基础配置
    """
    _logger = loggers.get_logger()

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self._res_df: Optional[pd.DataFrame] = None
        self._bundle: Optional[dict] = None
        # 内部判断是否画图
        self._plotter = False

    @abstractmethod
    def fig_plotter(self):
        pass

    @abstractmethod
    def _load_data(self):
        pass

    def plotter(self):
        """画图API"""
        if self._plotter:
            pass
        else:
            return self.fig_plotter()

    def _get_vecs(self, df: pd.DataFrame, gene: str) -> tuple[pd.Series, pd.Series]:
        """取得目标基因和对比基因的向量"""
        # 读取配置
        tar_gene = self.cfg.tar_gene

        # 调用外部函数取向量
        x_vec = fetch_gene_vector(df, tar_gene=tar_gene)
        y_vec = fetch_gene_vector(df, tar_gene=gene)
        return x_vec, y_vec

    def figplotter(self):
        """画图pipeline"""
        # 读取配置
        p_thr, signs = self.cfg.p_threshold, self.cfg.signs

        # 构建P值条件
        p_condition = self._res_df["P_value"] < p_thr
        # 构建相关性条件(可多选)
        sign_condition = None
        for sign in signs:
            if sign == "negative":
                cond = self._res_df["R"] < 0
            elif sign == "positive":
                cond = self._res_df["R"] > 0
            else:
                self._logger.warning(f"将忽略未知符号：{sign}")
                continue
            sign_condition = cond if sign_condition is None else (sign_condition | cond)

        # 构建日志描述映射
        sign_map = {'negative': '负相关 (R < 0)', 'positive': '正相关 (R > 0)'}
        if len(signs) == 1:
            sign_desc = sign_map[signs[0]]
        else:
            sign_desc = "或".join([sign_map[s] for s in signs])

        if p_condition is None or sign_condition is None:
            self._logger.error("配置项缺失有效的p值阈值或相关性取向")
            return

        FigurePlotter._logger.info(f"将以\n1,p值阈值为{p_thr}\n2,{sign_desc}相关为条件筛选因子")

        # 加载数据
        self._load_data()

        # 根据符号构建筛选条件
        targets = self._res_df[p_condition & sign_condition]

        FigurePlotter._logger.info("绘图中...")
        for _, row in targets.iterrows():
            matrix_name = row['Matrix']
            gene_name = row['Gene']
            FigurePlotter._logger.debug(f"当前绘图基因 {gene_name}")

            df = self._bundle[matrix_name]
            x_vec, y_vec = self._get_vecs(df, gene_name)

            self._save_corr_plot(x_vec, y_vec, row)

        FigurePlotter._logger.info("绘图完成！")

    def _save_corr_plot(self, x: pd.Series, y: pd.Series, info: pd.DataFrame):
        """画图并存储"""
        # 读取配置
        tar_gene, data_dir = self.cfg.tar_gene, self.cfg.data_dir

        plt.figure(figsize=(6, 6))

        # 画图并自动添加回归线
        sns.regplot(x=x, y=y, ci=95,
                    scatter_kws={'alpha': 0.6, 's': 80, 'color': '#34495e'},
                    line_kws={'color': '#c0392b', 'lw': 2})

        # 标注相关系数和p-value
        matrix_info = os.path.splitext(os.path.splitext(info['Matrix'])[0])[0]
        gene_info = info['Gene']
        title_str = f"{matrix_info}\n{tar_gene} vs {gene_info}\nR={info['R']:.3f}, P={info['P_value']:.4e}"
        plt.title(title_str, fontsize=10)
        plt.xlabel(f"{tar_gene} Expression")
        plt.ylabel(f"{gene_info} Expression")

        # 保存路径
        fig_dir = os.path.join(os.path.dirname(data_dir), "res", "figures")
        if not os.path.exists(fig_dir):
            os.makedirs(fig_dir)
        fig_path = os.path.join(fig_dir, f"{matrix_info}_{gene_info}.png")
        plt.savefig(fig_path, dpi=300, bbox_inches='tight')
        plt.close()


class DataPlotter(FigurePlotter):
    """直接从内存中调用数据画图"""
    def __init__(self, cfg: Config, data: DataHandler):
        """初始化

        Args:
            cfg: 基础配置
            data: 数据传递类，包括相关性分析DataFrame和筛选后的原始基因DataFrame数据
        """
        super().__init__(cfg)
        self.res_df: pd.DataFrame = data.res_df
        self.bundle: dict = data.bundle

    def fig_plotter(self):
        """筛选所需目标并画图"""
        # 读取索引和数据仓库
        FilePlotter._logger.info("读取索引和数据中...")
        if not self._res_df and not self._bundle:
            self._load_data()
        FigurePlotter._logger.info("索引和数据读取成功！")
        self.figplotter()

    def _load_data(self):
        if self.res_df is not None and not self.res_df.empty:
            self._res_df = self.res_df
        if self.bundle:
            self._bundle = self.bundle


class FilePlotter(FigurePlotter):
    """通过读取文件数据画图"""
    def __init__(self, cfg: Config):
        super().__init__(cfg)

    def fig_plotter(self):
        """筛选所需目标并画图"""
        FilePlotter._logger.info("从pkl中读取索引和数据中...")
        if not self._res_df or not self._bundle:
            self._load_data()
        FigurePlotter._logger.info("索引和数据读取成功！")
        self.figplotter()

    def _load_data(self):
        """从文件中加载数据"""
        # 读取配置
        data_dir, gse_id = self.cfg.data_dir, self.cfg.gse_id

        # 执行加载
        res_df_path = os.path.join(data_dir, "pkl", f"{gse_id}_correlation_summary.pkl")
        bundle_path = os.path.join(data_dir, "pkl", f"{gse_id}_processed_bundle.pkl")
        self._res_df = pd.read_pickle(res_df_path)
        self._bundle = pd.read_pickle(bundle_path)


if __name__ == "__main__":
    test_gse_id = "GSE300437"
    test_tar_gene = "Polb"
    test_cfg = Config(tar_gene=test_tar_gene, gse_id=test_gse_id)
    test_plotter = FilePlotter(test_cfg)
    if test_plotter.plotter:
        print("Done!")

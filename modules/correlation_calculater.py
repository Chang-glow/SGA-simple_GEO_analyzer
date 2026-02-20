import os
import scipy

import pandas as pd

from abc import ABC, abstractmethod
from typing import Optional

from modules.utils import loggers
from modules.utils.config_manager import Config, DataHandler


def fetch_gene_vector(df, tar_gene) -> pd.Series:
    """提取目标基因向量

    Args:
        df: 被提取的数据库DataFrame
        tar_gene: 提取的目标基因

    Returns:
        vector: 目标基因所属列转换的向量
    """
    logger = loggers.get_logger()

    if not isinstance(df, pd.DataFrame):
        logger.error(f"传入的df不是DataFrame，实际类型: {type(df)}，值: {df}")
        return pd.Series(dtype=float)

    target_gene_upper = str(tar_gene).upper()
    vector = None

    # 1. 尝试从索引查找
    index_upper = df.index.astype(str).str.upper()
    if target_gene_upper in index_upper.values:
        # 找到所有匹配的行（处理重复索引）
        vector = df.loc[df.index[index_upper == target_gene_upper]]

    # 2. 如果索引没找到，尝试从列查找
    else:
        potential_columns = [col for col in df.columns if 'SYMBOL' in col.upper() or 'GENE' in col.upper()]
        for col in potential_columns:
            col_values_upper = df[col].astype(str).str.upper()
            if target_gene_upper in col_values_upper.values:
                # 提取匹配的所有行
                vector = df[col_values_upper == target_gene_upper]
                break  # 找到了就跳出列循环

    # 3. 后处理：清洗聚合
    if vector is not None:
        # 只保留数值列，剔除掉注释列
        vector = vector.select_dtypes(include=['number'])

        # 处理多行情况
        if isinstance(vector, pd.DataFrame):
            if vector.empty:
                logger.warning(f"基因 {tar_gene} 匹配行为空或无数值数据")
                return pd.Series(dtype=float)
            vector = vector.mean(axis=0)

        return vector

    logger.warning(f"未能在矩阵中找到基因: {tar_gene}")
    return pd.Series(dtype=float)


class Analyzer(ABC):
    """分析从GEO下载的测序数据，父类，只实现分析函数，不实现存取

    Attributes:
        hfm_dict: 肝纤维化常见标志物字典，全称hepatic_fibrosis_marker_dict
        cfg: 基础配置
    """
    hfm_dict = {
        "Classic": ["Acta2", "Vim", "Col1a1", "Col3a1"],
        "Inflammation": ["Il6", "Tnfa", "Il4", "Il1b"],
        "Signaling_Advanced": ["Tem1", "Arrb1", "Gas6", "Axl", "Pdgfb"],
        "Apoptosis": ["Fas", "Fasl", "Bcl2", "Trp53"],
        "Hedgehog": ["Ptch1", "Smo"]
    }
    _logger = loggers.get_logger()

    def __init__(self, cfg: Config):
        """初始化分析对象

        Args:
            cfg: 基础配置
        """
        self.cfg = cfg
        self._bundle: Optional[dict] = None
        self._ana_res: Optional[pd.DataFrame] = None

    @staticmethod
    def scipy_analyze(vec1: pd.Series, vec2: pd.Series) -> tuple[Optional[float], Optional[float]]:
        """分析r、p值

        Args:
            vec1: 用于计算相关性的向量1，为目标基因数据向量
            vec2: 用于计算相关性的向量2，为标识物数据向量

        Returns:
            r: 两基因的相关性
            p: 两基因的相关性p-value
        """
        # 保证顺序性
        v1, v2 = vec1.align(vec2, join='inner')

        # 剔除缺失值
        mask = v1.notna() & v2.notna()
        v1, v2 = v1[mask].astype(float), v2[mask].astype(float)

        # 保证长度相同且大于3
        if len(v1) < 3 or v1.std() == 0 or v2.std() == 0:
            return None, None

        r, p = scipy.stats.pearsonr(v1, v2)
        return r, p

    def get_data(self) -> dict:
        """缓存读取数据

        Returns:
            self._bundle: 读取到的{文件名：矩阵}字典，存为属性
        """
        if self._bundle is None:
            self._bundle = self._load_data()
        return self._bundle

    @property
    def significant(self):
        """最显著值"""
        significant_findings = self.calculate()[self.calculate()['P_value'] < 0.05].sort_values('R')
        return significant_findings

    def calculate(self) -> pd.DataFrame:
        """用于调用数据的API"""
        if self._ana_res is not None and not self._ana_res.empty:
            return self._ana_res
        try:
            return self.data_analyzer()
        except Exception:
            self._logger.exception("分析失败")
            raise

    def _calculater(self, bundle: dict) -> Optional[pd.DataFrame]:
        """分析主pipeline

        Args:
            bundle: 打包的测序矩阵数据，格式为{文件名: 对应矩阵数据}

        Returns:
            result_df: DataFrame格式的分析结果
        """
        # 读取配置
        tar_gene = self.cfg.tar_gene

        # 提取bundle里的数据计算
        results_list = []
        df: pd.DataFrame
        for name, df in bundle.items():
            # 避开元数据矩阵
            if name == "meta":
                continue

            Analyzer._logger.info(f"--- 当前处理数据{name} ---")
            Analyzer._logger.info(f"提取目标基因{tar_gene}的数据中...")
            target_vec = fetch_gene_vector(df, tar_gene)

            Analyzer._logger.info("将以常见标识物分类进行计算并储存")
            for category, gene_list in self.hfm_dict.items():
                for gene in gene_list:
                    Analyzer._logger.debug(f"提取标识物基因{gene}的数据中...")
                    marker_vec = fetch_gene_vector(df, gene)

                    r, p = None, None
                    if not marker_vec.empty:
                        Analyzer._logger.debug("数据提取完成，计算相关性中...")
                        r, p = self.scipy_analyze(target_vec, marker_vec)

                    if r is not None:
                        Analyzer._logger.debug("相关性计算完成！")
                        results_list.append({
                            "Matrix": name,
                            "Category": category,
                            "Gene": gene,
                            "R": r,
                            "P_value": p
                        })

        # 转化为DataFrame，以便画图
        if results_list:
            Analyzer._logger.info("相关性计算完成！")
            result_df = pd.DataFrame(results_list)
        else:
            return None

        return result_df

    def _data_storage(self, result_df: pd.DataFrame, save_format: str):
        """存储DataFrame数据至pkl和csv"""
        # 读取配置
        data_dir = os.path.join(self.cfg.data_dir, self.cfg.gse_id)
        gse_id = self.cfg.gse_id

        # 映射文件格式向格式名与后缀名
        if save_format == "pkl":
            fmt = "pickle"
            ext = "pkl"
        elif save_format == "csv":
            fmt = ext = "csv"
        else:
            raise ValueError(f"不支持的格式:{save_format}")

        file_name = f"{gse_id}_correlation_summary.{ext}"

        storage_path = os.path.join(data_dir, ext, file_name)
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)

        save_mode = getattr(result_df, f"to_{fmt}")

        try:
            if fmt == "csv":
                save_mode(storage_path, index=False)
            else:
                save_mode(storage_path)
            self._logger.info(f"{fmt}文件已保存至{storage_path}")
        except PermissionError as e:
            self._logger.error(f"无法写入{fmt}，错误：{e}")
        except OSError as e:
            self._logger.error(f"系统错误：{e}")
        except Exception as e:
            self._logger.error(f"存储{fmt}时发生未知错误：{e}")

    @abstractmethod
    def _load_data(self) -> dict:
        pass

    @abstractmethod
    def data_analyzer(self) -> pd.DataFrame:
        pass


class DataAnalyzer(Analyzer):
    """基于直接读取DataFrame数据的分析流程"""
    def __init__(self, cfg: Config, data: DataHandler):
        super().__init__(cfg)
        self.bundle = data.bundle

    def _load_data(self) -> dict:
        return self.bundle

    def data_analyzer(self) -> Optional[pd.DataFrame]:
        """调用分析主pipeline，串联数据读取和分析得出相关性

        Returns:
            res_df: 目标基因和常见标识基因相关性分析结果及数据
        """
        # 读取配置
        storage = self.cfg.storage

        DataAnalyzer._logger.info("从打包的bundle中读取数据中...")
        bundle = self._load_data()
        if bundle:
            DataAnalyzer._logger.info("读取成功，将继续分析")

        result_df = self._calculater(bundle)
        if result_df is not None and not result_df.empty:
            self._ana_res = result_df
            if storage:
                self._data_storage(result_df, "pkl")
                self._data_storage(result_df, "csv")
            return result_df
        else:
            DataAnalyzer._logger.error("结果矩阵为空")
            raise


class FileAnalyzer(Analyzer):
    """基于读取pkl文件的数据分析流程"""
    def __init__(self, cfg: Config):
        super().__init__(cfg)
        data_dir = os.path.join(self.cfg.data_dir, self.cfg.gse_id)
        self.data_path = os.path.join(data_dir, "pkl", f"{self.cfg.gse_id}_processed_bundle.pkl")

    def read_pkl(self) -> dict:
        """读取pkl文件

        Returns:
            data_dict: 从pkl文件中提取的bundle
        """
        try:
            if not isinstance(self.data_path, str):
                raise TypeError("请输入正确的路径")
            whole_path = self.data_path

            if not os.path.exists(whole_path):
                raise FileNotFoundError(f"当前查找路径：{whole_path},该路径未找到文件")

            # 读取pkl中字典
            data_dict = pd.read_pickle(whole_path)

            if not isinstance(data_dict, dict):
                raise TypeError("读取到的结果并非字典")
            if not data_dict:
                raise ValueError("文件为空，未查询到有效数据")
            return data_dict

        except TypeError as e:
            DataAnalyzer._logger.error(f"【类型错误】：{e}")
            raise
        except FileNotFoundError as e:
            FileAnalyzer._logger.error(f"【路径错误】：{e}")
        except ValueError as e:
            FileAnalyzer._logger.warning(f"【数据错误】：{e}")
        except Exception as e:
            FileAnalyzer._logger.error(f"【未知错误】：{e}")

    def _load_data(self) -> dict:
        if not self._bundle:
            self._bundle = self.read_pkl()
        return self._bundle

    def data_analyzer(self) -> Optional[pd.DataFrame]:
        """调用分析主pipeline，串联数据读取和分析得出相关性

        Returns:
            res_df: 目标基因和常见标识基因相关性分析结果及数据
        """
        # 读取配置
        storage = self.cfg.storage

        FileAnalyzer._logger.info("从打包的pkl中读取数据中...")
        bundle = self._load_data()
        if bundle:
            FileAnalyzer._logger.info("读取成功，将继续分析")

        result_df = self._calculater(bundle)
        if result_df is not None and not result_df.empty:
            self._ana_res = result_df
            if storage:
                self._data_storage(result_df, "pkl")
                self._data_storage(result_df, "csv")
            return result_df
        else:
            DataAnalyzer._logger.error("结果矩阵为空")
            raise


if __name__ == "__main__":
    test_gse_id = "GSE300437"
    test_tar_gene = "Polb"
    test_cfg = Config(tar_gene=test_tar_gene, gse_id=test_gse_id)
    test_analyzer = FileAnalyzer(test_cfg)
    test_res_df = test_analyzer.calculate
    print(test_analyzer.significant)

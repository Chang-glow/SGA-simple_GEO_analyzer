import os
import re
import requests
import GEOparse
from typing import Optional, Dict

import pandas as pd

from modules.utils import loggers
from modules.utils.config_manager import Config
from modules.utils.parse_interpreter import parse_interpreter


class DataLoader:
    """从GEO下载数据并储存"""
    _logger = loggers.get_logger()

    def __init__(self, cfg: Config):
        """初始化数据获取对象

        Args:
            cfg: 基本配置项
        """
        self.cfg: Config = cfg
        self._data: Optional[Dict[str, pd.DataFrame]] = None
        self._chosen_meta = None
        self._download_data = None

    @staticmethod
    def get_path(data_dirs: str, prompt: str, debug: bool = False) -> str:
        """获取本地文件位置
        (其实这玩意目前没什么用也不想动他了但是函数本身好像又有点聊胜于无的作用所以就放在这吧(瘫))

        Args：
            prompt: 输入提示，用于指示想获得的路径
            debug: 测试用
        """
        while True:
            # 通过错误抛出循环ask for文件路径
            try:
                if not debug:
                    data_path = input(prompt)
                else:
                    data_path = prompt  # 测试时硬编码路径，并通过传参给prompt直接读，写完记得删
                whole_path = os.path.join(data_dirs, data_path)
                if not data_path:
                    raise ValueError("输入不能为空")
                if not os.path.exists(whole_path):
                    raise FileNotFoundError(f"未找到文件，请检查文件路径：{whole_path}")
                if not os.path.isfile(whole_path):
                    raise IsADirectoryError(f"该路径不是文件，可能是文件夹，请检查文件路径：{whole_path}")

                DataLoader._logger.info(f"找到文件{data_path}，准备开始读取")
                return whole_path

            except ValueError as e:
                DataLoader._logger.error(f"【输入错误】：{e}")
            except (FileNotFoundError or IsADirectoryError) as e:
                DataLoader._logger.error(f"【路径错误】：{e}")
            except Exception as e:
                DataLoader._logger.exception(f"【未知错误】:{e}")

    def loader(self) -> dict:
        """
        用于调用数据的API

        Returns:
            self._data: 存储的字典数据

        Raises:
            RuntimeError: 数据不存在时抛出错误
        """
        if not self._data:
            gse = self._get_gse()
            self._user_selection_flow(gse)
            data = self._build_bundle()
            if not data:
                raise RuntimeError("数据未下载创建")
            if data:
                return data
        else:
            return self._data

    def download_geo_data(self, url: str) -> Optional[str]:
        """从GEO下载所需数据

        Args:
            url: 下载链接

        Returns:
            local_path: 下载文件所在位置

        Raises:
            Exception: 下载错误时抛出
        """
        # 确定本地位置
        data_dir = os.path.join(self.cfg.data_dir, self.cfg.gse_id)
        file_name = os.path.basename(url)
        local_path = os.path.join(data_dir, file_name)

        # 检验是否存在文件
        if os.path.exists(local_path):
            DataLoader._logger.info(f"文件{file_name} 已存在，跳过下载。")
            return local_path

        # 转换请求头
        if url.startswith("ftp://"):
            url = url.replace("ftp://", "https://", 1)

        # 下载逻辑
        DataLoader._logger.info(f"正在从NCBI下载{file_name}...")
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            DataLoader._logger.info(f"{local_path}下载完成")
            return local_path
        except Exception as e:
            DataLoader._logger.error(f"下载失败: {e}")
            if os.path.exists(local_path):
                os.remove(local_path)
            return None

    def _get_gse(self) -> GEOparse.GEOTypes.GSE:
        """获取GEO数据包

        Returns:
            gse: 下载的数据包

        Raises:
            TypeError: 输入非字符串时抛出错误
            ValueError: GSE ID不合规时抛出
            FileNotFoundError: 未发现所需补充文件时抛出
            Exception: 其他错误时抛出
        """
        # 读取配置项
        data_dir = os.path.join(self.cfg.data_dir, self.cfg.gse_id)
        gse_id = self.cfg.gse_id

        dest_dir = os.path.normpath(data_dir)

        try:
            # 输入合法性监测
            is_str = isinstance(self.cfg.gse_id, str) and isinstance(dest_dir, str)
            if not is_str:
                raise TypeError("请输入字符串而非其他类型参数")

            is_gse = re.match(r'^GSE\d+$', gse_id)
            if not is_gse:
                raise ValueError("请输入正确的GSE ID！")

            # 下载所需GSE数据库
            DataLoader._logger.info(f"开始下载或调用现存{gse_id}_family.soft.gz")
            DataLoader._logger.info("正在检索远程服务器或本地缓存...")
            gse = GEOparse.get_GEO(geo=gse_id, destdir=dest_dir)

            if not gse:
                raise Exception("出现未知错误，请检查\n1、GSE编号是否正确\n2、下载地址是否正确/有权限写入")

            return gse

        except ValueError as e:
            DataLoader._logger.error(f"【输入错误】:{e}")

        except TypeError as e:
            DataLoader._logger.error(f"【类型错误】:{e}")

        except Exception as e:
            DataLoader._logger.error(f"【未知错误】:{e}")

    def _user_selection_flow(self, gse) -> None:
        """用户交互下载数据

        Args:
            gse: 下载的GES对象
        """
        try:
            # 从gse中读取补充文件列表
            sp_files = gse.metadata.get('supplementary_file', [])
            if not sp_files:
                DataLoader._logger.warning("未发现补充文件")
                raise FileNotFoundError("未发现补充文件")

            # 简单筛选去除明显不是目标文件内容
            candidates = [f for f in sp_files if (
                '.matrix' in f.lower()
                or '.count' in f.lower()
                or '.txt' in f.lower()
            ) and 'readme' not in f.lower()]

            # 手动确认需要的文件
            print("\n--- 发现以下疑似矩阵文件 ---")
            for i, url in enumerate(candidates):
                print(f"[{i}] {os.path.basename(url)}")

            selected_idx = parse_interpreter(prompt="请输入需要的矩阵序号(如1:8,11):", max_length=len(candidates))
            selected_urls = [candidates[i] for i in selected_idx]

            # 下载选中的文件
            downloaded_data = {}
            for url in selected_urls:
                file_path = self.download_geo_data(url)

                # 只有当路径不为None时才存入字典，防止后面read_csv报错
                if file_path:
                    downloaded_data[os.path.basename(url)] = file_path
                else:
                    DataLoader._logger.warning(f"文件 {os.path.basename(url)} 下载失败，将不会被加载。")

            if not downloaded_data:
                raise Exception("出现未知错误，请检查\n1、GSE编号是否正确\n2、下载地址是否正确/有权限写入")

            self._download_data = downloaded_data

            # 提取meta
            meta = gse.phenotype_data
            if not meta.empty:
                DataLoader._logger.info(f"元数据提取成功，样本数{len(meta)}")

            # 手动选择meta中的需要的title
            self._group_select(meta)

        except FileNotFoundError as e:
            DataLoader._logger.error(f"【文件未找到】:{e}")
        except Exception as e:
            DataLoader._logger.error(f"【未知错误】:{e}")

    def _group_select(self, meta) -> None:
        """从元数据中选择所需内容的双层状态机

        Args:
            meta: 元数据
        """
        # 默认尝试“title”
        current_col = "title" if "title" in meta.columns else meta.columns[0]
        # 选列选组状态机
        while True:  # 外层循环选矩阵
            unique_groups = meta[current_col].unique()
            print(f"\n--- 当前查看列:[{current_col}]发现以下样本分组描述 ---")
            for i, group_name in enumerate(unique_groups):
                print(f"[{i}] {group_name}")

            # 故技重施
            selected_group_indices = parse_interpreter(
                prompt="请输入需要的矩阵序号(如1:8,11，输入‘m’重新选择列):",
                max_length=len(unique_groups),
                whitelist="m"
            )

            # 若列中没有矩阵信息则重新选列
            if selected_group_indices == "m":
                print("\n--- 所有元数据列 ---")
                for i, col in enumerate(meta.columns):  # 内层循环选列
                    print(f"[{i}] {col}")
                selected_col = parse_interpreter(
                    prompt="请选择(可能)包含分组信息的列序号:",
                    max_length=len(meta.columns)
                )
                # 更新当前列回到上级循环
                current_col = meta.columns[selected_col[0]]
                continue

            # 若正常选中矩阵序号则过滤meta
            if isinstance(selected_group_indices, list):
                target_groups = [unique_groups[i] for i in selected_group_indices]
                condition = meta[current_col].isin(target_groups)
                self._chosen_meta = meta[condition]
                return

    def _build_bundle(self) -> Optional[dict]:
        """打包处理过的数据

        Returns:
            bundle: 打包过的数据，键为矩阵名，值为矩阵
        """
        # 读取配置
        data_dir = self.cfg.data_dir
        gse_id = self.cfg.gse_id
        tar_gene = self.cfg.tar_gene

        strict_mode = self.cfg.strict_mode
        storage = self.cfg.storage
        debug = self.cfg.debug

        chosen_meta = self._chosen_meta
        downloaded_data = self._download_data

        try:
            # 将data加载到df，并处理
            bundle = {"meta": chosen_meta}
            for datafile_name, file_path in downloaded_data.items():
                DataLoader._logger.info(f"正在将 {datafile_name} 加载至 DataFrame...")

                # 防止个别文件出错
                if not file_path:
                    DataLoader._logger.warning(f"文件 {datafile_name} 的路径为空，跳过处理。")
                    continue

                if not os.path.exists(file_path):
                    DataLoader._logger.warning(f"找不到本地文件: {file_path}")
                    continue

                df_temp = pd.read_csv(file_path, sep="\t", compression="gzip", index_col=0)

                bundle[datafile_name] = df_temp

                if strict_mode:
                    # 和meta取交集
                    common_samples = chosen_meta.index.intersection(df_temp.columns)
                    matrix_aligned = df_temp[common_samples]
                    meta_aligned = chosen_meta.loc[common_samples]

                    bundle[datafile_name] = {
                        "matrix_aligned": matrix_aligned,
                        "meta_aligned": meta_aligned
                    }

                # 测试有没有所需所需基因数据
                if debug:
                    try:
                        tar_data = pd.DataFrame()
                        if 'SYMBOL' in df_temp.columns:
                            tar_data = df_temp[df_temp['SYMBOL'] == tar_gene]
                            if not tar_data.empty:
                                print(f"在SYMBOL列中定位到{tar_gene}!")
                            else:
                                # 试试大小写不敏感匹配
                                tar_data = df_temp[df_temp['SYMBOL'].str.lower() == tar_gene.lower()]
                                if not tar_data.empty:
                                    print(f"在SYMBOL列中定位到{tar_gene}(大小写模糊匹配)!")

                        if not tar_data.empty:
                            print(f"--- {tar_gene}数据概览 ---")
                            print(tar_data)
                        else:
                            print(f"矩阵中存在SYMBOL列，但未找到名为'{tar_gene}'的行。")
                    except Exception as e:
                        print(f"Debug 过程中出现错误: {e}")

            if not bundle:
                raise Exception("没有获取到任何有效矩阵")

            if storage:
                # 存储为pickle文件
                save_path = os.path.join(data_dir, "pkl", f"{gse_id}_processed_bundle.pkl")
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                pd.to_pickle(bundle, save_path)

                if os.path.exists(save_path):
                    DataLoader._logger.info(f"{gse_id}_processed_bundle.pkl已存储完成！")

            self._data = bundle
            return bundle

        except Exception as e:
            DataLoader._logger.error(f"【未知错误】:{e}")


if __name__ == "__main__":
    test_gse_id = "GSE300437"
    test_tar_gene = "Polb"
    test_cfg = Config(tar_gene=test_tar_gene, gse_id=test_gse_id)
    loader = DataLoader(test_cfg)
    data_bundle = loader.loader()

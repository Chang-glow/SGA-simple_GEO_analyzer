import os
from utils import loggers


logger = loggers.get_logger()


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

            logger.info(f"找到文件{data_path}，准备开始读取")
            return whole_path

        except ValueError as e:
            logger.error(f"【输入错误】：{e}")
        except (FileNotFoundError or IsADirectoryError) as e:
            logger.error(f"【路径错误】：{e}")
        except Exception as e:
            logger.exception(f"【未知错误】:{e}")

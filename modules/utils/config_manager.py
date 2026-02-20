import os.path

import pandas as pd
from dataclasses import dataclass, field
from typing import Optional, List, cast
from hydra.core.config_store import ConfigStore

from paths import DATA_DIR


@dataclass
class Config:
    tar_gene: str
    gse_id: str
    data_dir: str = DATA_DIR
    storage: bool = True
    strict_mode: bool = False
    debug: bool = False
    p_threshold: float = 0.05
    signs: List[str] = field(default_factory=lambda: ["positive", "negative"])


@dataclass
class DataHandler:
    bundle: Optional[dict] = None
    res_df: Optional[pd.DataFrame] = None


cs = ConfigStore.instance()
cs.store(name="Config", node=Config)

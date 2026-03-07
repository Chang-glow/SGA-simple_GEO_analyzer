# **SGA: Simple GEO Analyzer (v1.1)**

**SGA** 是一个为生信初学者和课题组日常科研设计的轻量级、自动化 GEO 数据处理工具。它将复杂的 GEO 数据获取、清洗与相关性分析过程封装为简洁的命令行操作，实现了从原始数据到可视化结果的全流程闭环。

本项目是本人在生物科学本科学习期间，为解决课题组（Polb 相关课题）重复性劳动而开发的工具，特别针对肝纤维化相关的转录组分析进行了优化。

---

## **🌟 核心特性**

- **⚙️ 自动流水线**：只需提供 GSE ID，自动检索并下载 `.soft.gz` 家族文件及补充分类矩阵。  
- **🔄 断点续传**：自动探测本地 pkl 数据包及分析结果，支持“秒级”二次启动。  
- **📊 数据处理**：内置针对多矩阵数据集（如 *in vitro* / *in vivo* / 组织分类）的自动解析与对齐逻辑。  
- **📈 可视化**：自动生成相关性散点图（Seaborn 驱动，带拟合线与置信区间）。  
- **🔧 解耦配置**：基于 Hydra 框架，无需深入源码，通过修改 YAML 即可快速切换目标基因与参数。

---

## **📂 项目架构**

```
SGA/
├── main.py                      # 项目入口，调度数据获取、分析与绘图全流程
├── conf/                        # Hydra 配置文件存放
│   └── config.yaml.template     # 默认配置文件模板（含 tar_gene、gse_id 等参数）
├── modules/                      # 核心功能模块
│   ├── __init__.py
│   ├── data_loader.py            # GEO 数据下载、解析、样本筛选与清洗
│   ├── correlation_calculater.py # 相关性计算逻辑（Pearson 相关系数）
│   └── fig_plotter.py            # 自动化绘图模块（基于 Seaborn）
├── utils/                         # 工具模块
│   ├── __init__.py
│   ├── config_manager.py          # 基于 Hydra 的配置映射与数据传递对象
│   ├── loggers.py                 # 自定义日志总线，支持控制台输出与文件记录
│   ├── parse_user_input.py        # 用户交互输入解析（如下载矩阵选择、分组筛选）
│   └── paths.py                   # 路径管理，自动初始化项目所需文件夹
├── data/                          # 存放下载的原始数据及清洗后的 pkl 缓存（自动生成）
├── error_logs/                     # 存放运行过程中的错误日志（含时间戳，自动生成）
├── res/                            # 结果输出目录（自动生成）
│   └── figures/                    # 生成的回归分析散点图
├── .gitignore
├── LICENSE
├── README.md
├── environment.yml                 # Conda 环境配置
└── requirements.txt                # Pip 依赖清单
```

---

## **🚀 快速上手**

### **1. 环境准备**

```bash
# 克隆仓库
git clone https://github.com/YourUsername/SGA.git
cd SGA

# 使用 Conda 部署环境（推荐）
conda env create -f environment.yml
conda activate sga

# 或使用 pip 安装依赖
pip install -r requirements.txt
```

### **2. 执行分析**

```bash
# 运行前请修改 conf/config.yaml 中的 tar_gene 和 gse_id 参数
# 默认配置为 tar_gene: "GENE", gse_id: "GSE123456"，需替换为目标基因和数据集编号

# 启动分析
python main.py

# 也可在命令行覆盖配置（Hydra 语法）
python main.py tar_gene="Acta2" gse_id="GSE123456"
```

### **3. 查看输出**

- **清洗后的数据包**：`data/{GSE_ID}/pkl/`（含 `*_processed_pack.pkl`）  
- **相关性统计表格**：`data/{GSE_ID}/csv/`（含 `*_correlation_summary.csv`）  
- **可视化结果**：`res/figures/`（每个符合条件的基因对生成一张散点图）

---

## **📝 待办事项**

### ✨ 功能增强
- [ ] **多基因热图 (Multi-gene Heatmap)**：增加对多个标识物基因相关性矩阵的全局热图展示，支持层次聚类。

### 📊 数据与拓展
- [ ] **动态标识物库**：结合本地数据库与在线 API 调用（如 NCBI Entrez），实现标识物动态获取，不再局限于肝纤维化硬编码。
- [ ] **多数据源解析**：不局限于 GEO，支持更多公共数据平台（如 ArrayExpress、TCGA）或用户本地数据上传。
- [ ] **多分析模式**：不局限于基因的皮尔逊相关，扩展至其他统计方法（如斯皮尔曼相关、差异表达分析、聚类分析等）。

---

## **🤝 贡献与反馈**

如果你在处理特定 GEO 数据集时遇到报错，欢迎提交 Issue。非常欢迎任何关于分析逻辑的改进建议！

*📅 Update at: 2026-03-08*
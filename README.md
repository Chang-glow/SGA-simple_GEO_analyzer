# **SGA: Simple GEO Analyzer (v1.0)**

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
SGA-simple_GEO_analyzer/
├── main.py                 # 项目入口，调度数据获取、分析与绘图全流程
├── paths.py                # 路径管理，自动初始化项目所需文件夹
├── data/                   # 存放下载的原始数据及清洗后的 pkl 缓存
├── error_logs/             # 存放运行过程中的错误日志（含时间戳）
├── res/                    # 结果输出目录
│   └── figures/            # 生成的回归分析散点图
├── conf/                   # Hydra 配置文件存放
└── modules/                # 核心功能模块
    ├── data_loader.py      # GEO数据下载、解析、样本筛选与清洗
    ├── correlation_calculater.py # 相关性计算逻辑（Pearson 相关系数）
    ├── fig_plotter.py      # 自动化绘图模块（基于 Seaborn）
    └── utils/
        ├── loggers.py      # 自定义日志总线，支持控制台彩色输出与文件记录
        └── config_manager.py # 基于 Hydra 的配置映射与数据传递对象
```

---

## **🚀 快速上手**

### **1. 环境准备**

```bash
# 克隆仓库
git clone https://github.com/YourUsername/SGA-simple_GEO_analyzer.git
cd SGA-simple_GEO_analyzer

# 使用 Conda 部署环境
conda env create -f environment.yml
conda activate sga
```

### **2. 执行分析**

```bash
# 运行默认分析 (Polb vs GSE300437)
python main.py

# 指定其他基因或数据集
python main.py tar_gene="Acta2" gse_id="GSE123456"
```

### **3. 查看输出**

- **清洗后的数据**：`data/{GSE_ID}/pkl/`
- **统计表格 (CSV)**：`data/{GSE_ID}/csv/`
- **可视化结果**：`res/figures/`

---

## **📝 待办事项**

### ✨ 功能增强
- [ ] **多基因热图 (Multi-gene Heatmap)**：增加对多个标识物基因相关性矩阵的全局热图展示，支持层次聚类。
- [ ] **自动归一化检测**：引入分布判定算法，自动识别原始计数矩阵是否需要进行 $\log_2 x$ 转换。

### 🏗️ 架构优化
- [ ] **解耦下载与清洗逻辑**：将 DataLoader 拆分为独立子模块，增加“严格比对”自动判定机制，确保元数据与矩阵列名完美匹配。

### 📊 数据与拓展
- [ ] **动态标识物库**：结合本地数据库与在线 API 调用（如 NCBI Entrez），实现标识物动态获取，不再局限于肝纤维化硬编码。

### 🌐 国际化 (i18n)
- [ ] 支持中/英双语日志输出与分析报告生成，提升工具在国际学术社区的可移植性。

---

## **🤝 贡献与反馈**

如果你在处理特定 GEO 数据集时遇到报错，欢迎提交 Issue。非常欢迎任何关于分析逻辑的改进建议！

*📅 Update at: 2026-02-20*
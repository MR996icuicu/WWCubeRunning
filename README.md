# 鸣潮团子快跑竞猜比赛模拟器

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)  
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/downloads/)

## 📜 许可证  
本项目采用 **Apache License 2.0**，请遵守以下条款：  
- **必须保留**原始版权声明和许可证文件  
- **修改代码**需在文件中明确标注变更内容  
- **不得使用项目名称**进行商业背书  

完整条款见 [LICENSE](LICENSE) 文件。

一个模拟鸣潮团子竞速比赛的Python程序，用于分析押注策略和胜率预测。

## 功能特性

- 🎲 完整模拟比赛流程（骰子移动、堆叠机制、终点判定）
- 🏆 6种独特选手技能实现(支持自定义扩展)
- 📊 支持批量模拟与胜率统计
- ⚙️ 可配置赛道长度、技能参数等

## 快速开始

### 安装依赖
```bash
pip install -r requirements.txt  # 本项目仅需Python标准库

## 目录结构
.
├── LICENSE
├── README.md
├── requirements.txt
├── board.py        # 赛道与位置管理
├── main.py         # 主程序
├── ops.py          # 常规操作方法
├── player.py       # 选手定义
├── simulator.py    # 比赛流程控制
└── sill.py         # 技能系统于技能注册工厂
```


## ✨ 原创性声明  
本项目由 **[996icuicu/Institute of Automation，Chinese Academy of Sciences]** 原创开发，任何公开使用需：  
1. 在文档或界面中显著标注原作者  
2. 衍生作品需保留本声明和修改记录  

## 🤝 贡献指南  
提交PR前请：  
1. 签署开发者原创性声明（[DCO](https://developercertificate.org/)）  
2. 在此仓库中提`pull request`, 在活动期间作者会定时查看
3. 任何问题和bug请提`issue`
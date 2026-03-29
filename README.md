# EXTranslator

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-success.svg?style=for-the-badge)

一个集剧本文件提取、LLM自动化翻译、原文本替换导出于一身的 Python 本地化工程包。
> **Note:** 目前专为吉里吉里（KiriKiri）引擎的 `.ks` 脚本设计，并在《Fate/hollow ataraxia》汉化中通过了测试。

---

## ✨ Features

* **🎯 标签保护：** 使用 `<T*>` 占位符替换行内标签，有效保护原剧本中的底层逻辑标签与排版宏。
* **🚀 并发多线程：** 使用线程池，支持自定义并发数与批处理大小，实测并行200无报错。
* **🛡️ 相对路径：** 进度文件采用相对路径锚定，随时随地移动工程文件夹，翻译进度不丢失。
* **💾 断点续传：** 引入线程锁与 UUID 临时文件替换机制，就算非正常退出程序或闪退，也能保证进度文件不损坏。
* **🧠 自定义LLM：** 支持自定义系统提示词。

---

## 📁 Structure

```text
EXTranslator/
├── main.py             # 主程序入口 (交互式 UI)
├── config.py           # 全局参数与大模型 API 配置
├── ks_extractor.py     # 核心引擎：KS 文件正则提取、清洗与回写
├── llm_api.py          # 大模型通信模块 (支持请求重试)
├── json_handle.py      # 进度文件与相对路径管理模块
└── utils.py            # 工具箱
```

## 🛠️ Quick Start(源代码)
1. 克隆项目与环境准备
确保你的电脑上安装了 Python 3.10 或更高版本。

```bash
git clone [https://github.com/onprs/EXTranslator.git](https://github.com/onprs/EXTranslator.git)
cd EXTranslator
```
2. 配置你的自定义设置
打开 config.py，填入你的工程路径与大模型密钥：

# 核心路径设置
INPUT_PATH = "C:/你的解包路径/source" 
OUTPUT_PATH = "C:/你的导出路径/output"

# 大模型 API 设置
API_KEY = "sk-xxxxxxxxxxxxxxxxxxx"
BASE_URL = "[https://api.xxxx.com/v1](https://api.xxxx.com/v1)"
MODEL_NAME = "gpt-4o-mini"
3. 启动汉化引擎
```bash
python main.py
```
根据控制台提示，选择相应的操作即可开始全自动翻译流水线！

## 📅 To-Do List
[ ] 文本级去重机制： 跨文件识别重复语句，大幅度节省 API Token 消耗。

[ ] 多引擎支持： 兼容更多视觉小说引擎格式。

[ ] 字典映射注入： 支持外部专有名词表（Glossary）的强制匹配。

欢迎提交 Pull Request 或 Issue 来一起完善这个工具！

PS某人：
这个项目很不错，我单汪汪投了。
强烈建议大家尝试，如果有问题的话请向on老师反馈。(o(*￣▽￣*)ブ)

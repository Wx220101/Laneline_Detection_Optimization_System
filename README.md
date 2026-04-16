# Lane Detection Improvement Crew

基于 [crewAI](https://crewai.com) 构建的车道线检测系统改进智能代理。该项目利用两个专业 AI 代理协作分析和优化车道线检测系统，提供针对性的改进建议。

## 项目简介

这个 CrewAI 项目专门用于分析和改进车道线检测系统。通过两个专业的 AI 代理（车道检测分析师和改进工程师）的协作，能够：

- 分析当前车道线检测系统的性能和问题
- 识别系统瓶颈和改进机会
- 提出具体的优化建议和实施方案
- 生成详细的改进报告

## 系统架构

### AI 代理组成
- **车道检测分析师**: 负责分析系统性能，识别问题和改进点
- **改进工程师**: 基于分析师的发现，提出具体的改进方案

### 工作流程
1. 从 `knowledge/` 文件夹读取系统描述信息
2. 分析师分析系统架构和潜在问题
3. 工程师提出针对性的改进建议
4. 生成 `lane_detection_improvements.md` 改进报告

## 安装说明

### 系统要求
- Python >= 3.10, < 3.14
- 支持 DeepSeek API 或 OpenAI API

### 依赖管理
项目使用 [UV](https://docs.astral.sh/uv/) 进行依赖管理和包处理。

1. 安装 uv（如果尚未安装）：
```bash
pip install uv
```

2. 安装项目依赖：
```bash
uv sync
```
或使用 CrewAI CLI：
```bash
crewai install
```

## 配置设置

### API 配置
在 `.env` 文件中配置 API 密钥：

```bash
# DeepSeek API 配置（推荐）
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_API_URL=https://api.deepseek.com/v1

# 或者使用 OpenAI API
OPENAI_API_KEY=your_openai_api_key
```

### 系统知识库
将车道线检测系统的相关文档放入 `knowledge/` 文件夹：
- 系统架构说明
- 性能数据
- 现有问题描述
- 技术规格文档

## 运行项目

### 基本运行
从项目根目录运行：
```bash
crewai run
```

### 其他命令
```bash
# 训练模式
crewai train

# 测试模式
crewai test

# 交互模式
crewai chat
```

## 输出结果

运行完成后，会在项目根目录生成：
- `lane_detection_improvements.md`: 详细的系统改进建议报告

## 项目结构

```
lane-detection-improvement/
├── src/testintest/
│   ├── config/
│   │   ├── agents.yaml       # 代理配置
│   │   └── tasks.yaml        # 任务配置
│   ├── crew.py              # 主要代理逻辑
│   └── main.py              # 程序入口
├── knowledge/               # 系统知识库
├── .env                     # 环境变量配置
├── pyproject.toml           # 项目配置
└── uv.lock                  # 依赖锁定文件
```

## 自定义配置

### 修改代理行为
- 编辑 `src/testintest/config/agents.yaml` 定义代理角色和能力
- 编辑 `src/testintest/config/tasks.yaml` 定义任务流程

### 添加新功能
- 在 `src/testintest/crew.py` 中添加自定义逻辑和工具
- 在 `src/testintest/main.py` 中自定义输入参数

## 技术栈

- **框架**: CrewAI - 多代理协作框架
- **AI 模型**: DeepSeek Chat / OpenAI GPT-4
- **语言**: Python 3.10+
- **包管理**: UV
- **配置**: YAML 配置文件

## 支持与反馈

- 📖 [CrewAI 官方文档](https://docs.crewai.com)
- 🐛 [GitHub Issues](https://github.com/joaomdmoura/crewai)
- 💬 [Discord 社区](https://discord.com/invite/X4JWnZnxPb)
- 🤖 [文档聊天](https://chatg.pt/DWjSBZn)

让我们一起用 AI 的力量改进车道线检测系统！

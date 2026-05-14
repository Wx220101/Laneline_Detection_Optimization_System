# lane_recognition

基于 [CrewAI](https://crewai.com) 的 **Flow + Crew** 项目：默认运行 **车道线检测与跟踪控制改进** 流水线。车道优化 Crew 要求你在 **`repo_root_hint`** 中指定**本机要分析的 ROS/源码工程根路径**（建议绝对路径）；任务与 Agent 文案**仅**以该路径下的代码为事实依据。可选 **PDF 论文 RAG**（`knowledge/papers/`）。`knowledge/` 下仍可自行保留参考工程副本，但**不再**在 `tasks.yaml` 里写死某一条 knowledge 路径。另含一套可选的博客内容模板 Crew。

- **Python**：`>=3.10,<3.14`（见 `pyproject.toml`）
- **包管理**：推荐使用 [uv](https://docs.astral.sh/uv/)

---

## 仓库结构（与车道优化相关）

```
lane_recognition/
├── .env                          # API Key、MODEL、OPENAI_BASE_URL 等（勿提交）
├── pyproject.toml                # 依赖、crewai type=flow、脚本入口（含 lane-ui）
├── README.md                     # 本文件
├── AGENTS.md                     # CrewAI 协作约定（若存在）
├── scripts/
│   └── check_knowledge_pdfs.py   # 校验 knowledge/ 下 PDF 是否可被 pdfplumber 打开
├── knowledge/
│   ├── papers/
│   │   ├── perception/           # 感知 Agent 挂载的 PDF（根目录 *.pdf）
│   │   └── control/              # 控制 Agent 挂载的 PDF（根目录 *.pdf）
│   └── …/                         # 可选：自管参考/拷贝的 ROS 工程（路径自定，由 repo_root_hint 指向）
└── src/lane_recognition/
    ├── main.py                   # Flow 入口：默认 LaneOptimizationFlow
    ├── ui.py                     # 本地 Gradio：lane-ui
    └── crews/
        ├── lane_optimization_crew/
        │   ├── lane_optimization_crew.py   # PDF 路径、ONNX 嵌入、before_kickoff、按模式 kickoff
        │   └── config/
        │       ├── agents.yaml
        │       └── tasks.yaml
        └── content_crew/         # 可选：博客大纲→写作→编辑
```

---

## 项目做什么

| 组件 | 说明 |
|------|------|
| **`LaneOptimizationFlow`**（`main.py`） | 默认入口：调用 **`LaneOptimizationCrew`**，把 Crew 的 `result.raw` 写入 `output/lane_opt/00_summary.md`。 |
| **`LaneOptimizationCrew`** | 三 Agent：**感知**、**控制**、**集成**；顺序执行三 Task，目标：**车道线识别更准**、**回中更快**，产出 Markdown。 |
| **`repo_root_hint`（必填语义）** | 传入 Crew 的 `inputs`，写入 `tasks.yaml` / `agents.yaml` 的 `{repo_root_hint}`。Agent 须**只**以该根路径下的源码与配置为代码事实依据；勿留空，否则无法按「读你磁盘上的工程」这一约定工作。建议使用**绝对路径**（Windows 下注意 JSON 转义 `\\`）。 |
| **PDF 知识库** | `lane_perception_engineer` 读取 `knowledge/papers/perception/*.pdf`，`control_response_engineer` 读取 `knowledge/papers/control/*.pdf`；可作**理论与方法**补充，**不替代**你对 `repo_root_hint` 下源码的阅读结论。路径在 `lane_optimization_crew.py` 中硬编码，**勿改** `perception` / `control` 目录名，除非同步改代码。 |
| **向量嵌入** | Crew 使用 **本地 ONNX 嵌入**（`embedder: onnx`），与聊天 LLM 的 `OPENAI_BASE_URL`（如 DeepSeek）解耦，避免嵌入接口 404。 |
| **`before_kickoff`** | 尝试删除与 Agent `role` 对应的旧 Chroma 集合，避免换嵌入模型后冲突；集合不存在时静默跳过。 |
| **`lane-ui`** | 本地 Gradio：填写 `project_name`、`repo_root_hint`、`deliverable_dir`，可选仅感知 / 仅控制 / 全流程。见下文。 |
| **`ContentFlow` + `ContentCrew`** | 可选；需 `run_with_trigger` 且 `flow: "content"` 时运行，输出 `output/post.md`。 |

---

## 安装

```powershell
pip install uv
cd lane_recognition
uv sync
```

在项目根创建 `.env`，至少配置聊天 LLM 所需变量，例如：

- `OPENAI_API_KEY`
- 若使用兼容 OpenAI 的网关：`OPENAI_BASE_URL`
- `MODEL`（或你使用的 LiteLLM 路由名）

---

## 论文 PDF（可选）

1. 将感知相关 PDF 放入 **`knowledge/papers/perception/`**（仅该目录**根下**的 `*.pdf`）。  
2. 将控制相关 PDF 放入 **`knowledge/papers/control/`**。  
3. 自检（仓库根目录）：

```powershell
uv run python scripts/check_knowledge_pdfs.py
```

无法解析的 PDF 会在运行时被跳过并记录 warning；合法 PDF 会参与向量检索。

**Git**：若不想把 PDF 推上远程，在根目录 `.gitignore` 增加 `knowledge/papers/**/*.pdf`；否则可正常 `git add` 提交。单文件建议小于 100 MB（GitHub 限制可考虑 [Git LFS](https://git-lfs.com/)）。

---

## 运行方式

在**仓库根目录**执行：

```powershell
crewai run
```

或：

```powershell
uv run kickoff
```

入口见 `pyproject.toml` 中 `[project.scripts]` 的 `kickoff` / `run_crew` → `lane_recognition.main:kickoff`。

**本地界面（Gradio）**：

```powershell
uv run lane-ui
```

浏览器打开后填写 **`repo_root_hint`**（工程根绝对路径）、`project_name`、`deliverable_dir`，选择「仅感知 / 仅控制 / 全流程」后运行。详细逻辑见 `src/lane_recognition/ui.py` 与 `LaneOptimizationCrew.kickoff_lane_opt()`。

**画 Flow 图**：

```powershell
uv run plot
```

**带 JSON 触发参数**（覆盖 `project_name`、`repo_root_hint`、`deliverable_dir` 或切换 Flow）。**车道优化务必提供非空的 `repo_root_hint`**，指向你要分析的那份源码树（例如你从 knowledge 拷出的 catkin 包、或自己的 `ws/src`）：

```powershell
uv run run_with_trigger "{\"flow\": \"lane_opt\", \"project_name\": \"Lane Recognition\", \"repo_root_hint\": \"C:\\\\Users\\\\user\\\\my_CrewAI\\\\lane_recognition\\\\knowledge\\\\lane_follower_ws\\\\src\", \"deliverable_dir\": \"output/lane_opt\"}"
```

（请把 `repo_root_hint` 换成你本机真实路径；PowerShell 中字符串内反斜杠按需加倍。）

切换到博客模板：`"flow": "content", "topic": "你的主题"`。

---

## 运行产出（默认 `deliverable_dir = output/lane_opt`）

| 文件 | 说明 |
|------|------|
| `01_perception.md` | 感知 Task 输出（`tasks.yaml` 中 `output_file`）。 |
| `02_control.md` | 控制 Task 输出。 |
| `lane_improvement_plan.md` | 集成 Task：总览蓝图 + 操作清单 + 附录。 |
| `00_summary.md` | Flow 写入的 Crew `result.raw` 摘要存档。 |

---

## 常见问题

- **嵌入 404（OpenAI embeddings）**：当前已改用 ONNX；请使用本仓库最新 `lane_optimization_crew.py`。  
- **`onnx vs persisted: openai`**：本机 Chroma 曾有旧集合；`before_kickoff` 会尝试删除后重建；仍失败可 `crewai reset-memories -a`（影响面大）或清理 Chroma 持久化目录。  
- **首次运行较慢**：可能下载 ONNX 模型（约 80MB）到用户缓存目录。  
- **`repo_root_hint` 留空**：任务文案要求以该路径为唯一工程根；留空时模型无法按「读你指定工程」履约，报告质量不可预期，**请始终填写有效路径**。  
- **修改 Agent/Task 文案**：编辑 `src/lane_recognition/crews/lane_optimization_crew/config/agents.yaml` 与 `tasks.yaml`（以本仓库实际路径为准）。

---

## 文档与仓库

- [CrewAI 文档](https://docs.crewai.com)  
- [CrewAI GitHub](https://github.com/crewAIInc/crewAI)  

项目内更细的 CrewAI 约定见根目录 **`AGENTS.md`**（若存在）。

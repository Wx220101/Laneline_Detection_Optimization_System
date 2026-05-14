import logging
from pathlib import Path
from typing import Literal, cast

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource
from crewai.project import CrewBase, agent, before_kickoff, crew, task
from crewai.rag.chromadb.config import ChromaDBConfig
from crewai.rag.chromadb.types import ChromaEmbeddingFunctionWrapper
from crewai.rag.embeddings.factory import build_embedder
from crewai.rag.factory import create_client

# 与 Crew.embedder 一致；知识库 Chroma 集合若曾用默认 OpenAI 嵌入创建，需先删除再换 ONNX
_EMBEDDER_ONNX: dict = {"provider": "onnx", "config": {}}

# 仓库根目录（含 pyproject.toml）：lane_optimization_crew.py → 向上 4 级到项目根
_REPO_ROOT = Path(__file__).resolve().parents[4]
_PERCEPTION_PAPERS = _REPO_ROOT / "knowledge" / "papers" / "perception"
_CONTROL_PAPERS = _REPO_ROOT / "knowledge" / "papers" / "control"

_logger = logging.getLogger(__name__)


def _pdf_knowledge_from_dir(dir_path: Path) -> list[PDFKnowledgeSource] | None:
    """逐个加载 PDF，避免单个损坏/伪 PDF 导致整个 Crew 初始化失败。"""
    sources: list[PDFKnowledgeSource] = []
    for path in sorted(dir_path.glob("*.pdf")):
        if not path.is_file():
            continue
        try:
            sources.append(PDFKnowledgeSource(file_paths=[path]))
        except Exception as exc:  # noqa: BLE001 — 需捕获 pdfplumber 各类解析错误
            _logger.warning(
                "跳过无法解析的 PDF（可能损坏、非标准 PDF 或实为其它格式改后缀）: %s | %s",
                path,
                exc,
            )
    return sources or None


def _roles_with_pdf_knowledge(agents_config: dict) -> list[str]:
    """与 set_knowledge 使用的 collection_name（agent.role）一致，来自 YAML。"""
    roles: list[str] = []
    for key in ("lane_perception_engineer", "control_response_engineer"):
        block = agents_config.get(key)  # type: ignore[union-attr]
        if not isinstance(block, dict):
            continue
        role = block.get("role")
        if isinstance(role, str) and role.strip():
            roles.append(role)
    return roles


def _delete_knowledge_collection_if_exists(role: str) -> None:
    """与 KnowledgeStorage 相同命名规则删除 Chroma 集合；不存在则静默跳过（避免 reset() 打 ERROR 日志）。"""
    try:
        embed_fn = build_embedder(_EMBEDDER_ONNX)
        cfg = ChromaDBConfig(
            embedding_function=cast(ChromaEmbeddingFunctionWrapper, embed_fn)
        )
        client = create_client(cfg)
        client.delete_collection(collection_name=f"knowledge_{role}")
    except Exception as exc:  # noqa: BLE001
        msg = str(exc).lower()
        if (
            "does not exist" in msg
            or "does not exists" in msg
            or "not found" in msg
            or "doesn't exist" in msg
        ):
            _logger.debug("Chroma 知识库集合不存在，跳过删除: %s", exc)
            return
        _logger.warning("删除 Chroma 知识库集合时出现非预期错误: %s", exc)


@CrewBase
class LaneOptimizationCrew:
    """智能车道检测项目改进 Crew：感知精度 + 控制响应分工协作。"""

    agents: list[BaseAgent]
    tasks: list[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @before_kickoff
    def _drop_stale_knowledge_collections(self, inputs):  # noqa: ANN001
        """若此前用其他嵌入建过同名 Chroma 集合，换 ONNX 后会冲突；启动前尝试删除。集合不存在时忽略。"""
        for role in _roles_with_pdf_knowledge(self.agents_config):  # type: ignore[arg-type]
            _delete_knowledge_collection_if_exists(role)
        return inputs

    @agent
    def lane_perception_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["lane_perception_engineer"],  # type: ignore[index]
            verbose=True,
            knowledge_sources=_pdf_knowledge_from_dir(_PERCEPTION_PAPERS),
        )

    @agent
    def control_response_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["control_response_engineer"],  # type: ignore[index]
            verbose=True,
            knowledge_sources=_pdf_knowledge_from_dir(_CONTROL_PAPERS),
        )

    @agent
    def optimization_integrator(self) -> Agent:
        return Agent(
            config=self.agents_config["optimization_integrator"],  # type: ignore[index]
            verbose=True,
        )

    @task
    def perception_precision_task(self) -> Task:
        return Task(
            config=self.tasks_config["perception_precision_task"],  # type: ignore[index]
        )

    @task
    def control_response_task(self) -> Task:
        return Task(
            config=self.tasks_config["control_response_task"],  # type: ignore[index]
        )

    @task
    def integration_task(self) -> Task:
        return Task(
            config=self.tasks_config["integration_task"],  # type: ignore[index]
            context=[
                self.perception_precision_task(),
                self.control_response_task(),
            ],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Lane Optimization Crew"""
        # 本地 ONNX 嵌入（见 _EMBEDDER_ONNX）。若曾用默认 OpenAI 嵌入建库，由 _drop_stale_knowledge_collections 在 kickoff 前尝试删除旧集合（不存在则忽略）。
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            embedder=_EMBEDDER_ONNX,
        )

    def crew_for_mode(
        self, mode: Literal["perception", "control", "full"]
    ) -> Crew:
        """按模式构建子 Crew：仅感知、仅控制，或三 Agent 全流程（与 crew() 等价）。"""
        if mode == "full":
            return self.crew()
        if mode == "perception":
            return Crew(
                agents=[self.lane_perception_engineer()],
                tasks=[self.perception_precision_task()],
                process=Process.sequential,
                verbose=True,
                embedder=_EMBEDDER_ONNX,
            )
        return Crew(
            agents=[self.control_response_engineer()],
            tasks=[self.control_response_task()],
            process=Process.sequential,
            verbose=True,
            embedder=_EMBEDDER_ONNX,
        )

    def kickoff_lane_opt(
        self,
        inputs: dict,
        mode: Literal["perception", "control", "full"],
    ):
        """与 Flow 一致：先清理可能冲突的 Chroma 集合，再按模式 kickoff。"""
        prepared = self._drop_stale_knowledge_collections(dict(inputs))
        return self.crew_for_mode(mode).kickoff(inputs=prepared)

# -*- coding: utf-8 -*-
"""本地 Gradio 界面：选择仅感知、仅控制或三 Agent 全流程并运行 LaneOptimizationCrew。"""
from __future__ import annotations

import traceback
from pathlib import Path

import gradio as gr

from lane_recognition.crews.lane_optimization_crew.lane_optimization_crew import (
    LaneOptimizationCrew,
)

_MODE_CHOICES: list[tuple[str, str]] = [
    (
        "仅感知 — lane_perception_engineer（输出 01_perception.md）",
        "perception",
    ),
    (
        "仅控制 — control_response_engineer（输出 02_control.md）",
        "control",
    ),
    (
        "全流程 — 感知 → 控制 → optimization_integrator（含 lane_improvement_plan.md）",
        "full",
    ),
]

_CSS = """
footer {visibility: hidden}
.gradio-container { max-width: 920px !important; margin: auto; }
"""

_INTRO = """
### 车道优化 Agent 控制台

在此填写项目参数并选择运行模式。运行完成后，Markdown 会写入 **交付目录**（与 `tasks.yaml` 中 `output_file` 一致）。

终端里的 Crew 详细日志仍会输出到本机控制台。
"""


def _theme() -> gr.themes.Soft:
    return gr.themes.Soft(
        primary_hue=gr.themes.Color(
            c50="#e8f7fa",
            c100="#c7ecf2",
            c200="#9bdddd",
            c300="#6bc9c4",
            c400="#3cb0a8",
            c500="#2a9d8f",
            c600="#238275",
            c700="#1c665d",
            c800="#154a45",
            c900="#0e2f2c",
            c950="#0a2422",
        ),
        font=[gr.themes.GoogleFont("Noto Sans SC"), "sans-serif"],
    )


def _run(
    project_name: str,
    repo_root_hint: str,
    deliverable_dir: str,
    mode: str,
) -> str:
    project_name = (project_name or "").strip() or "Lane Recognition"
    repo_root_hint = (repo_root_hint or "").strip()
    deliverable_dir = (deliverable_dir or "").strip() or "output/lane_opt"

    Path(deliverable_dir).mkdir(parents=True, exist_ok=True)

    if mode not in ("perception", "control", "full"):
        return f"**错误**：未知模式 `{mode}`。"

    mode_label = next((a for a, v in _MODE_CHOICES if v == mode), mode)

    try:
        crew_base = LaneOptimizationCrew()
        result = crew_base.kickoff_lane_opt(
            inputs={
                "project_name": project_name,
                "repo_root_hint": repo_root_hint,
                "deliverable_dir": deliverable_dir,
            },
            mode=mode,  # type: ignore[arg-type]
        )
    except Exception:
        return (
            f"### 运行失败（{mode_label}）\n\n"
            f"```\n{traceback.format_exc()}\n```"
        )

    raw = getattr(result, "raw", str(result))
    files_note = {
        "perception": f"`{deliverable_dir}/01_perception.md`",
        "control": f"`{deliverable_dir}/02_control.md`",
        "full": (
            f"`{deliverable_dir}/01_perception.md`、"
            f"`{deliverable_dir}/02_control.md`、"
            f"`{deliverable_dir}/lane_improvement_plan.md`"
        ),
    }[mode]

    return (
        f"### 完成：{mode_label}\n\n"
        f"- **项目**：{project_name}\n"
        f"- **交付目录**：`{Path(deliverable_dir).resolve()}`\n"
        f"- **已写入**：{files_note}\n\n"
        "---\n\n"
        "#### 本次 Crew 汇总输出（raw）\n\n"
        f"{raw}"
    )


def build_demo() -> gr.Blocks:
    with gr.Blocks(
        title="车道优化 Agent 控制台",
    ) as demo:
        gr.Markdown(_INTRO)
        with gr.Row():
            project_name = gr.Textbox(
                label="项目代号 project_name",
                value="Lane Recognition",
                placeholder="Lane Recognition",
            )
        with gr.Row():
            repo_root_hint = gr.Textbox(
                label="仓库根路径提示 repo_root_hint（可空）",
                value="",
                placeholder="可选，便于 Agent 在描述中引用你的绝对路径",
            )
        with gr.Row():
            deliverable_dir = gr.Textbox(
                label="交付目录 deliverable_dir",
                value="output/lane_opt",
                placeholder="output/lane_opt",
            )
        mode = gr.Radio(
            label="运行模式",
            choices=[c[0] for c in _MODE_CHOICES],
            value=_MODE_CHOICES[2][0],
        )
        run_btn = gr.Button("开始运行", variant="primary", size="lg")
        out = gr.Markdown(label="结果")

        def _submit(pn: str, rh: str, dd: str, mode_display: str) -> str:
            key = next(v for label, v in _MODE_CHOICES if label == mode_display)
            return _run(pn, rh, dd, key)

        run_btn.click(
            fn=_submit,
            inputs=[project_name, repo_root_hint, deliverable_dir, mode],
            outputs=out,
        )

    return demo


def launch() -> None:
    demo = build_demo()
    demo.queue(default_concurrency_limit=1)
    demo.launch(
        inbrowser=True,
        server_name="127.0.0.1",
        theme=_theme(),
        css=_CSS,
    )


if __name__ == "__main__":
    launch()

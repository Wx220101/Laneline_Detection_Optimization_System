#!/usr/bin/env python
from pathlib import Path

from pydantic import BaseModel

from crewai.flow import Flow, listen, start

from lane_recognition.crews.content_crew.content_crew import ContentCrew
from lane_recognition.crews.lane_optimization_crew.lane_optimization_crew import (
    LaneOptimizationCrew,
)


class ContentState(BaseModel):
    topic: str = ""
    outline: str = ""
    draft: str = ""
    final_post: str = ""


class ContentFlow(Flow[ContentState]):

    @start()
    def plan_content(self, crewai_trigger_payload: dict = None):
        print("Planning content")

        if crewai_trigger_payload:
            self.state.topic = crewai_trigger_payload.get("topic", "AI Agents")
            print(f"Using trigger payload: {crewai_trigger_payload}")
        else:
            self.state.topic = "AI Agents"

        print(f"Topic: {self.state.topic}")

    @listen(plan_content)
    def generate_content(self):
        print(f"Generating content on: {self.state.topic}")
        result = (
            ContentCrew()
            .crew()
            .kickoff(inputs={"topic": self.state.topic})
        )

        print("Content generated")
        self.state.final_post = result.raw

    @listen(generate_content)
    def save_content(self):
        print("Saving content")
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        with open(output_dir / "post.md", "w") as f:
            f.write(self.state.final_post)
        print("Post saved to output/post.md")


class LaneOptState(BaseModel):
    project_name: str = "Lane Recognition"
    repo_root_hint: str = ""
    deliverable_dir: str = "output/lane_opt"
    final_summary: str = ""


class LaneOptimizationFlow(Flow[LaneOptState]):

    @start()
    def plan_lane_optimization(self, crewai_trigger_payload: dict = None):
        print("Planning lane optimization")

        if crewai_trigger_payload:
            self.state.project_name = crewai_trigger_payload.get(
                "project_name", self.state.project_name
            )
            self.state.repo_root_hint = crewai_trigger_payload.get("repo_root_hint", "")
            self.state.deliverable_dir = crewai_trigger_payload.get(
                "deliverable_dir", self.state.deliverable_dir
            )
            print(f"Using trigger payload: {crewai_trigger_payload}")

        print(f"Project: {self.state.project_name}")
        print(f"Deliverables: {self.state.deliverable_dir}")

    @listen(plan_lane_optimization)
    def generate_lane_opt_plan(self):
        print("Generating lane optimization deliverables")

        result = LaneOptimizationCrew().crew().kickoff(
            inputs={
                "project_name": self.state.project_name,
                "repo_root_hint": self.state.repo_root_hint,
                "deliverable_dir": self.state.deliverable_dir,
            }
        )

        # 专文件：01_perception.md、02_control.md 由前两步 Task 的 output_file 写入；
        # lane_improvement_plan.md 由集成 Task 写入。此处仍保存 result.raw 为 00_summary.md。
        self.state.final_summary = result.raw
        print("Lane optimization deliverables generated")

    @listen(generate_lane_opt_plan)
    def save_lane_opt_summary(self):
        print("Saving lane optimization summary")
        output_dir = Path(self.state.deliverable_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_dir / "00_summary.md", "w", encoding="utf-8") as f:
            f.write(self.state.final_summary)
        print(f"Summary saved to {output_dir / '00_summary.md'}")


def kickoff():
    """
    默认运行车道线优化 Flow。

    如需运行内容模板 Flow，可使用 run_with_trigger() 传入:
    {"flow": "content", "topic": "..."}。
    """
    lane_flow = LaneOptimizationFlow()
    lane_flow.kickoff()


def plot():
    lane_flow = LaneOptimizationFlow()
    lane_flow.plot()


def run_with_trigger():
    """
    Run the flow with trigger payload.
    """
    import json
    import sys

    # Get trigger payload from command line argument
    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    # Create flow and kickoff with trigger payload
    # The @start() methods will automatically receive crewai_trigger_payload parameter
    flow_name = trigger_payload.get("flow", "lane_opt")
    flow: Flow

    if flow_name == "content":
        flow = ContentFlow()
    else:
        flow = LaneOptimizationFlow()

    try:
        result = flow.kickoff({"crewai_trigger_payload": trigger_payload})
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the flow with trigger: {e}")


if __name__ == "__main__":
    kickoff()

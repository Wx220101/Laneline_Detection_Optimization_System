#!/usr/bin/env python
import sys
import warnings
from pathlib import Path

# Ensure the src directory is in the Python path
src_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(src_path))

from testintest.crew import Testintest

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def load_system_info_from_knowledge() -> str:
    """Load the lane detection system description from the knowledge folder."""
    project_root = Path(__file__).resolve().parent.parent.parent
    knowledge_root = project_root / "knowledge"
    system_info_parts = []

    system_info_parts.append("Current lane detection system information loaded from the knowledge folder:")
    system_info_parts.append(f"Knowledge root: {knowledge_root}")

    if not knowledge_root.exists():
        system_info_parts.append("Warning: knowledge folder not found.")
        return "\n".join(system_info_parts)

    target_dir = knowledge_root / '智能车道线检测与保持_彭之芯_吴泓霖_柳阳_42035803'
    if not target_dir.exists():
        system_info_parts.append("Warning: specific project folder not found under knowledge.")
        return "\n".join(system_info_parts)

    system_info_parts.append("\n## Document files:\n")
    doc_dir = target_dir / 'doc'
    if doc_dir.exists():
        for path in sorted(doc_dir.glob("*.md")):
            system_info_parts.append(f"- {path.name}")
            try:
                content = path.read_text(encoding='utf-8', errors='ignore')
                system_info_parts.append(content)
            except Exception:
                system_info_parts.append(f"  [failed to read {path.name}]")
    else:
        system_info_parts.append("- No doc directory found")

    system_info_parts.append("\n## Source folders and files:\n")
    src_dir = target_dir / 'src'
    if src_dir.exists():
        for path in sorted(src_dir.rglob("*.py")):
            rel = path.relative_to(project_root)
            system_info_parts.append(f"- {rel}")
    else:
        system_info_parts.append("- No src directory found")

    return "\n".join(system_info_parts)


def run():
    """
    Run the crew to analyze and improve lane detection system.
    """
    inputs = {
        'system_info': load_system_info_from_knowledge()
    }

    try:
        Testintest().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "system_info": load_system_info_from_knowledge()
    }
    try:
        Testintest().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        Testintest().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "system_info": load_system_info_from_knowledge()
    }

    try:
        Testintest().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

def run_with_trigger():
    """
    Run the crew with trigger payload.
    """
    import json

    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    inputs = {
        "crewai_trigger_payload": trigger_payload,
        "topic": "",
        "current_year": ""
    }

    try:
        result = Testintest().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")

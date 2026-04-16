from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
import os
from pathlib import Path
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class Testintest():
    """Lane Detection Improvement Crew - AI agents for analyzing and improving lane detection systems"""

    agents: list[BaseAgent]
    tasks: list[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    
    # Initialize LLM for supported provider
    def _get_llm(self) -> LLM:
        """Initialize LLM with a supported provider.

        Priority order:
        1. openai/gpt-4o when OPENAI_API_KEY is set
        2. deepseek/deepseek-chat when DEEPSEEK_API_KEY is set and LiteLLM is installed
        """
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            return LLM(
                model="openai/gpt-4o",
                api_key=openai_key,
            )

        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        if deepseek_key:
            try:
                import litellm  # noqa: F401
            except ImportError as exc:
                raise ImportError(
                    "DeepSeek requires LiteLLM support. Install it with:\n"
                    "  pip install litellm\n"
                    "or\n"
                    "  uv add 'crewai[litellm]'"
                ) from exc

            return LLM(
                model="deepseek/deepseek-chat",
                api_key=deepseek_key,
                base_url=os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1"),
            )

        raise EnvironmentError(
            "No supported LLM configuration found. Please set OPENAI_API_KEY for openai/gpt-4o "
            "or DEEPSEEK_API_KEY for DeepSeek with LiteLLM installed."
        )
    
    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def lane_detection_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['lane_detection_analyst'], # type: ignore[index]
            llm=self._get_llm(),
            verbose=True
        )

    @agent
    def improvement_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['improvement_engineer'], # type: ignore[index]
            llm=self._get_llm(),
            verbose=True
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['analysis_task'], # type: ignore[index]
        )

    @task
    def improvement_task(self) -> Task:
        return Task(
            config=self.tasks_config['improvement_task'], # type: ignore[index]
            context=[self.analysis_task()]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Lane Detection Improvement Crew
        
        This crew orchestrates two specialized AI agents:
        1. Lane Detection Analyst - Analyzes the current system and identifies issues
        2. Improvement Engineer - Proposes concrete improvement solutions
        
        The crew works sequentially, with the analyst's findings informing the engineer's recommendations.
        """
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )

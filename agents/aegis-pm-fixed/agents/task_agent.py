"""Task decomposition ADK agent."""

from __future__ import annotations

from google.adk.runners import Runner
from pydantic import BaseModel, Field

from agents.base_agent import BaseAegisAgent
from core.dag import DAGEngine
from core.schemas import Milestone, Plan, Task, TaskGraph, TaskStatus
from tools.memory_tools import retrieve_context_tool


class TaskOutput(BaseModel):
    """Structured task output from the task agent."""

    tasks: list[dict] = Field(default_factory=list)


class TaskAgent(BaseAegisAgent):
    """Decomposes milestones into atomic tasks with dependencies."""

    def __init__(self) -> None:
        """Initialize the task agent."""
        super().__init__(
            name="task_agent",
            model="gemini-2.0-flash",
            description="Decomposes milestones into atomic tasks with explicit dependencies",
            instruction=(
                "You are a task decomposition agent. Output strict JSON with a 'tasks' array. "
                "Each task must include id, name, description, dependencies, impact, effort, urgency, "
                "risk_score, status, assigned_agent, and tool_payload."
            ),
            tools=[retrieve_context_tool],
        )

    async def generate_task_graph(self, runner: Runner, goal_text: str, milestones: list[Milestone], user_id: str, session_id: str) -> TaskGraph:
        """Generate a validated task graph from milestones."""
        prompt = (
            "Convert these milestones into atomic tasks with explicit dependency IDs.\n"
            f"Goal: {goal_text}\n"
            f"Milestones: {[item.model_dump(mode='json') for item in milestones]}\n"
            "Return JSON only."
        )
        try:
            response = await self.run_structured(
                runner,
                user_id=user_id,
                session_id=session_id,
                prompt=prompt,
                schema=TaskOutput,
            )
            tasks = [Task.model_validate(item) for item in response.tasks]
        except Exception:
            tasks = self._fallback_tasks()
        self._validate_dependencies(tasks)
        graph = TaskGraph()
        engine = DAGEngine(graph)
        for task in tasks:
            engine.add_task(task)
        return graph

    def _validate_dependencies(self, tasks: list[Task]) -> None:
        """Validate dependency correctness before building the graph."""
        valid_ids = {task.id for task in tasks}
        for task in tasks:
            if task.id in task.dependencies:
                raise ValueError(f"Task {task.id} cannot depend on itself")
            for dependency in task.dependencies:
                if dependency not in valid_ids:
                    raise ValueError(f"Task {task.id} references unknown dependency {dependency}")

    def _fallback_tasks(self) -> list[Task]:
        """Generate a deterministic fallback task graph."""
        scope = Task(
            id="task-scope",
            name="Lock scope",
            description="Define MVP scope, KPIs, and owners.",
            dependencies=[],
            impact=0.95,
            effort=0.25,
            urgency=0.95,
            risk_score=0.30,
            status=TaskStatus.READY,
            assigned_agent="pm_agent",
            tool_payload={"actions": [{"tool": "send_slack_message", "channel": "#product", "text": "Scope lock started"}]},
        )
        backlog = Task(
            id="task-backlog",
            name="Create backlog",
            description="Create Jira tickets and GitHub planning issue.",
            dependencies=["task-scope"],
            impact=0.90,
            effort=0.35,
            urgency=0.90,
            risk_score=0.35,
            status=TaskStatus.PENDING,
            assigned_agent="task_agent",
            tool_payload={"actions": [{"tool": "create_jira_ticket", "project_key": "AEG", "summary": "Create backlog", "description": "Backlog build", "issue_type": "Epic", "priority": "High"}]},
        )
        build = Task(
            id="task-build",
            name="Create execution branch",
            description="Open the delivery branch for the MVP implementation.",
            dependencies=["task-backlog"],
            impact=0.85,
            effort=0.30,
            urgency=0.80,
            risk_score=0.40,
            status=TaskStatus.PENDING,
            assigned_agent="pm_agent",
            tool_payload={"actions": [{"tool": "create_github_branch", "repo": "owner/repo", "branch_name": "aegis/mvp-launch"}]},
        )
        report = Task(
            id="task-report",
            name="Publish execution report",
            description="Send the current delivery report to Slack.",
            dependencies=["task-build"],
            impact=0.70,
            effort=0.10,
            urgency=0.75,
            risk_score=0.20,
            status=TaskStatus.PENDING,
            assigned_agent="reporter_agent",
            tool_payload={"actions": [{"tool": "send_slack_report", "channel": "#exec"}]},
        )
        return [scope, backlog, build, report]

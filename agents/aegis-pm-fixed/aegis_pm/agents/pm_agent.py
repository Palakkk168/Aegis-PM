"""Project manager orchestration agent."""

from __future__ import annotations

from datetime import UTC, datetime
import time

from aegis_pm.agents.base import BaseAgent
from aegis_pm.agents.dev_agent import DevAgent
from aegis_pm.agents.planner_agent import PlannerAgent
from aegis_pm.agents.qa_agent import QAAgent
from aegis_pm.agents.reporter_agent import ReporterAgent
from aegis_pm.agents.risk_agent import RiskAgent
from aegis_pm.agents.task_agent import TaskAgent
from aegis_pm.memory.decision_log import DecisionLog
from aegis_pm.memory.state_store import StateStore
from aegis_pm.memory.vector_store import VectorStore
from aegis_pm.observability.metrics import MetricsRegistry
from aegis_pm.schemas import DecisionLogEntry, ExecutionPlan, ExecutionRun, GoalExecutionResult, GoalRequest, RunStatus, TaskNode, TaskStatus
from aegis_pm.tools.registry import ToolRegistry
from aegis_pm.workflows.scoring import score_task
from aegis_pm.workflows.task_graph import TaskGraphManager


class PMAgent(BaseAgent):
    """Master orchestrator for Aegis PM."""

    def __init__(
        self,
        planner: PlannerAgent,
        task_agent: TaskAgent,
        risk_agent: RiskAgent,
        dev_agent: DevAgent,
        qa_agent: QAAgent,
        reporter: ReporterAgent,
        tools: ToolRegistry,
        state_store: StateStore,
        vector_store: VectorStore,
        decision_log: DecisionLog,
        metrics: MetricsRegistry,
        max_parallel_tasks: int,
    ) -> None:
        """Create the orchestrator with its collaborators."""
        super().__init__("pm")
        self.planner = planner
        self.task_agent = task_agent
        self.risk_agent = risk_agent
        self.dev_agent = dev_agent
        self.qa_agent = qa_agent
        self.reporter = reporter
        self.tools = tools
        self.state_store = state_store
        self.vector_store = vector_store
        self.decision_log = decision_log
        self.metrics = metrics
        self.max_parallel_tasks = max_parallel_tasks

    async def run(self, request: GoalRequest) -> GoalExecutionResult:
        """Execute the end-to-end PM workflow for a goal."""
        run = ExecutionRun(project_name=request.project_name, goal=request.goal, status=RunStatus.running)
        await self.state_store.save_run(run)
        historical_context = await self.vector_store.retrieve(request.goal, limit=5)
        plan = await self._generate_plan(request, historical_context)
        run.plan = plan
        task_graph = TaskGraphManager(await self.task_agent.decompose(plan))
        run.tasks = task_graph.tasks
        await self._log_decision(run.run_id, "Initial plan generated", "Goal converted into milestones and task DAG.", list(run.tasks))
        await self.state_store.save_run(run)

        while not task_graph.is_complete():
            ready_tasks = task_graph.ready_tasks()
            if not ready_tasks:
                if task_graph.has_failed_path():
                    run.status = RunStatus.replanning
                    risks = await self.risk_agent.analyze(run, historical_context)
                    new_tasks = await self._replan(task_graph, risks, run)
                    if not new_tasks:
                        run.status = RunStatus.failed
                        break
                    continue
                break

            for task in ready_tasks:
                failure_rate = self._historical_failure_rate(task, historical_context)
                task.score = score_task(
                    task=task,
                    downstream_unlock_count=task_graph.downstream_unlock_count(task.task_id),
                    historical_failure_rate=failure_rate,
                )
            ready_tasks.sort(key=lambda task: task.score, reverse=True)
            wave = ready_tasks[: self.max_parallel_tasks]
            await self._execute_wave(run, wave, request)
            risks = await self.risk_agent.analyze(run, historical_context)
            if risks:
                run.risk_log.extend(risks)
                await self._replan(task_graph, risks, run)
            run.updated_at = datetime.now(UTC)
            await self.state_store.save_run(run)

        run.status = RunStatus.completed if task_graph.is_complete() else run.status
        report = await self.reporter.generate_report(run)
        run.report_id = report.report_id
        await self.state_store.save_report(report)
        await self.state_store.save_run(run)
        await self._store_run_memory(run, report)
        return GoalExecutionResult(run=run, report=report)

    async def _generate_plan(self, request: GoalRequest, historical_context: list[dict]) -> ExecutionPlan:
        """Generate the initial plan with memory context."""
        return await self.planner.generate_plan(
            project_name=request.project_name,
            goal=request.goal,
            context=historical_context,
        )

    async def _execute_wave(self, run: ExecutionRun, tasks: list[TaskNode], request: GoalRequest) -> None:
        """Execute one dependency-safe wave of tasks."""
        async def _run_single_task(task: TaskNode) -> None:
            start = time.perf_counter()
            task.status = TaskStatus.in_progress
            task.started_at = datetime.now(UTC)
            task.attempts += 1
            try:
                outputs = await self._execute_task(run.run_id, task, request)
                task.status = TaskStatus.completed
                task.completed_at = datetime.now(UTC)
                run.completed_task_ids.append(task.task_id)
                run.outputs.append({"task_id": task.task_id, "outputs": outputs})
                await self.metrics.increment("tasks_completed")
            except Exception as exc:  # noqa: BLE001
                task.status = TaskStatus.failed
                task.last_error = str(exc)
                run.failed_task_ids.append(task.task_id)
                await self.metrics.increment("tasks_failed")
            finally:
                elapsed_ms = (time.perf_counter() - start) * 1000
                await self.metrics.observe_latency("task_execution_ms", elapsed_ms)
                await self.state_store.save_run(run)
        import asyncio

        await asyncio.gather(*[_run_single_task(task) for task in tasks])

    async def _execute_task(self, run_id: str, task: TaskNode, request: GoalRequest) -> list[dict]:
        """Route a task to the correct execution agent."""
        await self._log_decision(
            run_id=run_id,
            summary=f"Executing task {task.title}",
            rationale=f"Task scored {task.score} and all dependencies are complete.",
            related_task_ids=[task.task_id],
        )
        if task.owner_role in {"pm", "planner", "dev", "reporter"}:
            return await self.dev_agent.execute(task, self.tools, request.integrations)
        if task.owner_role == "qa":
            return await self.qa_agent.execute(task, self.tools, request.integrations)
        return await self.dev_agent.execute(task, self.tools, request.integrations)

    async def _replan(self, task_graph: TaskGraphManager, risks: list, run: ExecutionRun) -> list[TaskNode]:
        """Add mitigation work and reroute blocked tasks."""
        new_tasks = await self.planner.replan(risks, task_graph.tasks)
        if not new_tasks:
            return []
        for new_task in new_tasks:
            original_id = new_task.metadata["replan_for"]
            task_graph.tasks[original_id].status = TaskStatus.skipped
            for task in task_graph.tasks.values():
                if original_id in task.dependencies and task.task_id != new_task.task_id:
                    task.dependencies = [
                        new_task.task_id if dependency == original_id else dependency
                        for dependency in task.dependencies
                    ]
        task_graph.add_tasks(new_tasks)
        run.tasks = task_graph.tasks
        run.status = RunStatus.running
        await self._log_decision(
            run.run_id,
            "Replan triggered",
            "Mitigation tasks inserted to recover from elevated risk or failure.",
            [task.task_id for task in new_tasks],
        )
        return new_tasks

    async def _store_run_memory(self, run: ExecutionRun, report) -> None:
        """Persist summary memory after a run finishes."""
        outcome = "completed" if run.status == RunStatus.completed else "failed"
        text = (
            f"Goal: {run.goal}\n"
            f"Outcome: {outcome}\n"
            f"Completed tasks: {len(run.completed_task_ids)}\n"
            f"Failed tasks: {len(run.failed_task_ids)}\n"
            f"Summary: {report.executive_summary}"
        )
        await self.vector_store.store(
            entry_id=run.run_id,
            text=text,
            metadata={"outcome": outcome, "project_name": run.project_name},
        )

    def _historical_failure_rate(self, task: TaskNode, historical_context: list[dict]) -> float:
        """Estimate failure rate from similar historical memories."""
        if not historical_context:
            return 0.0
        similar_failures = 0
        similar_total = 0
        for item in historical_context:
            text = item.get("text", "").lower()
            if task.owner_role in text or task.milestone.lower() in text:
                similar_total += 1
                if item.get("metadata", {}).get("outcome") == "failed":
                    similar_failures += 1
        if not similar_total:
            return 0.0
        return similar_failures / similar_total

    async def _log_decision(self, run_id: str, summary: str, rationale: str, related_task_ids: list[str]) -> None:
        """Persist an audit log decision entry."""
        entry = DecisionLogEntry(
            run_id=run_id,
            summary=summary,
            rationale=rationale,
            related_task_ids=related_task_ids,
        )
        await self.decision_log.append(entry)

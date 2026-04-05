"""Structured planning and replanning logic."""

from __future__ import annotations

import re

from aegis_pm.agents.base import BaseAgent
from aegis_pm.schemas import ExecutionPlan, Milestone, RiskRecord, TaskFactors, TaskNode, ToolAction, IntegrationTarget


DEADLINE_PATTERN = re.compile(r"(\d+)\s*days?", re.IGNORECASE)


class PlannerAgent(BaseAgent):
    """Turn vague goals into structured milestone plans."""

    def __init__(self) -> None:
        """Create the planner agent."""
        super().__init__("planner")

    async def generate_plan(self, project_name: str, goal: str, context: list[dict]) -> ExecutionPlan:
        """Generate a structured plan from a goal and retrieved memory."""
        deadline_days = self._extract_deadline_days(goal)
        assumptions = [
            "Cross-functional team has access to GitHub, Slack, and Jira.",
            "The goal represents an MVP delivery target rather than a full enterprise rollout.",
            "Execution should optimize for early risk discovery and dependency visibility.",
        ]
        milestones = [
            Milestone(
                name="Scope Lock",
                objective="Clarify MVP scope, owners, and success metrics.",
                due_day=max(2, int(deadline_days * 0.10)),
                exit_criteria=[
                    "Goal translated into measurable outcomes",
                    "Initial backlog created",
                    "Communication cadence established",
                ],
            ),
            Milestone(
                name="Architecture and Backlog",
                objective="Design delivery approach and create executable workstreams.",
                due_day=max(4, int(deadline_days * 0.25)),
                exit_criteria=[
                    "Architecture decisions documented",
                    "Task graph validated",
                    "Critical path identified",
                ],
            ),
            Milestone(
                name="Core Build",
                objective="Deliver the highest-value product capabilities.",
                due_day=max(8, int(deadline_days * 0.65)),
                exit_criteria=[
                    "Core features implemented",
                    "Delivery progress visible in tooling",
                    "Major blockers mitigated",
                ],
            ),
            Milestone(
                name="Quality Gate",
                objective="Validate readiness through QA and risk review.",
                due_day=max(10, int(deadline_days * 0.85)),
                exit_criteria=[
                    "Test coverage defined",
                    "Regression and launch risks assessed",
                    "Open defects triaged",
                ],
            ),
            Milestone(
                name="Launch Readiness",
                objective="Prepare stakeholders for release and next-step execution.",
                due_day=deadline_days,
                exit_criteria=[
                    "Stakeholder report generated",
                    "Open risks documented",
                    "Next sprint recommendations published",
                ],
            ),
        ]
        strategy = (
            "Execute in milestone waves, prioritize tasks that unlock downstream work, "
            "surface operational risks early, and keep all delivery artifacts synchronized "
            "across GitHub, Jira, and Slack."
        )
        retrieved_context = [item["text"] for item in context]
        return ExecutionPlan(
            goal=goal,
            project_name=project_name,
            deadline_days=deadline_days,
            strategy=strategy,
            milestones=milestones,
            assumptions=assumptions,
            retrieved_context=retrieved_context,
        )

    async def replan(self, risks: list[RiskRecord], existing_tasks: dict[str, TaskNode]) -> list[TaskNode]:
        """Create mitigation tasks that alter the graph after failures or high-risk findings."""
        mitigation_tasks: list[TaskNode] = []
        for risk in risks:
            if risk.title != "Task execution failed":
                continue
            if not risk.task_id or risk.task_id not in existing_tasks:
                continue
            if existing_tasks[risk.task_id].metadata.get("replan_for"):
                continue
            if any(task.metadata.get("replan_for") == risk.task_id for task in existing_tasks.values()):
                continue
            original = existing_tasks[risk.task_id]
            mitigation_task = TaskNode(
                title=f"Mitigate risk for {original.title}",
                description=(
                    f"Address risk '{risk.title}' by aligning owners, clarifying scope, "
                    f"and creating a recovery path before downstream execution resumes."
                ),
                owner_role="pm",
                milestone="Replanning",
                dependencies=[dependency for dependency in original.dependencies],
                factors=TaskFactors(
                    impact=min(10.0, original.factors.impact + 1.5),
                    effort=max(2.0, original.factors.effort - 1.0),
                    urgency=10.0,
                    risk=9.0,
                    dependency_weight=9.0,
                ),
                actions=[
                    ToolAction(
                        target=IntegrationTarget.slack,
                        operation="post_message",
                        params={
                            "text": (
                                f"Replanning required for task '{original.title}'. "
                                f"Mitigation: {risk.mitigation}"
                            )
                        },
                    ),
                    ToolAction(
                        target=IntegrationTarget.jira,
                        operation="create_issue",
                        params={
                            "summary": f"Mitigation task: {original.title}",
                            "description": risk.mitigation,
                            "issue_type": "Task",
                        },
                    ),
                ],
                acceptance_criteria=[
                    "Mitigation path recorded in Jira",
                    "Stakeholders notified in Slack",
                    "Downstream tasks repointed to the mitigation task",
                ],
                metadata={"replan_for": original.task_id, "risk_id": risk.risk_id},
            )
            mitigation_tasks.append(mitigation_task)
        return mitigation_tasks

    def _extract_deadline_days(self, goal: str) -> int:
        """Extract the deadline from the goal or fall back to 30 days."""
        match = DEADLINE_PATTERN.search(goal)
        if not match:
            return 30
        return max(7, int(match.group(1)))

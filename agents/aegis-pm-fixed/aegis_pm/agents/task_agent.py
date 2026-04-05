"""Task decomposition logic for milestone plans."""

from __future__ import annotations

from aegis_pm.agents.base import BaseAgent
from aegis_pm.schemas import ExecutionPlan, IntegrationTarget, TaskFactors, TaskNode, ToolAction


class TaskAgent(BaseAgent):
    """Decompose a plan into a dependency-aware execution graph."""

    def __init__(self) -> None:
        """Create the task agent."""
        super().__init__("task")

    async def decompose(self, plan: ExecutionPlan) -> list[TaskNode]:
        """Create a task DAG from an execution plan."""
        project = plan.project_name
        goal = plan.goal
        task_scope = TaskNode(
            title="Lock MVP scope and success metrics",
            description=f"Translate '{goal}' into measurable scope, owners, and acceptance criteria.",
            owner_role="pm",
            milestone="Scope Lock",
            factors=TaskFactors(impact=9, effort=3, urgency=10, risk=7, dependency_weight=10),
            actions=[
                ToolAction(
                    target=IntegrationTarget.slack,
                    operation="post_message",
                    params={"text": f"[{project}] Kickoff: aligning MVP scope and metrics for goal '{goal}'."},
                ),
                ToolAction(
                    target=IntegrationTarget.jira,
                    operation="create_issue",
                    params={
                        "summary": f"{project}: Define MVP scope",
                        "description": f"Create measurable scope and success metrics for goal: {goal}",
                        "issue_type": "Epic",
                    },
                ),
            ],
            acceptance_criteria=[
                "Scope definition shared",
                "Initial Jira epic created",
                "Stakeholders informed",
            ],
        )
        task_backlog = TaskNode(
            title="Design delivery architecture and backlog",
            description="Create system architecture decisions and a ranked backlog aligned to the goal.",
            owner_role="planner",
            milestone="Architecture and Backlog",
            dependencies=[task_scope.task_id],
            factors=TaskFactors(impact=9, effort=5, urgency=9, risk=8, dependency_weight=9),
            actions=[
                ToolAction(
                    target=IntegrationTarget.github,
                    operation="create_issue",
                    params={
                        "title": f"{project}: Architecture and backlog definition",
                        "body": "Document architecture choices, milestone breakdown, and ranked backlog.",
                        "labels": ["planning", "critical-path"],
                    },
                ),
                ToolAction(
                    target=IntegrationTarget.jira,
                    operation="create_issue",
                    params={
                        "summary": f"{project}: Backlog orchestration",
                        "description": "Create a ranked backlog with dependencies and execution owners.",
                        "issue_type": "Task",
                    },
                ),
            ],
            acceptance_criteria=[
                "Architecture ticket opened",
                "Backlog created in Jira",
                "Critical path documented",
            ],
        )
        task_ops = TaskNode(
            title="Establish delivery operating cadence",
            description="Set up communication rhythm, reporting expectations, and escalation pathways.",
            owner_role="pm",
            milestone="Architecture and Backlog",
            dependencies=[task_scope.task_id],
            factors=TaskFactors(impact=7, effort=2, urgency=8, risk=5, dependency_weight=7),
            actions=[
                ToolAction(
                    target=IntegrationTarget.slack,
                    operation="post_message",
                    params={"text": f"[{project}] Delivery cadence created: daily checkpoint, weekly risk review."},
                ),
                ToolAction(
                    target=IntegrationTarget.jira,
                    operation="create_issue",
                    params={
                        "summary": f"{project}: Delivery cadence",
                        "description": "Document daily checkpoint and escalation path for the execution loop.",
                        "issue_type": "Task",
                    },
                ),
            ],
            acceptance_criteria=[
                "Cadence shared",
                "Escalation owner defined",
                "Stakeholder update path documented",
            ],
        )
        task_build_core = TaskNode(
            title="Deliver core product capability",
            description="Execute the highest-value implementation work for the MVP core experience.",
            owner_role="dev",
            milestone="Core Build",
            dependencies=[task_backlog.task_id, task_ops.task_id],
            factors=TaskFactors(impact=10, effort=8, urgency=9, risk=8, dependency_weight=10),
            actions=[
                ToolAction(
                    target=IntegrationTarget.github,
                    operation="create_issue",
                    params={
                        "title": f"{project}: Build core capability",
                        "body": "Implement the highest-value product capability on the critical path.",
                        "labels": ["development", "mvp"],
                    },
                ),
                ToolAction(
                    target=IntegrationTarget.jira,
                    operation="create_issue",
                    params={
                        "summary": f"{project}: Core implementation",
                        "description": "Track development of the highest-value MVP capability.",
                        "issue_type": "Story",
                    },
                ),
            ],
            acceptance_criteria=[
                "Development issue created",
                "Jira story opened",
                "Implementation path visible",
            ],
        )
        task_build_support = TaskNode(
            title="Deliver supporting product capability",
            description="Implement the secondary capability required for a coherent MVP launch.",
            owner_role="dev",
            milestone="Core Build",
            dependencies=[task_backlog.task_id],
            factors=TaskFactors(impact=8, effort=6, urgency=8, risk=7, dependency_weight=8),
            actions=[
                ToolAction(
                    target=IntegrationTarget.github,
                    operation="create_issue",
                    params={
                        "title": f"{project}: Build supporting capability",
                        "body": "Implement the supporting workflow required for a usable MVP.",
                        "labels": ["development", "supporting-work"],
                    },
                ),
                ToolAction(
                    target=IntegrationTarget.jira,
                    operation="create_issue",
                    params={
                        "summary": f"{project}: Supporting implementation",
                        "description": "Track development of the supporting MVP capability.",
                        "issue_type": "Story",
                    },
                ),
            ],
            acceptance_criteria=[
                "Secondary delivery issue created",
                "Supporting Jira story opened",
                "Dependencies made visible",
            ],
        )
        task_qa_strategy = TaskNode(
            title="Define QA strategy and launch checks",
            description="Create test strategy, release criteria, and regression checklist.",
            owner_role="qa",
            milestone="Quality Gate",
            dependencies=[task_backlog.task_id],
            factors=TaskFactors(impact=8, effort=3, urgency=7, risk=8, dependency_weight=7),
            actions=[
                ToolAction(
                    target=IntegrationTarget.jira,
                    operation="create_issue",
                    params={
                        "summary": f"{project}: QA strategy",
                        "description": "Define QA scope, test approach, and launch checks.",
                        "issue_type": "Task",
                    },
                ),
                ToolAction(
                    target=IntegrationTarget.slack,
                    operation="post_message",
                    params={"text": f"[{project}] QA strategy task opened with launch readiness checks."},
                ),
            ],
            acceptance_criteria=[
                "QA scope agreed",
                "Regression checklist captured",
                "Release criteria documented",
            ],
        )
        task_validation = TaskNode(
            title="Run integration validation and risk review",
            description="Validate the product against release criteria and capture blocking risk.",
            owner_role="qa",
            milestone="Quality Gate",
            dependencies=[task_build_core.task_id, task_build_support.task_id, task_qa_strategy.task_id],
            factors=TaskFactors(impact=9, effort=5, urgency=9, risk=9, dependency_weight=9),
            actions=[
                ToolAction(
                    target=IntegrationTarget.jira,
                    operation="create_issue",
                    params={
                        "summary": f"{project}: Integration validation",
                        "description": "Run validation, capture blockers, and record risk posture.",
                        "issue_type": "Bug",
                    },
                ),
                ToolAction(
                    target=IntegrationTarget.slack,
                    operation="post_message",
                    params={"text": f"[{project}] Integration validation wave is starting."},
                ),
            ],
            acceptance_criteria=[
                "Validation issue created",
                "Risk posture announced",
                "Blocking defects captured",
            ],
        )
        task_report = TaskNode(
            title="Publish stakeholder execution report",
            description="Generate founder-level summary, remaining risks, and the next action list.",
            owner_role="reporter",
            milestone="Launch Readiness",
            dependencies=[task_validation.task_id],
            factors=TaskFactors(impact=8, effort=2, urgency=10, risk=5, dependency_weight=8),
            actions=[
                ToolAction(
                    target=IntegrationTarget.slack,
                    operation="post_message",
                    params={"text": f"[{project}] Final execution summary will be published after validation."},
                )
            ],
            acceptance_criteria=[
                "Stakeholder report generated",
                "Risks summarized",
                "Next actions proposed",
            ],
        )
        return [
            task_scope,
            task_backlog,
            task_ops,
            task_build_core,
            task_build_support,
            task_qa_strategy,
            task_validation,
            task_report,
        ]

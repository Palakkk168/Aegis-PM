"""Planner ADK agent."""

from __future__ import annotations

from datetime import timedelta

from google.adk.runners import Runner
from pydantic import BaseModel, Field

from agents.base_agent import BaseAegisAgent
from core.schemas import Goal, Milestone, Plan, TaskGraph
from tools.memory_tools import log_decision_tool, retrieve_context_tool


class PlannerOutput(BaseModel):
    """Structured output for the planner."""

    milestones: list[dict] = Field(default_factory=list)


class PlannerAgent(BaseAegisAgent):
    """Converts goals into milestone plans."""

    def __init__(self) -> None:
        """Initialize the planner agent."""
        super().__init__(
            name="planner_agent",
            model="gemini-2.0-flash",
            description="Converts goals into structured milestone plans",
            instruction=(
                "You are a planning agent. Output strict JSON with a 'milestones' array. "
                "Each milestone must include name, description, deadline, and task_ids."
            ),
            tools=[retrieve_context_tool, log_decision_tool],
        )

    async def generate_plan(self, runner: Runner, goal: Goal, context: list[str]) -> Plan:
        """Generate a milestone plan from a goal."""
        prompt = (
            "Create a milestone plan for this goal.\n"
            f"Goal: {goal.raw_input}\n"
            f"Deadline: {goal.deadline.isoformat()}\n"
            f"Relevant context: {context}\n"
            "Return JSON only."
        )
        try:
            response = await self.run_structured(
                runner,
                user_id=goal.user_id,
                session_id=goal.project_id,
                prompt=prompt,
                schema=PlannerOutput,
            )
            milestones = [
                Milestone(
                    name=item["name"],
                    description=item["description"],
                    deadline=item["deadline"],
                    task_ids=item.get("task_ids", []),
                )
                for item in response.milestones
            ]
        except Exception:
            milestones = self._fallback_milestones(goal)
        return Plan(milestones=milestones, task_graph=TaskGraph())

    async def replan(self, runner: Runner, state_json: str, risk_report_json: str, goal: Goal) -> Plan:
        """Generate a revised plan after risk escalation."""
        prompt = (
            "Replan this project based on the current state and risk report.\n"
            f"State: {state_json}\n"
            f"Risk report: {risk_report_json}\n"
            "Return JSON only."
        )
        try:
            response = await self.run_structured(
                runner,
                user_id=goal.user_id,
                session_id=goal.project_id,
                prompt=prompt,
                schema=PlannerOutput,
            )
            milestones = [
                Milestone(
                    name=item["name"],
                    description=item["description"],
                    deadline=item["deadline"],
                    task_ids=item.get("task_ids", []),
                )
                for item in response.milestones
            ]
        except Exception:
            milestones = self._fallback_milestones(goal)
        return Plan(milestones=milestones, task_graph=TaskGraph())

    def _fallback_milestones(self, goal: Goal) -> list[Milestone]:
        """Create deterministic milestones when the model is unavailable."""
        return [
            Milestone(name="Scope Lock", description="Define MVP scope and success metrics.", deadline=goal.deadline - timedelta(days=24)),
            Milestone(name="Backlog Build", description="Create backlog and delivery sequencing.", deadline=goal.deadline - timedelta(days=18)),
            Milestone(name="Core Execution", description="Execute the highest-impact delivery tasks.", deadline=goal.deadline - timedelta(days=8)),
            Milestone(name="Quality Gate", description="Validate quality, operational readiness, and launch risk.", deadline=goal.deadline - timedelta(days=3)),
            Milestone(name="Launch Report", description="Prepare stakeholder report and next actions.", deadline=goal.deadline),
        ]

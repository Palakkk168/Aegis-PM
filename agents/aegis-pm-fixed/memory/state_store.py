"""Redis-backed project state storage."""

from __future__ import annotations

import json
import networkx as nx

from datetime import UTC, datetime

from redis.asyncio import Redis

from config import get_settings
from core.schemas import Plan, ProjectState, Task, TaskGraph, TaskStatus


class StateStore:
    """Persist structured execution state in Redis."""

    def __init__(self) -> None:
        """Create the async Redis client."""
        settings = get_settings()
        self.ttl_seconds = settings.state_ttl_seconds
        self.redis = Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)

    async def save_state(self, project_id: str, state: ProjectState) -> None:
        """Save or replace the full project state."""
        await self.redis.set(
            f"project:{project_id}",
            json.dumps(self._state_to_dict(state), default=str),
            ex=self.ttl_seconds,
        )

    async def load_state(self, project_id: str) -> ProjectState | None:
        """Load a project state from Redis."""
        payload = await self.redis.get(f"project:{project_id}")
        if payload is None:
            return None
        return self._state_from_dict(json.loads(payload))

    async def update_task_status(self, project_id: str, task_id: str, status: TaskStatus) -> ProjectState | None:
        """Update a task status and persist the state."""
        state = await self.load_state(project_id)
        if state is None or state.plan is None:
            return state
        state.plan.task_graph.tasks[task_id].status = status
        if status == TaskStatus.COMPLETE and task_id not in state.completed:
            state.completed.append(task_id)
        if status == TaskStatus.FAILED and task_id not in state.failed:
            state.failed.append(task_id)
        state.updated_at = datetime.now(UTC)
        await self.save_state(project_id, state)
        return state

    async def set_paused(self, project_id: str, paused: bool) -> ProjectState | None:
        """Pause or resume a project."""
        state = await self.load_state(project_id)
        if state is None:
            return None
        state.paused = paused
        await self.save_state(project_id, state)
        return state

    def _state_to_dict(self, state: ProjectState) -> dict:
        """Serialize project state for Redis storage."""
        payload = state.model_dump(mode="json", exclude={"plan"})
        if state.plan is None:
            payload["plan"] = None
            return payload
        payload["plan"] = {
            "milestones": [milestone.model_dump(mode="json") for milestone in state.plan.milestones],
            "task_graph": {
                "tasks": {task_id: task.model_dump(mode="json") for task_id, task in state.plan.task_graph.tasks.items()},
                "edges": list(state.plan.task_graph.graph.edges()),
            },
            "created_at": state.plan.created_at.isoformat(),
        }
        return payload

    def _state_from_dict(self, payload: dict) -> ProjectState:
        """Deserialize project state from Redis payload."""
        plan_payload = payload.get("plan")
        if plan_payload is None:
            return ProjectState.model_validate(payload)
        graph = nx.DiGraph()
        for task_id, task_payload in plan_payload["task_graph"]["tasks"].items():
            graph.add_node(task_id)
        graph.add_edges_from(plan_payload["task_graph"]["edges"])
        task_graph = TaskGraph(
            graph=graph,
            tasks={task_id: Task.model_validate(task_payload) for task_id, task_payload in plan_payload["task_graph"]["tasks"].items()},
        )
        payload["plan"] = Plan.model_validate(
            {
                "milestones": plan_payload["milestones"],
                "task_graph": task_graph,
                "created_at": plan_payload["created_at"],
            }
        )
        return ProjectState.model_validate(payload)

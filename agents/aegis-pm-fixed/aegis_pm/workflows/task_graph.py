"""Task graph management for DAG-based execution."""

from __future__ import annotations

from collections import defaultdict, deque

from aegis_pm.schemas import TaskNode, TaskStatus


class TaskGraphManager:
    """Manage a task DAG and dependency-safe task retrieval."""

    def __init__(self, tasks: list[TaskNode]) -> None:
        """Initialize the manager and validate the graph."""
        self.tasks = {task.task_id: task for task in tasks}
        self._validate()

    def _validate(self) -> None:
        """Validate references and ensure the graph is acyclic."""
        indegree = {task_id: 0 for task_id in self.tasks}
        adjacency: dict[str, list[str]] = defaultdict(list)
        for task in self.tasks.values():
            for dependency in task.dependencies:
                if dependency not in self.tasks:
                    raise ValueError(f"Unknown dependency {dependency} for task {task.task_id}")
                adjacency[dependency].append(task.task_id)
                indegree[task.task_id] += 1
        queue = deque([task_id for task_id, value in indegree.items() if value == 0])
        visited = 0
        while queue:
            current = queue.popleft()
            visited += 1
            for child in adjacency[current]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)
        if visited != len(self.tasks):
            raise ValueError("Task graph must be acyclic")

    def ready_tasks(self) -> list[TaskNode]:
        """Return tasks whose dependencies have completed."""
        completed = {
            task_id
            for task_id, task in self.tasks.items()
            if task.status == TaskStatus.completed
        }
        ready: list[TaskNode] = []
        for task in self.tasks.values():
            if task.status not in {TaskStatus.pending, TaskStatus.ready, TaskStatus.blocked}:
                continue
            if all(dependency in completed for dependency in task.dependencies):
                task.status = TaskStatus.ready
                ready.append(task)
            elif any(self.tasks[dependency].status == TaskStatus.failed for dependency in task.dependencies):
                task.status = TaskStatus.blocked
        return ready

    def downstream_unlock_count(self, task_id: str) -> int:
        """Count tasks that depend directly on a task."""
        return sum(task_id in task.dependencies for task in self.tasks.values())

    def add_tasks(self, tasks: list[TaskNode]) -> None:
        """Add new tasks to the graph and revalidate the DAG."""
        for task in tasks:
            self.tasks[task.task_id] = task
        self._validate()

    def is_complete(self) -> bool:
        """Return whether all tasks have reached a terminal success state."""
        return all(task.status in {TaskStatus.completed, TaskStatus.skipped} for task in self.tasks.values())

    def has_failed_path(self) -> bool:
        """Return whether any task has failed."""
        return any(task.status == TaskStatus.failed for task in self.tasks.values())

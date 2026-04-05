"""DAG engine for task orchestration."""

from __future__ import annotations

from collections import deque

import networkx as nx

from core.schemas import Task, TaskGraph, TaskStatus


class CyclicDependencyError(ValueError):
    """Raised when the DAG contains one or more cycles."""


class DAGEngine:
    """Manage task graphs and dependency-safe execution state."""

    def __init__(self, task_graph: TaskGraph | None = None) -> None:
        """Initialize the engine with an optional graph."""
        self.task_graph = task_graph or TaskGraph()

    def add_task(self, task: Task) -> None:
        """Add a task and its dependency edges."""
        self.task_graph.tasks[task.id] = task
        self.task_graph.graph.add_node(task.id)
        for dependency in task.dependencies:
            self.task_graph.graph.add_edge(dependency, task.id)
        self.detect_cycles()

    def insert_task(self, task: Task) -> None:
        """Insert a task during execution and revalidate the graph."""
        self.add_task(task)

    def get_executable_tasks(self) -> list[Task]:
        """Return tasks whose dependencies are complete and status is ready."""
        executable: list[Task] = []
        for task in self.task_graph.tasks.values():
            if task.status not in {TaskStatus.PENDING, TaskStatus.READY}:
                continue
            predecessors = list(self.task_graph.graph.predecessors(task.id))
            if all(self.task_graph.tasks[pred].status == TaskStatus.COMPLETE for pred in predecessors):
                task.status = TaskStatus.READY
                executable.append(task)
        return executable

    def mark_complete(self, task_id: str) -> None:
        """Mark a task as complete."""
        self.task_graph.tasks[task_id].status = TaskStatus.COMPLETE

    def mark_failed(self, task_id: str) -> None:
        """Mark a task as failed."""
        self.task_graph.tasks[task_id].status = TaskStatus.FAILED

    def detect_cycles(self) -> list[list[str]]:
        """Detect all cycles and raise if any exist."""
        cycles = list(nx.simple_cycles(self.task_graph.graph))
        if cycles:
            raise CyclicDependencyError(f"Detected cycles: {cycles}")
        return cycles

    def topological_sort(self) -> list[str]:
        """Return a Kahn topological sort of the current graph."""
        indegree = {node: 0 for node in self.task_graph.graph.nodes}
        for source, target in self.task_graph.graph.edges:
            indegree[target] += 1
        queue = deque(node for node, degree in indegree.items() if degree == 0)
        ordered: list[str] = []
        while queue:
            current = queue.popleft()
            ordered.append(current)
            for neighbor in self.task_graph.graph.successors(current):
                indegree[neighbor] -= 1
                if indegree[neighbor] == 0:
                    queue.append(neighbor)
        if len(ordered) != len(indegree):
            raise CyclicDependencyError("Topological sort failed because a cycle exists")
        return ordered

    def get_critical_path(self) -> list[Task]:
        """Return the longest dependency chain in the DAG."""
        ordered = self.topological_sort()
        distances = {node: 0 for node in ordered}
        parents: dict[str, str | None] = {node: None for node in ordered}
        for node in ordered:
            for successor in self.task_graph.graph.successors(node):
                if distances[node] + 1 > distances[successor]:
                    distances[successor] = distances[node] + 1
                    parents[successor] = node
        end_node = max(distances, key=distances.get, default=None)
        if end_node is None:
            return []
        path: list[str] = []
        cursor: str | None = end_node
        while cursor is not None:
            path.append(cursor)
            cursor = parents[cursor]
        path.reverse()
        return [self.task_graph.tasks[task_id] for task_id in path]

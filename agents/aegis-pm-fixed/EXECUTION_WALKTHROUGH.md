# Example Walkthrough

Goal: `Launch AI SaaS in 30 days`

## Stage 1: Memory Retrieval
- `retrieve_context` looks up similar historical launches in ChromaDB under the current `project_id`
- Retrieved snippets are passed into `PlannerAgent.generate_plan`

## Stage 2: Plan Generation
- Planner produces milestones such as Scope Lock, Backlog Build, Core Execution, Quality Gate, and Launch Report
- The plan is persisted into Redis state

## Stage 3: Task Graph
- TaskAgent decomposes milestones into atomic tasks with explicit dependency IDs
- DAGEngine inserts nodes and edges, validates cycles, and exposes executable tasks

## Stage 4: Prioritization
- `core/decision_engine.py` scores ready tasks using impact, urgency, effort, and risk
- Highest scoring tasks are selected for the current execution wave

## Stage 5: Execution
- Tool payloads dispatch to:
  - GitHub issue creation
  - GitHub branch creation
  - Jira ticket creation or transitions
  - Slack updates and reports

## Stage 6: Risk Detection
- RiskAgent computes:
  - `complexity * 0.4`
  - `dependency_load * 0.3`
  - `historical_failure_rate * 0.3`
- If the project crosses the configured threshold, the replan engine triggers

## Stage 7: Replanning
- ReplanEngine inserts mitigation tasks into the DAG
- Downstream dependencies are rewired through mitigation work
- `replan_count` increments in project state and metrics

## Stage 8: Final Report
- ReporterAgent summarizes completion, blocked tasks, decision history, and next actions
- Optional Slack delivery sends the final report to an exec channel

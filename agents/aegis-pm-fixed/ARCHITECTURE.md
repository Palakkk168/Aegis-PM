# Aegis PM Architecture

## Layers

### Interface Layer
- FastAPI routes in `api/routes.py`
- Request correlation and error middleware in `api/middleware.py`

### Cognitive Layer
- `agents/pm_agent.py` as the root ADK orchestrator
- `agents/planner_agent.py` for milestone plans
- `agents/task_agent.py` for task DAG generation
- `agents/risk_agent.py` for deterministic risk scoring
- `agents/reporter_agent.py` for stakeholder reports

### Execution Layer
- `tools/github_tool.py`
- `tools/jira_tool.py`
- `tools/slack_tool.py`
- All tool functions are wrapped as ADK `FunctionTool`s

### Memory Layer
- `memory/vector_memory.py` for ChromaDB recall
- `memory/state_store.py` for Redis project state
- `memory/decision_log.py` for Postgres decision history
- `tools/memory_tools.py` exposes memory/logging as ADK tools

### Orchestration Layer
- `core/dag.py` for DAG management
- `core/decision_engine.py` for prioritization
- `workflows/execution_loop.py` for controller logic
- `workflows/replan_engine.py` for dynamic mitigation tasks
- `workflows/retry_manager.py` for retries and circuit breaking

## Execution Flow
1. Goal enters through `POST /projects`
2. Execution loop creates ADK session state
3. PlannerAgent generates milestones
4. TaskAgent generates a DAG
5. Decision engine prioritizes executable tasks
6. Tool actions execute against GitHub, Jira, or Slack
7. RiskAgent scores live state
8. ReplanEngine inserts mitigation tasks when risk crosses threshold
9. ReporterAgent generates the final report

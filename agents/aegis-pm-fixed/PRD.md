# Aegis PM PRD

## Vision
Aegis PM is an autonomous AI Project Manager built on Google ADK that converts ambiguous goals into executable plans, orchestrates delivery across human and AI teammates, predicts risk early, and dynamically replans when execution drifts.

## Users
- Startup founders moving from zero to product-market fit
- AI-native product and engineering teams
- Agencies managing multi-client delivery

## Core Outcomes
- Goal to milestone plan
- Task DAG generation with explicit dependencies
- Real execution through GitHub, Jira, and Slack
- Continuous risk prediction and dynamic replanning
- Persistent project memory, structured state, and decision logs
- Executive-ready reporting

## Functional Scope
- Natural-language goal intake
- Milestone and DAG generation
- Task prioritization with weighted scoring
- Async task execution with retries and circuit breaking
- ChromaDB memory retrieval
- Redis state persistence
- Postgres decision history
- FastAPI interface for project lifecycle control

## Non-Functional Scope
- Async-first Python architecture
- Fault tolerance with retry and circuit breaker controls
- Structured JSON logs with correlation IDs
- Multi-project isolation by `project_id`

## Constraints
- No hallucinated integrations
- No flat task execution
- Must preserve auditability
- Must operate through Google ADK agent primitives

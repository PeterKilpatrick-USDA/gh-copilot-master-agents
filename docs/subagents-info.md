# Multiagent Workflows in `gh-copilot-master-agents`

When working on complex tasks in this application, you can delegate subtasks to **subagents** (also known as a multiagent workflow). A subagent is an independent AI agent that performs focused work—such as researching a topic, analyzing code, or reviewing changes—and reports the results back to the main Orchestrator agent.

## What is it?

A multiagent workflow allows a primary agent to dispatch work to specialized subagents. 
* **Isolated Contexts:** Each subagent operates in its own isolated context window. This prevents the orchestrator from being overwhelmed.
* **Specialization & Parallelism:** Subagents can be specialized for different tasks (e.g., one focuses on architecture, another on security) and can often run in parallel to gather information quickly.

In the context of this repository, you have several specialized personas available in the `personas/` directory, such as:
* `c-sharp-expert`
* `repo-architect`
* `security-reviewer`
* `data-scientist`
* `ui-expert`

## Why Use Subagents Here?

- **Research before implementation**: Have `data-scientist` or `repo-architect` analyze data or codebase patterns before writing code.
- **Parallel code analysis**: Run multiple reviews simultaneously.
- **Code review with specialized focus**: Run `security-reviewer` alongside `c-sharp-expert` to get highly specific feedback.

## How to Coordinate Subagents

Subagents are typically orchestrator-initiated. You don't need to manually type "run a subagent" for every task. To allow a main agent to invoke subagents, you must ensure the `runSubagent` tool is enabled.

### Example Orchestration Pattern

You can use an agent like `queen-bee` as your **Coordinator**. The Coordinator manages the overall task and delegates subtasks to specialized worker agents.

```markdown
---
name: queen-bee
tools: ['runSubagent', 'read', 'search', 'edit']
agents: ['security-reviewer', 'repo-architect', 'c-sharp-expert']
---
You are the primary orchestration agent. For each feature request:

1. Use the `repo-architect` subagent to break down the feature into tasks and evaluate codebase impact.
2. Use the `c-sharp-expert` subagent to write the code for each task.
3. Use the `security-reviewer` subagent to check the implementation for any vulnerabilities.
```

### Controlling Subagent Visibility

You can control how your personas can be invoked using YAML frontmatter properties:

* `user-invocable`: Controls whether the agent appears in the agents dropdown in chat (default is `true`). Set to `false` for agents that are *only* accessible as subagents.
* `disable-model-invocation`: Prevents the agent from being invoked as a subagent by other agents (default is `false`).

For example, if `security-reviewer` should only be called by `queen-bee` and not directly by the user:

```markdown
---
name: security-reviewer
user-invocable: false
disable-model-invocation: false
tools: ['read', 'search']
---
Review code for security vulnerabilities...
```

## Next Steps for This App

To fully incorporate this into `gh-copilot-master-agents`:
1. Ensure deployment scripts correctly process and register subagent dependencies.
2. Designate or create an orchestrator agent (e.g., `queen-bee`).
3. Update the frontmatter of your existing personas to include `user-invocable: false` if they are meant to be pure subagents.

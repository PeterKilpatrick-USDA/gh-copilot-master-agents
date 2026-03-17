# gh-copilot-master-agents

**⚠️ WORK IN PROGRESS (WIP)**

This repository serves as the master list of NASS agent personas for use in VS Code with GitHub Copilot. It centralizes custom instructions, roles, and guidelines for different AI personas (e.g., C# Expert, Data Scientist, Security Reviewer). 

## What This Repo Does
- Stores and maintains `.agent.md` files in the `personas/` directory under in this repo.
- Acts as a master template collection for specialized AI assistants within the organization.

## To Use
This repository includes a Python deployment script (`deploy_agents.py`) featuring a Tkinter GUI to easily manage and distribute these agents. 

Run the script using Python:
\`\`\`bash
python deploy_agents.py
\`\`\`


### Features of the Script:
1. **Target Selection**: Select which sibling repositories on your local machine should receive the agent files.
2. **Agent Selection**: Choose specific `.agent.md` files to copy from the `personas/` folder.
3. **Preview**: Review your selected deployment configuration before submitting.
4. **Automated Directory Creation**: Automatically creates the required `.github/personas/` directory structure under the target repositories.
5. **Smart Copying**: Copies the agent files to the selected targets, automatically skipping files in the destination that are already newer.
6. **Logging**: All operations are timestamped and recorded in the local `logs/` directory.

## Agent Template: `agent-template.agent.md`

This file provides a starting point for creating your own custom agent personas. To use it:
- Review the template and fill in the mission, behavior, and boundaries for your agent.
- Select the tools your agent should have access to by editing the `tools:` section. Remove any tools that are not relevant to your agent's role.
- Save your customized agent file and deploy it as needed.

### Available Tools
Below are the tools you can enable for your agent, with a brief description of each:

- **changes**: View and summarize recent changes in the codebase (e.g., git diffs).
- **edit**: Make direct edits to files in the workspace.
- **extensions**: Manage VS Code extensions (search, install, etc.).
- **fetch**: Retrieve and summarize content from web pages.
- **githubRepo**: Search for code snippets in public GitHub repositories.
- **new**: Create new files or directories in the workspace.
- **openSimpleBrowser**: Open a URL in the VS Code Simple Browser.
- **problems**: List and summarize problems or errors in the codebase (e.g., lint or compile errors).
- **runCommands**: Run shell or terminal commands in the workspace.
- **runNotebooks**: Execute code cells in Jupyter Notebooks.
- **runSubagent**: Launch a sub-agent to handle complex or multi-step tasks.
- **runTasks**: Create and run VS Code tasks (e.g., build, run, test tasks).
- **runTests**: Run unit tests and report results.
- **search**: Search for text or code patterns in the workspace.
- **testFailure**: Retrieve and summarize test failure information.
- **todos**: Manage a structured to-do list for tracking progress.
- **usages**: List all usages or references of a symbol (function, class, etc.) in the codebase.
- **vscodeAPI**: Access VS Code extension API documentation and references.

#### Python-Specific Tools
- **ms-python.python/configurePythonEnvironment**: Set up a Python environment for the workspace or a specific file.
- **ms-python.python/getPythonEnvironmentInfo**: Retrieve details about the current Python environment (type, version, installed packages).
- **ms-python.python/getPythonExecutableCommand**: Get the command needed to run Python in the current environment.
- **ms-python.python/installPythonPackage**: Install Python packages into the selected environment.

> **Tip:** Review the template and create your own agent that others can use!

## Worth Exploring
Organization level: Placing agent files like /agents/CUSTOM-AGENT-NAME.md inside a .github-private repository makes them automatically available across the entire organization. This is a great alternative to copying them manually into every single repository.

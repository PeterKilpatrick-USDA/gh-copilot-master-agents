# gh-copilot-master-agents

**⚠️ WORK IN PROGRESS (WIP)**

This repository serves as the master list of NASS agent personas for use in VS Code with GitHub Copilot. It centralizes custom instructions, roles, and guidelines for different AI personas (e.g., C# Expert, Data Scientist, Security Reviewer). 

## What This Repo Does
- Stores and maintains single-source-of-truth Copilot `.agent.md` files in the `personas/` directory under `gh-copilot-master-agents`.
- Acts as a master template collection for specialized AI assistants within the organization.

## `deploy_agents.py`
This repository includes a Python deployment script (`deploy_agents.py`) featuring a Tkinter GUI to easily manage and distribute these agents. 

### Features of the Script:
1. **Target Selection**: Select which sibling repositories on your local machine should receive the agent files.
2. **Agent Selection**: Choose specific `.agent.md` files to copy from the `personas/` folder.
3. **Preview**: Review your selected deployment configuration before submitting.
4. **Automated Directory Creation**: Automatically creates the required `.github/personas/` directory structure under the target repositories.
5. **Smart Copying**: Copies the agent files to the selected targets, automatically skipping files in the destination that are already newer.
6. **Logging**: All operations are timestamped and recorded in the local `logs/` directory.

### Usage
Run the script using Python:
\`\`\`bash
python deploy_agents.py
\`\`\`

## Worth Exploring
**Organization level:** Placing agent files like `/agents/CUSTOM-AGENT-NAME.md` inside a `.github-private` repository makes them automatically available across the entire organization. This is a great alternative to copying them manually into every single repository.
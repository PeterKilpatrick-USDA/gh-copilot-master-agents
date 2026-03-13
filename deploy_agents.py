#!/usr/bin/env python3
"""
deploy_agents.py - Deploy GitHub Copilot agent files to selected repositories.

This script provides a Tkinter GUI that allows you to:
  1. Select which sibling repositories should receive agent files.
  2. Select which agent (.agent.md) files to copy from the personas/ folder.
  3. Preview your selection before submitting.
  4. Automatically create .github/agents/ directories in target repos as needed.
  5. Copy agents, skipping destination files that are already newer.

All operations are logged with timestamps to the logs/ directory.

Agent files live in the personas/ folder of THIS repository.
They are deployed into the .github/personas/ folder of each target repository.

Usage:
    python deploy_agents.py
"""

import logging
import os
import shutil
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logging(script_dir: Path) -> logging.Logger:
    """Configure timestamped logging to both a log file and the console."""
    log_dir = script_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"deploy_agents_{timestamp}.log"

    logger = logging.getLogger("deploy_agents")
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


# ---------------------------------------------------------------------------
# Discovery helpers
# ---------------------------------------------------------------------------

def get_script_dir() -> Path:
    """Return the absolute directory that contains this script."""
    return Path(__file__).resolve().parent


def find_sibling_repos(script_dir: Path) -> list:
    """
    Return sorted names of sibling directories one level above script_dir.
    Hidden directories (starting with '.') are excluded.
    """
    parent_dir = script_dir.parent
    repos = [
        item.name
        for item in sorted(parent_dir.iterdir())
        if item.is_dir() and item != script_dir and not item.name.startswith(".")
    ]
    return repos


def find_agent_files(script_dir: Path) -> list:
    """
    Discover all *.md files in the personas/ folder and return metadata dicts.

    Agent files are stored here as plain .md files (e.g. "ui-expert.md") to
    satisfy repository path restrictions.  They will be deployed into target
    repos as "<stem>.agent.md" (e.g. "ui-expert.agent.md") which is the
    naming convention expected by GitHub Copilot.

    Each dict contains:
        source_filename  - filename in THIS repo, e.g. "ui-expert.md"
        deploy_filename  - filename written to target repos, e.g. "ui-expert.agent.md"
        stem             - base name, e.g. "ui-expert"
        display_name     - human-friendly label read from frontmatter 'name', e.g. "UI Expert"
        description      - description from frontmatter or first body line
        path             - absolute Path of the source file
    """
    agents_dir = script_dir / "personas"
    agents = []
    if agents_dir.exists():
        for filepath in sorted(agents_dir.glob("*.md")):
            stem = filepath.stem  # e.g. "ui-expert"
            agents.append(
                {
                    "source_filename": filepath.name,
                    "deploy_filename": f"{stem}.agent.md",
                    "stem": stem,
                    "display_name": _extract_display_name(filepath, stem),
                    "description": _extract_description(filepath),
                    "path": filepath,
                }
            )
    return agents


def _stem_to_display_name(stem: str) -> str:
    """Convert a file stem to a human-friendly display name (fallback only).

    Examples:
        "data-scientist"    -> "Data Scientist"
        "security_reviewer" -> "Security Reviewer"
    """
    return stem.replace("-", " ").replace("_", " ").title()


def _parse_frontmatter(filepath: Path) -> dict:
    """Parse YAML frontmatter key/value pairs from a file.

    Returns a dict of lowercased keys -> string values.
    Stops reading at the closing '---' line.
    Returns an empty dict if no frontmatter is present.
    """
    result: dict = {}
    try:
        lines = filepath.read_text(encoding="utf-8").splitlines()
        if not lines or lines[0].strip() != "---":
            return result
        for line in lines[1:]:
            if line.strip() == "---":
                break
            key, sep, value = line.partition(":")
            if sep:
                result[key.strip().lower()] = value.strip().strip("\"'")
    except OSError:
        pass
    return result


def _extract_display_name(filepath: Path, stem: str) -> str:
    """Return the agent's display name.

    Prefers the 'name' field in YAML frontmatter; falls back to converting
    the file stem (e.g. 'ui-expert' -> 'UI Expert' via title-casing).
    """
    fm = _parse_frontmatter(filepath)
    return fm.get("name") or _stem_to_display_name(stem)


def _extract_description(filepath: Path) -> str:
    """Return the agent's description.

    Prefers the 'description' field in YAML frontmatter; falls back to
    the first non-blank, non-heading line in the file body.
    """
    fm = _parse_frontmatter(filepath)
    if fm.get("description"):
        return fm["description"]
    try:
        for line in filepath.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and not stripped.startswith("---"):
                return stripped[:120]
    except OSError:
        pass
    return "No description available."


# ---------------------------------------------------------------------------
# Deployment logic
# ---------------------------------------------------------------------------

def deploy_agents(
    script_dir: Path,
    selected_repos: list,
    selected_agents: list,
    logger: logging.Logger,
    test_mode: bool = False,
) -> list:
    """
    Copy selected agent files into the .github/personas/ folder of each selected
    repository, creating directories as needed.

    Returns a list of human-readable result messages.
    """
    parent_dir = script_dir.parent
    messages = []

    for repo_name in selected_repos:
        repo_path = parent_dir / repo_name
        github_dir = repo_path / ".github"
        agents_dir = github_dir / "agents"

        # Ensure .github/ exists
        if not github_dir.exists():
            msg = f"Would create .github directory for repo '{repo_name}'" if test_mode else f"Created .github directory for repo '{repo_name}'"
            if not test_mode:
                github_dir.mkdir(parents=True, exist_ok=True)
            logger.info(msg)
            messages.append(msg)

        # Ensure .github/agents/ exists
        if not agents_dir.exists():
            msg = f"Would create .github/agents directory for repo '{repo_name}'" if test_mode else f"Created .github/agents directory for repo '{repo_name}'"
            if not test_mode:
                agents_dir.mkdir(parents=True, exist_ok=True)
            logger.info(msg)
            messages.append(msg)

        # Copy each selected agent file
        for agent in selected_agents:
            src: Path = agent["path"]
            dst: Path = agents_dir / agent["deploy_filename"]

            if dst.exists():
                src_mtime = src.stat().st_mtime
                dst_mtime = dst.stat().st_mtime
                if src_mtime > dst_mtime:
                    msg = (
                        f"Would overwrite existing older {agent['deploy_filename']} "
                        f"file for repo '{repo_name}'"
                    ) if test_mode else (
                        f"Overwrote existing older {agent['deploy_filename']} "
                        f"file for repo '{repo_name}'"
                    )
                    if not test_mode:
                        shutil.copy2(src, dst)
                else:
                    msg = (
                        f"Would not overwrite newer {agent['deploy_filename']} "
                        f"file for repo '{repo_name}'"
                    ) if test_mode else (
                        f"Did not overwrite newer {agent['deploy_filename']} "
                        f"file for repo '{repo_name}'"
                    )
            else:
                msg = f"Would copy {agent['deploy_filename']} to repo '{repo_name}'" if test_mode else f"Copied {agent['deploy_filename']} to repo '{repo_name}'"
                if not test_mode:
                    shutil.copy2(src, dst)

            logger.info(msg)
            messages.append(msg)

    return messages


# ---------------------------------------------------------------------------
# Tkinter GUI
# ---------------------------------------------------------------------------

class DeployAgentsApp(tk.Tk):
    """Single-screen Tkinter application for deploying agent files."""

    _TITLE_FONT = ("TkDefaultFont", 13, "bold")
    _DESC_COLOR = "gray"
    _WRAP_PX = 270

    def __init__(
        self,
        script_dir: Path,
        repos: list,
        agents: list,
        logger: logging.Logger,
        test_mode: bool = False,
    ):
        super().__init__()
        self.script_dir = script_dir
        self.all_repos = repos
        self.all_agents = agents
        self.logger = logger
        self.test_mode = test_mode

        self.title("Deploy GitHub Copilot Agents")
        self.resizable(True, True)
        self.minsize(720, 540)

        self._build_ui()
        self._update_preview()
        self._center_window()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        main = ttk.Frame(self, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        # ---- Title ----
        ttk.Label(
            main,
            text="Deploy GitHub Copilot Agent Files",
            font=self._TITLE_FONT,
        ).pack(pady=(0, 10))

        # ---- Two-column selection area ----
        cols = ttk.Frame(main)
        cols.pack(fill=tk.BOTH, expand=True)
        cols.columnconfigure(0, weight=1)
        cols.columnconfigure(1, weight=1)

        self._build_repo_panel(cols)
        self._build_agent_panel(cols)

        # ---- "You Selected" preview ----
        preview_frame = ttk.LabelFrame(main, text="You Selected", padding=6)
        preview_frame.pack(fill=tk.X, pady=(10, 6))

        self.preview_var = tk.StringVar(value="Nothing selected yet.")
        ttk.Label(
            preview_frame,
            textvariable=self.preview_var,
            wraplength=680,
            justify=tk.LEFT,
        ).pack(anchor="w")

        # ---- Action buttons ----
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(
            side=tk.RIGHT, padx=(5, 0)
        )
        self.submit_btn = ttk.Button(
            btn_frame, text="Submit", command=self._on_submit
        )
        self.submit_btn.pack(side=tk.RIGHT)

    def _build_repo_panel(self, parent):
        import os
        frame = ttk.LabelFrame(parent, text="Repositories", padding=6)
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        # Show local repo root path and make it clickable
        local_root = str(self.script_dir.parent)
        label_frame = ttk.Frame(frame)
        label_frame.pack(anchor="w", fill=tk.X)
        # Clickable link-style label for local repo root
        def open_explorer(event=None):
            os.startfile(local_root)
        # Normal label for description
        desc_label = ttk.Label(
            label_frame,
            text="Your Local Repositories - ",
            font=("TkDefaultFont", 9, "bold")
        )
        desc_label.pack(side=tk.LEFT, anchor="w")
        # Clickable link-style label for just the path
        link_label = tk.Label(
            label_frame,
            text=local_root,
            font=("TkDefaultFont", 9, "underline"),
            fg="blue",
            cursor="hand2"
        )
        link_label.pack(side=tk.LEFT, anchor="w")
        link_label.bind("<Button-1>", open_explorer)

        # "ALL" checkbox
        self.all_repos_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frame,
            text="ALL repositories",
            variable=self.all_repos_var,
            command=self._on_all_repos_toggle,
        ).pack(anchor="w")
        ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=4)

        # Scrollable list, but with multi-column support
        outer = ttk.Frame(frame)
        outer.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(outer, height=220, highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas)
        inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.repo_vars: dict = {}

        if not self.all_repos:
            ttk.Label(
                inner,
                text="No sibling repositories found.",
                foreground=self._DESC_COLOR,
            ).grid(row=0, column=0, sticky="w")
        else:
            # Arrange checkboxes in up to 4 columns
            num_cols = min(4, max(1, (len(self.all_repos) + 9) // 10))
            for idx, repo in enumerate(self.all_repos):
                var = tk.BooleanVar(value=False)
                self.repo_vars[repo] = var
                row = idx // num_cols
                col = idx % num_cols
                ttk.Checkbutton(
                    inner,
                    text=repo,
                    variable=var,
                    command=self._update_preview,
                ).grid(row=row, column=col, sticky="w", padx=2, pady=1)

    def _build_agent_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="Agents", padding=6)
        frame.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        # "ALL" checkbox
        self.all_agents_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frame,
            text="ALL agents",
            variable=self.all_agents_var,
            command=self._on_all_agents_toggle,
        ).pack(anchor="w")
        ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=4)

        # Scrollable list
        inner = self._scrollable_inner(frame)
        self.agent_vars: dict = {}

        if not self.all_agents:
            ttk.Label(
                inner,
                text="No agent *.md files found in personas/",
                foreground=self._DESC_COLOR,
            ).pack(anchor="w")
        else:
            for agent in self.all_agents:
                var = tk.BooleanVar(value=False)
                self.agent_vars[agent["source_filename"]] = var

                row = ttk.Frame(inner)
                row.pack(anchor="w", fill=tk.X, pady=(2, 0))

                ttk.Checkbutton(
                    row,
                    text=agent["display_name"],
                    variable=var,
                    command=self._update_preview,
                ).pack(anchor="w")

                if agent["description"]:
                    ttk.Label(
                        row,
                        text=f"    {agent['description']}",
                        foreground=self._DESC_COLOR,
                        wraplength=self._WRAP_PX,
                    ).pack(anchor="w")

    @staticmethod
    def _scrollable_inner(parent) -> ttk.Frame:
        """Create a canvas+scrollbar combo and return the inner Frame."""
        outer = ttk.Frame(parent)
        outer.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(outer, height=220, highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas)

        inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        return inner

    def _center_window(self):
        self.update_idletasks()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        x = max(0, (self.winfo_screenwidth() // 2) - (w // 2))
        y = max(0, (self.winfo_screenheight() // 2) - (h // 2))
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_all_repos_toggle(self):
        checked = self.all_repos_var.get()
        for var in self.repo_vars.values():
            var.set(checked)
        self._update_preview()

    def _on_all_agents_toggle(self):
        checked = self.all_agents_var.get()
        for var in self.agent_vars.values():
            var.set(checked)
        self._update_preview()

    # ------------------------------------------------------------------
    # Selection helpers
    # ------------------------------------------------------------------

    def _get_selected_repos(self) -> list:
        if self.all_repos_var.get():
            return list(self.all_repos)
        return [repo for repo, var in self.repo_vars.items() if var.get()]

    def _get_selected_agents(self) -> list:
        if self.all_agents_var.get():
            return list(self.all_agents)
        return [
            a
            for a in self.all_agents
            if a["source_filename"] in self.agent_vars and self.agent_vars[a["source_filename"]].get()
        ]

    # ------------------------------------------------------------------
    # Preview
    # ------------------------------------------------------------------

    def _update_preview(self):
        repos = self._get_selected_repos()
        agents = self._get_selected_agents()

        if not repos and not agents:
            self.preview_var.set("Nothing selected yet.")
            return

        if repos:
            if self.all_repos_var.get():
                repo_str = f"ALL repos ({', '.join(repos)})"
            else:
                repo_str = ", ".join(repos)
        else:
            repo_str = "None"

        if agents:
            names = [a["display_name"] for a in agents]
            if self.all_agents_var.get():
                agent_str = f"ALL agents ({', '.join(names)})"
            else:
                agent_str = ", ".join(names)
        else:
            agent_str = "None"

        self.preview_var.set(
            f"Repositories : {repo_str}\n"
            f"Agents       : {agent_str}\n\n"
            "Selected agent file(s) will be copied into the "
            ".github/personas/ folder of each selected repository. "
            "Missing folders will be created automatically. "
            "Destination files that are already newer will NOT be overwritten."
        )

    # ------------------------------------------------------------------
    # Submit
    # ------------------------------------------------------------------

    def _on_submit(self):
        repos = self._get_selected_repos()
        agents = self._get_selected_agents()

        if not repos:
            messagebox.showwarning(
                "No Repositories Selected",
                "Please select at least one repository.",
            )
            return
        if not agents:
            messagebox.showwarning(
                "No Agents Selected",
                "Please select at least one agent.",
            )
            return

        # Log the user selection
        repo_names = ", ".join(repos)
        agent_names = ", ".join(a["display_name"] for a in agents)
        all_r = self.all_repos_var.get()
        all_a = self.all_agents_var.get()

        if all_r and all_a:
            self.logger.info(
                "User selected ALL repos (%s) and ALL agents (%s).",
                repo_names,
                agent_names,
            )
        elif all_r:
            self.logger.info(
                "User selected ALL repos (%s) and agents: %s.",
                repo_names,
                agent_names,
            )
        elif all_a:
            self.logger.info(
                "User selected repos: %s and ALL agents (%s).",
                repo_names,
                agent_names,
            )
        else:
            self.logger.info(
                "User selected repos: %s and agents: %s.",
                repo_names,
                agent_names,
            )

        # Confirm dialog
        confirm_msg = (
            f"Deploy {len(agents)} agent(s) to {len(repos)} repository(s)?\n\n"
            f"Repositories : {repo_names}\n"
            f"Agents       : {agent_names}"
        )
        if not messagebox.askyesno("Confirm Deployment", confirm_msg):
            self.logger.info("User cancelled the deployment at the confirmation dialog.")
            return

        # Run deployment
        messages = deploy_agents(self.script_dir, repos, agents, self.logger)

        # Show result summary
        result_text = "\n".join(messages) if messages else "No file operations were performed."
        messagebox.showinfo(
            "Deployment Complete",
            f"Deployment finished successfully.\n\n{result_text}\n\n"
            "Full details have been saved to the logs/ folder.",
        )
        self.destroy()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    script_dir = get_script_dir()
    logger = setup_logging(script_dir)
    logger.info("deploy_agents.py started.")

    repos = find_sibling_repos(script_dir)
    agents = find_agent_files(script_dir)

    logger.info(
        "Found %d sibling repository(s): %s",
        len(repos),
        ", ".join(repos) if repos else "none",
    )
    logger.info(
        "Found %d agent file(s): %s",
        len(agents),
        ", ".join(a["source_filename"] for a in agents) if agents else "none",
    )

    if not agents:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "No Agent Files Found",
            f"No agent *.md files were found in:\n"
            f"  {script_dir / "personas"}\n\n"
            "Please add agent files before running this script.",
        )
        logger.error("No agent files found. Exiting.")
        return

    # Check for test mode flag
    import sys
    test_mode = '--test' in sys.argv or '--dry-run' in sys.argv
    app = DeployAgentsApp(script_dir, repos, agents, logger, test_mode=test_mode)
    app.mainloop()

    logger.info("deploy_agents.py finished.")


if __name__ == "__main__":
    main()

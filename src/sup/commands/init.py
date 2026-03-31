"""sup init — scaffold sup into a project."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from sup.config import init_config

console = Console()

_PRE_COMMIT_ENTRY = """\
  - repo: https://github.com/YOUR_ORG/sup
    rev: v0.1.0
    hooks:
      - id: sup-check
"""

_GITHUB_ACTION = """\
name: Supply Chain Quarantine

on:
  pull_request:
    paths:
      - "requirements.txt"
      - "pyproject.toml"
      - "poetry.lock"
      - "Pipfile.lock"
      - "package.json"
      - "package-lock.json"
      - "yarn.lock"
      - "go.mod"
      - "Cargo.toml"
      - "Cargo.lock"
      - "Gemfile.lock"

jobs:
  quarantine:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install sup
        run: pip install sup-quarantine

      - name: Quarantine check
        run: sup check
"""


@click.command()
@click.option("--github-action", is_flag=True, help="Generate GitHub Action workflow.")
@click.option("--pre-commit", "precommit", is_flag=True, help="Show pre-commit config snippet.")
@click.option("--config", "do_config", is_flag=True, help="Create default config file.")
@click.option("--all", "do_all", is_flag=True, help="Do everything.")
def init(github_action: bool, precommit: bool, do_config: bool, do_all: bool) -> None:
    """Set up sup in your project."""
    if not any([github_action, precommit, do_config, do_all]):
        do_all = True

    if do_all or do_config:
        path = init_config()
        console.print(f"[green]Config created:[/green] {path}")

    if do_all or github_action:
        workflow_dir = Path(".github/workflows")
        workflow_dir.mkdir(parents=True, exist_ok=True)
        workflow_path = workflow_dir / "sup-quarantine.yml"
        if workflow_path.exists():
            console.print(f"[yellow]Already exists:[/yellow] {workflow_path}")
        else:
            workflow_path.write_text(_GITHUB_ACTION)
            console.print(f"[green]Created:[/green] {workflow_path}")

    if do_all or precommit:
        console.print("\n[bold]Add to your .pre-commit-config.yaml:[/bold]\n")
        console.print(_PRE_COMMIT_ENTRY)

    console.print("\n[bold]Quick start:[/bold]")
    console.print("  sup check                              # scan your project")
    console.print("  sup check --warn-only                  # scan without blocking")
    console.print("  sup wrap pip install requests==2.31.0  # check before install")
    console.print("  sup allow add PACKAGE VERSION -r 'reviewed' --by you")
    console.print("  sup cache stats                        # check cache health")

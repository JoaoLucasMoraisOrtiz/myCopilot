from __future__ import annotations

from dataclasses import asdict
from typing import Dict, List

from codingos.runtime.models import WorldState


class ContextScout:
    """Builds a precise 'world state' for the planner.

    In the POC we keep this as an interface + minimal heuristics.
    In the real version, it will:
      - discover languages, frameworks, build tooling
      - identify entrypoints, modules, configs
      - generate a compact domain map and relationships
    """

    def __init__(self, repo_root: str):
        self.repo_root = repo_root

    def scout(self) -> WorldState:
        # Placeholder: returning an empty WorldState with repo_root only.
        # Later we will implement filesystem scan via Gemini CLI tools (ls/glob/grep/read-file)
        # orchestrated by MCP.
        return WorldState(repo_root=self.repo_root)

    def to_dict(self) -> Dict:
        return asdict(self.scout())

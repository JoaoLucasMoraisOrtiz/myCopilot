from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


@dataclass
class AceCorrection:
    id: str
    created_at: float
    original_action: str
    error: str
    corrected_action: str
    tags: List[str]
    context_signature: str
    source: str = "auto"  # auto|human
    approved: bool = False
    usage_count: int = 0
    last_used: Optional[float] = None
    notes: str = ""


class AceMemory:
    """Minimal persistent store for ACE-style corrections.

    This is intentionally simple (JSON file) to keep the POC portable.
    We can later swap it for SQLite + embeddings.
    """

    def __init__(self, path: str):
        self.path = path
        self._data: Dict[str, Any] = {"version": 1, "corrections": []}
        self._loaded = False

    def load(self) -> None:
        if self._loaded:
            return
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        else:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            self._flush()
        self._loaded = True

    def _flush(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def add_correction(
        self,
        *,
        original_action: str,
        error: str,
        corrected_action: str,
        tags: List[str],
        context_signature: str,
        source: str = "auto",
        approved: bool = False,
        notes: str = "",
    ) -> AceCorrection:
        self.load()
        correction = AceCorrection(
            id=str(uuid.uuid4()),
            created_at=time.time(),
            original_action=original_action,
            error=error,
            corrected_action=corrected_action,
            tags=tags,
            context_signature=context_signature,
            source=source,
            approved=approved,
            notes=notes,
        )
        self._data["corrections"].append(asdict(correction))
        self._flush()
        return correction

    def list_corrections(self, *, approved: Optional[bool] = None) -> List[Dict[str, Any]]:
        self.load()
        items = self._data.get("corrections", [])
        if approved is None:
            return items
        return [c for c in items if bool(c.get("approved")) == approved]

    def find_relevant(
        self,
        *,
        tags: List[str],
        context_signature: Optional[str] = None,
        top_k: int = 5,
        require_approved: bool = True,
    ) -> List[Dict[str, Any]]:
        """Very simple retrieval: tag overlap + optional exact context_signature match.

        We can later upgrade to embeddings + semantic retrieval.
        """
        self.load()
        candidates = []
        for c in self._data.get("corrections", []):
            if require_approved and not c.get("approved", False):
                continue
            overlap = len(set(tags) & set(c.get("tags", [])))
            if overlap <= 0:
                continue
            score = overlap
            if context_signature and c.get("context_signature") == context_signature:
                score += 10
            candidates.append((score, c))
        candidates.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in candidates[:top_k]]

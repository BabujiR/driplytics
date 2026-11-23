"""Import report: the audit trail a reviewer reads before trusting any score."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


class UnbalancedLedgerError(AssertionError):
    pass


@dataclass
class ImportReport:
    source: str
    format: str
    timezone: str
    total_values: int
    accepted: int
    rejected: int
    duplicates: int
    rejected_by_reason: dict[str, int]
    accepted_uncertain: int
    unmapped_tags: dict[str, int]  # raw tag -> number of values
    scoring_allowed: bool
    scoring_blocked_reasons: list[str]
    dst: dict[str, int]
    totalizer_events: list[dict]
    totalizer_gaps: int
    tags: list[dict]  # per-tag summary
    blank_cells_ignored: int = 0
    rejected_examples: dict[str, list[dict]] = field(default_factory=dict)
    elapsed_s: float = 0.0
    values_per_second: float = 0.0
    output_path: str | None = None

    def __post_init__(self) -> None:
        self.check_balance()

    def check_balance(self) -> None:
        if self.accepted + self.rejected + self.duplicates != self.total_values:
            raise UnbalancedLedgerError(
                f"accepted {self.accepted} + rejected {self.rejected} + duplicates {self.duplicates}"
                f" != total {self.total_values}"
            )
        if sum(self.rejected_by_reason.values()) != self.rejected:
            raise UnbalancedLedgerError("rejected_by_reason does not sum to rejected")

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, path: str | Path | None = None) -> str:
        text = json.dumps(self.to_dict(), indent=2, default=str)
        if path:
            Path(path).write_text(text)
        return text

    def summary(self) -> str:
        lines = [
            f"Source: {self.source} ({self.format}, local zone {self.timezone})",
            f"Values: {self.total_values:,} = accepted {self.accepted:,}"
            f" + rejected {self.rejected:,} + duplicates {self.duplicates:,}",
        ]
        for r, n in sorted(self.rejected_by_reason.items(), key=lambda kv: -kv[1]):
            if n:
                lines.append(f"  rejected {r}: {n:,}")
        if self.unmapped_tags:
            lines.append(f"Unmapped tags: {', '.join(sorted(self.unmapped_tags))}")
        lines.append(
            "Scoring: "
            + ("ALLOWED" if self.scoring_allowed else "BLOCKED - " + "; ".join(self.scoring_blocked_reasons))
        )
        return "\n".join(lines)

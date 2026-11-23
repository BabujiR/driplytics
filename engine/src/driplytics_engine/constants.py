"""Shared enums and code tables.

Every input value ends in exactly one Outcome. Rejected values carry exactly one
Reason. Reasons are checked in the order they are declared in REASON_PRIORITY, so
a row with both a bad timestamp and an unmapped tag is counted once, as
UNPARSEABLE_TIMESTAMP.
"""

from __future__ import annotations

from enum import StrEnum


class Outcome(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"


class Reason(StrEnum):
    UNPARSEABLE_TIMESTAMP = "unparseable_timestamp"
    UNMAPPED_TAG = "unmapped_tag"
    EMPTY_VALUE = "empty_value"
    BAD_QUALITY = "bad_quality"  # quality flag says Bad, or a PI digital state such as "I/O Timeout"
    NON_NUMERIC_VALUE = "non_numeric_value"
    UNRECOGNIZED_STATE = "unrecognized_state"  # state tag value matches neither state_true nor state_false
    NONEXISTENT_LOCAL_TIME = "nonexistent_local_time"  # inside the spring-forward gap
    CONFLICTING_DUPLICATE = "conflicting_duplicate"  # same tag + UTC time, different values


# Integer codes used inside vectorized code (0 = no reason / still valid).
REASON_PRIORITY: list[Reason] = list(Reason)
REASON_CODE: dict[Reason, int] = {r: i + 1 for i, r in enumerate(REASON_PRIORITY)}
CODE_REASON: dict[int, Reason] = {v: k for k, v in REASON_CODE.items()}


class Quality(StrEnum):
    GOOD = "good"
    UNCERTAIN = "uncertain"
    BAD = "bad"


class Role(StrEnum):
    FLOW = "flow"
    PRESSURE = "pressure"
    LEVEL = "level"
    TEMPERATURE = "temperature"
    PUMP_STATE = "pump_state"  # canonical value 1.0 = running, 0.0 = stopped
    VALVE_STATE = "valve_state"  # canonical value 1.0 = CLOSED, 0.0 = not closed
    OTHER = "other"

    @property
    def is_state(self) -> bool:
        return self in (Role.PUMP_STATE, Role.VALVE_STATE)

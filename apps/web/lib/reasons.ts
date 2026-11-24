/** Rejection reasons from the engine (driplytics_engine.constants.Reason), in plain words. */

export interface ReasonText {
  label: string;
  explain: string;
}

export const REASONS: Record<string, ReasonText> = {
  unparseable_timestamp: {
    label: "Timestamp could not be read",
    explain: "The time cell isn't a valid date and time (for example 2026-11-31, or text).",
  },
  unmapped_tag: {
    label: "Tag not mapped",
    explain: "The tag has no role yet. Map it, then import again to use these values.",
  },
  empty_value: { label: "Empty value", explain: "The value cell is blank." },
  bad_quality: {
    label: "Bad quality",
    explain: "The historian marked the value Bad, or sent a status such as I/O Timeout instead of a value.",
  },
  non_numeric_value: { label: "Not a number", explain: "A flow, pressure or level value that isn't a number." },
  unrecognized_state: {
    label: "Unknown on/off state",
    explain: "A pump or valve state that matches neither its 'true' nor its 'false' text in the tag mapping.",
  },
  nonexistent_local_time: {
    label: "Time that doesn't exist",
    explain: "A local time inside the hour skipped when clocks sprang forward (daylight saving).",
  },
  conflicting_duplicate: {
    label: "Conflicting duplicate",
    explain: "The same tag and time appear more than once with different values.",
  },
};

export function reasonText(code: string): ReasonText {
  return REASONS[code] ?? { label: code.replaceAll("_", " "), explain: "" };
}

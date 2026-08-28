import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

LOG_PATH = Path(__file__).resolve().parent.parent / "logs" / "audit.jsonl"

FAILED_MFA_THRESHOLD = 3
FAILED_MFA_WINDOW_MINUTES = 10


def load_events():
    events = []
    with open(LOG_PATH, "r") as f:
        for line in f:
            events.append(json.loads(line))
    return events


def parse_time(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def flag_failed_mfa_clusters(events):
    mfa_failures = [
        e
        for e in events
        if e["eventType"] == "user.authentication.auth_via_mfa"
        and e["outcome"] == "FAILURE"
    ]

    by_actor = defaultdict(list)
    for e in mfa_failures:
        by_actor[e["actor"]].append(parse_time(e["published"]))

    findings = []
    for actor, timestamps in by_actor.items():
        timestamps.sort()
        for i in range(len(timestamps) - FAILED_MFA_THRESHOLD + 1):
            window_start = timestamps[i]
            window_end = timestamps[i + FAILED_MFA_THRESHOLD - 1]
            if (window_end - window_start) <= timedelta(
                minutes=FAILED_MFA_WINDOW_MINUTES
            ):
                findings.append(
                    {
                        "actor": actor,
                        "failure_count": FAILED_MFA_THRESHOLD,
                        "window_start": window_start.isoformat(),
                        "window_end": window_end.isoformat(),
                        "rule": f"{FAILED_MFA_THRESHOLD}+ failed MFA attempts within {FAILED_MFA_WINDOW_MINUTES} min",
                    }
                )
                break  # one flag per actor is enough for this demo

    return findings


if __name__ == "__main__":
    events = load_events()
    print(f"Loaded {len(events)} events from {LOG_PATH}\n")

    findings = flag_failed_mfa_clusters(events)

    if not findings:
        print("No suspicious MFA failure clusters detected.")
    else:
        print(f"{len(findings)} suspicious pattern(s) detected:\n")
        for f in findings:
            print(f"  Actor: {f['actor']}")
            print(f"  Rule:  {f['rule']}")
            print(f"  Window: {f['window_start']} to {f['window_end']}")
            print()

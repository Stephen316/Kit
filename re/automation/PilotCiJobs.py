import re
from collections import Counter
from datetime import datetime, timedelta


# the API's two URLs bind each timing row to the same repository and run
def job_identity(item):
    job, run, attempt = (item[key] for key in ("id", "run_id", "run_attempt"))
    if any(type(value) is not int or value < 1 for value in (job, run, attempt)):
        raise ValueError("invalid GitHub Actions job or attempt identity")
    url = item["url"]
    match = re.fullmatch(
        r"(https://api\.github\.com/repos/[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+)/actions/jobs/[1-9][0-9]*",
        url,
    )
    if (
        match is None
        or url != f"{match[1]}/actions/jobs/{job}"
        or item["run_url"] != f"{match[1]}/actions/runs/{run}"
        or not re.fullmatch("[0-9a-f]{40}", item["head_sha"])
    ):
        raise ValueError("GitHub Actions job differs from its run or revision")
    return match[1].casefold(), job


# the observation uses source timestamps on the same UTC clock
def utc_time(value):
    if value is None:
        return None
    timestamp = datetime.fromisoformat(value)
    if timestamp.utcoffset() != timedelta():
        raise ValueError("GitHub Actions job time requires UTC")
    return timestamp.timestamp()


# settled jobs belong to their completion window and each interval keeps its own coverage
def ci_summary(records, start, end):
    outcomes = Counter()
    unfinished = 0
    pre_start_count = execution_count = 0
    pre_start_seconds = execution_seconds = 0.0
    for item in records:
        created, started, finished = (
            utc_time(item.get(key))
            for key in ("created_at", "started_at", "completed_at")
        )
        status, outcome = item["status"], item["conclusion"]
        if status != "completed" or finished is None or finished >= end:
            if any(
                time is not None and start <= time < end for time in (created, started)
            ):
                unfinished += 1
            continue
        if not start <= finished < end:
            continue
        if not isinstance(outcome, str) or not outcome:
            raise ValueError("completed GitHub Actions job needs a conclusion")
        outcomes[outcome] += 1
        if outcome == "skipped" or started is None or started > finished:
            continue
        execution_count += 1
        execution_seconds += finished - started
        if created is not None and created <= started:
            pre_start_count += 1
            pre_start_seconds += started - created

    executable = outcomes.total() - outcomes["skipped"]
    measured = "unmeasured"
    if execution_count:
        measured = (
            "measured"
            if pre_start_count == executable and not unfinished
            else "partial"
        )
    return {
        "status": measured,
        "conclusions": dict(outcomes),
        "unfinished_observations": unfinished,
        "pre_start_jobs": pre_start_count,
        "created_to_start_job_seconds": pre_start_seconds if pre_start_count else None,
        "execution_timed_jobs": execution_count,
        "start_to_finish_job_seconds": execution_seconds if execution_count else None,
    }

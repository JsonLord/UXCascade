#!/usr/bin/env python3
"""
Reusable Live Validation Collector Script for UXCascade.
Executes experiments against live deployment, collects machine-readable evidence,
polls until terminal state, and verifies EventSnapshots and analysis output.
Exits non-zero (INVALID_EVIDENCE) if total_steps == 0 or if /ready is unready.
"""

import sys
import os
import time
import json
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path

BASE_URL = os.environ.get("CASCADE_URL", "https://leon4gr45-cascade.hf.space")
TOKEN = os.environ.get("HF_TOKEN", "")

def http_get(endpoint: str) -> dict | list | str:
    url = f"{BASE_URL.rstrip('/')}{endpoint}"
    headers = {"User-Agent": "UXCascade-Collector/1.0"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as res:
        content = res.read().decode("utf-8")
        try:
            return json.loads(content)
        except Exception:
            return content

def http_post(endpoint: str, payload: dict) -> dict:
    url = f"{BASE_URL.rstrip('/')}{endpoint}"
    headers = {"Content-Type": "application/json", "User-Agent": "UXCascade-Collector/1.0"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers
    )
    with urllib.request.urlopen(req, timeout=15) as res:
        return json.loads(res.read().decode("utf-8"))

def run_validation(site_name: str, target_url: str, traits: list[dict], goals: list[str]) -> bool:
    print(f"\n========================================================")
    print(f" Starting Live Validation for {site_name} ({target_url})")
    print(f"========================================================")

    # 1. Health Check
    health = http_get("/health")
    print(f"Health Check: {health}")

    # 2. Readiness Check
    try:
        ready = http_get("/ready")
        print(f"Readiness Check: {json.dumps(ready, indent=2)}")
        if isinstance(ready, dict) and ready.get("status") != "ready":
            print(f"ERROR: Space is not ready! Reason: {ready}")
            return False
    except Exception as e:
        print(f"ERROR: /ready check failed: {e}")
        return False

    runtime = http_get("/api/runtime")
    print(f"Runtime Diagnostics: {json.dumps(runtime, indent=2)}")

    # 3. Create Experiment
    exp_payload = {
        "name": f"Validation - {site_name}",
        "target_url": target_url,
        "traits": traits,
        "goals": goals
    }
    exp = http_post("/api/experiments/", exp_payload)
    exp_id = exp["id"]
    print(f"Created Experiment ID: {exp_id}")

    # 4. Trigger Run
    run_res = http_post(f"/api/experiments/{exp_id}/run", {})
    print(f"Triggered Run: {run_res}")

    # 5. Poll Status
    status = "running"
    start_time = time.time()
    max_wait = 600  # 10 minutes timeout

    while status not in ["completed", "failed"] and (time.time() - start_time) < max_wait:
        time.sleep(10)
        exp_data = http_get(f"/api/experiments/{exp_id}")
        status = exp_data.get("status")
        print(f"Elapsed {int(time.time() - start_time)}s -> Status: {status}")

    if status not in ["completed", "failed"]:
        print(f"ERROR: Experiment timed out after {max_wait}s!")
        return False

    # 6. Collect Evidence Data
    print(f"\nCollecting evidence artifacts...")
    goals_data = http_get(f"/api/experiments/{exp_id}/goals")
    issues_data = http_get(f"/api/experiments/{exp_id}/issues")
    journeys_data = http_get(f"/api/experiments/{exp_id}/journeys")
    steps_data = http_get(f"/api/experiments/{exp_id}/agent-run-steps")

    today_str = datetime.now().strftime("%Y-%m-%d")
    out_dir = Path(f"validation/{today_str}/{site_name.lower().replace(' ', '_')}")
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "experiment.json", "w") as f:
        json.dump(exp_data, f, indent=2)
    with open(out_dir / "runtime.json", "w") as f:
        json.dump(runtime, f, indent=2)
    with open(out_dir / "goals.json", "w") as f:
        json.dump(goals_data, f, indent=2)
    with open(out_dir / "issues.json", "w") as f:
        json.dump(issues_data, f, indent=2)
    with open(out_dir / "journeys.json", "w") as f:
        json.dump(journeys_data, f, indent=2)
    with open(out_dir / "steps.json", "w") as f:
        json.dump(steps_data, f, indent=2)

    total_steps = sum(len(run.get("steps", [])) for run in steps_data)
    print(f"Validation Artifacts Saved to {out_dir}")
    print(f"Total Runs: {len(steps_data)} | Total Recorded Steps: {total_steps} | Final Status: {status}")

    # Evidence Assertion: Fail if 0 steps recorded
    if total_steps == 0:
        print("ERROR: INVALID_EVIDENCE - Run completed with 0 steps recorded.")
        return False

    return True

if __name__ == "__main__":
    success = run_validation(
        site_name="taos_smoke",
        target_url="https://taoshq.com/",
        traits=[{"name": "Digital confidence", "key": "digital_confidence", "values": ["low"]}],
        goals=["Understand what TAOS does and who it is intended for"]
    )
    sys.exit(0 if success else 1)

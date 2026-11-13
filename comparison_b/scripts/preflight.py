from pathlib import Path
import os
import sys
import json
import subprocess
from verify_version import UPSTREAM, EXPECTED

def main():
    if sys.version_info < (3,11): raise SystemExit("Python 3.11 or newer is required")
    if not (UPSTREAM/".git").exists(): raise SystemExit("Submodule is not initialized; no install/run performed")
    sha=subprocess.check_output(["git","-C",str(UPSTREAM),"rev-parse","HEAD"],text=True).strip()
    if sha!=EXPECTED: raise SystemExit("Upstream commit differs from pin")
    host=os.getenv("OPEN_DEEP_RESEARCH_HOST","127.0.0.1")
    if host!="127.0.0.1": raise SystemExit("Refusing non-loopback server bind")
    audit=subprocess.run(["uv","audit","--locked","--output-format","json"],cwd=UPSTREAM,text=True,capture_output=True,check=False)
    start=audit.stdout.find("{")
    if start<0: raise SystemExit("Dependency audit did not return structured output; refusing to run")
    try: report=json.loads(audit.stdout[start:])
    except json.JSONDecodeError as exc: raise SystemExit("Dependency audit output was invalid; refusing to run") from exc
    summary=report.get("summary",{})
    if not isinstance(summary.get("vulnerabilities"),int) or not isinstance(summary.get("adverse_statuses"),int):
        raise SystemExit("Dependency audit summary was incomplete; refusing to run")
    if summary["vulnerabilities"] or summary["adverse_statuses"]:
        raise SystemExit(f"Security gate blocked run: {summary['vulnerabilities']} advisories and {summary['adverse_statuses']} adverse package statuses")
    if audit.returncode: raise SystemExit("Dependency audit failed; refusing to run")
    print("preflight passed")

if __name__=="__main__": main()

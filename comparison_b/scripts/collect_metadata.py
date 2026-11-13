import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys

def main():
    root=Path(__file__).resolve().parents[1]/"upstream"/"open_deep_research"
    if not (root/".git").exists(): raise SystemExit("Submodule not initialized")
    sha=subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip()
    meta={"system_id":"open_deep_research","upstream_commit":sha,"python":sys.version,"collected_at":datetime.now(timezone.utc).isoformat(),"status":"preflight_only"}
    print(json.dumps(meta,indent=2))

if __name__=="__main__": main()

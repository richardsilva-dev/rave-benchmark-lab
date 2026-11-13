from pathlib import Path
import os
import sys
from verify_version import UPSTREAM, EXPECTED

def main():
    if sys.version_info < (3,11): raise SystemExit("Python 3.11 or newer is required")
    if not (UPSTREAM/".git").exists(): raise SystemExit("Submodule is not initialized; no install/run performed")
    import subprocess
    sha=subprocess.check_output(["git","-C",str(UPSTREAM),"rev-parse","HEAD"],text=True).strip()
    if sha!=EXPECTED: raise SystemExit("Upstream commit differs from pin")
    host=os.getenv("OPEN_DEEP_RESEARCH_HOST","127.0.0.1")
    if host!="127.0.0.1": raise SystemExit("Refusing non-loopback server bind")
    print("preflight passed; dependency audit and license review are separate required steps")

if __name__=="__main__": main()

from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
UPSTREAM=ROOT/"upstream"/"open_deep_research"
EXPECTED="1b7d2e80db9faa586165c60e09096dbbfd483a64"

def main():
    if not (UPSTREAM/".git").exists(): raise SystemExit("Open Deep Research submodule is not initialized")
    actual=subprocess.check_output(["git","-C",str(UPSTREAM),"rev-parse","HEAD"],text=True).strip()
    if actual!=EXPECTED: raise SystemExit(f"Pinned commit mismatch: expected {EXPECTED}, found {actual}")
    print(f"verified {actual}")

if __name__=="__main__": main()

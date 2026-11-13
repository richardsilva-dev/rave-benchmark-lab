param([string]$HostAddress = "127.0.0.1")
if ($HostAddress -ne "127.0.0.1") { throw "Only loopback binding is allowed." }
python .\scripts\preflight.py
if ($LASTEXITCODE -ne 0) { throw "Preflight failed." }
throw "Runner command is not configured until the pinned upstream interface is inspected; refusing to guess its entrypoint."

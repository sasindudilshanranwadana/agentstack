# agentstack installer (Windows PowerShell). Thin launcher: verify Python +
# Docker, then hand off to the cross-platform Python wizard.
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  Write-Error "Python 3 is required. Install it from https://www.python.org and re-run."
  exit 1
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  Write-Error "Docker Desktop is required: https://docs.docker.com/get-docker/"
  exit 1
}

docker network create agentstack 2>$null | Out-Null
python -m wizard @args

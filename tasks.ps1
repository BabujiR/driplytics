# Driplytics developer commands for Windows PowerShell. Usage: .\tasks.ps1 <target>
# Same targets as the Makefile. Run ".\tasks.ps1 help" to list them.
param([Parameter(Position = 0)][string]$Task = "help")
$ErrorActionPreference = "Stop"

function Run([string]$cmd) {
  Write-Host "> $cmd" -ForegroundColor Cyan
  Invoke-Expression $cmd
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

function Ensure-Pnpm {
  # Node 25+ no longer bundles corepack; fall back to a global pnpm install.
  if (Get-Command pnpm -ErrorAction SilentlyContinue) { Write-Host "  pnpm $(pnpm --version) already installed"; return }
  if (Get-Command corepack -ErrorAction SilentlyContinue) { Run "corepack enable" }
  if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) { Run "npm install -g pnpm@10" }
}

function Test-Prereqs {
  $ok = $true
  $tools = @(
    @{ Name = "uv";     Hint = 'Install: powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"  (or: winget install --id=astral-sh.uv -e)' },
    @{ Name = "node";   Hint = "Install Node.js 22 LTS or newer: https://nodejs.org  (or: winget install OpenJS.NodeJS.LTS)" },
    @{ Name = "docker"; Hint = "Install Docker Desktop: https://www.docker.com/products/docker-desktop/  (or: winget install Docker.DockerDesktop)" },
    @{ Name = "git";    Hint = "Install Git: https://git-scm.com/download/win  (or: winget install Git.Git)" }
  )
  foreach ($t in $tools) {
    $cmd = Get-Command $t.Name -ErrorAction SilentlyContinue
    if ($cmd) {
      $v = (& $t.Name --version 2>$null | Select-Object -First 1)
      Write-Host ("  [ok]      {0,-7} {1}" -f $t.Name, $v) -ForegroundColor Green
    } else {
      Write-Host ("  [missing] {0,-7} {1}" -f $t.Name, $t.Hint) -ForegroundColor Yellow
      $ok = $false
    }
  }
  if (Get-Command node -ErrorAction SilentlyContinue) {
    $major = [int]((node --version).TrimStart("v").Split(".")[0])
    if ($major -lt 22) { Write-Host "  [old]     node    v$major found; Driplytics needs Node 22 or newer" -ForegroundColor Yellow; $ok = $false }
  }
  if (-not $ok) {
    Write-Host "`nInstall the missing tools, then CLOSE AND REOPEN PowerShell so PATH updates, and run this again." -ForegroundColor Yellow
  }
  return $ok
}

switch ($Task) {
  "doctor"    { if (-not (Test-Prereqs)) { exit 1 } }
  "install"   { if (-not (Test-Prereqs)) { exit 1 }; Run "uv sync --all-packages"; Ensure-Pnpm; Run "pnpm install" }
  "dev"       { Run "docker compose up --build" }
  "up"        { Run "docker compose up --build -d" }
  "down"      { Run "docker compose down" }
  "logs"      { Run "docker compose logs -f" }
  "ps"        { Run "docker compose ps" }
  "test"      { Run "uv run --all-packages pytest"; Run "pnpm test" }
  "test-py"   { Run "uv run --all-packages pytest" }
  "test-js"   { Run "pnpm test" }
  "test-db"   { Run "uv run --all-packages pytest -m db" }
  "migrate"   { Run "docker compose run --rm migrate" }
  "token"     { Run "uv run python apps/api/scripts/dev_token.py alice --tenant" }
  "demo"      { Run "uv run python apps/api/scripts/dev_import.py" }
  "check"     { Run "uv run ruff check ."; Run "uv run ruff format --check ."; Run "uv run mypy"; Run "uv run python scripts/check_portability.py"; Run "uv run --all-packages pytest -ra" }
  "lint"      { Run "uv run ruff check ."; Run "uv run ruff format --check ."; Run "uv run mypy"; Run "pnpm lint" }
  "typecheck" { Run "uv run mypy"; Run "pnpm typecheck" }
  "fmt"       { Run "uv run ruff format ."; Run "uv run ruff check --fix ."; Run "pnpm format" }
  "bench"     { Run "uv run python engine/scripts/benchmark.py --days 1" }
  "clean"     { Run "docker compose down -v" }
  default {
    Write-Host "Targets: doctor, install, dev, up, down, logs, ps, test, test-py, test-js, test-db, migrate, token, demo, check, lint, typecheck, fmt, bench, clean"
  }
}

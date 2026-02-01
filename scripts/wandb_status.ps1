$envPath = Join-Path $PSScriptRoot "..\.env"
if (Test-Path $envPath) {
  Get-Content $envPath | ForEach-Object {
    if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
    $parts = $_ -split '=', 2
    if ($parts.Length -eq 2) {
      $name = $parts[0].Trim()
      $name = $name -replace '^\uFEFF', ''
      $value = $parts[1].Trim().Trim('"')
      Set-Item -Path "Env:$name" -Value $value
    }
  }
}

if (-not $env:WANDB_API_KEY) {
  Write-Host "WANDB_API_KEY not set in environment. Check your .env file."
  exit 1
}

$python = Join-Path $PSScriptRoot "..\.venv\Scripts\python"
& $python -m wandb status

<# scripts/ensure-path.ps1
   Makes pwsh see the hostâ€™s usual binaries (git, winget, choco, etc.)
#>
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Split-PathList([string]$s) {
  if ([string]::IsNullOrWhiteSpace($s)) { @() }
  else { $s -split ';' | ForEach-Object { $_.Trim() } | Where-Object { $_ } }
}

function Expand-Dirs([string[]]$items) {
  foreach ($p in $items) {
    $expanded = [Environment]::ExpandEnvironmentVariables($p)
    if (Test-Path -LiteralPath $expanded) { $expanded }
  }
}

$machPath = [Environment]::GetEnvironmentVariable('Path','Machine')
$userPath = [Environment]::GetEnvironmentVariable('Path','User')
$procPath = $env:Path

$defaults = @(
  "$Env:SystemRoot\System32",
  "$Env:SystemRoot",
  "$Env:SystemRoot\System32\Wbem",
  "$Env:SystemRoot\System32\WindowsPowerShell\v1.0",
  "$Env:SystemRoot\System32\OpenSSH",
  "$Env:ProgramFiles\PowerShell\7",
  "$Env:ProgramFiles\Git\cmd",
  "$Env:ProgramFiles\Git\bin",
  "$Env:ProgramData\chocolatey\bin",
  "$Env:LOCALAPPDATA\Microsoft\WindowsApps",
  "$Env:USERPROFILE\AppData\Local\Microsoft\WindowsApps"
)

$merged = @()
$seen = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)

foreach ($chunk in @(
  (Expand-Dirs (Split-PathList $machPath)),
  (Expand-Dirs (Split-PathList $userPath)),
  (Expand-Dirs (Split-PathList $procPath)),
  (Expand-Dirs $defaults)
)) {
  foreach ($d in $chunk) {
    if ($seen.Add($d)) { $merged += $d }
  }
}

$env:Path = ($merged -join ';')

Write-Host "PATH updated for this session."
Get-Command git   -ErrorAction SilentlyContinue | Out-Host
Get-Command winget -ErrorAction SilentlyContinue | Out-Host
Get-Command choco  -ErrorAction SilentlyContinue | Out-Host
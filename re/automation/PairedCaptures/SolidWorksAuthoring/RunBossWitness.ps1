# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$ExecutablePath,
    [switch]$CompileOnly,
    [ValidateSet('edit', 'reopen')]
    [string]$PhaseName,
    [string]$WitnessDirectory,
    [ValidatePattern('^[0-9a-f]{64}$')]
    [string]$PlanSha256,
    [ValidatePattern('^[0-9a-f]{64}$')]
    [string]$InputSha256
)

$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSEdition -ne 'Desktop' -or -not [Environment]::Is64BitProcess -or
    [Threading.Thread]::CurrentThread.GetApartmentState() -ne 'STA') {
    throw 'Run the compiler or collector with 64-bit Windows PowerShell 5.1 in STA mode.'
}
if ($CompileOnly -and ($PhaseName -or $WitnessDirectory -or $PlanSha256 -or $InputSha256)) {
    throw 'A compile-only command takes no native phase arguments.'
}
if (-not $CompileOnly -and (-not $PhaseName -or -not $WitnessDirectory -or -not $PlanSha256 -or -not $InputSha256)) {
    throw 'A native phase requires its witness directory, exact phase and input pins.'
}

$registration = (Get-Item -LiteralPath 'Registry::HKEY_CLASSES_ROOT\SldWorks.Application\CLSID').GetValue('')
$registered = (Get-Item -LiteralPath "Registry::HKEY_CLASSES_ROOT\CLSID\$registration\LocalServer32").GetValue('')
$exe = Get-Item -LiteralPath $ExecutablePath
if ($exe.FullName -ine (Get-Item -LiteralPath $registered).FullName -or $exe.Name -ine 'SLDWORKS.exe') {
    throw 'The executable is not the registered SOLIDWORKS installation.'
}
$interop = Get-Item -LiteralPath (Join-Path $exe.DirectoryName 'api/redist/SolidWorks.Interop.sldworks.dll')
$constants = Get-Item -LiteralPath (Join-Path $exe.DirectoryName 'api/redist/SolidWorks.Interop.swconst.dll')
$build = '34.4.1.1011'
if (@($exe, $interop, $constants).Where({ $_.VersionInfo.FileVersion -cne $build }).Count -ne 0) {
    throw 'The installation and interops must match the licensed witness build.'
}
$web = Join-Path ([Runtime.InteropServices.RuntimeEnvironment]::GetRuntimeDirectory()) 'System.Web.Extensions.dll'
$collectors = @('P04Readback.cs', 'P02Readback.cs', 'BossWitnessReadback.cs') | ForEach-Object {
    Join-Path $PSScriptRoot $_
}
Add-Type -Path $constants.FullName
Add-Type -Path $interop.FullName
Add-Type -Path $collectors -ReferencedAssemblies @($interop.FullName, $constants.FullName, 'System.Core.dll', $web)
if ($CompileOnly) {
    Write-Output "Compiled rectangular Boss witness for $build"
    return
}

function Write-NewJson([string]$Path, $Value) {
    $temp = "$Path.$([Guid]::NewGuid().ToString('N'))"
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes(($Value | ConvertTo-Json -Depth 12) + [Environment]::NewLine)
    try {
        $stream = [IO.File]::Open($temp, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
        try {
            $stream.Write($bytes, 0, $bytes.Length)
            $stream.Flush($true)
        } finally {
            $stream.Dispose()
        }
        [IO.File]::Move($temp, $Path)
    } finally {
        [IO.File]::Delete($temp)
    }
}

$root = (Get-Item -LiteralPath $WitnessDirectory).FullName
$planPath = Join-Path $root 'Plan.json'
$plan = Get-Content -LiteralPath $planPath -Raw | ConvertFrom-Json
if ((Get-FileHash -LiteralPath $planPath -Algorithm SHA256).Hash.ToLowerInvariant() -cne $PlanSha256 -or
    $plan.build -cne $build -or
    (Get-FileHash -LiteralPath $exe.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -cne $plan.image_sha256) {
    throw 'The witness plan or installed image differs from its pin.'
}
$phaseDirectory = (Get-Item -LiteralPath (Join-Path $root $PhaseName)).FullName
$documentPath = if ($PhaseName -ceq 'edit') {
    Join-Path $phaseDirectory 'Scratch.SLDPRT'
} else {
    Join-Path $root 'Restored.SLDPRT'
}
if ((Get-FileHash -LiteralPath $documentPath -Algorithm SHA256).Hash.ToLowerInvariant() -cne $InputSha256) {
    throw 'The exact phase archive differs from its input pin.'
}
if (Get-Process -Name SLDWORKS -ErrorAction SilentlyContinue) {
    throw 'The dedicated native desktop still has a SOLIDWORKS process.'
}
$process = [Diagnostics.Process]::GetCurrentProcess()
try {
    $collector = [ordered]@{
        pid = $process.Id
        created = $process.StartTime.ToUniversalTime().ToFileTimeUtc()
    }
} finally {
    $process.Dispose()
}
Write-NewJson (Join-Path $phaseDirectory 'Ready.json') ([ordered]@{
    phase = $PhaseName
    plan_sha256 = $PlanSha256
    input_sha256 = $InputSha256
    collector = $collector
})
$launchPath = Join-Path $phaseDirectory 'Launch.json'
$clock = [Diagnostics.Stopwatch]::StartNew()
while (-not (Test-Path -LiteralPath $launchPath -PathType Leaf)) {
    if ($clock.Elapsed.TotalSeconds -ge 60) { throw 'The bounded launcher did not publish a held process.' }
    Start-Sleep -Milliseconds 50
}
$launch = Get-Content -LiteralPath $launchPath -Raw | ConvertFrom-Json
if ($launch.phase -cne $PhaseName -or $launch.plan_sha256 -cne $PlanSha256 -or
    $launch.input_sha256 -cne $InputSha256) {
    throw 'The native launch does not match this exact phase.'
}
[P04Readback]::RunBossPhase($planPath, $documentPath, (Join-Path $root 'Control.SLDPRT'), $exe.FullName,
    $launchPath, (Join-Path $phaseDirectory 'Raw.json'))

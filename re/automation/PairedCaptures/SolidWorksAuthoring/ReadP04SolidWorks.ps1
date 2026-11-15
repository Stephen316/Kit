[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$OutputDirectory,
    [Parameter(Mandatory)]
    [string]$InteropAssembly,
    [string]$SourceRoot,
    [string]$SourceRevision
)

$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSEdition -ne 'Desktop' -or
    [Threading.Thread]::CurrentThread.GetApartmentState() -ne 'STA' -or
    -not [Environment]::Is64BitProcess) {
    throw 'Run with 64-bit Windows PowerShell 5.1 in STA mode.'
}

if ([bool]$SourceRoot -ne [bool]$SourceRevision) {
    throw 'Provide both pinned source arguments for a staged launcher.'
}
$repository = if ($SourceRoot) {
    (Resolve-Path -LiteralPath $SourceRoot).Path
} else {
    (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../../..')).Path
}
$revision = git -C $repository rev-parse --verify 'HEAD^{commit}'
if ($LASTEXITCODE -ne 0 -or $revision -cnotmatch '^[a-f0-9]{40}$') {
    throw 'A complete Git checkout is required.'
}
if ($SourceRevision -and $SourceRevision -cne $revision) {
    throw 'The checkout revision differs from the staged launcher source pin.'
}

function Get-Pin([string]$RelativePath) {
    $path = Join-Path $repository $RelativePath
    $item = Get-Item -LiteralPath $path
    if ($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw "Expected a regular source file at $RelativePath"
    }
    $blob = git -C $repository rev-parse --verify ("{0}:{1}" -f $revision, $RelativePath)
    if ($LASTEXITCODE -ne 0 -or $blob -cnotmatch '^[a-f0-9]{40}$') {
        throw "Source is not pinned in Git at $RelativePath"
    }
    $actual = git -C $repository hash-object --no-filters -- $path
    if ($LASTEXITCODE -ne 0 -or $actual -cne $blob) {
        throw "Source bytes differ from Git at $RelativePath"
    }
    return [ordered]@{
        path = $RelativePath
        git_blob = $blob
        sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
        size_bytes = $item.Length
    }
}

function Copy-Pinned($Pin, [string]$Destination) {
    [IO.File]::Copy((Join-Path $repository $Pin.path), $Destination, $false)
    Assert-Bytes $Destination $Pin
}

function Assert-Bytes([string]$Path, $Pin) {
    if ((Get-Item -LiteralPath $Path).Length -ne $Pin.size_bytes -or
        (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() -cne $Pin.sha256) {
        throw "File bytes changed at $Path"
    }
}

function Write-NewJson([string]$Path, $Value) {
    $content = [Text.Encoding]::UTF8.GetBytes(($Value | ConvertTo-Json -Depth 48) + "`n")
    $file = [IO.File]::Open($Path, [IO.FileMode]::CreateNew)
    try {
        $file.Write($content, 0, $content.Length)
        $file.Flush($true)
    } finally {
        $file.Dispose()
    }
}

$captureRoot = 're/automation/PairedCaptures/P04/solidworks-c1986308375a'
$authoringRoot = 're/automation/PairedCaptures/SolidWorksAuthoring'
$receipt = Get-Pin "$captureRoot/receipt.json"
if ($receipt.sha256 -cne '7fd2fffa3c690998753a80cab81da2f1c2446c9fcec39574e3983a7f4345cae5') {
    throw 'The recorded P04 receipt differs from its audited identity.'
}
$existing = Get-Content -LiteralPath (Join-Path $repository $receipt.path) -Raw | ConvertFrom-Json
$measurements = Get-Pin "$captureRoot/measurements.json"
if ($existing.recipe_id -cne 'P04' -or $existing.measurements -cne 'measurements.json' -or
    $existing.errors -ne 0 -or $existing.measurement_receipt_sha256 -cne $measurements.sha256 -or
    $existing.native_files.Count -ne 11) {
    throw 'The recorded P04 receipt and measurements do not agree.'
}
$spec = Get-Pin 're/automation/PairSpecs.json'
$control = Get-Pin 're/solidworks/examples/.SLDPRT/example.SLDPRT'
if ($spec.sha256 -cne '3c93e024f9fbdda50e610bda3b363bf30e8e7cdc914ef0728087befe129951bf' -or
    $control.sha256 -cne 'd1bbca099ccac1330024619390df3c6b76320a6a6c281a5009578b2fb63e7408') {
    throw 'The specification or healthy control differs from the capture.'
}
$collector = Get-Pin "$authoringRoot/P04Readback.cs"
$launcher = Get-Pin "$authoringRoot/ReadP04SolidWorks.ps1"
Assert-Bytes $PSCommandPath $launcher
$files = [ordered]@{}
foreach ($reported in $existing.native_files) {
    if ($reported.file -cnotmatch '^P04-solidworks-[A-Za-z0-9_-]+\.SLDPRT$' -or
        $files.Contains($reported.file) -or $reported.save_errors -ne 0 -or $reported.save_warnings -ne 0) {
        throw 'The P04 receipt contains an unexpected file entry.'
    }
    $pin = Get-Pin "$captureRoot/$($reported.file)"
    if ($pin.sha256 -cne $reported.sha256 -or $pin.size_bytes -ne $reported.size_bytes) {
        throw "A native file differs from its audited receipt at $($pin.path)"
    }
    $files.Add($reported.file, $pin)
}
Assert-Bytes (Join-Path $repository $receipt.path) $receipt

$registration = (Get-Item -LiteralPath 'Registry::HKEY_CLASSES_ROOT\SldWorks.Application\CLSID').GetValue('')
$server = Get-Item -LiteralPath "Registry::HKEY_CLASSES_ROOT\CLSID\$registration\LocalServer32"
$binary = Get-Item -LiteralPath ($server.GetValue(''))
$interop = Get-Item -LiteralPath $InteropAssembly
$constants = Get-Item -LiteralPath (Join-Path $interop.DirectoryName 'SolidWorks.Interop.swconst.dll')
$programRoot = $binary.DirectoryName.TrimEnd('\') + '\'
if ($binary.VersionInfo.FileVersion -cne '34.4.1.1011' -or
    $interop.Name -cne 'SolidWorks.Interop.sldworks.dll' -or
    $interop.VersionInfo.FileVersion -cne '34.4.1.1011' -or
    $constants.VersionInfo.FileVersion -cne '34.4.1.1011' -or
    -not $interop.FullName.StartsWith($programRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'The registered SOLIDWORKS server and installed interop must match build 34.4.1.1011.'
}
if (Get-Process -Name SLDWORKS -ErrorAction SilentlyContinue) {
    throw 'SOLIDWORKS is already running. Use a dedicated desktop session with the application stopped.'
}

$output = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputDirectory)
$prefix = $repository.TrimEnd('\') + '\'
if (Test-Path -LiteralPath $output) {
    throw 'Choose a new output directory.'
}
if ($output.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Choose an output directory outside the repository.'
}
$parent = Get-Item -LiteralPath (Split-Path -Parent $output)
if (-not $parent.PSIsContainer -or ($parent.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
    throw 'Use an existing plain output parent directory.'
}
$output = (New-Item -ItemType Directory -Path $output).FullName
$inputs = (New-Item -ItemType Directory -Path (Join-Path $output 'inputs')).FullName
$controlCopy = Join-Path $inputs 'control.SLDPRT'
Copy-Pinned $control $controlCopy
foreach ($name in $files.Keys) {
    Copy-Pinned $files[$name] (Join-Path $inputs $name)
}

$collectorCopy = Join-Path $output 'P04Readback.cs'
Copy-Pinned $collector $collectorCopy
$provenance = [ordered]@{
    source_revision = $revision
    recipe = 'P04'
    existing_receipt = $receipt
    existing_measurements = $measurements
    specification = $spec
    launcher = $launcher
    collector = $collector
    control = $control
    native_files = $files
    installed_executable_sha256 = (Get-FileHash -LiteralPath $binary.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    installed_interop_sha256 = (Get-FileHash -LiteralPath $interop.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    installed_constants_sha256 = (Get-FileHash -LiteralPath $constants.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
}
$provenancePath = Join-Path $output 'plan.json'
Write-NewJson $provenancePath $provenance
$planPin = @{
    sha256 = (Get-FileHash -LiteralPath $provenancePath -Algorithm SHA256).Hash.ToLowerInvariant()
    size_bytes = (Get-Item -LiteralPath $provenancePath).Length
}

$webExtensions = Join-Path ([Runtime.InteropServices.RuntimeEnvironment]::GetRuntimeDirectory()) 'System.Web.Extensions.dll'
Add-Type -Path $constants.FullName
Add-Type -Path $interop.FullName
Add-Type -Path $collectorCopy -ReferencedAssemblies @($interop.FullName, $constants.FullName, 'System.Core.dll', $webExtensions)
$run = [P04Readback]::Run($inputs, [string[]]@($files.Keys), $binary.FullName) | ConvertFrom-Json
foreach ($name in $files.Keys) {
    Assert-Bytes (Join-Path $inputs $name) $files[$name]
    Assert-Bytes (Join-Path $repository $files[$name].path) $files[$name]
}
Assert-Bytes $controlCopy $control
Assert-Bytes (Join-Path $repository $control.path) $control
Assert-Bytes (Join-Path $repository $receipt.path) $receipt
Assert-Bytes (Join-Path $repository $measurements.path) $measurements
Assert-Bytes $collectorCopy $collector
Assert-Bytes $provenancePath $planPin

$reportPath = Join-Path $output 'measurements.json'
Write-NewJson $reportPath ([ordered]@{
    schema = 1
    claim = 'supplemental_native_observation'
    plan_sha256 = $planPin.sha256
    source_bytes_verified_after_readback = $true
    run = $run
})
$verified = @($run.observations | Where-Object { $_.face_verified_before_and_after_rebuild })
$status = $run.status
if ($status -ceq 'observed' -and $verified.Count -ne $files.Count) {
    $status = 'incomplete'
}
Write-NewJson (Join-Path $output 'receipt.json') ([ordered]@{
    schema = 1
    status = $status
    plan_sha256 = $planPin.sha256
    measurements_sha256 = (Get-FileHash -LiteralPath $reportPath -Algorithm SHA256).Hash.ToLowerInvariant()
    observed_files = @($run.observations | Where-Object { $_.status -ceq 'observed' }).Count
    supporting_faces_verified = $verified.Count
})
if ($status -cne 'observed') {
    throw "Readback or face identity verification is incomplete. Inspect $reportPath"
}
Write-Output $output

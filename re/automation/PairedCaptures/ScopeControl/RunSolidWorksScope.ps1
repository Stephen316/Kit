[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$OutputDirectory,
    [Parameter(Mandatory)]
    [ValidatePattern('^[0-9a-f]{40}$')]
    [string]$SourceRevision
)

$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSEdition -ne 'Desktop' -or
    [Threading.Thread]::CurrentThread.GetApartmentState() -ne 'STA' -or
    -not [Environment]::Is64BitProcess) {
    throw 'Use 64-bit Windows PowerShell 5.1 in STA mode.'
}
$repository = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../../..')).Path
if ((git -C $repository rev-parse --verify HEAD) -cne $SourceRevision -or $LASTEXITCODE -ne 0) {
    throw 'The scope-control checkout is not at its selected source revision.'
}

function Get-Pin([string]$RelativePath) {
    $path = Join-Path $repository $RelativePath
    $info = Get-Item -LiteralPath $path
    if ($info.PSIsContainer -or ($info.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw "Expected a plain source file at $RelativePath."
    }
    $blob = git -C $repository rev-parse --verify ("${SourceRevision}:${RelativePath}")
    if ($LASTEXITCODE -ne 0 -or (git -C $repository hash-object --no-filters -- $path) -cne $blob -or
        $LASTEXITCODE -ne 0) {
        throw "Source bytes differ from Git at $RelativePath."
    }
    return [ordered]@{
        path = $RelativePath
        git_blob = $blob
        sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
        size_bytes = $info.Length
    }
}

function Write-NewJson([string]$Path, $Value) {
    $stage = "$Path.$([Guid]::NewGuid().ToString('N'))"
    try {
        $content = [Text.Encoding]::UTF8.GetBytes(($Value | ConvertTo-Json -Depth 45) + "`n")
        $file = [IO.File]::Open($stage, [IO.FileMode]::CreateNew)
        try {
            $file.Write($content, 0, $content.Length)
            $file.Flush($true)
        } finally { $file.Dispose() }
        [IO.File]::Move($stage, $Path)
    } finally { [IO.File]::Delete($stage) }
}

$relative = 're/automation/PairedCaptures/ScopeControl'
$launcher = Get-Pin "$relative/RunSolidWorksScope.ps1"
$collector = Get-Pin "$relative/SolidWorksScopeControl.cs"
$specification = Get-Pin "$relative/ScopeControlSpec.json"
$available = Get-Process -Name SLDWORKS -ErrorAction SilentlyContinue
if ($available) { throw 'SOLIDWORKS is already running.' }

$registration = (Get-Item -LiteralPath 'Registry::HKEY_CLASSES_ROOT\SldWorks.Application\CLSID').GetValue('')
$server = (Get-Item -LiteralPath "Registry::HKEY_CLASSES_ROOT\CLSID\$registration\LocalServer32").GetValue('')
$binary = Get-Item -LiteralPath $server
$interop = Get-Item -LiteralPath (Join-Path $binary.DirectoryName 'api/redist/SolidWorks.Interop.sldworks.dll')
$constants = Get-Item -LiteralPath (Join-Path $binary.DirectoryName 'api/redist/SolidWorks.Interop.swconst.dll')
$build = '34.4.1.1011'
if (@($binary, $interop, $constants).Where({ $_.VersionInfo.FileVersion -cne $build }).Count) {
    throw "The registered installation and installed interop must all match $build."
}

$output = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputDirectory)
if ((Test-Path -LiteralPath $output) -or
    $output.StartsWith($repository.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Choose a new private output directory outside the checkout.'
}
$parent = Get-Item -LiteralPath (Split-Path -Parent $output)
if (-not $parent.PSIsContainer -or ($parent.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
    throw 'Use an existing plain output parent directory.'
}
$output = (New-Item -ItemType Directory -Path $output).FullName
$specificationText = Get-Content -LiteralPath (Join-Path $repository $specification.path) -Raw
$web = Join-Path ([Runtime.InteropServices.RuntimeEnvironment]::GetRuntimeDirectory()) 'System.Web.Extensions.dll'
Add-Type -Path $constants.FullName
Add-Type -Path $interop.FullName
Add-Type -Path (Join-Path $repository $collector.path) -ReferencedAssemblies @($interop.FullName, $constants.FullName, 'System.Core.dll', $web)

$authored = [SolidWorksScopeControl]::Author($specificationText, $output, $binary.FullName)
Write-NewJson (Join-Path $output 'authoring.json') ($authored | ConvertFrom-Json)
$finished = [SolidWorksScopeControl]::Measure($specificationText, $output, $binary.FullName, $authored) | ConvertFrom-Json
foreach ($pin in @($launcher, $collector, $specification)) {
    if ((Get-Pin $pin.path).sha256 -cne $pin.sha256) {
        throw "Pinned source changed during native evidence capture at $($pin.path)."
    }
}

$reportPath = Join-Path $output 'report.json'
Write-NewJson $reportPath ([ordered]@{
    schema = 1
    scope = 'two-body-through-all-discovery'
    application = 'solidworks'
    application_build = $build
    source_revision = $SourceRevision
    specification_sha256 = $specification.sha256
    native_processes = $finished.native_processes
    sources = [ordered]@{ launcher = $launcher; collector = $collector; specification = $specification }
    cases = $finished.cases
})
Write-Output (Get-FileHash -LiteralPath $reportPath -Algorithm SHA256).Hash.ToLowerInvariant()

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
if ((git -C $repository rev-parse HEAD) -cne $SourceRevision -or $LASTEXITCODE -ne 0) {
    throw 'Select the exact recorded source revision.'
}
$authoring = 're/automation/PairedCaptures/SolidWorksAuthoring'
$pinned = @(
    "$authoring/RunTwoPad.ps1", "$authoring/TwoPadCapture.cs", "$authoring/SolidWorksCapture.cs",
    "$authoring/TwoPadComSession.cs",
    're/automation/PairSpecs.json', 're/solidworks/examples/.SLDPRT/example.SLDPRT'
)
function Read-Pins {
    $result = [ordered]@{}
    foreach ($name in $pinned) {
        $path = Join-Path $repository $name
        $info = Get-Item -LiteralPath $path
        if ($info.PSIsContainer -or ($info.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw "Expected a regular file for $name."
        }
        $blob = git -C $repository rev-parse --verify ("${SourceRevision}:${name}")
        if ($LASTEXITCODE -ne 0 -or (git -C $repository hash-object --no-filters -- $path) -cne $blob -or
            $LASTEXITCODE -ne 0) {
            throw "Source bytes differ from the selected Git commit for $name."
        }
        $result[$name] = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    return $result
}
function Write-Record([string]$Path, [string]$Content) {
    $file = [IO.File]::Open($Path, [IO.FileMode]::CreateNew)
    try {
        $bytes = [Text.Encoding]::UTF8.GetBytes($Content + "`n")
        $file.Write($bytes, 0, $bytes.Length)
        $file.Flush($true)
    } finally { $file.Dispose() }
}

$sources = Read-Pins
if (Get-Process -Name SLDWORKS -ErrorAction SilentlyContinue) {
    throw 'The capture requires a separately owned, empty SOLIDWORKS desktop.'
}
$classId = (Get-Item -LiteralPath 'Registry::HKEY_CLASSES_ROOT\SldWorks.Application\CLSID').GetValue('')
$server = (Get-Item -LiteralPath "Registry::HKEY_CLASSES_ROOT\CLSID\$classId\LocalServer32").GetValue('')
$binary = Get-Item -LiteralPath $server
$interop = Get-Item -LiteralPath (Join-Path $binary.DirectoryName 'api/redist/SolidWorks.Interop.sldworks.dll')
$constants = Get-Item -LiteralPath (Join-Path $binary.DirectoryName 'api/redist/SolidWorks.Interop.swconst.dll')
$build = '34.4.1.1011'
if (@($binary, $interop, $constants).Where({ $_.VersionInfo.FileVersion -cne $build }).Count) {
    throw "The registered application and installed interop must match $build."
}
$installed = [ordered]@{
    executable = (Get-FileHash -LiteralPath $binary.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    interop = (Get-FileHash -LiteralPath $interop.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    constants = (Get-FileHash -LiteralPath $constants.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
}
if ($installed.executable -cne '200ac2597814daaead89c1de698a45341850fa2fe0d8c094debb316009e7ea7f' -or
    $installed.interop -cne '423c0fd109006a13700a7b4703b56200ccde38552c96c327af371921408d7477' -or
    $installed.constants -cne 'b15e28ed5b2e8332d409ca79635f933a60e8cc0d9bd5ec980e2a2301220e7741') {
    throw 'The installed SOLIDWORKS files do not match the licensed measurement build pins.'
}
$output = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputDirectory)
$parent = Get-Item -LiteralPath (Split-Path -Parent $output)
if ((Test-Path -LiteralPath $output) -or -not $parent.PSIsContainer -or
    ($parent.Attributes -band [IO.FileAttributes]::ReparsePoint) -or
    $output.StartsWith($repository.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Use a new private output directory outside the repository.'
}
$output = (New-Item -ItemType Directory -Path $output).FullName
$web = Join-Path ([Runtime.InteropServices.RuntimeEnvironment]::GetRuntimeDirectory()) 'System.Web.Extensions.dll'
$code = @(
    (Join-Path $repository "$authoring/SolidWorksCapture.cs"),
    (Join-Path $repository "$authoring/TwoPadCapture.cs"),
    (Join-Path $repository "$authoring/TwoPadComSession.cs")
)
$phase = 'compile'
try {
    Add-Type -Path $constants.FullName
    Add-Type -Path $interop.FullName
    Add-Type -Path $code -ReferencedAssemblies @($interop.FullName, $constants.FullName, 'System.Core.dll', $web)
    $phase = 'authoring'
    $authored = [SolidWorksCapture]::CaptureTwoPad($repository, $output, $binary.FullName, $null)
    Write-Record (Join-Path $output 'authoring.json') $authored
    $phase = 'reopen'
    $observations = [SolidWorksCapture]::CaptureTwoPad($repository, $output, $binary.FullName, $authored) | ConvertFrom-Json
    if ((Read-Pins | ConvertTo-Json -Compress) -cne ($sources | ConvertTo-Json -Compress)) {
        throw 'Pinned measurement inputs changed during the capture.'
    }
    $reportPath = Join-Path $output 'report.json'
    Write-Record $reportPath (([ordered]@{
        schema = 1
        scope = 'solidworks-face-supported-two-pad-discovery'
        source_revision = $SourceRevision
        application_build = $build
        installed_files = $installed
        sources = $sources
        observations = $observations
    }) | ConvertTo-Json -Depth 45 -Compress)
    Write-Output (Get-FileHash -LiteralPath $reportPath -Algorithm SHA256).Hash.ToLowerInvariant()
} catch {
    $failure = $_.Exception.GetBaseException()
    Write-Record (Join-Path $output 'failure.json') (([ordered]@{
        phase = $phase
        source_revision = $SourceRevision
        application_build = $build
        installed_files = $installed
        type = $failure.GetType().Name
        message = $failure.Message
    }) | ConvertTo-Json -Compress)
    throw
}

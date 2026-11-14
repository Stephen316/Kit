[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('P01', 'P02', 'P03', 'P04', 'P05')]
    [string]$Recipe,
    [Parameter(Mandatory)]
    [ValidateSet('first', 'second')]
    [string]$Phase,
    [Parameter(Mandatory)]
    [string]$OutputDirectory,
    [Parameter(Mandatory)]
    [string]$InteropAssembly
)

$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSEdition -ne 'Desktop' -or
    [Threading.Thread]::CurrentThread.GetApartmentState() -ne 'STA' -or
    -not [Environment]::Is64BitProcess) {
    throw 'Run with 64-bit Windows PowerShell in STA mode.'
}
$repository = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../../..')).Path
$interop = (Resolve-Path -LiteralPath $InteropAssembly).Path
$webExtensions = Join-Path ([Runtime.InteropServices.RuntimeEnvironment]::GetRuntimeDirectory()) 'System.Web.Extensions.dll'
$output = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputDirectory)
$caseFolder = Join-Path $output $Recipe
if ($Phase -eq 'first' -and (Test-Path -LiteralPath $caseFolder)) {
    throw 'Select a new recipe directory for the first save.'
}
if ($Phase -eq 'second' -and -not (Test-Path -LiteralPath (Join-Path $caseFolder 'first.json') -PathType Leaf)) {
    throw 'The first phase receipt is missing.'
}

Add-Type -Path $interop
Add-Type -Path (Join-Path $PSScriptRoot 'SolidWorksCapture.cs') -ReferencedAssemblies @($interop, 'System.Core.dll', $webExtensions)
[SolidWorksCapture]::Run($repository, $output, $Recipe, $Phase)

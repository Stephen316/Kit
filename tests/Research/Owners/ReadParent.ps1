param([int]$ProcessNumber)
$ErrorActionPreference = 'Stop'
$Value = Get-CimInstance -ClassName Win32_Process | Where-Object { $_.ProcessId -eq $ProcessNumber }
if ($null -eq $Value) { exit 3 }
[Console]::Write($Value.ParentProcessId)

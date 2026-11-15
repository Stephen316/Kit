# Windows owner fixture collector startup

At PR head `786736c55`, the Windows `timeout-missing` owner guard fixture timed out waiting for a disposable PowerShell collector to exit. The failure occurred before the recovery code read the missing ticket. The other 89 cases in the job passed. [Hosted failure](https://github.com/TryUniCAD/Kit/actions/runs/43770822331/job/132986200968)

Use the base Python executable in isolated mode for the disposable collector that only supplies an exit code. Keep the distinct owned PowerShell target process, its Win32 handle, the original deadline and all recovery assertions. The production SOLIDWORKS collector continues to run its normal PowerShell command.

# Run the SOLIDWORKS capture harness

Use a licensed 64-bit SOLIDWORKS installation with an English part template and Windows PowerShell 5.1. The harness uses the registered SOLIDWORKS COM server. Check the revision it reports before comparing the results to the original SOLIDWORKS 2026 build `34.4.1`.

The [capture source](../../../re/automation/PairedCaptures/SolidWorksAuthoring/SolidWorksCapture.cs) matches the preserved authoring harness with SHA-256 `0e90cdfc47f4295e15907505c9870620bb8fab2f82437d57a7f7521c22adb238`. The [launcher](../../../re/automation/PairedCaptures/SolidWorksAuthoring/RunSolidWorks.ps1) resolves the recipe and control from the repository and requires an explicit destination and case.

1. Close or save open SOLIDWORKS work and use an isolated application session. Choose an unused output location outside the repository's capture folders.
2. Run the first phase for an explicit case. Set the interop path to the installed `SolidWorks.Interop.sldworks.dll` for the registered build.

   ```powershell
   powershell.exe -NoProfile -STA -File re/automation/PairedCaptures/SolidWorksAuthoring/RunSolidWorks.ps1 -Recipe P01 -Phase first -OutputDirectory C:/Temp/KitCapture -InteropAssembly 'C:/Path/SOLIDWORKS/SolidWorks.Interop.sldworks.dll'
   ```

3. Quit SOLIDWORKS fully after the first phase finishes. Run the same command with `-Phase second`. The harness requires a different application process ID from the first phase and verifies the unchanged baseline-A SHA-256 before continuing.
4. Inspect the new case directory for both baselines, edited and variant parts, `measurements.json`, and `receipt.json`. Keep the original capture bundles and their digests intact. Repeat runs produce new evidence, including new native file hashes.

For discovery use P01, P03, and P04. Keep P02 reserved for circular-sketch qualification and P05 reserved for frozen-rule holdout evaluation. The launcher selects only the named case.

The original capture record documents the independently authored fixtures and their measured results. The checked-in launcher received a static syntax check after its paths were made configurable. [SOLIDWORKS capture entry](../../Changes/Research/SolidWorksPairedCaptures.md)

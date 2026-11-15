# SOLIDWORKS discovery census face producer

The discovery census resolves the neutral sketch's face producer through the saved feature selection path, including the typed `end-face:` occurrence. It reports a producer only when the path identifies one known timeline feature. The hosted support check requires matched native support, selection presence and the expected `BlindBoss` producer across all eleven P04 discovery captures.

Generate the report with `python re/automation/SolidworksCensus.py --output /private/SolidworksDiscoveryCensus.json`. Hosted CI runs the support check against the report from that exact revision. The original captures measured the face support type. The discovery recipe supplies the expected producer name. The [separate licensed face replay](SolidWorksLicensedCutSupport.md) verifies the owner ID, cap normal and area against both native observation phases.

The previous [hosted census](https://github.com/TryUniCAD/Kit/actions/runs/43765839649) decoded all 25 files and matched 757 comparisons. Its eleven unobserved rows were the P04 face producers. [Typed face occurrence in census output](../../../../Gotchas/Conversion/SolidWorksHistoricalFaceCensus.md)

The local research replay at `d5102489` decoded the same 25 files and matched all 768 comparisons. All eleven P04 entries recorded `BlindBoss` as the face producer. The report SHA-256 is `8986598e5e43898076c15e660092d8709871fd7529aae55715e4d30da10a6f10`. Hosted verification of the updated check is pending.

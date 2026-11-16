# Add previews to a fresh SOLIDWORKS boss candidate

Add the optional `preview_colors` field to the fixture JSON passed to `VerifyFreshBoss.py`. Its value can be `[[244, 248, 252], [25, 36, 53], [136, 166, 191]]`. The three distinct RGB triples set the background, outline and fill in that order. Each channel must be an integer from 0 to 255. Use `--candidate PATH` to export the verified `.SLDPRT` or omit it to get only the report. [Candidate export](SolidWorksFreshBossCandidate.md)

The existing package encoder renders the fresh sketch and signed blind boss into the 1420 × 710 DIB and 640 × 480 PNG members. Before export, independent readers decode both stored members and the verifier checks the requested palette, each full raster and the PNG resolution. The 32-member report includes `preview_sha256.Preview` and `preview_sha256.PreviewPNG` for the two native member byte strings. The `archive_sha256` still identifies the whole assembled part. Omitting the palette keeps the original 30-member archive and report.

The preview scope covers those two image members. `VisualStates` and licensed SOLIDWORKS open, driving edit, rebuild, save and reopen require separate evidence. [Fresh boss fixture](SolidWorksFreshBossFixture.md)

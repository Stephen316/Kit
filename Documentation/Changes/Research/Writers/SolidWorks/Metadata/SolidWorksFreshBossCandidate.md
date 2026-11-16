# Export a verified fresh SOLIDWORKS boss candidate

Pass `--candidate PATH` to `VerifyFreshBoss.py` with the ordinary fixture context. For example, run `python -B re/solidworks/WriterResearch/VerifyFreshBoss.py --fixture-context fixture.json --candidate output/FreshBoss.SLDPRT` in the hosted Kit environment. The programmatic entry point also accepts a keyword-only `Candidate` path. Omitting it returns the existing verification report and writes no candidate. The fixture context still supplies the document identity recorded inside the archive. [Fixture context and readback](SolidWorksFreshBossFixture.md) · [Research entry point](../../../../../../re/solidworks/WriterResearch/VerifyFreshBoss.py)

The candidate bytes come from the independently authored neutral Front sketch and blind boss. The verifier reads back the assembled part, feature ownership, dimensions, signed bounds, mass and sidecars before staging any file. The reported `archive_sha256` identifies the exact published bytes.

Choose an unused `.SLDPRT` path in an existing directory that supports hard links. The verifier writes, flushes and closes a temporary sibling before publishing it in one filesystem operation. The operation refuses an existing destination, including a competing publisher that arrives during staging. A staged write failure leaves the destination absent, and the verifier removes the temporary sibling as it exits.

This is a source-only research candidate. Pinned static checks cover the changed entry point. Hosted publication and no-replace verification, and licensed SOLIDWORKS open, driving edit, rebuild, save and reopen, remain separate evidence steps.

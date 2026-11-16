# Compare two retained SOLIDWORKS automatic-scope saves

The scope archive command accepts an optional second private archive with `--compare-repeat <archive>`. Give the save at `c996f65f` as the positional archive and the preceding save at `12e4936e` as the repeat. The command checks both archive digests, both resolved-stream digests and both sets of committed authoring sources. It applies the existing bounded walk to each save and retains both sets of raw observations. [Original archive and replay command](ProvisionalScopeArchive.md)

The second archive has SHA-256 `9a40bae98367deb569d0cf2662cadb8421807dee49470af12233390b8f6bfdd6`. Its resolved stream has SHA-256 `1e67e1aeccdb7a856f65175486d42c062100ad147c2a6c18108b7a138df04a46`. Both streams are 25,362 bytes. The saved scope word is 1, and the same ordered scope records identify body 101 from feature 32 and body 102 from feature 40. Both preserve recent atom IDs 103 and 104 and carry candidate Cut profile slot 350. The inspected surface clock words differ between saves and remain recorded.

The offline replay produced the comparison report SHA-256 `84d8a91c3f7fab14f870301c82621647c68f1110efe1070f929780df999fbace`. The single-archive command reproduced its original report SHA-256 `4da047efcf25cb09ce91132549ef7c4d082bb851cf97edf1271cd9f4833079ac`. The results cover exact provisional automatic saves. The native Auto-select setting, profile-slot resolution, freshly reopened explicit controls and semantic qualification remain open. [Licensed scope control](ThroughAllScopeControl.md)

Use the [typed configuration and resolved prefix replay](AutomaticScopeResolvedPrefix.md) to follow the first boss to its allocated sketch in both archives.

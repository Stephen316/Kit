# Verify P04 body identity in the saved partition

```text
python re/solidworks/archive/PartitionIdentity.py
```

The audit verifies the original P04 SOLIDWORKS receipt and independent reopen inventory at Git revision `466dcb172dfa3803463e07ccde963ba01671d200`. Each of the eleven native archives is read from its Git blob and matched against its recorded size and SHA-256. The typed Cut reader independently follows each operation to the end of ResolvedFeatures.

All eleven active partitions use schema `SCH_3701250_37102_13006`. The ordinary decoder produces one solid region in every file. The saved native shell 7 and region 47 point back to each other and identify body owner 3. Each shell's reciprocal face chain covers its entire decoded region. The ten blind cuts each have eleven linked faces. The through-all cut has ten. The named `ATOM_ID_2001` attribute for owner 3 stores atom 102. The typed Cut operation also stores atom 102 and identifies body 101, its earlier Boss feature 34, and Cut feature 46. The identity holds through the original width, height, depth, plane and units variations.

The P04 audit report SHA-256 is `831482558f7597f916f5e673f0337d7ab4416a0839fabde8dcc372301402d5f5`. Its per-file evidence includes the active stream and partition hashes, native region and shell offsets, individual face links, and the saved atom attribute and value offsets.

The [two archived automatic-scope saves](AutomaticScopeBodyIdentity.md) exercise the same parser with two owners. In both saves their native shell chains and atom attributes identify resolved bodies 101 and 102 independently of the region bounds. Run that earlier command with `--compare-repeat` and `--inspect-map` for the full paired comparison. The one-body P04 evidence applies to this measured schema. Independent multi-body explicit-selection coverage remains outstanding.

# SOLIDWORKS configuration manager part return

The A12 [research codec](../../../../re/solidworks/WriterResearch/CmgrPartEnd.py) reads and constructs the inline part object and its containing part return in `Contents/CMgr`. The caller supplies the archive generation, condition 1 and atom IDs in enumeration order. The supported shape is an ordinary generation-19000 standalone part with condition 1 clear, empty optional lists and pointers, no frozen features and at most two atom-map entries with zero values. [Native field and branch evidence](../../../../re/solidworks/WriterResearch/CmgrAtoms.md)

The read-only replay used 25 receipt-pinned saves at `466dcb172dfa3803463e07ccde963ba01671d200`. It retained the archive map from the opening, resumed at the independently attributed linked-atom starts and parsed both aliases back to part object 4. The part return and the following 14 bytes of manager fields preserve the next index and both maps. The next token defines the external object.

| Captures | Part span in bytes | Next archive index | Saved atom IDs in order |
| --- | --- | --- | --- |
| 6 P01 | 1692–1804 | 9 | Empty |
| 8 P03 | 1758–1878 | 11 | 101 |
| 8 P04 | 1840–1968 | 12 | 101, 102 |
| 3 P04 | 1840–1968 | 12 | 102, 101 |

The replay digest is `093d6b0ba1546d7812a14cf2e592d4b2a0e30a2714d8851671a41fad5ea4fc27`. It covers each file digest, part start and return offsets, ordered atom IDs and part slice digest in receipt order.

Hosted `CheckCmgr` invokes [`VerifyCmgrColor.py`](../../../../re/solidworks/WriterResearch/VerifyCmgrColor.py) in a separate process. The verifier compares generated part bytes with each pinned archive, checks that the writer leaves its shared allocator unchanged and requires all four observed record forms. Hosted reconstruction and full native open, rebuild, edit and save remain pending.

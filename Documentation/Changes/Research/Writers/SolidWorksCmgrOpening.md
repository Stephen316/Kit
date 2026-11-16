# SOLIDWORKS configuration manager opening construction

The [research constructor](../../../../re/solidworks/WriterResearch/CmgrOpening.md) writes the manager and its first part up to the start of the part's visual properties. The caller supplies the clean node states, the checked part material flag, the `Default` configuration name and the manager feature FILETIME. The constructor allocates the class and object slots and advances the first native configuration ID from 0 to 1.

The [inherited feature constructor](../../../../re/solidworks/WriterResearch/CmgrInherited.py) writes the common feature fields after the part's visual record. It takes the part feature FILETIME separately. The format limit is generation 19000 on the pinned SOLIDWORKS `34.4.1.1011` profile. The visual record, base configuration and subsequent objects are composed separately.

Read-only replay reproduced bytes 0–278 and 1095–1206 in six receipt-pinned P01 and eight P03 saves. The [comparison](../../../../re/solidworks/WriterResearch/VerifyCmgrOpen.py) also verifies the next archive index 9 and the native configuration allocator state. The existing hosted archive verifier now calls this comparison. A hosted run and a licensed native open of a composed artifact remain pending.

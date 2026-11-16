# SOLIDWORKS configuration manager material and RealView construction

The [standalone research constructor](../../../../re/solidworks/WriterResearch/CmgrVisualPrefix.py) writes the inline generation-19000 material and RealView records through the enclosing visual object's DSPBR presence word. It takes the document's allocated PW appearance ID, packed visual colors, legacy material ID name, native material locator and explicit RealView settings. The locator belongs to the target installation. The semantic material profile is the untextured default `color.p2m` with shader `defaultplastic`.

A read-only replay reproduced bytes 278–795 in six receipt-pinned P01 and eight P03 saves and preserved next archive index 9. The [hosted verifier](../../../../re/solidworks/WriterResearch/VerifyCmgrColor.py) applies the [separate comparison](../../../../re/solidworks/WriterResearch/VerifyCmgrVisual.py) to those same recipe IDs. [Field ownership and remaining limits](../../../../re/solidworks/WriterResearch/CmgrVisual.md#material-and-realview-research-constructor)

Hosted execution of the added comparison, production composition and licensed acceptance remain pending.

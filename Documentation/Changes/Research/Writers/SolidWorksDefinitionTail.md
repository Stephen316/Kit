# Encode the SOLIDWORKS part Definition tail

The A12 research codec in [DefinitionTail.py](../../../../re/solidworks/WriterResearch/DefinitionTail.py) reads and constructs the terminal fragment of `Contents/Definition`. Generation 18000 uses one little-endian double. The observed generation-19000 path writes a signed 32-bit zero count for the empty variability vector followed by the part's little-endian double. The encoder takes the chosen generation and an interpreted terminal value supplied by the caller.

The decoder takes the generation and a caller-established start of the terminal fragment. It checks the zero count where present and requires the final double to end at the stream boundary. Unsupported generations, nonzero counts, short fields and trailing data are refused. The observed archive-version threshold of 18114 explains the extra field. The two evidenced generations define the research codec's admission.

The generation-18000 emitter and 25 receipt-pinned generation-19000 captures establish the two layouts. The research decoder read all 25 generation-19000 tails and reported a terminal value of `1000.0` after validating each zero count. The complete Definition encoder still requires the earlier fields and application verification of generated documents. [Native tail evidence](../../../../re/solidworks/WriterResearch/DefinitionJournal.md#part-definition-tail)

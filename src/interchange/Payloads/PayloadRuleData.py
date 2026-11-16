from interchange.Payloads.DirectPayloadRules import KDirectPayloadRules
from interchange.Payloads.SemanticPayloadRules import KSemanticPayloadRules

# format evidence stays ordered because stronger native tags must win before fallbacks
KFormatPayloadRules = KDirectPayloadRules + KSemanticPayloadRules

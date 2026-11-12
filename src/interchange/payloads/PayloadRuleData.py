from interchange.payloads.DirectPayloadRules import KDirectPayloadRules
from interchange.payloads.SemanticPayloadRules import KSemanticPayloadRules

# format evidence stays ordered because stronger native tags must win before fallbacks
KFormatPayloadRules = KDirectPayloadRules + KSemanticPayloadRules

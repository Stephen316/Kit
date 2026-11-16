from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Core.Cut.CutRuleSource import CutRuleSource
from convert.adapters.solidworks.Resolved.Support.SupportPlane import SupportPlane


# the cut owns both its active frame and the rule sources from the selected configuration
@Dataclass(frozen=True, slots=True)
class CutSource:
    Support: SupportPlane
    BossId: int
    CutId: int
    Rules: CutRuleSource

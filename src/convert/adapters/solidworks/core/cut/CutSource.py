from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.core.cut.CutRuleSource import CutRuleSource
from convert.adapters.solidworks.resolved.support.SupportPlane import SupportPlane


# the cut owns both its active frame and the rule sources from the selected configuration
@Dataclass(frozen=True, slots=True)
class CutSource:
    Support: SupportPlane
    BossId: int
    Rules: CutRuleSource

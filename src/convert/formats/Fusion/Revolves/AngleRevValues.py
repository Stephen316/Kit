# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.RevolveSpan import GetAngleSpan
from interchange.records.RecordParameter import Parameter


# current parameter values remain authoritative when a body needs numeric sweep limits
def ReadAngleSpan(
    Definition: AngularRevolve, Params: dict[str, Parameter]
) -> tuple[float, float]:
    Along = Params.get(Definition.AlongParameterId)
    Against = (
        None
        if Definition.AgainstParameterId is None
        else Params.get(Definition.AgainstParameterId)
    )
    if Along is None or (Definition.AgainstParameterId is not None and Against is None):
        raise ValueError("Missing Fusion Revolve angle parameter")
    return GetAngleSpan(
        float(Along.value.value),
        None if Against is None else float(Against.value.value),
        Definition.SideMode,
    )

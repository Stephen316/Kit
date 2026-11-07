# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from interchange.brep.topology.BrepModel import BrepModel


# independent results preserve their distinct body topology in the same component document
def JoinRevModels(Models: tuple[BrepModel, ...]) -> BrepModel:
    return BrepModel(
        curves=tuple(Item for Model in Models for Item in Model.curves),
        pcurves=tuple(Item for Model in Models for Item in Model.pcurves),
        surfaces=tuple(Item for Model in Models for Item in Model.surfaces),
        vertices=tuple(Item for Model in Models for Item in Model.vertices),
        edges=tuple(Item for Model in Models for Item in Model.edges),
        coedges=tuple(Item for Model in Models for Item in Model.coedges),
        loops=tuple(Item for Model in Models for Item in Model.loops),
        wires=tuple(Item for Model in Models for Item in Model.wires),
        faces=tuple(Item for Model in Models for Item in Model.faces),
        face_uses=tuple(Item for Model in Models for Item in Model.face_uses),
        shells=tuple(Item for Model in Models for Item in Model.shells),
        shell_uses=tuple(Item for Model in Models for Item in Model.shell_uses),
        regions=tuple(Item for Model in Models for Item in Model.regions),
        bodies=tuple(Item for Model in Models for Item in Model.bodies),
    )

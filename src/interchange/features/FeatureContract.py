# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from interchange.core.ModelBase import ModelBase


# feature definitions share one runtime contract so future kinds remain extensible
class FeatureDef(ModelBase):
    locals()["__slots__"] = ()

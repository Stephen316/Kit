# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import Field
from typing import ClassVar
from typing import Protocol


# reflection needs a narrow dataclass contract without weakening constructors to arbitrary values
class DataRecord(Protocol):
    __dataclass_fields__: ClassVar[dict[str, Field[object]]]


# record reconstruction calls record constructors with decoded field keyword values
class RecordCtor(Protocol):

    # callable contract lets decoders accept record constructors without type coupling
    def __call__(self, **FieldValues: object) -> object:
        """Callable contract lets decoders accept record constructors."""

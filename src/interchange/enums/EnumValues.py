# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from interchange.enums.EnumBase import WireEnum


# value categories preserve parameter meaning beyond primitive python representation
class ValueKind(WireEnum):
    LENGTH = "length"
    ANGLE = "angle"
    QUANTITY = "quantity"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    STRING = "string"
    KLength = "length"
    KAngle = "angle"
    KQuantity = "quantity"
    KNumber = "number"
    KInteger = "integer"
    KBoolean = "boolean"
    KString = "string"


# parameter roles retain whether downstream systems may drive each value
class ParameterRole(WireEnum):
    DRIVING = "driving"
    DRIVEN = "driven"
    REFERENCE = "reference"
    DERIVED = "derived"
    KDriving = "driving"
    KDriven = "driven"
    KReference = "reference"
    KDerived = "derived"

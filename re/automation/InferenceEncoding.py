# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import math
import struct
from dataclasses import dataclass
from fractions import Fraction

import numpy

FORMATS = {
    "u8": "B",
    "i8": "b",
    "u16": "H",
    "i16": "h",
    "u32": "I",
    "i32": "i",
    "u64": "Q",
    "i64": "q",
    "f32": "f",
    "f64": "d",
}
ENDIANS = {"little": "<", "big": ">"}
POWERS = {-2, -1, 1, 2, 3}


def number(value):
    if type(value) not in (int, float) or not -1e100 <= value <= 1e100:
        raise ValueError("inference quantities must be finite bounded numbers")
    return Fraction(str(value))


@dataclass(frozen=True)
class Encoding:
    kind: str
    endian: str
    unit: str
    scale: Fraction
    offset: Fraction
    power: int
    factors: tuple

    @classmethod
    def from_record(cls, record, controls):
        if (
            not isinstance(record, dict)
            or not {"type", "endian", "unit", "scale", "offset"} <= record.keys()
            or record.keys()
            - {"type", "endian", "unit", "scale", "offset", "power", "factors"}
        ):
            raise ValueError("invalid inference encoding keys")
        kind, endian, unit = (record[key] for key in ("type", "endian", "unit"))
        if (
            not isinstance(kind, str)
            or kind not in FORMATS
            or not isinstance(endian, str)
            or endian not in ENDIANS
            or not isinstance(unit, str)
            or not unit.strip()
            or len(unit) > 32
        ):
            raise ValueError("invalid inference encoding type, endian, or unit")
        power, factors = record.get("power", 1), record.get("factors", {})
        if (
            type(power) is not int
            or power not in POWERS
            or not isinstance(factors, dict)
            or len(factors) > 2
            or factors.keys() - controls
            or any(
                type(item) is not int or item not in POWERS for item in factors.values()
            )
        ):
            raise ValueError("invalid inference formula")
        scale, offset = number(record["scale"]), number(record["offset"])
        if not scale:
            raise ValueError("an inference encoding must vary with its input")
        if kind.endswith("8"):
            endian = "little"
        return cls(
            kind, endian, unit, scale, offset, power, tuple(sorted(factors.items()))
        )

    @property
    def codec(self):
        return struct.Struct(ENDIANS[self.endian] + FORMATS[self.kind])

    @property
    def floating(self):
        return self.kind.startswith("f")

    def record(self):
        return {
            "type": self.kind,
            "endian": self.endian,
            "unit": self.unit,
            "scale": str(self.scale),
            "offset": str(self.offset),
            "power": self.power,
            "factors": dict(self.factors),
        }

    def expected(self, sample, tolerance):
        try:
            coefficient = self.scale
            for name, power in self.factors:
                coefficient *= sample.controls[name] ** power
            scaled = coefficient * sample.value**self.power + self.offset
            if not self.floating:
                if scaled.denominator != 1:
                    return None
                value = scaled.numerator
                return Expected(self.codec.pack(value), value, None)
            value = float(scaled)
            if not math.isfinite(value):
                return None
            interval = None
            if tolerance:
                low, high = sample.value - tolerance, sample.value + tolerance
                bounds = [low, high]
                if low <= 0 <= high:
                    if self.power < 0:
                        return None
                    bounds.append(0)
                projected = [
                    coefficient * bound**self.power + self.offset for bound in bounds
                ]
                interval = float(min(projected)), float(max(projected))
                if not all(math.isfinite(bound) for bound in interval):
                    return None
            return Expected(self.codec.pack(value), value, interval)
        except (OverflowError, struct.error, ZeroDivisionError):
            return None


@dataclass(frozen=True)
class Expected:
    exact: bytes
    value: int | float
    interval: tuple | None

    def matches(self, data, observed):
        return data == self.exact or (
            self.interval is not None
            and self.interval[0] <= observed <= self.interval[1]
        )

    def patterns(self, encoding):
        yield self.exact
        if encoding.floating:
            dtype = numpy.float32 if encoding.kind == "f32" else numpy.float64
            rounded = dtype(encoding.codec.unpack(self.exact)[0])
            with numpy.errstate(over="ignore", under="ignore"):
                for direction in (dtype(-numpy.inf), dtype(numpy.inf)):
                    neighbor = float(numpy.nextafter(rounded, direction))
                    if math.isfinite(neighbor):
                        encoded = encoding.codec.pack(neighbor)
                        if self.matches(encoded, neighbor):
                            yield encoded

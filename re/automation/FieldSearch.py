"""Search aligned record bodies for bounded numeric encodings of measured values."""

from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from math import isfinite
import struct


@dataclass(frozen=True)
class Sample:
    identity: str
    millimetres: float
    body: bytes


@dataclass(frozen=True)
class Encoding:
    kind: str
    order: str
    unit: str
    sign: str

    @property
    def format(self):
        return ORDERS[self.order] + FORMATS[self.kind]

    @property
    def width(self):
        return struct.calcsize(self.format)

    @property
    def label(self):
        return f"{self.kind}:{self.order}:{self.unit}:{self.sign}"


FORMATS = {"f32": "f", "f64": "d", "i16": "h", "i32": "i", "i64": "q"}
ORDERS = {"little": "<", "big": ">"}
UNITS = {
    "m": Fraction(1, 1000),
    "cm": Fraction(1, 10),
    "mm": Fraction(1),
    "in": Fraction(5, 127),
    "um": Fraction(1000),
}
ENCODINGS = tuple(
    Encoding(*values) for values in product(FORMATS, ORDERS, UNITS, ("signed", "magnitude"))
)


def patterns(encoding, millimetres):
    scaled = Fraction(str(millimetres)) * UNITS[encoding.unit]
    if encoding.sign == "magnitude":
        scaled = abs(scaled)
    try:
        if encoding.kind.startswith("i"):
            return {struct.pack(encoding.format, int(scaled))} if scaled.denominator == 1 else set()
        raw = struct.pack(encoding.format, float(scaled))
    except (OverflowError, struct.error):
        return set()
    if not isfinite(struct.unpack(encoding.format, raw)[0]):
        return set()
    code = int.from_bytes(raw, encoding.order)
    limit = 1 << (encoding.width * 8)
    neighbours = (code - 1, code, code + 1)
    if struct.unpack(encoding.format, raw)[0] == 0:
        sign = limit // 2
        neighbours = (0, 1, sign, sign + 1)
    values = set()
    for candidate in neighbours:
        if 0 <= candidate < limit:
            encoded = candidate.to_bytes(encoding.width, encoding.order)
            if isfinite(struct.unpack(encoding.format, encoded)[0]):
                values.add(encoded)
    return values


def offsets(body, values):
    result = set()
    for needle in values:
        start = body.find(needle)
        while start != -1:
            result.add(start)
            start = body.find(needle, start + 1)
    return result


def aligned_hits(samples, located):
    common = {}
    for anchor in ("start", "end"):
        shifts = [0 if anchor == "start" else len(sample.body) for sample in samples]
        positions = set.intersection(
            *(set(hit - shift for hit in hits) for hits, shift in zip(located, shifts, strict=True))
        )
        for position in sorted(positions):
            key = tuple(position + shift for shift in shifts)
            common.setdefault(key, []).append({"anchor": anchor, "offset": position})
    return common


def search(samples, encodings=ENCODINGS):
    """Intersect exact and adjacent-float pattern hits over a measured sample grid."""
    samples = tuple(samples)
    encodings = tuple(encodings)
    if (
        len(samples) < 2
        or len({sample.identity for sample in samples}) != len(samples)
        or len({sample.millimetres for sample in samples}) < 2
        or any(not sample.body or not isfinite(sample.millimetres) for sample in samples)
    ):
        raise ValueError("field search needs distinct samples and finite contrasting values")

    candidates, rejected = [], []
    for encoding in encodings:
        predicted = [patterns(encoding, sample.millimetres) for sample in samples]
        if not all(predicted):
            rejected.append(
                {
                    "encoding": encoding.label,
                    "reason": "unrepresentable",
                    "examples": [
                        sample.identity
                        for sample, values in zip(samples, predicted, strict=True)
                        if not values
                    ],
                }
            )
            continue
        located = [
            offsets(sample.body, values) for sample, values in zip(samples, predicted, strict=True)
        ]
        if not all(located):
            rejected.append(
                {
                    "encoding": encoding.label,
                    "reason": "predicted_bytes_absent",
                    "examples": [
                        sample.identity
                        for sample, hits in zip(samples, located, strict=True)
                        if not hits
                    ],
                }
            )
            continue
        matched = aligned_hits(samples, located)
        if not matched:
            rejected.append(
                {
                    "encoding": encoding.label,
                    "reason": "no_consistent_alignment",
                    "sample_hits": {
                        sample.identity: sorted(hits)
                        for sample, hits in zip(samples, located, strict=True)
                    },
                }
            )
            continue
        for positions, anchors in matched.items():
            rows = {}
            for sample, position in zip(samples, positions, strict=True):
                data = sample.body[position : position + encoding.width]
                value = struct.unpack(encoding.format, data)[0]
                rows[sample.identity] = {
                    "body_offset": position,
                    "bytes_hex": data.hex(),
                    "value_in_candidate_unit": value,
                }
            candidates.append({"encoding": encoding.label, "alignments": anchors, "samples": rows})
    return {"models_examined": len(encodings), "candidates": candidates, "rejected": rejected}

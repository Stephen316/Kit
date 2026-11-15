# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import hashlib
import math
import re
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations

import numpy

from InferenceEncoding import Encoding, number
from Records import canonical, digest, label

MAX_SAMPLES = 48
MAX_ENCODINGS = 128
MAX_HYPOTHESES = 24
MAX_SPAN = 1024 * 1024
MAX_WORK = 32 * MAX_SPAN
MAX_STREAM_BYTES = 128 * MAX_SPAN
MAX_REPORT_BYTES = 768 * 1024
SAMPLE_FIELDS = {
    "id",
    "lineage",
    "sha256",
    "stream",
    "data",
    "start",
    "length",
    "value",
    "controls",
}


@dataclass(frozen=True)
class Sample:
    identity: str
    lineage: str
    sha256: str
    stream: str
    data: bytes
    start: int
    length: int
    value: Fraction
    controls: dict

    @classmethod
    def from_record(cls, record, controls):
        if not isinstance(record, dict) or record.keys() != SAMPLE_FIELDS:
            raise ValueError(
                "inference samples require an exact evidence and span record"
            )
        identity, lineage = label(record["id"]), label(record["lineage"])
        checksum, stream, data = (record[key] for key in ("sha256", "stream", "data"))
        start, length = record["start"], record["length"]
        if (
            not isinstance(checksum, str)
            or not re.fullmatch(r"[a-f0-9]{64}", checksum)
            or not isinstance(stream, str)
            or not stream.strip()
            or len(stream) > 192
            or not isinstance(data, bytes)
            or type(start) is not int
            or type(length) is not int
            or not 0 <= start < len(data)
            or not 1 <= length <= min(MAX_SPAN, len(data) - start)
        ):
            raise ValueError("inference sample has invalid source pin, stream, or span")
        control_values = record["controls"]
        if not isinstance(control_values, dict) or control_values.keys() != controls:
            raise ValueError(
                "inference sample does not cover the declared control axes"
            )
        return cls(
            identity,
            lineage,
            checksum,
            stream,
            data,
            start,
            length,
            number(record["value"]),
            {key: number(value) for key, value in control_values.items()},
        )

    def record(self):
        return {
            "lineage": self.lineage,
            "sha256": self.sha256,
            "stream_sha256": hashlib.sha256(self.data).hexdigest(),
            "stream": self.stream,
            "start": self.start,
            "length": self.length,
            "value": str(self.value),
            "controls": {name: str(value) for name, value in self.controls.items()},
        }


def identity(sample):
    return sample.identity


def parse_inputs(discovery, holdout, challenges, encodings, confounds, tolerance):
    if (
        any(
            not isinstance(split, (tuple, list))
            for split in (discovery, holdout, challenges)
        )
        or len(discovery) < 2
        or sum(map(len, (discovery, holdout, challenges))) > MAX_SAMPLES
        or not isinstance(encodings, (tuple, list))
        or not 1 <= len(encodings) <= MAX_ENCODINGS
        or not isinstance(confounds, (tuple, list))
        or len(confounds) > 8
    ):
        raise ValueError(
            "inference split, encoding, or control count is outside budget"
        )
    controls = {label(name) for name in confounds}
    if len(controls) != len(confounds):
        raise ValueError("inference controls must be unique")
    tolerance = number(tolerance)
    if tolerance < 0:
        raise ValueError("inference tolerance must be nonnegative")
    splits = tuple(
        tuple(
            sorted(
                (Sample.from_record(entry, controls) for entry in split), key=identity
            )
        )
        for split in (discovery, holdout, challenges)
    )
    samples = sum(splits, ())
    if len({item.identity for item in samples}) != len(samples) or len(
        {item.sha256 for item in samples}
    ) != len(samples):
        raise ValueError(
            "inference needs distinct sample IDs and source files across splits"
        )
    if len({item.stream for item in samples}) != 1:
        raise ValueError("inference spans must come from one aligned stream scope")
    discovery_lineages = {item.lineage for item in (*splits[0], *splits[2])}
    if discovery_lineages & {item.lineage for item in splits[1]}:
        raise ValueError("discovery and challenge lineages cannot appear in holdout")
    if sum(len(item.data) for item in samples) > MAX_STREAM_BYTES:
        raise ValueError("inference evidence exceeds the stream byte budget")
    codec_options = {Encoding.from_record(record, controls) for record in encodings}
    if sum(item.length for item in splits[0]) * len(codec_options) > MAX_WORK:
        raise ValueError("inference work exceeds the bounded search budget")
    ordered = sorted(codec_options, key=encoding_key)
    return splits, ordered, controls, tolerance


def encoding_key(encoding):
    return canonical(encoding.record())


def distinguish(samples, controls):
    target, axes = None, {}
    for left, right in combinations(samples, 2):
        changed = {
            name for name in controls if left.controls[name] != right.controls[name]
        }
        pair = [left.identity, right.identity]
        if left.value != right.value and not changed and target is None:
            target = pair
        if left.value == right.value and len(changed) == 1:
            axes.setdefault(changed.pop(), pair)
    return {
        "target_pair": target,
        "control_pairs": axes,
        "unresolved_controls": sorted(controls - axes.keys()),
    }


def find_patterns(sample, expected, encoding, size):
    found = numpy.zeros(size, dtype=bool)
    for pattern in expected.patterns(encoding):
        stop = sample.start + size + len(pattern) - 1
        location = sample.data.find(pattern, sample.start, stop)
        while location != -1:
            found[location - sample.start] = True
            location = sample.data.find(pattern, location + 1, stop)
    return found


def matching_offsets(samples, encoding, expecteds):
    size = min(sample.length for sample in samples) - encoding.codec.size + 1
    if size < 1:
        return ()
    remaining = numpy.ones(size, dtype=bool)
    dtype = (
        numpy.dtype(f"{encoding.codec.format[0]}f{encoding.codec.size}")
        if encoding.floating
        else None
    )
    for sample, expected in zip(samples, expecteds, strict=True):
        matches = find_patterns(sample, expected, encoding, size)
        if expected.interval is not None:
            values = numpy.ndarray(
                (size,),
                dtype=dtype,
                buffer=sample.data,
                offset=sample.start,
                strides=(1,),
            )
            low, high = expected.interval
            with numpy.errstate(invalid="ignore"):
                indices = numpy.flatnonzero(remaining & ~matches)
                observed = values[indices].astype(numpy.float64, copy=False)
                matches[indices] = (observed >= low) & (observed <= high)
        remaining &= matches
        if not remaining.any():
            return ()
    return numpy.flatnonzero(remaining).tolist()


def observe(sample, encoding, expected, offset):
    codec = encoding.codec
    row = {"sample": sample.identity, "offset": sample.start + offset}
    if offset + codec.size > sample.length:
        return {**row, "status": "outside_aligned_span"}
    if expected is None:
        return {**row, "status": "unrepresentable"}
    data = sample.data[row["offset"] : row["offset"] + codec.size]
    actual = codec.unpack(data)[0]
    matches = expected.matches(data, actual)
    if matches:
        status = "pattern" if data in expected.patterns(encoding) else "tolerance"
    else:
        status = "mismatch"
    return {
        **row,
        "status": status,
        "bytes": data.hex(),
        "expected": expected.value,
        "observed": (
            str(actual)
            if isinstance(actual, float) and not math.isfinite(actual)
            else actual
        ),
    }


def freeze(samples, encodings, tolerance):
    found = []
    for encoding in encodings:
        expecteds = [encoding.expected(sample, tolerance) for sample in samples]
        if any(expected is None for expected in expecteds):
            continue
        if len({expected.exact for expected in expecteds}) < 2:
            continue
        for offset in matching_offsets(samples, encoding, expecteds):
            if len(found) == MAX_HYPOTHESES:
                raise ValueError(
                    "inference hypothesis limit exceeded before independent evaluation"
                )
            observations = [
                observe(sample, encoding, expected, offset)
                for sample, expected in zip(samples, expecteds, strict=True)
            ]
            if len({row["bytes"] for row in observations}) < 2:
                continue
            found.append(
                (
                    encoding,
                    {
                        "relative_offset": offset,
                        "encoding": encoding.record(),
                        "width": encoding.codec.size,
                        "discovery": observations,
                    },
                )
            )
    return found


def search_fields(
    discovery, holdout, *, encodings, tolerance=0.0, confounds=(), challenges=()
):
    splits, encodings, controls, tolerance = parse_inputs(
        discovery, holdout, challenges, encodings, confounds, tolerance
    )
    discovery, holdout, challenges = splits
    discrimination = distinguish(discovery, controls)
    varying = len({sample.value for sample in discovery}) > 1
    frozen = freeze(discovery, encodings, tolerance) if varying else []
    report = {
        "discovery": {sample.identity: sample.record() for sample in discovery},
        "discrimination": discrimination,
        "tolerance": str(tolerance),
        "search_space": [encoding.record() for encoding in encodings],
    }
    discovery_sha256 = digest(
        {**report, "hypotheses": [candidate for _, candidate in frozen]}
    )
    hypotheses, counterexamples = [], []
    for encoding, candidate in frozen:
        candidate_id = digest({"discovery_sha256": discovery_sha256, **candidate})
        accepted = True
        for split, samples in (("holdout", holdout), ("challenges", challenges)):
            candidate[split] = []
            for sample in samples:
                evidence = observe(
                    sample,
                    encoding,
                    encoding.expected(sample, tolerance),
                    candidate["relative_offset"],
                )
                candidate[split].append(evidence)
                if evidence["status"] not in {"pattern", "tolerance"}:
                    accepted = False
                    counterexamples.append(
                        {
                            "hypothesis": candidate_id,
                            "split": split,
                            "sample": sample.identity,
                        }
                    )
        candidate["id"] = candidate_id
        candidate["confidence"] = "partial" if accepted else "refuted"
        hypotheses.append(candidate)
    if (
        not varying
        or not discrimination["target_pair"]
        or discrimination["unresolved_controls"]
    ):
        status = "insufficient_discrimination"
    elif not hypotheses:
        status = "unresolved"
    elif all(candidate["confidence"] == "refuted" for candidate in hypotheses):
        status = "refuted"
    elif len(hypotheses) > 1:
        status = "ambiguous"
    else:
        status = "hypothesis"
    result = {
        **report,
        "status": status,
        "discovery_sha256": discovery_sha256,
        "holdout": {sample.identity: sample.record() for sample in holdout},
        "challenges": {sample.identity: sample.record() for sample in challenges},
        "hypotheses": hypotheses,
        "counterexamples": counterexamples,
    }
    if len(canonical(result).encode("utf-8")) > MAX_REPORT_BYTES:
        raise ValueError("inference result exceeds the bounded report budget")
    return result

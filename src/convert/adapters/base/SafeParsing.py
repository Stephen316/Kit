# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

"""Hardened untrusted-XML parsing shared by every CAD adapter."""

from __future__ import annotations as Annotations

from re import compile as CompilePattern
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import fromstring as ParseTreeText  # noqa: DUO107

# doctype detection stays lexical because every entity expansion vector requires one declared doctype
KDoctypeMark = CompilePattern("<![dD][oO][cC][tT][yY][pP][eE]")


# parsing rejects document types before feeding because references cannot expand without declarations
def ParseUntrusted(ValueData: str | bytes) -> Element:
    ScanValue = (
        ValueData.decode("latin-1") if isinstance(ValueData, bytes) else ValueData
    )
    if KDoctypeMark.search(ScanValue) is not None:
        raise ValueError("untrusted XML must not declare a doctype")
    return ParseTreeText(ValueData)

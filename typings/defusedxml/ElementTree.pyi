# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from collections.abc import Iterator, Sequence

from _typeshed import SupportsRead
from xml.etree.ElementTree import Element, ParseError, TreeBuilder, XMLParser

__all__: tuple[str, ...]

def parse(
    source: str | SupportsRead[str] | SupportsRead[bytes],
    parser: XMLParser | TreeBuilder | None = None,
    *,
    forbid_dtd: bool = ...,
    forbid_entities: bool = ...,
    forbid_external: bool = ...,
) -> Element: ...
def iterparse(
    source: str | SupportsRead[str] | SupportsRead[bytes],
    events: Sequence[str] | None = None,
    parser: XMLParser | TreeBuilder | None = None,
    *,
    forbid_dtd: bool = ...,
    forbid_entities: bool = ...,
    forbid_external: bool = ...,
) -> Iterator[tuple[str, Element]]: ...
def fromstring(
    text: str | bytes,
    *,
    forbid_dtd: bool = ...,
    forbid_entities: bool = ...,
    forbid_external: bool = ...,
) -> Element: ...
def XML(
    text: str | bytes,
    *,
    forbid_dtd: bool = ...,
    forbid_entities: bool = ...,
    forbid_external: bool = ...,
) -> Element: ...

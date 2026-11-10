# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from decimal import Decimal

from convert.adapters.freecad.EditRead.PlaneRev.ExprToken import (
    KExprToken,
    ReadExprNumber,
    ReadExprTokens,
)

# nested groups and prefix operators must stay within a safe parse depth
KMaxExprDepth = 64

# prefix signs bind before arithmetic in the written expression grammar
KSignPriority = 50

# a conditional branch can contain another conditional without parentheses
KChoicePriority = 10

# arithmetic groups depend on native operator precedence
KInfixPriority = {
    "<": 20,
    ">": 20,
    "<=": 20,
    ">=": 20,
    "==": 20,
    "+": 30,
    "-": 30,
    "*": 40,
    "/": 40,
    "%": 40,
}

# only native calls used by the placement and sweep writers can qualify
KCallArities = {
    "abs": (1,),
    "atan2": (2,),
    "min": (2, 5),
    "placement": (2,),
    "rotation": (2,),
    "vcross": (2,),
    "vdot": (2,),
    "vector": (3,),
}

# postfix form preserves tree structure without recursing during comparison
KExprNode = str | tuple[Decimal, str] | tuple[str, int]


# expression structure can be compared without evaluating native properties
class ExprParser:

    # a local cursor keeps each validation isolated from other expressions
    def __init__(self, Tokens: tuple[KExprToken, ...]) -> None:
        super().__init__()
        self.Tokens = Tokens
        self.Index = 0
        self.Nodes: list[KExprNode] = []

    # a sentinel lets the parser distinguish a complete expression from extra text
    def PeekText(self) -> str:
        if self.Index == len(self.Tokens):
            return ""
        return self.Tokens[self.Index][1]

    # required punctuation is consumed through the same bounded token cursor
    def TakeToken(self, Wanted: str = "") -> KExprToken:
        if self.Index >= len(self.Tokens):
            raise ValueError("incomplete plane expression")
        Token = self.Tokens[self.Index]
        if Wanted and Token[1] != Wanted:
            raise ValueError("unexpected plane expression token")
        self.Index += 1
        return Token

    # one output cursor keeps flat trees independent of parser nesting depth
    def EmitNode(self, NodeValue: KExprNode) -> None:
        self.Nodes.append(NodeValue)


# call identity and argument count prevent a different operand tree from matching
def ParseCall(Parser: ExprParser, NameValue: str, Depth: int) -> None:
    Arities = KCallArities.get(NameValue)
    if Arities is None:
        raise ValueError("unsupported plane expression function")
    _ = Parser.TakeToken("(")
    ParseBranch(Parser, 0, Depth + 1)
    Count = 1
    while Parser.PeekText() == ";":
        _ = Parser.TakeToken(";")
        ParseBranch(Parser, 0, Depth + 1)
        Count += 1
    _ = Parser.TakeToken(")")
    if Count not in Arities:
        raise ValueError("invalid plane expression function arity")
    Parser.EmitNode((NameValue, Count))


# grouping punctuation may disappear while unary operations must retain their identity
def ParseOperand(Parser: ExprParser, Depth: int) -> None:
    KindValue, TextValue = Parser.TakeToken()
    if TextValue == "(":
        ParseBranch(Parser, 0, Depth + 1)
        _ = Parser.TakeToken(")")
    elif TextValue in ("+", "-"):
        ParseBranch(Parser, KSignPriority, Depth + 1)
        Parser.EmitNode("u" + TextValue)
    elif KindValue == "Number":
        UnitValue = Parser.PeekText()
        if UnitValue in ("mm", "deg"):
            _ = Parser.TakeToken()
        else:
            UnitValue = ""
        Parser.EmitNode((ReadExprNumber(TextValue), UnitValue))
    elif KindValue == "Names" and Parser.PeekText() == "(":
        ParseCall(Parser, TextValue, Depth)
    elif KindValue == "Names" and "." in TextValue:
        Parser.EmitNode(TextValue)
    elif KindValue == "Literal":
        Parser.EmitNode(TextValue)
    else:
        raise ValueError("invalid plane expression operand")


# precedence preserves calculation order even when native saves simplify parentheses
def ParseBranch(Parser: ExprParser, Minimum: int, Depth: int) -> None:
    if Depth > KMaxExprDepth:
        raise ValueError("plane expression nesting limit exceeded")
    ParseOperand(Parser, Depth)
    while TextValue := Parser.PeekText():
        if TextValue == "?" and Minimum <= KChoicePriority:
            _ = Parser.TakeToken("?")
            ParseBranch(Parser, 0, Depth + 1)
            _ = Parser.TakeToken(":")
            ParseBranch(Parser, KChoicePriority, Depth + 1)
            Parser.EmitNode("?:")
            continue
        Priority = KInfixPriority.get(TextValue)
        if Priority is None or Priority < Minimum:
            break
        _ = Parser.TakeToken()
        ParseBranch(Parser, Priority + 1, Depth + 1)
        Parser.EmitNode(TextValue)


# validating the whole stream prevents otherwise valid prefixes from hiding extra syntax
def ParsePlaneExpr(TextValue: str) -> list[KExprNode]:
    Parser = ExprParser(ReadExprTokens(TextValue))
    ParseBranch(Parser, 0, 0)
    if Parser.PeekText():
        raise ValueError("trailing plane expression token")
    return Parser.Nodes

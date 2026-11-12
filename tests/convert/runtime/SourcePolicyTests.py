import ast as AstLib

from tests.convert.runtime.RuntimeAstRules import CheckNode
from tests.convert.runtime.RuntimeRules import KSourcePath


# production imports and calls stay inside the portable offline runtime boundary
def CheckDeps() -> None:
    for SourcePath in KSourcePath.rglob("*.py"):
        SyntaxTree = AstLib.parse(
            SourcePath.read_text("utf-8"),
            filename=str(SourcePath),
        )
        for NodeData in AstLib.walk(SyntaxTree):
            CheckNode(SourcePath, NodeData)


# executable pass statements stay prohibited because production paths must never contain stubs
def CheckNoPass() -> None:
    for SourcePath in KSourcePath.rglob("*.py"):
        SourceBytes = SourcePath.read_bytes()
        SyntaxTree = AstLib.parse(SourceBytes, filename=str(SourcePath))
        assert not any(
            isinstance(NodeData, AstLib.Pass) for NodeData in AstLib.walk(SyntaxTree)
        ), SourcePath


# wheel source stays limited to the two intentional public production packages
def CheckLayout() -> None:
    PackageNames = {
        SourcePath.name
        for SourcePath in KSourcePath.iterdir()
        if SourcePath.is_dir() and any(SourcePath.rglob("*.py"))
    }
    assert PackageNames == {"convert", "interchange"}

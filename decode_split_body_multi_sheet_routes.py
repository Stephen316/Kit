"""Explicit two-source Split sheet groups without ordinal result pairing."""
from decode_split_body_sheet_routes import _resolve_split_sheet_tool,_qualify_split_sheet_routes

SCOPE=('Observed SplitBody sheet tool, two historical source BODY descriptors and two separately owned '
       'new BODY anchors; reciprocal current collection contains these five distinct BODY identities. '
       'Initial same-asset ASM stored-ID proof is separate. Ordered source and new-anchor lists do not '
       'establish per-source/result pairing; API identity, selected face identity, lifecycle and regeneration unresolved.')


def resolve_split_body_multi_sheet_tool(data,records,tool_id,feature,known):
    """Pure two-source role-group callback; singleton defaults remain unchanged."""
    return _resolve_split_sheet_tool(data,records,tool_id,feature,known,expected_target_count=2,scope=SCOPE)


def qualify_split_body_multi_sheet_routes(data,records,member,members,evidence):
    """Late explicit BODY stored-ID proof with two-source evidence revalidation."""
    return _qualify_split_sheet_routes(data,records,member,members,evidence,resolver=resolve_split_body_multi_sheet_tool,scope=SCOPE)

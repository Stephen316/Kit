from BrepCylinder import Record, Reference, field
from IdentityModel import HistoryIdentity


def preamble(identity: HistoryIdentity):
    return Record("Begin-of-ASM-History-Data", (
        field("payload_name", "history_stream", "Second leaf identifier after the history boundary name chain"),
        field("current_state_id", identity.stream_current_state_id, "Stream current state identity; research label"),
        field("max_state_id", identity.max_state_id, "Stream maximum allocated state identity; research label"),
        field("max_states_to_keep", 0, "Zero disables native history pruning"),
        field("next_entity_tag", identity.next_entity_tag, "Next entity tag; research label"),
        field("reference_a", Reference(-1), "Null history-stream profile reference"),
        field("reference_b", Reference(0), "Current journal node index in this two-node profile"),
        field("reference_c", Reference(1), "Initial journal node index in this two-node profile"),
        field("reference_d", Reference(-1), "Null history-stream profile reference"),
    ))


def state_header(state_id, node_index, previous_node, next_node):
    return (
        field("state_id", state_id, "Explicit kernel state identity; not a feature or topology record index"),
        field("backward", 1, "Delta-state backward flag; observed value 1"),
        field("state_flag", 0, "Observed delta-state state flag"),
        field("previous_node", Reference(previous_node), "Journal node index or null at current head"),
        field("next_node", Reference(next_node), "Journal node index or null at initial tail"),
        field("partner_node", Reference(node_index), "Partner ring is self-linked in this linear two-state profile"),
        field("state_ref_50", Reference(-1), "Qualified null state reference; general role unresolved"),
        field("owner", Reference(0), "Observed journal owner-reference profile"),
        field("has_name", False, "No optional delta-state name follows"),
    )


def insertion_state(identity: HistoryIdentity, record_count):
    return Record("delta_state", (
        *state_header(identity.current_state_id, 0, -1, 1),
        field("board_present", 1, "One insertion bulletin board follows"),
        field("board_owner", Reference(0), "Bulletin board owner profile"),
        field("board_status", identity.board_status, "Native mainline/stacked/succeeded/failed status enum"),
        *(value for index in range(1, record_count) for value in (
            field(f"insert_{index}_present", 1, "One insertion change follows"),
            field(f"insert_{index}_old", Reference(-1), "No previous record revision"),
            field(f"insert_{index}_new", Reference(index), "Newly allocated active record index"),
        )),
        field("changes_end", 0, "End of changes on this board"),
        field("boards_end", 0, "End of bulletin boards"),
        field("state_list_count", 0, "Empty state list; general role unresolved"),
    ))


def initial_state(identity: HistoryIdentity):
    return Record("delta_state", (
        *state_header(identity.initial_state_id, 1, 0, -1),
        field("boards_end", 0, "Initial state has no bulletin boards"),
        field("state_list_count", 0, "Empty state list; general role unresolved"),
    ))

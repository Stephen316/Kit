# journal bytes must remain consistent across callers so topology changes retain their native revision relationships
KJournalBytes = 32 * 1024 * 1024

# journal entities must remain consistent across callers so topology changes retain their native revision relationships
KJournalEntities = 1 << 18

# journal states must remain consistent across callers so topology changes retain their native revision relationships
KJournalStates = 4096

# journal roots must remain consistent across callers so topology changes retain their native revision relationships
KJournalRoots = 1 << 16

# journal boards must remain consistent across callers so topology changes retain their native revision relationships
KJournalBoards = 1 << 14

# board changes must remain consistent across callers so topology changes retain their native revision relationships
KBoardChanges = 1 << 18

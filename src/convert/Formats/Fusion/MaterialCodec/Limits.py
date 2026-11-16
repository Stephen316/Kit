# max count needs one explicit bound so material reconstruction cannot accept inconsistent resource or layout limits
KMaxCount = 10000

# max string must remain consistent across callers so typed appearance properties retain their native identifiers
KMaxString = 1048576

# max stream must remain consistent across callers so typed appearance properties retain their native identifiers
KMaxStream = 67108864

# block size needs one explicit bound so material reconstruction cannot accept inconsistent resource or layout limits
KBlockSize = 136

# block payload must remain consistent across callers so typed appearance properties retain their native identifiers
KBlockPayload = 128

# end block must remain consistent across callers so typed appearance properties retain their native identifiers
KEndBlock = 0xFFFFFFFF

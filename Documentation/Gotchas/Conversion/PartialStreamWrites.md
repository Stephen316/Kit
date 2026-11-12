# Partial stream writes

Staging might appear to provide rollback for every destination. The final caller-stream write can fail after writing some bytes. Use a fresh stream after a failed write. See [stream staging](../../../src/convert/adapters/staging/StreamStaging.py).

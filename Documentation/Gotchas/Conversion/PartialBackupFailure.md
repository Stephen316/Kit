# Partial backup failure

Exception handling might appear to guarantee recovery during replacement. A later backup failure can leave the caller without records of earlier moved targets. Temporary storage cleanup can delete those originals. Keep independent backups and prefer unused destinations. See [path boundaries](../../Reference/Architecture/Engine.md#path-destinations).

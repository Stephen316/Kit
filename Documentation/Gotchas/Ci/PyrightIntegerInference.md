# Pyright integer inference

An `isinstance` check might appear necessary after unpacking. Pyright 1.1.414 already infers integer values for literal `H` and `I` formats. Keep bounds checks and return an explicit integer. See [the compatibility record](../../Changes/PyrightCompatibility.md).

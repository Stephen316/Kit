"""Read primitive surface geometry through Fusion's public API."""


def surface_evidence(surface):
    result = {"kind": surface.objectType.split("::")[-1]}
    for key in ("origin", "axis", "normal", "uDirection", "vDirection"):
        if hasattr(surface, key):
            result[key] = getattr(surface, key).asArray()
    for key in ("radius", "halfAngle", "majorRadius", "minorRadius"):
        if hasattr(surface, key):
            result[key] = getattr(surface, key)
    return result

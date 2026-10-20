"""Mixed curved and circular fitted-spline patterns through shared native roles."""

from decode_sketch_curved_patterns import decode_sketch_curved_patterns


def decode_sketch_mixed_patterns(data, records, features):
    """No feature mutation; standard curved-helper merge interface is retained."""
    result = decode_sketch_curved_patterns(data, records, features,
        allow_multiple_seeds=True, allow_circular_fitted=True)
    result["scope"] = "Observed mixed Arc/Circle, Ellipse/Line, FittedSpline/Arc and single circular FittedSpline native pattern roles; other prior curved variants retained"
    return result

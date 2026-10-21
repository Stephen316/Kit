"""Observed circular cone/cylinder, sphere and torus ASM surface records."""

import math


def decode_analytic_surface(record):
    tokens = record["tokens"]

    def read(index, kind):
        if tokens[index]["kind"] != kind:
            raise ValueError("Unexpected analytic surface token at field "+str(index))
        return tokens[index]["value"]

    def direction(index):
        vector = read(index, "direction_vector")
        if not math.isclose(sum(v*v for v in vector), 1., abs_tol=1e-9):
            raise ValueError("Non-unit analytic surface axis")
        return vector

    def perpendicular(a, b):
        if not math.isclose(sum(x*y for x,y in zip(a,b)), 0., abs_tol=1e-9):
            raise ValueError("Analytic surface reference axes are not perpendicular")

    def bounds(cursor):
        values = []
        for _ in range(4):
            finite = read(cursor, "boolean_token")
            cursor += 1
            values.append(read(cursor, "double") if finite else None)
            if finite:
                cursor += 1
        if cursor != len(tokens):
            raise ValueError("Unsupported analytic surface parameter trailer")
        return values

    result = {"raw_origin": read(3, "position_vector"),
              "coordinate_scope": "Raw ASM coordinates and lengths; body transform and unit context not applied"}
    name = record["name"]
    if name == "sphere-surface":
        radius = read(4, "double")
        a, b = direction(5), direction(6)
        perpendicular(a, b)
        if radius <= 0:
            raise ValueError("Unsupported sphere radius")
        result.update(kind="Sphere", raw_radius=radius, stored_axis_one=a, stored_axis_two=b,
                      is_v_reversed=read(7, "boolean_token"))
        intervals = bounds(8)
    elif name == "torus-surface":
        axis, reference = direction(4), direction(7)
        perpendicular(axis, reference)
        major, minor = read(5, "double"), read(6, "double")
        if not 0 < minor < major:
            raise ValueError("Only observed ring-torus radii supported")
        result.update(kind="Torus", axis=axis, raw_major_radius=major, raw_minor_radius=minor,
                      stored_reference_axis=reference, is_v_reversed=read(8, "boolean_token"))
        intervals = bounds(9)
    elif name == "cone-surface":
        axis = direction(4)
        reference = read(5, "direction_vector")
        perpendicular(axis, reference)
        ratio, radius = read(6, "double"), read(11, "double")
        if radius <= 0 or not math.isclose(ratio, 1., abs_tol=1e-10):
            raise ValueError("Only observed circular cone/cylinder radii supported")
        if not math.isclose(math.sqrt(sum(v*v for v in reference)), radius, rel_tol=1e-9, abs_tol=1e-9):
            raise ValueError("Cone radius and reference vector length disagree")
        if read(7, "boolean_token") or read(8, "boolean_token"):
            raise ValueError("Unsupported cone prefix flags")
        sine, cosine = read(9, "double"), read(10, "double")
        kind = "Cylinder" if math.isclose(sine, 0., abs_tol=1e-12) else "Cone"
        negative_cylinder_pair = (kind == "Cylinder" and math.isclose(cosine, -1., abs_tol=1e-9))
        if (not math.isclose(sine*sine+cosine*cosine, 1., abs_tol=1e-9)
                or (cosine <= 0 and not negative_cylinder_pair)):
            raise ValueError("Invalid cone angular pair")
        result.update(kind=kind, axis=axis, raw_radius=radius, stored_reference_axis=reference,
                      stored_axis_ratio=ratio, is_v_reversed=read(12, "boolean_token"))
        if negative_cylinder_pair:
            result.update(stored_cone_angular_pair=[sine, cosine],
                          parameterization_scope="Observed zero-slope negative-cosine cylinder; stored axis retained, signed parameter direction unresolved")
        if kind == "Cone":
            signed = math.atan2(sine, cosine)
            result.update(half_angle_radians=abs(signed), stored_signed_half_angle_radians=signed,
                          stored_sine_half_angle=sine, stored_cosine_half_angle=cosine,
                          angular_scope="Unsigned angle matches observed API values; signed native pair retained for parameterization")
        intervals = bounds(13)
    else:
        raise ValueError("Unsupported analytic surface record")
    result.update(u_interval=intervals[:2], v_interval=intervals[2:])
    return result

KSubtypeFamily: dict[str, str] = {
    "exact_spl_sur": "surface",
    "cyl_spl_sur": "surface",
    "sum_spl_sur": "surface",
    "helix_spl_line": "surface",
    "sweep_sur": "surface",
    "loft_spl_sur": "surface",
    "cl_loft_spl_sur": "surface",
    "srf_srf_v_bl_spl_sur": "surface",
    "VBL_SURF": "surface",
    "g2_blend_spl_sur": "surface",
    "t_spl_sur": "surface",
    "t_spl_subtrans_object": "subtrans",
    "exact_int_cur": "curve",
    "par_int_cur": "curve",
    "int_int_cur": "curve",
    "spring_int_cur": "curve",
    "helix_int_cur": "curve",
    "exp_par_cur": "pcurve",
}

KScopeFamily: dict[str, str] = {
    "surfacescope": "surface",
    "curvescope": "curve",
    "pcurvescope": "pcurve",
}

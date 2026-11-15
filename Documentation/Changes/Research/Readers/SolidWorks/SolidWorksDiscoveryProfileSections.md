# Compare SOLIDWORKS discovery profile sections

The discovery census now compares the area and world-space centroid of the public reader's saved profile loop with the independently reopened SOLIDWORKS section. It uses the four ordered, non-construction edges from the neutral closed profile. It checks endpoint continuity and computes an area-weighted centroid from two oriented triangles in the saved sketch plane.

Generate the report with `python re/automation/SolidworksCensus.py --output /private/SolidworksDiscoveryCensus.json`. Each eligible sketch has `section_area_mm2` and `section_center_world_mm` comparisons. The report uses an absolute area tolerance of `0.00000001 mm²` and the recipe's absolute length tolerance for the centroid. These comparisons cover the bounded four-edge discovery profiles. More general profiles and writes need their own acceptance evidence. [Census guide](../../../../Reference/Research/SolidworksResearchReader.md#discovery-census), [Licensed P04 support replay](SolidWorksLicensedCutSupport.md)

The replay at `3e98e3f9` matched the area and centroid of all 36 sections across 25 files. It reproduced the 818 existing hosted comparisons on the same asset and measurement digests. The expanded report contains 890 matched comparisons and has SHA-256 `71eebfaf9f2532ff81504dd620f6d5e83dd02b47e111188fb349a57153fed69b`.

At PR head `47de6ad0`, hosted merge `b008c6a82a1556c0e0018bfb5fa0e47e2dcc4f8e` repeated all 890 comparisons. The downloaded JSON SHA-256 is `ec7d9af5cb2a54d056c896453bab9e291352d02f878cd4fe866164aadd7f84c9`. [Hosted archive](https://github.com/TryUniCAD/Kit/actions/runs/43772995626/artifacts/14184911847)

# SOLIDWORKS resolved-feature inch lengths

The part reader records the document display unit from the typed `SW_UnitsLinear` property in `docProps/ISolidWorksInformation.xml`. The three audited inch captures store code 3, and their millimetre controls store code 0. The SOLIDWORKS API calls these values `swINCHES` and `swMM`. [SOLIDWORKS length unit enumeration](https://help.solidworks.com/2026/english/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swLengthUnit_e.html)

For linear dimensions printed in decimal inches, including radii and diameters, the reader requires a unique same-name scalar in the feature's resolved records or its linked child. The scalar must carry a native identifier and an eligible role. Its metre value must agree with the display text at the document's recorded precision. The inclusive half-step bounds allow either adjacent display value at an exact halfway point. The neutral length comes from the binary value in millimetres. The original display text and the scalar's native offset remain available for inspection.

The discovery census compares seven dimensions and three blind depths across the P01, P03 and P04 inch captures with the independently measured source. P04's six sketch dimensions also have typed metre records in the selected configuration stream. Matching names and values alone cannot establish which sketch owns those records. These six dimensions remain outside the resolved-feature check and require native ownership evidence.

The P02 public reader regression uses the saved inch variant's `diameter_mm` dimension. Its display string is `<MOD-DIAM>0.39` and the reopened SOLIDWORKS measurement records a system value of `0.01 m`. The expected neutral diameter is `10 mm`.

When the reader cannot bind a linear inch dimension to a native scalar, it retains the original display data for inspection. Public conversion and writing reject the unresolved part before touching the destination.

See the [SOLIDWORKS research reader guide](../../Reference/Research/SolidworksResearchReader.md#discovery-census) for the process boundary and report.

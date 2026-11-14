# SOLIDWORKS resolved-feature inch lengths

The part reader records the document display unit from the typed `SW_UnitsLinear` property in `docProps/ISolidWorksInformation.xml`. The three audited inch captures store code 3, and their millimetre controls store code 0. The SOLIDWORKS API calls these values `swINCHES` and `swMM`. [SOLIDWORKS length unit enumeration](https://help.solidworks.com/2026/english/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swLengthUnit_e.html)

For a length printed in decimal inches, the reader uses a unique, named, feature-owned resolved scalar when its metre value agrees with the display text at the document's recorded precision. The neutral length comes from the binary value in millimetres. The original display text and the scalar's native offset remain available for inspection.

The discovery census compares seven dimensions and three blind depths across the P01, P03 and P04 inch captures with the independently measured source. P04's six sketch dimensions also have typed metre records in the selected configuration stream. Matching names and values alone cannot establish which sketch owns those records. These six dimensions remain outside the resolved-feature check and require native ownership evidence.

See the [SOLIDWORKS research reader guide](../../Reference/Research/SolidworksResearchReader.md#discovery-census) for the process boundary and report.

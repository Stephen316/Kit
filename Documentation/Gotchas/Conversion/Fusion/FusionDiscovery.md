# Fusion discovery

Discovery now exposes the [qualified public adapter](../../../Changes/Fusion/Adapter/FusionPublicAdapter.md). That registration does not make every Fusion file losslessly convertible. Default strict reads qualify the complete authored feature graph. In contrast, `strict=False` explicitly selects the older partial projection. Partial documents retain a diagnostic and source archive payload and are rejected by the native writer.

The earlier [research import](../../../Changes/Fusion/FusionResearchImport.md) excluded Fusion entirely; its registration restriction is historical.

# Fusion entity tokens do not provide comparable identities

## Expectation

Equal entity-token strings could appear to provide an identity key across capture observations.

## Actual behavior

Autodesk states that one entity can have different token strings over time.
Tokens must resolve through `Design.findEntityByToken` before comparing the returned entities.
See the [official property contract](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_SketchEntity_entityToken.htm).
This is a documented API limitation, not a new native experiment.

## Workaround

Fresh-process binding capture compares native objects within each observation.
It assigns observation-local point and curve identifiers and records unresolved or ambiguous targets explicitly.
Do not compare these identifiers across documents, recomputations or process restarts.
Use independent geometry and relationship evidence when qualifying cross-observation correspondence.

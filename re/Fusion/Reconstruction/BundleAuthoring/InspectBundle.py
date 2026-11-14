import hashlib
import io
import json
import pathlib
import zipfile


def inspect_bundle(source):
    payload = source.read_bytes()
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        manifest = json.loads(archive.read("Manifest.json"))
        description = json.loads(archive.read("DesignDescription.json"))
        graph = description["designDescription"]["designGraphs"][0]
        owners = {item["id"]: item for item in graph["designObjects"]}
        documents = []
        for item in graph["designObjects"]:
            member = archive.read(item["relativePath"])
            with zipfile.ZipFile(io.BytesIO(member)) as document:
                redirect = json.loads(document.read("RedirectionsStream.dat"))
            expected = [
                {"target": owners[relation["id"]]["relativePath"],
                 "role": relation["metadata"]["neutronRole"], "type": group["type"]}
                for group in item["references"] for relation in group["relationships"]
            ]
            observed = [
                {"target": relation["relativePath"],
                 "role": entry["neutronRole"]["value"], "type": relation["type"]}
                for relation in redirect["references"] for entry in relation["properties"]
                if "neutronRole" in entry
            ]
            design_matches = []
            for design in redirect["designs"]:
                target = next(owner for owner in owners.values()
                              if owner["relativePath"] == design["targetFileName"])
                design_matches.append({
                    "target": target["relativePath"],
                    "versionMatches": design["file-version"] == target["version"],
                    "lineageMatches": design["lineageUrn"] == target["lineage"],
                    "versionUrnMatches": design["versionUrn"] == target["about"],
                })
            documents.append({
                "id": item["id"], "member": item["relativePath"],
                "bytes": len(member), "sha256": hashlib.sha256(member).hexdigest(),
                "descriptionReferences": expected, "redirectionReferences": observed,
                "referencesMatch": expected == observed, "designIdentityChecks": design_matches,
                "metadataFields": sorted(item["metadata"]),
            })
        return {
            "source": str(source), "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(), "manifest": manifest,
            "descriptionName": description["name"], "descriptionVersion": description["version"],
            "rootIds": graph["rootIds"], "documentCount": len(documents),
            "members": [{"name": item.filename, "bytes": item.file_size,
                         "compressedBytes": item.compress_size, "method": item.compress_type}
                        for item in archive.infolist()],
            "documents": documents,
        }


if __name__ == "__main__":
    target = pathlib.Path(__file__).with_name("BundleEvidence.json")
    target.write_text(json.dumps(inspect_bundle(pathlib.Path("re/Fusion/examples/.f3z/example1.f3z")), indent=2) + "\n")

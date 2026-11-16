from tests.Research.Archives.SolidWorksWriterStreamTests import LoadReport


# both native preview wrappers must preserve their authored pixel order and framing
def CheckPreviews() -> None:
    Report = LoadReport("VerifyPartPreviews.py", 8)
    assert Report["constructed"] is True
    assert (
        Report["replay_sha256"]
        == "58e800f573b900c94a1fb040778afcd5803485109579a6bae0a24824475040b3"
    )

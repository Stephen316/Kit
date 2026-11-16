# SOLIDWORKS standalone configuration storage index

The [generation-19000 research codec](../../../../re/solidworks/WriterResearch/CmgrIndex.py) constructs the `Contents/CMgrHdr2` active configuration index for the rebuilt standalone `Default` part. It takes the configuration identity, the session update and model geometry-change stamps, and the manager's independent saved time.

Read-only replay reproduced all 137 bytes in six P01 and eight P03 archives, joined the configuration identity to the selected storage names, and checked the separate ModelHeader and ModelStamps values. The existing hosted archive verifier includes the replay. [Storage dispatch, marker evidence and remaining limits](../../../../re/solidworks/authoring/PartStorage/ConfigurationIndex.md)

Generation-folder packaging and licensed acceptance of a generated load-critical stream set remain open.

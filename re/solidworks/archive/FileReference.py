"""Expose the package file reference reader to archive research callers."""

from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Resolved.SavedFileRef import ReadFileRef as read_file_reference

read_text = ArchiveCursor.ReadText

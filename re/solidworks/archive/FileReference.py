"""Expose the package file reference reader to archive research callers."""

from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.resolved.SavedFileRef import ReadFileRef as read_file_reference

read_text = ArchiveCursor.ReadText

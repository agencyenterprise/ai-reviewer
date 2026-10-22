"""The proposed-edit redline passes, as one import surface.

Splitting the work up -- what an outcome is, where in a paragraph a redline
goes, which edits get one, and writing them -- keeps each piece small enough to
read, but a caller wants the whole thing and does not care where the lines
fall. So the public names live here, and the modules behind them are free to be
reorganised.

- `models`: the outcome and plan rows, and the docx-editor
  workspace both passes open.
- `lines`: whether an edit's markdown line is the mapped paragraph's own.
- `placement`: where one edit's redline goes in its paragraph,
  or why it cannot go anywhere.
- `planning`: the read-only pre-flight over every edit.
- `apply`: what docx-editor is asked to write.
"""

from lib.services.docx.tracked_changes.apply import apply_tracked_changes
from lib.services.docx.tracked_changes.models import EditOutcome, PlannedEdit
from lib.services.docx.tracked_changes.planning import (
    plan_tracked_changes,
    unplaceable_outcomes,
)

__all__ = [
    "EditOutcome",
    "PlannedEdit",
    "apply_tracked_changes",
    "plan_tracked_changes",
    "unplaceable_outcomes",
]

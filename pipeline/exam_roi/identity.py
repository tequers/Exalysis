"""Validate paper identifiers and their destinations at the state boundary."""

from pathlib import Path
import re


class ExamIdentityError(ValueError):
    """An ID or record path cannot safely identify a course-state file."""


_RESERVED = {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}
_RESERVED.update(f"{prefix}{number}" for prefix in ("COM", "LPT")
                 for number in "123456789¹²³")


def validate_exam_id(exam_id):
    """Return a valid single filename stem, without silently rewriting custom IDs.

    Apply Windows filename restrictions on every platform so an ID cannot become
    a path, stream name, or device name when a course is moved between systems.
    The final .json filename must fit common 255-byte/UTF-16-unit component limits.
    """
    reason = None
    if not isinstance(exam_id, str) or not exam_id.strip():
        reason = "the ID must be nonempty text"
    elif exam_id in {".", ".."}:
        reason = "'.' and '..' are reserved path components"
    elif re.search(r'[<>:"/\\|?*\x00-\x1f\x7f]', exam_id):
        reason = "paths, separators, control characters, and Windows filename punctuation are not allowed"
    elif exam_id != exam_id.strip() or exam_id.endswith("."):
        reason = "the ID must not start or end with whitespace, or end with a dot"
    elif exam_id.split(".", 1)[0].rstrip().upper() in _RESERVED:
        reason = "the ID is a reserved device filename"
    else:
        try:
            filename = exam_id + ".json"
            if len(filename.encode("utf-8")) > 255 or len(filename.encode("utf-16-le")) // 2 > 255:
                reason = "the ID is too long for a record filename"
        except UnicodeEncodeError:
            reason = "the ID contains invalid Unicode"
    if reason:
        raise ExamIdentityError(
            f"Invalid exam ID {exam_id!r}: {reason}. "
            "Choose a plain ID such as 'exam_2026_A' with --exam-id; do not supply a path.")
    return exam_id


def exam_record_path(course_dir, state_name, exam_id, *, expected_path=None):
    """Resolve one record without following a redirected directory or file.

    Call before using a path and again just before saving after long-running
    analysis. This guards path containment; course writer locking belongs to the
    separate storage ticket.
    """
    validate_exam_id(exam_id)
    if state_name not in {"parsed", "candidates"}:
        raise ExamIdentityError("Record state directory must be 'parsed' or 'candidates'")
    try:
        course = Path(course_dir).resolve()
        state = course / state_name
        if state.resolve() != state or (state.exists() and not state.is_dir()):
            raise ExamIdentityError(
                f"Unsafe state directory {state}: it is redirected or is not a directory. "
                "Use a real state directory inside the course folder.")
        destination = state / f"{exam_id}.json"
        if expected_path is not None and destination != expected_path:
            raise ExamIdentityError(
                f"The course destination changed during analysis of {exam_id!r}. "
                "Restore the original course directory and retry; no candidate was saved.")
        resolved = destination.resolve()
        if resolved.parent != state or resolved != destination or destination.is_symlink():
            raise ExamIdentityError(
                f"Unsafe record destination {destination}: it is redirected. "
                "Choose another --exam-id or restore a regular record file inside this state directory.")
        if destination.exists():
            if not destination.is_file() or destination.stat().st_nlink > 1:
                raise ExamIdentityError(
                    f"Unsafe record destination {destination}: it is not a regular file with a single filesystem link. "
                    "Choose another --exam-id; directories and hard-linked records cannot be replaced.")
        return destination
    except (OSError, RuntimeError) as exc:
        raise ExamIdentityError(
            f"Cannot verify the record destination for {exam_id!r}: {exc}. "
            "Check the course directory and use a regular state file.") from exc

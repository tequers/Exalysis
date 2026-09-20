"""Course records, writer exclusion, and recoverable commits.

Use ``with CourseStore(paths) as store`` around a read/modify/write operation.
``load()`` returns a consistent snapshot; ``commit()`` replaces supplied records
as one transaction. See docs/course-state-recovery.md for the disk protocol.
"""

import base64
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import socket
import tempfile

from .identity import ExamIdentityError, exam_record_path, validate_exam_id
from .evaluation import CONTRACT_VERSION, validate_topic_scores, validate_connection_review


class StorageError(ValueError):
    """Course state could not be read or committed; never an export failure."""


class CourseLockError(StorageError):
    """Another process holds this course's operating-system lock."""


class RecordError(StorageError):
    def __init__(self, path, reason):
        self.path = Path(path)
        super().__init__(
            f"Saved record {self.path}: {reason}. Nothing was discarded. "
            "Restore this record from a known-good backup or explicitly repair it before retrying; "
            "--force does not bypass saved-record errors.")


@dataclass(frozen=True)
class CourseSnapshot:
    taxonomy: dict
    papers: dict
    candidates: dict


@dataclass(frozen=True)
class CoursePaths:
    folder: Path

    def __post_init__(self):
        object.__setattr__(self, "folder", Path(self.folder).resolve())

    @property
    def taxonomy_file(self):
        return self.folder / "taxonomy.json"

    @property
    def parsed_dir(self):
        return self.folder / "parsed"

    @property
    def candidates_dir(self):
        return self.folder / "candidates"

    @property
    def output_xlsx(self):
        return self.folder / "Exam_ROI_Pipeline.xlsx"

    @property
    def output_json(self):
        return self.folder / "Exam_ROI_Pipeline.json"


def _decode(data, path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key {key!r}")
            result[key] = value
        return result

    def invalid_constant(value):
        raise ValueError(f"non-finite JSON number {value}")

    def finite_float(value):
        result = float(value)
        if not math.isfinite(result):
            invalid_constant(value)
        return result

    try:
        return json.loads(data.decode("utf-8-sig"), object_pairs_hook=unique,
                          parse_constant=invalid_constant, parse_float=finite_float)
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise RecordError(path, f"invalid JSON ({exc})") from exc


def _validate(record, path, *, taxonomy=False):
    """Check the saved format, independently of candidate acceptance policy.

    Unversioned historical papers remain readable. Do not reinterpret their
    evaluation judgments here; taxonomy aggregation owns that decision.
    """
    def require(ok, message):
        if not ok:
            raise RecordError(path, message)

    require(isinstance(record, dict), "expected a JSON object")
    version = record.get("storage_schema_version", 1)
    require(type(version) is int and version == 1,
            f"unsupported storage_schema_version {version!r}; this application reads version 1")
    evaluation_version = record.get("evaluation_contract_version", "legacy-unversioned")
    require(evaluation_version in ("legacy-unversioned", "1.0.0", "1.1.0", CONTRACT_VERSION),
            f"unsupported evaluation_contract_version {evaluation_version!r}")
    if taxonomy:
        require(isinstance(record.get("topics"), dict), "topics must be an object")
        for name, topic in record["topics"].items():
            require(bool(name) and isinstance(topic, dict), f"invalid topic {name!r}")
            for field, maximum in (("Diff", 6), ("Conn", 3)):
                value = topic.get(field)
                require(value is None or (type(value) is int and 1 <= value <= maximum),
                        f"topic {name!r} has invalid {field} {value!r}")
            for field in ("human_overrides", "model_estimate"):
                if field in topic:
                    require(isinstance(topic[field], dict), f"topic {name!r}: {field} must be an object")
            if "automatic_summary" in topic:
                require(type(topic["automatic_summary"]) is bool,
                        f"topic {name!r}: automatic_summary must be a boolean")
        return
    require(record.get("exam_id") == path.stem,
            f"exam_id {record.get('exam_id')!r} does not match filename ID {path.stem!r}")
    require(isinstance(record.get("per_topic"), dict), "per_topic must be an object")
    for name, topic in record["per_topic"].items():
        require(isinstance(topic, dict), f"per_topic entry {name!r} must be an object")
        for field in ("marks_total", "mark_fraction"):
            if field in topic:
                value = topic[field]
                require(type(value) in (int, float) and value >= 0,
                        f"per_topic entry {name!r}: {field} must be a nonnegative number")
        if "format_distribution" in topic:
            distribution = topic["format_distribution"]
            require(isinstance(distribution, dict)
                    and all(type(value) in (int, float) and value >= 0
                            for value in distribution.values()),
                    f"per_topic entry {name!r}: format_distribution must contain nonnegative numbers")
    for field in ("source_provenance", "model_provenance", "topic_judgments", "connection_review"):
        if field in record:
            require(isinstance(record[field], dict), f"{field} must be an object")
    if "questions" in record:
        require(isinstance(record["questions"], list)
                and all(isinstance(question, dict) for question in record["questions"]),
                "questions must be a list of objects")
    for field in ("source_path", "source_file", "year_label"):
        if field in record:
            require(record[field] is None or isinstance(record[field], str),
                    f"{field} must be text or null")
    if "source_provenance" in record and "resolved_path" in record["source_provenance"]:
        require(isinstance(record["source_provenance"]["resolved_path"], str),
                "source_provenance.resolved_path must be text")
    if "year" in record:
        require(record["year"] is None or type(record["year"]) is int,
                "year must be an integer or null")
    if "total_marks" in record:
        require(type(record["total_marks"]) in (int, float) and record["total_marks"] > 0,
                "total_marks must be a positive number")
    if "record_kind" in record:
        require(record["record_kind"] in ("candidate-analysis", "accepted-analysis"),
                f"unsupported record_kind {record['record_kind']!r}")
    if "candidate_status" in record:
        require(record["candidate_status"] in ("validated", "needs-review"),
                f"unsupported candidate_status {record['candidate_status']!r}")
    if evaluation_version == CONTRACT_VERSION:
        require("questions" in record and "topic_judgments" in record,
                "current-contract records require questions and topic_judgments")
        judgments = record["topic_judgments"]
        require(set(judgments) == set(record["per_topic"]),
                "topic_judgments and per_topic must name the same topics")
        # Check stored evidence using the existing domain validator. Storage
        # checks the referenced record's shape; aggregation still decides which
        # course topics and historical judgments contribute to a report.
        allowed = set(judgments)
        for name, judgment in judgments.items():
            require(isinstance(judgment, dict), f"topic judgment {name!r} must be an object")
            for field in ("prerequisites", "unlocks"):
                references = judgment.get(field, [])
                require(isinstance(references, list) and all(isinstance(value, str) for value in references),
                        f"topic judgment {name!r}: {field} must be a list of topic names")
                allowed.update(references)
        context = record.get("evaluation_context") or {}
        advisory_quotes = (
            isinstance(context, dict) and context.get("quote_validation") == "advisory")
        try:
            validate_topic_scores(judgments, list(judgments), record["questions"], allowed,
                                  already_validated=True,
                                  allow_unverified_quotes=advisory_quotes)
            if record.get("connection_review", {}).get("evaluation_contract_version") == CONTRACT_VERSION:
                edges = record["connection_review"].get("edges", [])
                for edge in edges:
                    for field in ("prerequisite", "dependent"):
                        value = edge.get(field)
                        if isinstance(value, str):
                            allowed.add(value)
                validate_connection_review(record["connection_review"], record["questions"], allowed)
        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            raise RecordError(path, f"invalid stored evaluation evidence ({exc})") from exc


def _encode(record, path, *, taxonomy=False):
    try:
        data = (json.dumps(record, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise RecordError(path, f"cannot serialize JSON ({exc})") from exc
    _validate(_decode(data, path), path, taxonomy=taxonomy)
    return data


def _sync_directory(path):
    # Windows does not expose POSIX directory fsync. File contents are still
    # flushed before os.replace. Power-loss durability depends on the filesystem.
    if os.name != "nt":
        descriptor = os.open(path, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


class CourseStore:
    def __init__(self, paths: CoursePaths, *, checkpoint=None):
        self.paths = paths
        self._lock = None
        self._checkpoint = checkpoint or (lambda _boundary: None)

    def _safe_path(self, relative):
        if self.paths.folder.resolve() != self.paths.folder:
            raise ExamIdentityError("The course destination changed. Restore the original course directory and retry.")
        parts = Path(relative).parts
        if len(parts) == 2 and parts[0] in {"parsed", "candidates"} and parts[1].endswith(".json"):
            return exam_record_path(self.paths.folder, parts[0], parts[1][:-5])
        if relative not in {"taxonomy.json", ".course.lock", ".course-transaction.json"}:
            raise RecordError(self.paths.folder / relative, "unsupported storage path")
        path = self.paths.folder / relative
        if path.resolve() != path or path.is_symlink():
            raise RecordError(path, "redirected storage path")
        if path.exists() and (not path.is_file() or path.stat().st_nlink != 1):
            raise RecordError(path, "expected a regular file with one filesystem link")
        return path

    def __enter__(self):
        if self._lock is not None:
            raise StorageError("CourseStore is already open; use its existing load/commit session.")
        path = self._safe_path(".course.lock")
        handle = open(path, "a+b")
        try:
            # A persistent byte is needed by Windows byte-range locking. The
            # file is never removed, so every process locks the same inode.
            if path.stat().st_size == 0:
                handle.write(b"\n")
                handle.flush()
            handle.seek(0)
            try:
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                handle.seek(1)
                owner = handle.read(2048).decode("utf-8", errors="replace").strip()
                raise CourseLockError(
                    f"Course {self.paths.folder} is locked by another command. "
                    f"Owner information: {owner or 'not yet available'}. "
                    "Wait for that command to finish, or stop it if it is stuck, then retry. "
                    "Do not delete .course.lock; a terminated process releases its lock automatically.") from exc
            self._lock = handle
            handle.seek(1)
            handle.truncate()
            handle.write(json.dumps({"pid": os.getpid(), "host": socket.gethostname(),
                                     "started_at": datetime.now(timezone.utc).isoformat()}).encode("utf-8"))
            handle.flush()
            os.fsync(handle.fileno())
            self._recover()
            return self
        except BaseException as exc:
            if self._lock is not None:
                self.__exit__(None, None, None)
            else:
                handle.close()
            if isinstance(exc, OSError):
                raise StorageError(
                    f"Cannot open or recover course state in {self.paths.folder}: {exc}. "
                    "Keep the transaction journal and records in place, fix the filesystem error, "
                    "then rerun status to recover.") from exc
            raise

    def __exit__(self, *_args):
        if self._lock is not None:
            # Closing releases the kernel lock, including on exceptions. Owner
            # metadata may stay stale; acquiring the kernel lock proves it safe.
            self._lock.close()
            self._lock = None

    def _require_open(self):
        if self._lock is None:
            raise StorageError("Use CourseStore inside a with block for load/commit operations.")
        if self._safe_path(".course-transaction.json").exists():
            raise StorageError("An interrupted transaction is pending. Close and reopen CourseStore to recover it.")

    def _read(self, path, *, taxonomy=False):
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise RecordError(path, f"cannot read ({exc})") from exc
        record = _decode(data, path)
        _validate(record, path, taxonomy=taxonomy)
        return record

    def load_record(self, state, exam_id):
        self._require_open()
        path = self._safe_path(f"{state}/{validate_exam_id(exam_id)}.json")
        return self._read(path) if path.exists() else None

    def load(self):
        self._require_open()
        taxonomy_path = self._safe_path("taxonomy.json")
        taxonomy = self._read(taxonomy_path, taxonomy=True) if taxonomy_path.exists() else {"topics": {}}
        records = {}
        for state in ("parsed", "candidates"):
            # Check the directory even if it is empty or redirected.
            exam_record_path(self.paths.folder, state, "storage-check")
            folder = self.paths.folder / state
            try:
                paths = sorted(folder.iterdir())
            except FileNotFoundError:
                paths = []
            except OSError as exc:
                raise RecordError(folder, f"cannot list saved records ({exc})") from exc
            records[state] = {
                path.stem: self._read(self._safe_path(f"{state}/{path.name}"))
                for path in paths if path.suffix.lower() == ".json"
            }
        return CourseSnapshot(taxonomy, records["parsed"], records["candidates"])

    def _atomic_write(self, relative, data, boundary):
        path = self._safe_path(relative)
        path.parent.mkdir(exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=".course-write-", suffix=".tmp", dir=path.parent)
        try:
            with os.fdopen(descriptor, "wb") as output:
                output.write(data)
                output.flush()
                os.fsync(output.fileno())
            self._checkpoint(f"{boundary}:staged")
            self._safe_path(relative)
            os.replace(temporary, path)
            _sync_directory(path.parent)
            self._checkpoint(f"{boundary}:replaced")
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def _write_journal(self, journal, boundary):
        data = json.dumps(journal, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self._atomic_write(".course-transaction.json", data, boundary)

    @staticmethod
    def _image(data):
        if data is None:
            return None
        return {"base64": base64.b64encode(data).decode("ascii"),
                "sha256": hashlib.sha256(data).hexdigest()}

    def _journal_entries(self, journal, journal_path):
        if (not isinstance(journal, dict) or type(journal.get("version")) is not int or journal["version"] != 1
                or journal.get("phase") not in ("prepared", "committed")
                or not isinstance(journal.get("entries"), dict) or not journal["entries"]):
            raise RecordError(journal_path, "corrupt or incompatible transaction journal")
        result = {}
        for relative, images in journal["entries"].items():
            path = self._safe_path(relative)
            if relative in {".course.lock", ".course-transaction.json"}:
                raise RecordError(journal_path, f"invalid transaction target {relative!r}")
            decoded = {}
            for side in ("before", "after"):
                try:
                    image = images[side]
                    if image is None and side == "before":
                        decoded[side] = None
                        continue
                    data = base64.b64decode(image["base64"], validate=True)
                    if hashlib.sha256(data).hexdigest() != image["sha256"]:
                        raise ValueError("image checksum mismatch")
                except (KeyError, TypeError, ValueError) as exc:
                    raise RecordError(journal_path, f"invalid {side} image for {relative}: {exc}") from exc
                _validate(_decode(data, path), path, taxonomy=relative == "taxonomy.json")
                decoded[side] = data
            current = path.read_bytes() if path.exists() else None
            if current not in (decoded["before"], decoded["after"]):
                raise RecordError(path, "record differs from both transaction images; recovery will not overwrite it")
            result[relative] = decoded
        return result

    def _recover(self):
        path = self._safe_path(".course-transaction.json")
        if not path.exists():
            return
        journal = _decode(path.read_bytes(), path)
        entries = self._journal_entries(journal, path)
        side = "after" if journal["phase"] == "committed" else "before"
        for relative, images in entries.items():
            destination = self._safe_path(relative)
            data = images[side]
            if data is None:
                if destination.exists():
                    destination.unlink()
                    _sync_directory(destination.parent)
                self._checkpoint(f"recovery:{relative}:removed")
            elif not destination.exists() or destination.read_bytes() != data:
                self._atomic_write(relative, data, f"recovery:{relative}")
        path.unlink()
        _sync_directory(path.parent)
        self._checkpoint("recovery:cleaned")

    def commit(self, *, taxonomy=None, papers=None, candidates=None):
        """Replace the supplied records together. Omitted records stay unchanged.

        The caller chooses acceptance eligibility. This method only owns saving
        an already chosen state. A failed commit must be recovered by reopening
        the store before another load or commit.
        """
        self._require_open()
        self.load()  # Refuse to overwrite or work around any damaged saved record.
        updates = {}
        if taxonomy is not None:
            updates["taxonomy.json"] = taxonomy
        for state, records in (("parsed", papers), ("candidates", candidates)):
            for exam_id, record in (records or {}).items():
                updates[f"{state}/{validate_exam_id(exam_id)}.json"] = record
        entries = {}
        for relative, record in updates.items():
            path = self._safe_path(relative)
            after = _encode(record, path, taxonomy=relative == "taxonomy.json")
            before = path.read_bytes() if path.exists() else None
            if before == after:
                continue
            entries[relative] = {"before": self._image(before), "after": self._image(after)}
        if not entries:
            return
        journal = {"version": 1, "phase": "prepared", "entries": entries}
        try:
            self._write_journal(journal, "prepare")
            for relative, images in entries.items():
                self._atomic_write(relative, base64.b64decode(images["after"]["base64"]),
                                   f"record:{relative}")
            journal["phase"] = "committed"
            self._write_journal(journal, "commit")
            self._safe_path(".course-transaction.json").unlink()
            _sync_directory(self.paths.folder)
            self._checkpoint("cleanup")
        except OSError as exc:
            raise StorageError(
                f"Course-state commit interrupted for {self.paths.folder}: {exc}. "
                "Reopen the course or rerun the command to recover its last committed state. "
                "Keep .course-transaction.json and all records in place; this is not an export failure.") from exc

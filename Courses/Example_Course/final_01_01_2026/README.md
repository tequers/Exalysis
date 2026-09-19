# Example Course — placeholder

This is the one example `Course/Exam` shipped in the repo, meant to give a first-time reader
something to point the pipeline at without needing their own past exams (real course material is
never committed — see the repo root `.gitignore` and [`docs/glossary.md`](../../../docs/glossary.md)).

It's currently empty scaffolding, not a filled-in example yet. To populate it and try the
pipeline end-to-end:

```bash
cd pipeline
python pipeline.py "../Courses/Example_Course/final_01_01_2026" add-exam
python pipeline.py "../Courses/Example_Course/final_01_01_2026" status
```

Drop one or more past exam files (`.txt` or `.pdf`) into this folder (or its `exams/` subfolder)
first — synthetic ones are fine, that's the point of this folder. `add-exam` with no filename
picks up everything it finds there.

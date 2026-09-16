# Example Course — placeholder

This is the one example `Course/Exam` shipped in the repo, meant to give a first-time reader
something to point the pipeline at without needing their own past exams (real course material is
never committed — see the repo root `.gitignore` and [`CONTEXT.md`](../../../CONTEXT.md)).

It's currently empty scaffolding, not a filled-in example yet. To populate it and try the
pipeline end-to-end:

```bash
cd pipeline
python pipeline.py add-folder "../Courses/Example_Course/final_01_01_2026/exams" --course "Example_Course" --exam final_01_01_2026
python pipeline.py rebuild --course "Example_Course" --exam final_01_01_2026
```

Drop one or more past exam files (`.txt` or `.pdf`) into `exams/` first — synthetic ones are
fine, that's the point of this folder.

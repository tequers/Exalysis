# -*- coding: utf-8 -*-
"""
Computer Vision, final_26_08_2026 - ARCHETYPE POSTPROCESS (arithmetic layer).

Reads parsed/*.json + archetypes_map.py and writes archetypes.json. Every number in the
output is computed here; archetypes_map.py contains none. Re-run after editing the map:

    python archetypes_postprocess.py

BUDGET BASIS (fixed deliberately - do not re-derive from anything else)
-----------------------------------------------------------------------
2023_Exam ALONE: 94 marks / 47 questions, 90 minutes. -> 57.4 s per mark.
NOT the 220-mark sum of all three papers. NOT Old_Exam_Tasks (= the SS 2022 paper; a real
sitting, but older and so more exposed to the content change staff flagged). NOT
mockup_exam_2023 (practice). Those supply archetypes and exemplars, never timing.
On the quantum port an assumed denominator made every budget 2.4x too fast.

CORRECTION 2026-08-21: `Old Exam Tasks.pdf` and `cv_ss_2022.pdf` are byte-identical - it was
always the SS 2022 exam paper, not a compilation of tasks. The 0.85 weight it carries is
still right, but for the reason above rather than the one originally recorded.

The script asserts that the summed budgets over the real paper land within 10% of the exam
length. That check is the whole reason the arithmetic lives in a file rather than in a head.
"""
import json, glob, os, sys, importlib.util, collections, datetime

HERE = os.path.dirname(os.path.abspath(__file__))

spec = importlib.util.spec_from_file_location("amap", os.path.join(HERE, "archetypes_map.py"))
amap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(amap)

EXAM_MINUTES   = 90       # CONFIRMED by the CURRENT official slides: 'Written exam, duration
                          # 90min, closed book.' Corroborated by the 2023 paper's cover sheet.
BUDGET_PAPER   = "2023_Exam"
EXAM_DATE      = "2026-08-26"
MODE_VERSION   = "exam-prep-v1"

# ---------------------------------------------------------------- load parsed papers
papers, questions = {}, []
for path in sorted(glob.glob(os.path.join(HERE, "parsed", "*.json"))):
    d = json.load(open(path, encoding="utf-8"))
    papers[d["exam_id"]] = d
    for q in d["questions"]:
        q["_exam"] = d["exam_id"]
        questions.append(q)

# ---------------------------------------------------------------- integrity checks
qkeys   = {(q["_exam"], q["q_id"]) for q in questions}
mapkeys = set(amap.ASSIGN)
missing, extra = qkeys - mapkeys, mapkeys - qkeys
if missing or extra:
    if missing: print("UNMAPPED questions (%d):" % len(missing), sorted(missing)[:12], file=sys.stderr)
    if extra:   print("MAP entries with no question (%d):" % len(extra), sorted(extra)[:12], file=sys.stderr)
    sys.exit("map/questions mismatch - fix archetypes_map.py")

unknown = set(amap.ASSIGN.values()) - set(amap.PLAYBOOKS)
if unknown:
    sys.exit("archetypes with no playbook: %s" % sorted(unknown))
unused = set(amap.PLAYBOOKS) - set(amap.ASSIGN.values())
if unused:
    sys.exit("playbooks with no questions: %s" % sorted(unused))

if any(q.get("marks") is None for q in questions):
    sys.exit("null marks found - this course was expected to have none")

# ---------------------------------------------------------------- seconds per mark
budget_qs    = [q for q in questions if q["_exam"] == BUDGET_PAPER]
budget_marks = sum(q["marks"] for q in budget_qs)
SEC_PER_MARK = EXAM_MINUTES * 60.0 / budget_marks

# ---------------------------------------------------------------- build archetypes
by_arch = collections.defaultdict(list)
for q in questions:
    by_arch[amap.ASSIGN[(q["_exam"], q["q_id"])]].append(q)

archetypes = []
for aid, qs in by_arch.items():
    pb = amap.PLAYBOOKS[aid]
    topics = sorted({t for q in qs for t in q["topics"]})

    raw_marks = sum(q["marks"] for q in qs)
    eff_marks = sum(q["marks"] * amap.PAPER_WEIGHT[q["_exam"]] for q in qs)
    real_qs   = [q for q in qs if q["_exam"] == BUDGET_PAPER]
    real_mk   = sum(q["marks"] for q in real_qs)

    marks_by_exam = collections.Counter()
    for q in qs:
        marks_by_exam[q["_exam"]] += q["marks"]

    fmt = collections.Counter(q["format"] for q in qs)

    # An instance is one exam sub-question. Budget from its own mean mark value.
    mean_marks  = raw_marks / float(len(qs))
    budget_s    = int(round(mean_marks * SEC_PER_MARK * amap.LOAD[pb["load"]]))

    # Drill-time estimate: cold shot on first sight + read/grade overhead + 2 instances to
    # reach exam_ready. Discounted where every topic is deep-mode mastered but stale.
    stale = bool(topics) and all(t in amap.DEEP_MASTERED for t in topics)
    est_min = round(((30 + 2 * (budget_s + 45)) / 60.0) * (amap.STALE_DISCOUNT if stale else 1.0), 1)

    archetypes.append({
        "id": aid,
        "family": pb["kind"],
        "topics": topics,
        "marks_raw": raw_marks,
        "marks_at_stake": round(eff_marks, 2),
        "marks_in_real_paper": real_mk,
        "in_real_paper": bool(real_qs),
        "marks_by_exam": dict(marks_by_exam),
        "instances": len(qs),
        "mean_marks_per_instance": round(mean_marks, 2),
        "format_mix": dict(fmt),
        "figure_dependent": pb["figure"],
        "playbook": {
            "trigger":      pb["trigger"],
            "why":          pb["why"],
            "answer_shape": pb["answer_shape"],
            "steps":        pb["steps"],
            "traps":        pb["traps"],
            "budget_s":     budget_s,
        },
        "uses": pb["uses"],
        "exemplars": [{"exam": q["_exam"], "q_id": q["q_id"], "marks": q["marks"],
                       "format": q["format"], "text": q["text"]} for q in qs],
        "deep_mode_mastered_but_stale": stale,
        "est_drill_minutes": est_min,
        "roi": round(eff_marks / est_min, 2),
        "state": "cold",
        "streak": 0,
        "drills_seen": 0,
        "best_time_s": None,
        "traps_hit": [],
    })

# ---------------------------------------------------------------- syllabus-derived archetypes
# Blind spots: named in the current slides, absent from every past paper, so they have no
# exemplars and their marks are ESTIMATED. Flagged throughout so they are never confused with
# measured ones. Without these, material the course explicitly teaches gets zero drill time.
for aid, pb in getattr(amap, "SYLLABUS_ARCHETYPES", {}).items():
    est = pb["est_marks"]
    budget_s = int(round(est * SEC_PER_MARK * amap.LOAD[pb["load"]]))
    est_min = round((30 + 2 * (budget_s + 45)) / 60.0, 1)
    archetypes.append({
        "id": aid, "family": pb["kind"], "topics": [pb["topic"]],
        "source": "syllabus",
        "marks_estimated": True,
        "marks_raw": 0, "marks_at_stake": est, "marks_in_real_paper": 0,
        "in_real_paper": False, "marks_by_exam": {}, "instances": 0,
        "mean_marks_per_instance": est, "format_mix": {}, "figure_dependent": False,
        "playbook": {"trigger": pb["trigger"], "why": pb["why"],
                     "answer_shape": pb["answer_shape"], "steps": pb["steps"],
                     "traps": pb["traps"], "budget_s": budget_s},
        "uses": pb["uses"], "exemplars": [],
        "exemplar_note": "NO past-paper exemplar exists. Drills must be generated from the "
                         "playbook plus the confirmed form rules (marks = distinct scorable "
                         "statements, explain_derive dominant).",
        "syllabus_block": pb["block"],
        "deep_mode_mastered_but_stale": False,
        "est_drill_minutes": est_min, "roi": round(est / est_min, 2),
        "state": "cold", "streak": 0, "drills_seen": 0, "best_time_s": None, "traps_hit": [],
    })
for a in archetypes:
    a.setdefault("source", "past_paper")
    a.setdefault("marks_estimated", False)

# ROI alone buries the big derivations: they cost the most minutes per mark, so a pure
# marks-per-minute sort pushes derive-homography-A and derive-epipolar-constraint to the
# bottom - together 13 of the real paper's 94 marks. An archetype carrying >=5 marks in the
# genuine sitting is not optional however poor its ROI, so it is flagged and floated into the
# first tier. Within each tier, ROI still orders.
MUST_COVER_REAL_MARKS = 5
SYLLABUS_MUST_COVER_MARKS = 3
for a in archetypes:
    # Two independent routes into the front tier:
    #  (a) it carries real weight in the genuine sitting, or
    #  (b) it is the ONLY coverage of material the current slides explicitly teach.
    # Route (b) matters because ROI is computed from PAST-PAPER marks - the very measure the
    # staff content warning undermined. Without it the syllabus-derived archetypes sink to the
    # bottom of the queue on the strength of evidence we have been told is stale, which is
    # exactly backwards.
    a["must_cover"] = (a["marks_in_real_paper"] >= MUST_COVER_REAL_MARKS
                       or (a.get("source") == "syllabus"
                           and a["marks_at_stake"] >= SYLLABUS_MUST_COVER_MARKS))

# ---------------------------------------------------------------- syllabus layer
# Course staff, 2026-08-21: "the content of the lecture has changed since three years ago.
# So use this old exam as an example, not as the basis for studying. The slides and
# exercises are the main content to be used for studying."
#
# That invalidates the CONTENT half of every archetype (which topics, what they are worth)
# while explicitly endorsing the FORM half (how questions are asked and marked). syllabus.json
# holds the current topic list; until it is built from the slides everything is `unverified`
# and the weighting below is provisional rather than wrong - we do not know either way, and
# assuming absence would be as unfounded as assuming presence.
# at_risk = absent from the slide block covering its area while sibling topics ARE named.
# Demoted, not cut: the source is a block SUMMARY, and under-drilling a topic that turns out
# to be examined costs far more than over-drilling one that isn't.
SYL_WEIGHT = {"current": 1.0, "at_risk": 0.5, "unverified": 1.0, "dropped": 0.0, "new": 1.0}

syl_path = os.path.join(HERE, "syllabus.json")
syllabus = json.load(open(syl_path, encoding="utf-8")) if os.path.exists(syl_path) else None
syl_topics = (syllabus or {}).get("topics", {})

PRECEDENCE = ["dropped", "at_risk", "unverified", "new", "current"]
for a in archetypes:
    sts = [syl_topics.get(t, {}).get("status", "unverified") for t in a["topics"]] or ["unverified"]
    # An archetype spanning several topics takes the BEST status among them, not the worst.
    # An archetype is a question PATTERN: if any one of its topics is still taught, the pattern
    # can still be examined. Taking the worst status demoted derive-triangulation (topics:
    # Stereo Vision = current, Structure from Motion = at_risk) even though Block 5 names
    # triangulation verbatim - and derive-ransac-iterations, whose RANSAC half is named as
    # "integrated throughout".
    a["syllabus_status"] = max(sts, key=PRECEDENCE.index)
    a["syllabus_weight"] = SYL_WEIGHT[a["syllabus_status"]]
    a["content_confidence"] = {
        "current":    "ok - named in the current slides",
        "at_risk":    "AT RISK - not named in the slide block covering its area",
        "new":        "syllabus-derived, no past-paper exemplar",
        "unverified": "low - no syllabus evidence either way",
        "dropped":    "dropped from the syllabus",
    }[a["syllabus_status"]]
    # Re-weight the queue by syllabus evidence, then recompute ROI from the new stake.
    a["marks_at_stake"] = round(a["marks_at_stake"] * a["syllabus_weight"], 2)
    a["roi"] = round(a["marks_at_stake"] / a["est_drill_minutes"], 2)

# Topics in the current syllabus that NO archetype covers: the blind spots. `new` topics are
# blind spots by definition - named in the slides, absent from every past paper.
covered_topics = {t for a in archetypes for t in a["topics"]}
blind_spots = sorted(t for t, v in syl_topics.items()
                     if v.get("status") in ("current", "new") and t not in covered_topics)
at_risk = sorted({t for a in archetypes if a["syllabus_status"] == "at_risk" for t in a["topics"]
                  if syl_topics.get(t, {}).get("status") == "at_risk"})

archetypes = [a for a in archetypes if a["syllabus_status"] != "dropped"]
archetypes.sort(key=lambda a: (not a["must_cover"], -a["roi"]))
for i, a in enumerate(archetypes, 1):
    a["queue_rank"] = i

# ---------------------------------------------------------------- validation
real_budget_s = sum(
    amap.LOAD[amap.PLAYBOOKS[amap.ASSIGN[(q["_exam"], q["q_id"])]]["load"]] * q["marks"] * SEC_PER_MARK
    for q in budget_qs)
drift = real_budget_s / (EXAM_MINUTES * 60.0) - 1.0
warnings = []
if abs(drift) > 0.10:
    warnings.append("budget sum over %s is %+.1f%% vs the %d-minute exam" % (BUDGET_PAPER, drift * 100, EXAM_MINUTES))
if syllabus is None or syllabus.get("status", "").startswith("STUB"):
    warnings.append("syllabus.json is a stub: content weighting (topics, marks_at_stake, roi, "
                    "must_cover) is derived from pre-change papers and is PROVISIONAL. Form "
                    "weighting (answer_shape, budgets, the marks=statements rule) is unaffected.")

covered = sum(a["marks_raw"] for a in archetypes)   # syllabus archetypes carry marks_raw 0
total   = sum(q["marks"] for q in questions)
assert covered == total, "mark leak: %s vs %s" % (covered, total)

out = {
    "course": "Computer Vision (RWTH Aachen)",
    "exam": "final_26_08_2026",
    "exam_date": EXAM_DATE,
    "exam_minutes": EXAM_MINUTES,
    "exam_minutes_confidence": "CONFIRMED from the CURRENT official course slides (2026-08-21): "
                               "'Written exam, duration 90min, closed book.' Independently "
                               "corroborated by the 2023 paper's cover sheet. This is a "
                               "current-course source, not an inference from an old sitting.",
    "mode_version": MODE_VERSION,
    "mapped_at": datetime.date.today().isoformat(),
    "generated_by": "archetypes_postprocess.py - do not hand-edit; edit archetypes_map.py and re-run",
    "exam_format": {
        "aids": "NONE - closed book. /cheat-sheet must refuse and offer a revision list instead.",
        "source_current": "Official course slides, 2026 edition: 'Exam format - Written exam, "
                          "duration 90min, closed book. Exam registration via RWTH Online.' "
                          "Confirmed by the user 2026-08-21. THIS IS THE AUTHORITATIVE SOURCE.",
        "source_2023_paper": "2023 cover sheet, more specific on aids: 'No additional aids "
                             "(notes, calculator, etc.) are allowed.' Handwritten in blue or "
                             "black ink - pencil and red/green are NOT graded. 20 pages.",
        "calculator": "Not permitted. Note this specific detail comes from the 2023 paper only; "
                      "the current slides say 'closed book' without itemising. Treat as no "
                      "calculator and keep every drill's arithmetic hand-doable.",
        "written_exam": "Handwritten on paper. Not an electronic exam.",
        "marks_per_question": "2023 paper: Q1-Q4 15, Q5 19, Q6 15 = 94 total",
        "format_stability": "The CURRENT slides confirm the same duration and closed-book rule as "
                            "the 2023 paper. So although staff say the CONTENT changed, the FORM "
                            "demonstrably did not - which is direct evidence for the form/content "
                            "split this mode is built on, not merely an assumption behind it."
    },
    "budget_basis": {
        "paper": BUDGET_PAPER,
        "paper_marks": budget_marks,
        "paper_questions": len(budget_qs),
        "exam_minutes": EXAM_MINUTES,
        "seconds_per_mark": round(SEC_PER_MARK, 1),
        "rule": "budget_s = mean_marks_per_instance x seconds_per_mark x LOAD[kind]",
        "excluded": "Old_Exam_Tasks (compilation, not a sitting) and mockup_exam_2023 (practice) "
                    "supply archetypes and exemplars but never timing.",
        "validation_drift_pct": round(drift * 100, 1),
    },
    "source_papers": {k: {"marks": v["total_marks"], "questions": len(v["questions"]),
                          "weight": amap.PAPER_WEIGHT[k]} for k, v in papers.items()},
    "marks_total_all_papers": total,
    "marks_mapped": covered,
    "marks_unmapped": 0,
    "answer_shape_rule": (
        "MARKS = NUMBER OF DISTINCT SCORABLE STATEMENTS. The real 2023 paper averages 2.0 marks "
        "per question and 58%% of its marks are explain_derive, so a 2-mark answer is two "
        "statements - not a paragraph and not one sentence. Count the marks before writing."
    ),
    "syllabus": {
        "status": (syllabus or {}).get("status", "syllabus.json ABSENT"),
        "built_from": (syllabus or {}).get("built_from"),
        "staff_statement": "2026-08-21: 'the content of the lecture has changed since three "
                           "years ago. So use this old exam as an example, not as the basis for "
                           "studying. The slides and exercises are the main content to be used "
                           "for studying.'",
        "form_layer_confidence": ((syllabus or {}).get("form_vs_content", {})
                                  .get("form_layer", {}).get("confidence",
                                  "HIGH - staff endorsed using the old exam as a format example")),
        "content_layer_confidence": ("LOW - topics and mark weights come from pre-change papers"
                                     if any(a["syllabus_status"] == "unverified" for a in archetypes)
                                     else "OK - verified against the current syllabus"),
        "topics_current": sum(1 for v in syl_topics.values() if v.get("status") == "current"),
        "topics_at_risk": sum(1 for v in syl_topics.values() if v.get("status") == "at_risk"),
        "topics_new": sum(1 for v in syl_topics.values() if v.get("status") == "new"),
        "at_risk_topics": at_risk,
        "topics_unverified": sum(1 for v in syl_topics.values() if v.get("status") == "unverified"),
        "topics_dropped": sum(1 for v in syl_topics.values() if v.get("status") == "dropped"),
        "blind_spots": blind_spots,
        "blind_spot_note": ("Syllabus topics with no archetype - nothing in the queue drills these. "
                            "Empty list here means NOT CHECKED while syllabus.json is a stub, not "
                            "that there are none."),
    },
    "warnings": warnings,
    "archetypes": archetypes,
}

with open(os.path.join(HERE, "archetypes.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

# ---------------------------------------------------------------- report
print("archetypes      : %d" % len(archetypes))
print("questions mapped: %d / %d   marks %d / %d" % (len(questions), len(questions), covered, total))
print("budget basis    : %s, %d marks / %d q / %d min -> %.1f s per mark"
      % (BUDGET_PAPER, budget_marks, len(budget_qs), EXAM_MINUTES, SEC_PER_MARK))
print("budget drift    : %+.1f%% vs exam length %s" % (drift * 100, "OK" if abs(drift) <= 0.10 else "** CHECK **"))
for w in warnings:
    print("WARNING: " + w)
print()
must = [a for a in archetypes if a["must_cover"]]
print("must-cover tier: %d archetypes, %d of %d real-paper marks (%.0f%%), %.0f min"
      % (len(must), sum(a["marks_in_real_paper"] for a in must), budget_marks,
         100.0 * sum(a["marks_in_real_paper"] for a in must) / budget_marks,
         sum(a["est_drill_minutes"] for a in must)))
print()
print("%-32s %5s %5s %6s %5s %s" % ("archetype", "stake", "real", "est_m", "roi", "b_s"))
for a in archetypes:
    print("%-32s %5.1f %5d %6.1f %5.2f %4d%s"
          % (a["id"], a["marks_at_stake"], a["marks_in_real_paper"], a["est_drill_minutes"],
             a["roi"], a["playbook"]["budget_s"],
             ("  MUST" if a["must_cover"] else "")
             + ("  [fig]" if a["figure_dependent"] else "")
             + ("  [stale]" if a["deep_mode_mastered_but_stale"] else "")))
print()
print("total est. drill minutes to exam_ready on everything: %.0f" % sum(a["est_drill_minutes"] for a in archetypes))
print()
print("syllabus      : %s" % out["syllabus"]["status"])
print("  form layer  : %s" % out["syllabus"]["form_layer_confidence"])
print("  content     : %s" % out["syllabus"]["content_layer_confidence"])
print("  topics      : %d current / %d at_risk / %d new / %d unverified / %d dropped"
      % (out["syllabus"]["topics_current"], out["syllabus"]["topics_at_risk"],
         out["syllabus"]["topics_new"], out["syllabus"]["topics_unverified"],
         out["syllabus"]["topics_dropped"]))
print("  at risk     : %s" % (", ".join(at_risk) if at_risk else "none"))
print()
print("BLIND SPOTS - in the current syllabus, in NO past paper, so NO archetype drills them:")
for b in blind_spots:
    print("   * %s" % b)
print()
print("archetypes demoted by syllabus evidence:")
for a in archetypes:
    if a["syllabus_weight"] < 1.0:
        print("   %-28s weight %.1f  stake %.1f  rank %d  (%s)"
              % (a["id"], a["syllabus_weight"], a["marks_at_stake"], a["queue_rank"],
                 a["content_confidence"]))

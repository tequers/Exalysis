"""Re-apply exam conditions, time budgets and likelihood weighting after a re-map."""
import json, sys, datetime, pathlib
sys.stdout.reconfigure(encoding='utf-8')
EX = pathlib.Path(r"C:\Users\alber\Claude\Projects\0_Projects\Exams_Analysis_AI_pipeline\Courses\Introduction_to_quantum_computers\final_20_08_2026")
P = EX / "archetypes.json"
d = json.load(open(P, encoding='utf-8'))

EXAM_MIN, PAPER_MARKS = 90, 100.0          # from the real 2024 paper: "Maximum Points: 100"
SRC_TOTALS = {"E1": 182.0, "E2": 310.0, "E3": 100.0}
REAL = "E3"                                 # Summer_Semester_2024 — the real format
REAL_W = 3.0                                # a real-exam instance counts 3x an e-test sub-part
LADDER = [30, 45, 60, 90, 120, 180, 240, 300, 420]
def human(x): return min(LADDER, key=lambda v: abs(v - x))

# ── budgets from mark SHARE of the paper the instance came from ───────────────
for a in d['archetypes']:
    num = den = 0.0
    for ex, mk in a['marks_by_exam'].items():
        n = sum(1 for e in a['exemplars'] if e.startswith(ex + ':')) or 1
        w = REAL_W if ex == REAL else 1.0
        num += w * (mk / n) / SRC_TOTALS[ex]
        den += w
    share = num / den if den else 0.0
    a['mark_share_per_instance'] = round(share, 5)
    a['playbook']['budget_s'] = human(max(30, min(420, share * EXAM_MIN * 60 * 0.8)))

# ── likelihood: the professor said heavy calculation / Python will be avoided ──
LOAD = {
 'shor-order-finding':('heavy',0.5,'gcd and powers by hand; the 2024 paper still asked it, so not cut'),
 'qec-threshold':('heavy',0.5,'recursive error arithmetic'),
 'compute-tensor-product':('medium',0.8,'mechanical but slow'),
 'energy-levels-photon':('medium',0.7,'eV differences only'),
 'hamiltonian-time-evolution':('medium',0.85,'2024 asked the light form: eigenvalues + duration'),
 'circuit-trace-state':('medium',0.9,'core; 2024 asked it at 8 marks'),
 'bomb-tester':('medium',0.7,'absent from the 2024 paper'),
 'shor-circuit-states':('medium',0.85,''),
 'oracle-circuit-to-function':('medium',0.9,'tracing, not arithmetic'),
}
ABSENT_2024 = 0.6   # archetypes the real paper never touched
for a in d['archetypes']:
    load, lik, why = LOAD.get(a['id'], ('light', 1.0, 'no arithmetic beyond simple squares/lookups'))
    in_real = REAL in a['marks_by_exam']
    if not in_real:
        lik *= ABSENT_2024
        why = (why + '; ' if why else '') + 'absent from the 2024 real paper'
    a['calc_load'], a['exam_likelihood'], a['calc_note'] = load, round(lik, 2), why
    a['in_real_exam'] = in_real
    a['effective_marks'] = round(a['marks_at_stake'] * a['exam_likelihood'], 1)

d['exam_minutes'] = EXAM_MIN
d['exam_minutes_confidence'] = 'estimated by user 2026-08-17; the 2024 paper does not state a duration'
d['real_paper'] = {
  'exam_id': 'Summer_Semester_2024', 'marks': 100, 'questions': 19,
  'why_it_matters': '19 questions at ~5.3 marks each, vs 129 and 113 sub-part questions on the practice e-tests. The real exam is a small number of substantial multi-part questions, NOT a rapid-fire e-test. At 90 min that is ~4.7 min per question and 54 s per mark, against the e-tests\u2019 ~45 s per question.',
  'weighting': 'Instances from this paper count %gx an e-test sub-part when deriving budgets, and archetypes absent from it are down-weighted to %g.' % (REAL_W, ABSENT_2024)
}
d['budget_basis'] = {
  'formula': 'budget_s = mark_share_per_instance * exam_seconds * 0.8, clamped [30,420]',
  'mark_share_per_instance': 'each instance\u2019s marks as a fraction of ITS OWN source paper, so the 100-mark exam and the 182/310-mark e-tests are comparable',
  'seconds_per_mark_real': round(EXAM_MIN * 60 / PAPER_MARKS, 1),
  'superseded': 'An earlier derivation used 22 s/mark from an assumed 246-mark paper. The real paper is 100 marks, so that was 2.4x too fast. budget_s_authored keeps the original hand-written seeds.',
  'correction': 'k_drill in progress.json:exam_prep.calibration corrects these from measured performance.'
}
d['exam_format'] = {
 'source': 'Email from course staff, 2026-08-17, plus the 2024 paper itself.',
 'delivery': 'Electronic exam via Dynexite, in person, on the exam room computers. The practice e-tests are Moodle; the exam is Dynexite.',
 'closed_book': True,
 'permitted': ['paper and pens for working', 'ONE A4 page of handwritten notes, single sided, handwritten not printed'],
 'forbidden': ['calculators', 'phones', 'any other electronic device', 'printed notes or printouts'],
 'question_style': 'Similar to the e-test questions, but avoiding heavy calculations and Python. No programming required.',
 'answer_entry': 'Typed into Dynexite in a fixed syntax: ket(01), sqrt(2), 1/sqrt(2), matrices as stacked input boxes. The 2024 paper shows partial credit stated per sub-part (e.g. "50%, 25% if non-normalized").',
 'programming_required': False,
 'practice_etests': 'Re-opened in Moodle under "exam preparation". Staff warning: re-solving may change the homework point total Moodle displays; they do not count for bonus points.'
}
d['mapped_at'] = datetime.date.today().isoformat()
json.dump(d, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

def est(a): return 3 + 2 * a['playbook']['budget_s'] / 60.0
q = sorted(d['archetypes'], key=lambda a: -a['effective_marks'] / est(a))
print('%-34s %5s %5s %6s %6s %s' % ('archetype', 'mk', 'eff', 'budget', '2024?', 'load'))
for a in q[:16]:
    print('%-34s %5.0f %5.1f %5ds %6s %s' % (a['id'], a['marks_at_stake'], a['effective_marks'],
          a['playbook']['budget_s'], ('yes' if a['in_real_exam'] else '-'), a['calc_load']))
print('\ntotal archetypes %d · marks %.0f · in 2024 paper: %d'
      % (len(d['archetypes']), sum(a['marks_at_stake'] for a in d['archetypes']),
         sum(1 for a in d['archetypes'] if a['in_real_exam'])))

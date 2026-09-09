"""
Run the real pipeline over 'Summer Semester 2024.txt' with the two LLM judgement
calls supplied by Claude instead of an API key.

Everything else -- mark aggregation, format distribution, taxonomy update, parsed
JSON writing, spreadsheet rebuild -- is the pipeline's own code, untouched.
"""
import sys, json, pathlib
ROOT = pathlib.Path(r"C:\Users\alber\Claude\Projects\0_Projects\Exams_Analysis_AI_pipeline")
sys.path.insert(0, str(ROOT / "pipeline"))
sys.stdout.reconfigure(encoding="utf-8")
import pipeline as P

EXAM_ROOT = ROOT / "Courses" / "Introduction_to_quantum_computers" / "final_20_08_2026"
P.TAXONOMY_FILE = EXAM_ROOT / "taxonomy.json"
P.PARSED_DIR    = EXAM_ROOT / "parsed"
P.OUTPUT_XLSX   = EXAM_ROOT / "Exam_ROI_Pipeline.xlsx"

# ── Stage 1 output: questions extracted from the paper by Claude ──────────────
# Points verified against the paper's stated "Maximum Points: 100".
Q = [
 ("E1", 8, "mcq", "The correct BV circuit measures s depending on f. With which of the following changes will the circuit still compute the same s? (extra measurement on bottom wire after U_f; second H^(x)n replaced by DFT_2^n; extra measurement before U_f; first H^(x)n replaced by DFT_2^n)",
  ["Bernstein-Vazirani Algorithm", "Quantum Measurement", "Quantum Fourier Transform"]),
 ("E2", 4, "short_answer", "Bernstein-Vazirani on 3 bits with f given by a truth table. What is the outcome s of the measurement? (bitstring)",
  ["Bernstein-Vazirani Algorithm"]),
 ("E3", 8, "short_answer", "Evaluate the circuit (H on top, CNOT, then X on top). Give the state at positions psi_1, psi_2, psi_3 in ket notation, without |+>,|-> and without (x).",
  ["Tensor Products", "Unitary Matrices", "Quantum Amplitudes and Probabilities"]),
 ("E4", 5, "short_answer", "A is one qubit in [1,0]; B is two qubits in [-3i/5, 0, 4/5, 0]. What is the state of the composed system AB?",
  ["Tensor Products"]),
 ("E5", 3, "short_answer", "psi in C^32 with a 1 every 4th position. DFT_32 psi is periodic with a non-zero element every t-th position. What is the period t?",
  ["Quantum Fourier Transform"]),
 ("E6", 3, "mcq", "Which statements are true? (a transversal gate G for the Shor code maps non-entangled states to non-entangled states; the Shor code can correct X-, Y-, Z- but not H-errors)",
  ["Quantum Error Correction", "Stabilizer Formalism"]),
 ("E7", 5, "short_answer", "Given a circuit of CNOTs and Toffolis on x1,x2,x3,y,aux, for which function f is this an implementation of U_f?",
  ["Unitary Matrices", "Quantum Gate Universality"]),
 ("E8", 4, "mcq", "You want to implement the SWAP gate. Which of the following gate sets can be used? (Clifford; Toffoli+H; Clifford+T; X,Y,Z,S,T,H)",
  ["Quantum Gate Universality"]),
 ("E9", 8, "short_answer", "H = [[0,1],[1,0]] as a Hamiltonian. Give E_0 and E_1 from the time-independent Schroedinger equation, then: how long should you apply H to implement an X gate?",
  ["Hamiltonian Dynamics"]),
 ("E10", 4, "short_answer", "Two-qubit state [-i/2, 1/sqrt2, 0, i/2]. Measuring both qubits: probability of outcome 00, and the post-measurement state after outcome 00.",
  ["Quantum Measurement", "Quantum Amplitudes and Probabilities"]),
 ("E11", 4, "short_answer", "Same two-qubit state, partial measurement with A_1={00,11}, A_2={01,10}. Probability of observing A_2, and the post-measurement state after A_2.",
  ["Partial Measurement"]),
 ("E12", 3, "short_answer", "Compute the norms: ||[1,1]||, |||0>+|1>||, |||0>||, and ||0|| (the scalar zero, not the ket).",
  ["Quantum State Validity", "Quantum Amplitudes and Probabilities"]),
 ("E13", 7, "mcq", "True or false? (U with all entries 1/sqrt2 is a valid quantum operation; two identical consecutive measurements with a Z in between always agree; two identical consecutive measurements always agree; [1/2,-1/2,1/2,-1/2] is entangled; two identical consecutive measurements with an X in between always agree)",
  ["Unitary Matrices", "Quantum Measurement", "Tensor Products"]),
 ("E14", 5, "short_answer", "psi = [2/3, 0, ?, 1/3]. Which value should be at the third position so that psi is a valid quantum state?",
  ["Quantum State Validity"]),
 ("E15", 8, "short_answer", "Shor's algorithm with n=100 and f(x) = 5^x mod 124. Give ord(5) mod 124, ord(124) mod 5, and the value that the upper-wire measurement outcome c is close to a multiple of.",
  ["Shor's Algorithm"]),
 ("E16", 7, "mcq", "True or false? (a finite continued fraction is always rational; more Grover iterations necessarily increases success probability; DFT_2^n|0^n> is entangled; optimal Grover has success probability exactly 1; a two-solution g run for the one-solution optimal t keeps probability >= 0.9997)",
  ["Grover's Algorithm", "Shor's Algorithm", "Quantum Fourier Transform"]),
 ("E17", 4, "short_answer", "psi is stabilized by {XX, -YZ}. What is the stabilizer set of (H (x) I) psi?",
  ["Stabilizer Formalism"]),
 ("E18", 6, "short_answer", "Which state is stabilized by the set {ZI, -IZ}? Give it in ket notation, without |+>,|-> and without (x).",
  ["Stabilizer Formalism"]),
 ("E19", 4, "mcq", "Which of the following circuits create a uniform superposition sum_x 2^(-n/2)|x>? (|0^n> -> H^(x)n; |+> -> X on top wire only; |0^n> -> X^(x)n; |+> -> H on top wire only)",
  ["Unitary Matrices", "Tensor Products"]),
]
QUESTIONS = [{"q_id": q, "text": t, "marks": float(m), "format": f} for q, m, f, t, _ in Q]
TAGS = {q: tops for q, m, f, t, tops in Q}

assert sum(x["marks"] for x in QUESTIONS) == 100.0, sum(x["marks"] for x in QUESTIONS)

# ── Substitute only the two LLM judgement calls ───────────────────────────────
P.stage1_extract     = lambda exam_text, total_marks: QUESTIONS
P._stage2_tag        = lambda questions, topic_names: (TAGS, [])
P._stage2_score_new  = lambda new_names, taxonomy_list: {}

src = EXAM_ROOT / "exams" / "Summer Semester 2024.txt"
P.process_exam_file(src, year=2024, total_marks=100.0, exam_id="Summer_Semester_2024", force=True)

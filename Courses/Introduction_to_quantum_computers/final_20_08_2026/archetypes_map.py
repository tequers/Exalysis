import json, glob, re, sys, os, datetime
sys.stdout.reconfigure(encoding='utf-8')

PARSED = r"C:\Users\alber\Claude\Projects\0_Projects\Exams_Analysis_AI_pipeline\Courses\Introduction_to_quantum_computers\final_20_08_2026\parsed"
OUT    = r"C:\Users\alber\Claude\Projects\0_Projects\Exams_Analysis_AI_pipeline\Courses\Introduction_to_quantum_computers\final_20_08_2026\archetypes.json"

# id, stem, regex on text, required-topic (or None), playbook
# order matters: first match wins
R = [
 ("validity-probabilistic-matrix","The following matrix is a valid probabilistic process",
  r"valid probabilistic process|probabilistic process.*matrix|write the given probabilistic process", None,
  ("a square matrix, asks 'valid stochastic/probabilistic?'",
   ["check every entry >= 0","sum each COLUMN","every column sums to exactly 1"],
   ["rows vs columns - it is columns that sum to 1","a negative entry kills it instantly, check before summing"],45),
  ["column-sum-test"]),

 ("validity-prob-distribution","The following vector is a valid probabilistic state",
  r"valid probabilistic state|valid probability distribution", None,
  ("a column vector of reals, asks 'valid probability distribution?'",
   ["all entries >= 0","sum the entries","equals exactly 1"],
   ["entries must be >= 0, not just real","sums to 1, NOT squares to 1 - that is the quantum test"],30),
  []),

 ("validity-quantum-state","The following vector is a valid quantum state",
  r"valid quantum state", None,
  ("a column vector or ket, possibly complex, asks 'valid quantum state?'",
   ["take |a_i|^2 for every amplitude","sum them","equals exactly 1"],
   ["complex entries: |a+bi|^2 = a^2+b^2, NOT (a+bi)^2","|i/sqrt2|^2 = 1/2, not -1/2","squares sum to 1 here, NOT the entries themselves"],45),
  ["complex-modulus"]),

 ("validity-unitary","The following matrix is a valid unitary",
  r"valid unitary|is a valid unitary", None,
  ("a square matrix, possibly complex, asks 'valid unitary?'",
   ["form U-dagger (transpose then conjugate)","multiply U-dagger U","is it the identity?"],
   ["dagger = transpose AND conjugate; forgetting the conjugate passes bad matrices",
    "fast check: columns orthonormal - cheaper than the full product",
    "for e^D with D diagonal: e^D is unitary iff every diagonal entry is purely imaginary; hermitian iff every entry is real"],60),
  ["complex-modulus"]),

 ("correct-false-nonsense","Is <expression> correct, false or nonsense",
  r"correct, false or nonsense|correct, false, or nonsense|if it is correct, false", None,
  ("a notation claim, three options: correct / false / nonsense",
   ["type-check first: do the dimensions and objects even match?","if types are wrong -> NONSENSE, stop",
    "if types are fine, evaluate both sides","equal -> correct, unequal -> false"],
   ["'nonsense' means ill-typed, not merely wrong - do not use it for a false-but-well-formed claim",
    "||psi>+|phi>> style nesting is a type error, not an arithmetic one"],45),
  []),

 ("gate-universality","Universal, universal for 1-qubit gates, or not universal?",
  r"universal", None,
  ("a gate set, asks universal / universal for 1-qubit / not universal",
   ["is there an entangling 2-qubit gate (CNOT/CZ)? no -> at best 1-qubit",
    "do the 1-qubit gates generate a dense subgroup? finite sets like {X,Y,Z} do not",
    "rotations R_X,R_Y,R_Z -> dense on 1 qubit; {CNOT,H,T} -> fully universal"],
   ["{X,Y,Z} is finite -> NOT universal even for 1 qubit","no entangling gate means never fully universal"],30),
  []),

 ("physical-qubit-truefalse","True/False on ions, cooling, photon energy",
  r"True or False|true or false", "Physical Qubit Implementation",
  ("a one-line physical claim about ions/cooling/energy levels, true or false",
   ["photon energy for E_a -> E_b is exactly (E_b - E_a), never a multiple",
    "cooling = driving to the lowest energy level","a >2-level ion CAN be a qubit if two levels are addressable in isolation"],
   ["'needs 2(E_2-E_1)' style distractors are always false","'more than 2 levels cannot be a qubit' is false"],30),
  []),

 ("amplitude-and-probability","Amplitude and probability of 0 / of 1",
  r"amplitude of|probability of (0|1) for quantum state", None,
  ("a 2-entry quantum state, asks amplitude and/or probability of an outcome",
   ["amplitude of outcome k = the k-th entry, verbatim, complex included",
    "probability of outcome k = |that entry|^2","|a+bi|^2 = a^2+b^2"],
   ["amplitude is NOT squared - a huge number of marks die here",
    "answer every sub-part; these come in 4s (amp 0, prob 0, amp 1, prob 1)"],45),
  ["complex-modulus"]),

 ("build-prob-distribution","Write the probability distribution vector for a described experiment",
  r"probability distribution vec|fair coin|modified die|average \(mean value\)|mean value of the entries", None,
  ("a described random experiment, asks for its distribution vector or a statistic of one",
   ["enumerate the outcome space in a FIXED order and say what the order is",
    "count favourable cases / total cases per outcome","check the vector sums to 1 before writing it"],
   ["3 coin tosses counting heads -> 4 outcomes (0,1,2,3), not 8",
    "mean of entries of an n-dim distribution is 1/n, independent of the distribution"],90),
  []),

 ("stochastic-proof-gapfill","Fill in the gaps in the proof about stochastic matrices",
  r"fill in the gaps in the following proof", None,
  ("a proof written out with boxes to complete",
   ["read the line BELOW the gap first - it tells you what the gap must produce",
    "name the property being used at each step (non-negativity, column sums, linearity)",
    "close with the statement the proof set out to prove"],
   ["do not skip the final line - the concluding statement carries marks",
    "gaps want a justification, not a restatement"],150),
  []),

 ("apply-unitary-to-state","Apply the given unitary to the given state",
  r"apply (the )?(hadamard|unitary|quantum circuit)|result of U\||apply unitary U", None,
  ("a unitary (matrix or |ab> -> |...> rule) and a state, asks for the output",
   ["if given as a rule, apply it to each BASIS ket separately",
    "if given as a matrix, do the matrix-vector product",
    "carry the amplitudes through unchanged; recombine and simplify"],
   ["U|ab> rules act on basis states - you must expand the superposition first",
    "1/sqrt2 factors survive the whole computation; do not drop them"],90),
  ["complex-modulus"]),

 ("ket-to-vector","Write a ket superposition as a column vector",
  r"as vector|in ket notation as vectors|write .*\|.*\u27e9 as", None,
  ("a superposition in ket notation, asks for the column vector",
   ["fix the basis order: |00>,|01>,|10>,|11> - binary counting order",
    "the ket's binary string IS the index","put each amplitude at its index, zeros everywhere else"],
   ["|101> in 3 qubits is index 5 of 8, not index 3",
    "the vector has 2^n entries - most of them zero; write them all"],60),
  ["tensor-index-order"]),

 ("tensor-dimension-entries","Dimension / entry count / specific entry of a tensor product",
  r"tensor product .*dimension|number of entries in tensor product|entry of tensor product|first entry|last entry|dimension of", None,
  ("a tensor product of vectors, asks a dimension or a particular entry",
   ["dim(x (x) y) = n * m, always multiply","n copies of a d-dim vector -> d^n entries",
    "entry at index i: write i in the factor bases and multiply the corresponding components"],
   ["dimensions MULTIPLY, they do not add",
    "index order is fixed by the factor order - reversing it is the single most common loss here"],60),
  ["tensor-index-order"]),

 ("compute-tensor-product","Compute the tensor product of the given vectors / matrices",
  r"compute various (vector|matrix) tensor products|compute .*tensor product", None,
  ("two vectors or two matrices, asks for their tensor product explicitly",
   ["fix the output order: every entry of the FIRST factor scales the WHOLE second factor",
    "vectors: n*m entries, block by block","matrices: (n*p) x (m*q), each a_ij scales a full copy of B"],
   ["order matters: A (x) B is not B (x) A - reversing it is the classic loss here",
    "write every entry, including the zeros"],90),
  ["tensor-index-order"]),

 ("tensor-detect-entangled","Is this vector a tensor product / is this state entangled?",
  r"could be the result of a tensor product|entangled or not|if it is entangled", None,
  ("a vector in R^4 or a 2-qubit state, asks product vs entangled",
   ["write it as [a,b,c,d]","product iff a*d == b*c","cross-product equal -> separable, unequal -> entangled"],
   ["the a*d == b*c test is the whole question - do not try to factor by hand",
    "|00>+|11> has ad=1, bc=0 -> entangled"],45),
  ["tensor-index-order"]),

 ("partial-measurement-postmeasurement","Non-normalized then normalized post-measurement state",
  r"non-normalized|post-measurement state|new normalized distribution|after observing outcome", None,
  ("a state plus an observed outcome, asks for the resulting state",
   ["zero out every component inconsistent with the outcome -> that is the NON-normalized state",
    "compute the norm of what is left","divide by it -> the normalized state",
    "probability of the outcome = the squared norm before dividing"],
   ["ALWAYS write the post-measurement state - omitting it is the single most expensive habit on this paper",
    "answer both parts when both are asked: non-normalized AND normalized"],90),
  ["complex-modulus"]),

 ("partial-measurement-matrix","Give the matrix M such that phi = M psi for a partial measurement",
  r"matrix M_|M_red|M_blue|formula for computing probability of outcome i in partial|transformed to Def 1|define sets and probabilities", None,
  ("a partial measurement outcome, asks for the projector matrix or the probability formula",
   ["M is diagonal: 1 on basis states consistent with the outcome, 0 elsewhere",
    "it is a projector: M^2 = M, M-dagger = M","P(i) = ||M_i psi||^2"],
   ["M is not unitary and not normalized - it is a projector, that is the point",
    "the probability formula squares the norm; do not report the norm itself"],90),
  []),

 ("partial-measurement-membership","Is <string> in C_ab for M_1 (x) I (x) M_2?",
  r"in C_\d|C_10|C_00|C_11|C_01|M_1 ⊗ I ⊗ M_2", None,
  ("a basis string and a measurement class C_ab, asks membership",
   ["identify which qubit positions each M actually measures","read off those positions from the string, in order",
    "compare to the subscript ab"],
   ["the I factor is NOT measured - skip its position entirely when reading off",
    "position order follows the tensor order, left to right"],30),
  ["tensor-index-order"]),

 ("measurement-probability-sequence","Probability of measuring 0/1 at first / second measurement",
  r"probability of measuring .*(first|second) measurement|at second measurement|first measurement in first quantum circuit|consecutive measurement|select right outcomes|true or false about probabilistic", None,
  ("a circuit with two measurements, asks a marginal or conditional probability",
   ["for the FIRST measurement: |amplitude|^2 on the matching basis states, summed",
    "for the SECOND without knowing the first: sum over both first-outcomes (total probability)",
    "for the SECOND knowing the first: collapse the state first, THEN square"],
   ["'without knowing the first result' means marginalize, not condition",
    "conditioning requires renormalizing after the collapse"],90),
  ["complex-modulus"]),

 ("circuit-trace-state","State of the system at an intermediate point in a circuit",
  r"state after applying|in which state is|state right before|psi_2 in quantum teleportation|\u03c8_[234]|state after the", None,
  ("a circuit diagram and a named point, asks for the state there",
   ["write the input state as a full vector in the fixed basis order",
    "apply gates strictly left to right, one at a time, writing the state after each",
    "stop at exactly the named point"],
   ["do not skip ahead - the question names a specific point and grades that state",
    "H on n qubits produces 2^n terms; keep the 2^(-n/2) factor"],150),
  ["tensor-index-order","apply-unitary-to-state"]),

 ("hamiltonian-total-energy","Total energy of a state under H",
  r"total energy", None,
  ("a Hamiltonian H and a state psi, asks total (expected) energy",
   ["compute H psi","take the inner product <psi| (H psi)","that scalar is the energy"],
   ["it is <psi|H|psi>, not an eigenvalue, unless psi happens to be an eigenvector",
    "conjugate the bra side when psi is complex"],90),
  ["complex-modulus"]),

 ("hamiltonian-ground-state","Ground state of H",
  r"ground state", None,
  ("a Hamiltonian matrix, asks for the ground state",
   ["find the eigenvalues","take the SMALLEST one","report its normalized eigenvector"],
   ["ground = minimum eigenvalue, not maximum","normalize the eigenvector before reporting it"],90),
  []),

 ("hamiltonian-time-evolution","Which unitary / gate does applying H for time t implement?",
  r"apply(ing)? .*for t|which gate is implemented|which unitary|laser|for \u03c0 time|H\u0303|PDP", None,
  ("a Hamiltonian plus a duration, asks the resulting unitary or named gate",
   ["diagonalize H = P D P-dagger","U = P e^(-i D t) P-dagger : exponentiate the eigenvalues only",
    "multiply out and compare to the named gates (X, Z, H, S, T, CNOT)"],
   ["exponentiate the DIAGONAL, never the matrix entrywise",
    "sign of the exponent: e^(-iHt), the minus is load-bearing",
    "a global phase does not change the gate - factor it out before comparing"],180),
  ["complex-modulus"]),

 ("energy-levels-photon","Energy levels, photon energy, sideband cooling",
  r"energy level|\beV\b|sideband cooling|\bcooling\b|ion trap", None,
  ("a ladder of energy levels in eV, asks a photon energy or a cooling step",
   ["photon energy = difference between the two levels, exactly",
    "cooling drives downward; identify the target lowest level",
    "an unstable level that decays is a pump route, not a qubit level"],
   ["use the difference, never the absolute level value",
    "check which levels are stable before choosing the qubit pair"],120),
  []),

 ("bv-fill-the-boxes","Fill the boxes so the circuit outputs the given state",
  r"fill the boxes", None,
  ("a BV/oracle circuit with empty boxes and a target output state",
   ["read the TARGET state and ask what basis it lives in",
    "|x,f(x)> -> H^(x)n on the first register then U_f",
    "(-1)^f(x)|x> (x) |-> -> put the second register in |-> first (X then H), then U_f (phase kickback)",
    "|x> (x) |0> -> uncompute: apply U_f twice, or undo the second register"],
   ["phase kickback needs |-> in the second register - forgetting the X before the H loses it",
    "the (-1)^f(x) phase survives the second Hadamard layer; do not cancel it"],120),
  ["apply-unitary-to-state"]),

 ("bv-outcome","Outcome of the BV circuit for a given f",
  r"bernstein-vazirani|outcome of the (measurement|circuit)|f\(x\) = 0 for all x|f\(x\) = \u00ac\(x", "Bernstein-Vazirani Algorithm",
  ("a specific f, asks what BV measures",
   ["BV returns s where f(x) = x.s","f identically 0 -> s = 0^n","f identically 1 -> s = 0^n with a global -1 phase, measurement still 0^n",
    "from a truth table: read s off by evaluating f on each e_i (single-1 strings)"],
   ["the measured string is s, not f(s)","a global phase never changes a measurement outcome",
    "f(x) = not(x.s) still measures s - negation is a phase"],90),
  ["bv-fill-the-boxes"]),

 ("bv-uf-replacement","Are these unitaries good replacements for U_f?",
  r"good replacements for U_f|replacements for U_f", None,
  ("candidate transformations, asks which validly implement U_f",
   ["U_f must be unitary and reversible","it must act as |x,y> -> |x, y XOR f(x)>",
    "check it preserves x and only touches y through XOR"],
   ["anything that overwrites y (rather than XOR) is irreversible -> bad",
    "anything that changes x is bad regardless of what it does to y"],90),
  ["validity-unitary"]),

 ("qft-phase-decomposition","DFT_{2^n}|x> as a product of single-qubit phases",
  r"DFT_\{?2\^3|e\^a|\|101\u27e9 = ", None,
  ("DFT of a basis ket written as a tensor product of (|0>+e^a|1>)/sqrt2 factors",
   ["write x as a binary fraction read from the RIGHT",
    "factor k (from the left) gets phase 2*pi*i*0.x_(n-k+1)...x_n",
    "read each exponent off that fraction"],
   ["the binary fraction is read backwards relative to the ket - this is the whole trap",
    "each factor uses a DIFFERENT number of trailing bits; do not reuse the first one"],150),
  ["tensor-index-order"]),

 ("qft-matrix-inverse","Matrix of DFT_2, of R_k-dagger, or of DFT_N inverse",
  r"matrix representation of DFT|R_3\u2020|R_k|DFT_N\^?\(?-1|inverse DFT|S_k", None,
  ("asks for an explicit DFT / rotation matrix or its inverse",
   ["DFT_N entry (k,l) = omega^(k*l)/sqrt(N) with omega = e^(2*pi*i/N)",
    "DFT_2 = (1/sqrt2)[[1,1],[1,-1]] = H","inverse = conjugate the phases: omega -> omega-bar"],
   ["the inverse conjugates the exponent, it does not negate the matrix",
    "R_k-dagger flips the sign in the exponent only, the 1 entries stay"],90),
  []),

 ("qft-binary-fraction-modulus","Absolute value of e^(2 pi i . binary fraction)",
  r"absolute value \|e\^|binary fraction", None,
  ("a complex exponential of a binary fraction, asks its modulus",
   ["|e^(i theta)| = 1 for every real theta","answer 1"],
   ["the fraction is a distractor - the modulus is always 1",
    "if the question asks for the VALUE not the modulus, compute the angle properly"],20),
  ["complex-modulus"]),

 ("grover-query-count","How many queries / iterations does Grover need?",
  r"grover|how many (queries|iterations)|only one input gives output|256 bit key|FLIP_|rotated after t iterations|maximize chance of measuring", None,
  ("a search problem with a stated oracle cost, asks the query or time complexity",
   ["Grover needs O(sqrt(N)) queries; N = 2^n -> 2^(n/2)",
    "multiply by the oracle's own cost to get total time",
    "for a k-bit key, N = 2^k -> 2^(k/2)"],
   ["sqrt of the SEARCH SPACE, not of n","an O(n^2) oracle multiplies the total; it does not change the query count"],90),
  []),

 ("grover-state-matching","Which psi_i equals phi_j across two circuits?",
  r"compare .*(\u03c8|\u03c6|psi|phi)|which \u03c8_i equals", None,
  ("two circuits with labelled intermediate states, asks which correspond",
   ["trace both circuits to their labelled points","match on the state vector, not on the position in the diagram"],
   ["equal states can sit at different depths - compare vectors, not diagram positions"],60),
  ["circuit-trace-state"]),

 ("bv-circuit-modification","Will the circuit still compute the same result after this change?",
  r"still compute the same s|with which of the following changes", None,
  ("a correct algorithm circuit plus a list of modifications, asks which preserve the output",
   ["ask what the step is FOR, not what it computes",
    "a measurement on a register that is already unentangled from the answer changes nothing",
    "a measurement BEFORE the oracle destroys the superposition the oracle needs -> breaks it",
    "H^(x)n vs DFT_2^n: identical on the first layer (both make the uniform superposition), different on the second (the inverse must undo the first)"],
   ["an ignored measurement outcome still collapses the state - 'ignored' is not 'harmless'",
    "the two H layers do DIFFERENT jobs; a swap that is safe on layer 1 is not safe on layer 2"],120),
  ["bv-outcome","measurement-probability-sequence"]),

 ("oracle-circuit-to-function","Which classical function f does this reversible circuit implement?",
  r"for which function f is this an implementation of u_f|implementation of \$?u_f", None,
  ("a circuit of CNOTs/Toffolis over x-wires, a y-wire and an aux wire; asks for f",
   ["track the aux wire: each CNOT/Toffoli XORs a product term onto it",
    "the term written into y is whatever aux holds at the CNOT(aux -> y)",
    "gates AFTER that CNOT uncompute aux - ignore them for f",
    "read f off as the XOR of the accumulated AND-terms"],
   ["the uncomputation half of the circuit is not part of f - counting it doubles the terms",
    "Toffoli(a,b -> t) contributes a AND b, CNOT(a -> t) contributes a"],180),
  []),

 ("uniform-superposition-check","Which of these circuits create a uniform superposition?",
  r"create a uniform superposition", None,
  ("candidate circuits, asks which produce sum_x 2^(-n/2)|x>",
   ["uniform superposition = EVERY basis state with equal amplitude and equal sign",
    "H^(x)n on |0^n> is the canonical one",
    "X gates only permute basis states - they never create superposition",
    "acting on one wire of an already-uniform state breaks uniformity on that wire only"],
   ["|+> on every wire is ALREADY uniform - any extra gate on one wire breaks it",
    "H on |+> gives |0>, not a superposition"],90),
  ["apply-unitary-to-state"]),

 ("compute-norm","Compute the norm of the given object",
  r"compute the norms|\|\|.*\|\| \?", None,
  ("a vector, a ket expression, or a scalar; asks its norm",
   ["norm = sqrt(sum of |entries|^2)","|0>+|1> is the UNNORMALIZED [1,1] -> sqrt(2)",
    "a single basis ket has norm 1","the scalar 0 has norm 0"],
   ["|0>+|1> is not |+> - there is no 1/sqrt2 unless it is written",
    "||0|| (the scalar) and |||0>|| (the ket) are different questions - read the bars carefully"],60),
  []),

 ("dft-period","Period of the DFT of a periodic state",
  r"periodic in the sense|what is the period t", None,
  ("a periodic basis-state vector in C^N, asks the period of its DFT",
   ["read the input period r (spacing of the non-zero entries)",
    "DFT of a period-r comb on N points is a comb of period N/r",
    "answer N/r"],
   ["the periods are INVERSE - a tighter input comb gives a wider output comb",
    "count the input spacing carefully; off-by-one here doubles or halves the answer"],90),
  []),

 ("shor-order-finding","Order finding and factor extraction",
  r"non-trivial factor|ord\(a|ord\(1|order of a|N=2419|continuous fraction|continued fraction", None,
  ("N, a candidate a, and an order r, asks for a factor",
   ["r = ord(a) mod N","if r is odd or a^(r/2) = -1 mod N, the attempt fails - say so",
    "otherwise gcd(a^(r/2) - 1, N) and gcd(a^(r/2) + 1, N)","report the non-trivial one"],
   ["ord(a^2) = r / gcd(r,2) - it is r/2 when r is even, r when r is odd",
    "always check the odd-r and -1 failure conditions before computing gcd"],150),
  []),

 ("shor-circuit-states","States inside the Shor circuit",
  r"shor's algorithm: (state|probability|assuming outcome)|x mod", "Shor's Algorithm",
  ("a small Shor circuit, asks a state or probability at a named point",
   ["build the first register in uniform superposition","apply f(x) into the second register",
    "measuring the second register collapses the first to the matching periodic set","renormalize"],
   ["the first register keeps ALL x consistent with the measured f value - it is a set, not one term",
    "renormalize after every collapse"],120),
  ["partial-measurement-postmeasurement"]),

 ("stabilizer-transform","Stabilizer set of a transformed state",
  r"stabiliz", None,
  ("a state given by its stabilizer set plus a unitary, asks the new stabilizer set",
   ["conjugate every generator: S -> U S U-dagger","use the Clifford table (H: X<->Z, Y->-Y; S: X->Y)",
    "apply U only on the tensor factors U touches","carry every sign through"],
   ["signs are load-bearing: -Y stays negative unless the conjugation flips it",
    "conjugation is U S U-dagger, not U S"],150),
  []),

 ("shor-code-syndrome","Which error hit this Shor-code codeword?",
  r"shor code|corrupted codeword|\|0\u0303\u27e9|\|1\u0303\u27e9|Z\^\u22979", None,
  ("a corrupted 9-qubit codeword, asks the error or the resulting stabilizer set",
   ["compare block by block against the clean encoding","a flipped sign inside a block -> phase error on that block",
    "a flipped bit inside a triple -> bit-flip error at that position","name the error and its location"],
   ["Z^(x)9 on |0-tilde> is a logical operation, not a detectable error",
    "check all three blocks - the error is often in the one you skim"],150),
  []),

 ("qec-threshold","Fault-tolerance threshold arithmetic",
  r"threshold|fault tolerant|physical gates per logical|recursive layer", None,
  ("gate counts and error probabilities, asks a threshold or a failure probability",
   ["failure per logical gate ~ (number of physical gates) * p","concatenation squares the effective error each level",
    "below threshold means the squared term beats the linear one"],
   ["multiply by the gate count before comparing to the threshold"],90),
  []),

 ("bomb-tester","Bomb tester probabilities",
  r"bomb", None,
  ("the Elitzur-Vaidman setup with a stated beam splitter, asks outcome probabilities",
   ["no bomb: the interferometer recombines - amplitudes interfere, one detector gets everything",
    "bomb present: the bomb measures the path, so treat each path classically then square",
    "report the probability per detector"],
   ["with the bomb present you must collapse first, THEN square - interference is gone",
    "a non-50/50 beam splitter changes the amplitudes; do not reuse the 1/sqrt2 result"],120),
  ["measurement-probability-sequence"]),
]


# Seven question groups whose stem wording defeats the regexes but whose MOVE is
# unambiguous on reading them. Curated rather than pattern-matched, so that 100% of
# the paper's marks land on an archetype instead of 92%.
OVERRIDES = {
    ("E1", "Q34"): "compute-tensor-product",      # expand |+>(x)|+>(x)|+> into the computational basis
    ("E1", "Q37"): "ket-to-vector",               # inverse direction: vector -> ket notation
    ("E2", "Q14"): "qft-phase-decomposition",     # DFT|0^n> = uniform superposition
    ("E2", "Q21"): "qft-phase-decomposition",     # DFT on |111000>
    ("E2", "Q6"):  "bv-outcome",                  # why a balanced f never measures 0^n
    ("E2", "Q11"): "qft-matrix-inverse",          # properties of DFT_N as defined
    ("E2", "Q38"): "validity-unitary",
    ("E3", "E3"):  "circuit-trace-state",        # psi_1/psi_2/psi_3 through H, CNOT, X
    ("E3", "E9"):  "hamiltonian-time-evolution", # E_0/E_1 then "how long to implement X"
    ("E3", "E4"):  "compute-tensor-product",     # composed system A (x) B
    ("E3", "E8"):  "gate-universality",          # which gate sets can build SWAP

}

qs = []
for i, f in enumerate(sorted(glob.glob(os.path.join(PARSED, '*.json'))), 1):
    d = json.load(open(f, encoding='utf-8'))
    for q in d['questions']:
        qs.append(dict(ex='E%d' % i, qid=q['q_id'], text=q['text'], marks=q.get('marks') or 0.0,
                       fmt=q.get('format'), topics=q.get('topics', []), src=os.path.basename(f)))

# --- group sub-parts with their parent -------------------------------------
# Q6a..Q6d are the parts of Q6; the PARENT carries the marks and the parts carry
# marks:null. Matching per-question therefore lands marks on whichever row happened
# to match, which is wrong. The question GROUP is the real unit.
def base(qid):
    return re.sub(r'[a-z]+$', '', qid)

groups = {}
for q in qs:
    groups.setdefault((q['ex'], base(q['qid'])), []).append(q)

def group_marks(members, key):
    parent = [m for m in members if m['qid'] == key[1]]
    if parent and parent[0]['marks'] > 0:
        return parent[0]['marks']          # parent states the group total
    return round(sum(m['marks'] for m in members), 1)

buckets = {r[0]: [] for r in R}
unmatched = []
for key, members in sorted(groups.items()):
    mk = group_marks(members, key)
    # score every rule by how many members of the group it matches; most matches wins,
    # ties broken by rule order. A generic parent stem never outvotes specific children.
    best, best_n = OVERRIDES.get(key), 0
    for idx, (rid, stem, rx, req_topic, pb, uses) in ([] if best else enumerate(R)):
        n = 0
        for m in members:
            if req_topic and req_topic not in m['topics']:
                continue
            if re.search(rx, m['text'], re.I):
                n += 1
        if n > best_n:
            best, best_n = rid, n
    rec = dict(key=key, members=members, marks=mk,
               topics=sorted({t for m in members for t in m['topics']}),
               fmts=sorted({m['fmt'] for m in members}),
               ids=['%s:%s' % (m['ex'], m['qid']) for m in members])
    (buckets[best] if best else unmatched).append(rec)

arch = []
for rid, stem, rx, req_topic, pb, uses in R:
    b = buckets[rid]
    if not b:
        continue
    topics = sorted({t for g in b for t in g['topics']})
    marks = round(sum(g['marks'] for g in b), 1)
    fmts = sorted({f for g in b for f in g['fmts']})
    ids = [i for g in b for i in g['ids']]
    arch.append({
        "id": rid, "stem": stem, "format": fmts[0] if len(fmts) == 1 else "mixed:" + "/".join(fmts),
        "topics": topics, "marks_at_stake": marks,
        "instances": sum(len(g['members']) for g in b), "question_groups": len(b),
        "exemplars": ids[:14],
        "marks_by_exam": {e: round(sum(g['marks'] for g in b if g['key'][0]==e),1)
                          for e in sorted({g['key'][0] for g in b})},
        "playbook": {"trigger": pb[0], "steps": pb[1], "traps": pb[2], "budget_s": pb[3]},
        "uses": uses, "state": "cold", "streak": 0, "best_time_s": None, "drills_seen": []
    })

# est drill minutes = 1 (cold) + 2 (playbook) + 2 * budget/60
for a in arch:
    a['_est_min'] = round(1 + 2 + 2 * a['playbook']['budget_s'] / 60.0, 1)
    a['_roi'] = round(a['marks_at_stake'] / a['_est_min'], 2)
arch.sort(key=lambda a: -a['_roi'])

covered = sum(a['marks_at_stake'] for a in arch)
lost = round(sum(g['marks'] for g in unmatched), 1)
print("questions: %d   groups: %d   matched groups: %d   unmatched groups: %d" % (len(qs), len(groups), len(groups) - len(unmatched), len(unmatched)))
print("marks covered: %.1f   marks unmatched: %.1f" % (covered, lost))
print("\nUNMATCHED (marks>0):")
for g in sorted(unmatched, key=lambda x: -x['marks']):
    if g['marks'] > 0:
        print("  %-8s %-5s %-58s %s" % (g['key'][0] + ':' + g['key'][1], g['marks'], g['members'][0]['text'][:58], ','.join(g['topics'])[:34]))

print("\nQUEUE by marks/min:")
for a in arch:
    print("  %-34s %6.1f mk  %4.1f min  roi %5.2f  q=%-3d %s" % (a['id'], a['marks_at_stake'], a['_est_min'], a['_roi'], a['instances'], ','.join(a['topics'])[:38]))

for a in arch:
    a.pop('_est_min'); a.pop('_roi')

doc = {
    "exam": "Introduction to Quantum Computing (RWTH Aachen)",
    "exam_date": "2026-08-20",
    "exam_minutes": None,
    "exam_minutes_note": "not yet supplied - budgets below are provisional, authored per-archetype rather than derived",
    "total_marks": 492.0,
    "mapped_at": datetime.date.today().isoformat(),
    "mode_version": "EXAM_PREP_PROMPT_v1",
    "source_exemplars": sorted(os.path.basename(f) for f in glob.glob(os.path.join(PARSED, '*.json'))),
    "marks_mapped": covered,
    "marks_unmapped": lost,
    "archetypes": arch
}
json.dump(doc, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print("\nwrote", OUT)

# Course Glossary — Introduction to Quantum Computing

RWTH Aachen, summer term 2025 (Dominique Unruh; notes by Jannik Hellenkamp, Stefan Stump, Dominique Unruh).

## Canonical Vocabulary

- **Deterministic possibilities**: the finite set of possible outcomes of a *probabilistic* system (e.g. heads/tails for a coin). Always assumed to be given in some fixed order, even if arbitrary — this order fixes the entry order in vectors/matrices later.
- **Probability distribution**: a vector 𝑑 ∈ ℝⁿ with Σ𝑑ᵢ = 1 and 𝑑ᵢ ≥ 0 for all 𝑖. Written Pr[𝑥] = 𝑝 for "possibility 𝑥 has probability 𝑝".
- **Probabilistic process**: a matrix 𝐴 ∈ ℝᴺˣᴺ whose every column is a valid probability distribution; also called a **stochastic matrix**. Applying a process: 𝑦 = 𝐴𝑥.
- **Classical possibilities**: the quantum-world analogue of deterministic possibilities (e.g. up/down for a photon). Also assumed ordered.
- **Quantum state**: a vector 𝜓 ∈ ℂⁿ with Σ|𝜓ᵢ|² = 1. Entries are called **amplitudes** (can be negative or complex, unlike probabilities). Pr[𝑥] = |𝜓ₓ|².
- **Unitary transformation / unitary matrix**: a matrix 𝑈 with 𝑈†𝑈 = 𝑈𝑈† = 𝐼; the quantum analogue of a stochastic matrix — guarantees the output of applying 𝑈 to a quantum state is again a quantum state.
- **Observing** (probabilistic systems) vs. **measuring** (quantum systems): observing a probabilistic system is passive — it only updates knowledge and has no effect on the system. **Measuring a quantum state changes the system** — this distinction is stated explicitly as a key contrast, not just terminology.
- **Post-measurement-state (p.m.s.)**: the state of the system right after a (complete) measurement — abbreviation "p.m.s." used throughout. A **complete measurement in the computational basis** collapses to some basis vector 𝑒ᵢ with probability |𝜓ᵢ|².
- **Partial observation / partial measurement**: measuring only whether the system lies in one of several disjoint *alternatives* 𝐴₁,…,𝐴ₘ (a partition of the possibility set), rather than the full outcome. Gives Pr[outcome = 𝑘] and a (re-normalized) conditional distribution/state.
- **Beam splitter**: a semi-transparent-mirror-like unitary 𝐵 (later identified with the Hadamard-gate) that puts an incoming up/down photon path into superposition of both output paths.
- **Elitzur–Vaidman bomb tester**: the worked example showing a bomb can be detected (with some probability, ≈1 in an improved setup) *without* the photon ever passing through the box — a result impossible classically, used to motivate why superposition/interference matters before measurement.
- **Composite system / tensor product (⊗)**: combining two systems 𝐴, 𝐵 into system 𝐴𝐵 via 𝜇_𝐴𝐵 = 𝜇_𝐴 ⊗ 𝜇_𝐵 (states/distributions) or 𝑆 ⊗ 𝑇 (matrices/processes).
- **Entangled**: a composite quantum state 𝜓_𝐴𝐵 that *cannot* be written as a tensor product 𝜓_𝐴 ⊗ 𝜓_𝐵 of two separate states — the two subsystems' states depend on each other.
- **Qubit**: a quantum state 𝜓 ∈ ℂ². Quantum circuits are drawn as horizontal *wires* (a wire can carry multiple qubits).
- **Global phase (factor)**: a complex factor 𝑐 with |𝑐| = 1 by which two otherwise-identical quantum states/results can differ. It "makes no observable physical difference" — two states differing only by global phase are treated as physically the same.
- **Ket notation**: |𝑥⟩ ≔ 𝑒ᵢ, the standard basis vector for classical possibility 𝑥 (its 𝑖-th position). Also used more loosely to mark "𝜓 is a quantum state" via |𝜓⟩ (not necessarily a classical possibility). Special kets: |+⟩ ≔ (|0⟩+|1⟩)/√2, |−⟩ ≔ (|0⟩−|1⟩)/√2.
- **Bra / braket notation**: ⟨𝜓| ≔ |𝜓⟩† (conjugate transpose / Hermitian adjoint of the ket). ⟨𝜓|𝜙⟩ ≔ ⟨𝜓|·|𝜙⟩ is the inner product of 𝜓 and 𝜙.
- **Phase kickback**: the phenomenon where the output of a function 𝑓, applied via a unitary 𝑈_𝑓 to an ancilla in state |−⟩, gets encoded as a (−1)^𝑓(𝑥) phase factor on the *input* register rather than changing the ancilla.
- **Oracle / query**: a black-box unitary implementing a function 𝑓 that an algorithm can "query" (evaluate) but not otherwise inspect. Algorithm cost is measured in number of queries.
- **Bernstein–Vazirani algorithm**: finds a hidden bitstring secret 𝑠 (where 𝑓(𝑥) = 𝑥·𝑠 mod 2) with a single query, vs. 𝑛 queries classically.
- **Discrete Fourier Transform (DFT)**: unitary matrix DFT_𝑁 ≔ (1/√𝑁)(𝜔^𝑘𝑙) with 𝜔 = 𝑒^(2𝑖π/𝑁) the 𝑁-th root of unity; used to extract the period of a periodic vector/state. ⚠️ Naming note: the lecture notes consistently say "Discrete Fourier Transform / DFT", never "Quantum Fourier Transform (QFT)" — but the exam taxonomy for this course labels the same topic "Quantum Fourier Transform". Both names refer to the identical matrix/circuit; use "DFT" when following the notes' derivation, recognize "QFT" as the exam's label for the same thing.
- **Shor's algorithm**: factors an integer 𝑁 by reducing factoring to **order finding** (find 𝑟 = ordₙ(𝑎), the smallest 𝑟 with 𝑎^𝑟 mod 𝑁 = 1), which is a special case of **period finding**, solved via the DFT plus a continued-fraction post-processing step.
- **Continued fraction expansion / convergent**: writing a number as 𝑡 = 𝑎₀ + 1/(𝑎₁ + 1/(𝑎₂ + …)), written [𝑎₀; 𝑎₁, 𝑎₂, …]; a prefix [𝑎₀; 𝑎₁,…,𝑎ᵢ] is a **convergent**, used in Shor's post-processing to recover the period 𝑟 from an approximate fraction.
- **Grover's algorithm**: searches for the unique 𝑥₀ with 𝑓(𝑥₀) = 1 in ~√(2ⁿ) steps (vs. ~2ⁿ classically), using the oracle 𝑉_𝑓 (phase-flips marked states) and **FLIP∗** (reflects about the uniform superposition |∗⟩), repeated 𝑡 times.
- **Hamiltonian**: the Hermitian matrix 𝐻 describing the total energy of a quantum system; total energy = ⟨𝜓|𝐻|𝜓⟩. **Energy eigenstates** of 𝐻 evolve simply as 𝜓(𝑡) = 𝑒^(−𝑖𝐸𝑡/ℏ)𝜓(0).
- **Schrödinger equation** (time-dependent): 𝑑𝜓(𝑡)/𝑑𝑡 = (𝑖/ℏ)𝐻(𝑡)𝜓(𝑡) — sign convention as written in the notes.
- **Cooling** (Doppler cooling, sideband cooling): initializing a trapped-ion qubit to |0⟩ by laser-induced energy reduction.
- **Universal set of gates**: a gate set 𝐺 such that any unitary can be approximated to arbitrary precision by a circuit built from 𝐺 (no auxiliary qubits). "Universal for single-qubit gates" = same, restricted to 𝑛 = 1.
- **Clifford gates**: the set {CNOT, 𝐻, 𝑆}; efficiently classically simulable (**Gottesmann–Knill theorem**) but *not* universal — adding the **𝑇 gate** makes {Clifford, 𝑇} universal.
- **Stabilizer / stabilizer state**: a state 𝜓 is stabilized by a set 𝑀 of unitaries iff 𝑈𝜓 = 𝜓 for all 𝑈 ∈ 𝑀. 𝜓 is a **stabilizer state** iff some 𝑀 ⊆ Pauli uniquely stabilizes it (up to global phase). Notation: 𝜓 ∼ 𝑀.
- **Transversal gate**: a logical gate implementable by applying identical physical gates to each physical qubit of the code block independently — the notes flag that other, slightly different definitions of "transversal" exist elsewhere.
- **Fault-tolerant (FT) implementation**: a gate implementation satisfying the three error-containment requirements (A), (B), (C) so that ≤1 physical error in never produces >1 error per output block.
- **Threshold theorem**: if the physical gate error rate is below a certain threshold, the logical error rate can be driven arbitrarily low via fault-tolerant computation (threshold believed between 0.1% and 1% in reality).
- **Repetition code / bit-flip code / phase-flip code / Shor's code / Steane code**: classical repetition code (encode 1 bit as 3 copies) → quantum bit-flip code (corrects 𝑋-errors) → phase-flip code (corrects 𝑍-errors, uses |+⟩/|−⟩ basis) → **Shor's code** (9 qubits, combines both, corrects arbitrary single-qubit error) → **Steane code** (7 qubits, corrects one error, better suited to fault tolerance since more gates are transversal on it).
- **NP** (complexity class): language 𝐿 with a poly-time verifier 𝐴 s.t. YES-instances have a witness 𝜔 with 𝐴(𝑥,𝜔)=1 and NO-instances have none.
- **QMA (Quantum Merlin Arthur)**: quantum analogue of NP — poly-time quantum verifier accepts a good quantum witness |𝜓⟩ with probability ≥ 2/3 on YES-instances and ≤ 1/3 on NO-instances for all witnesses. **2-local Hamiltonian problem** is a QMA-complete example.

## Notation Conventions

- **Pr[𝑥] = 𝑝**: standard probability notation throughout, including for measurement/observation outcomes, e.g. Pr[outcome = 𝑘].
- **≔**: "defined as" (used consistently for all new definitions, distinguishing definition from mere equation).
- **†** (dagger): conjugate transpose / Hermitian adjoint, used both on matrices (𝑈†) and on kets (⟨𝜓| ≔ |𝜓⟩†).
- **⊗**: tensor product, for both states/distributions and matrices/gates; 𝐻^⊗ⁿ denotes 𝐻 applied to all 𝑛 wires in parallel.
- **|𝑥⟩, ⟨𝜓|, ⟨𝜓|𝜙⟩**: ket, bra, braket (inner product) — introduced only in Chapter 8; earlier circuit diagrams use |⟩ informally as "just a label" before the formal definition.
- **Tilde (˜)**: marks a *logical/encoded* operation or qubit, e.g. |0⟩̃, 𝑋̃, as opposed to the physical qubit/gate.
- **0.𝑗₁𝑗₂…**: binary fraction notation (e.g. 0.101₂ = 1/2 + 1/8 = 5/8), used in the DFT circuit derivation.
- **Index vs. name looseness**: the notes are explicit that they distinguish the *name* 𝑥ᵢ of a possibility from its *index* 𝑖 in careful definitions (e.g. Definition 5.1), but then say "we will often be less precise and simply pretend the deterministic possibilities are the numbers 1,…,𝑁" for later, less formal use — both forms may appear.
- **Ordering convention**: deterministic/classical possibilities must always be given a fixed (if arbitrary) order before being written as vector/matrix entries — this ordering is never optional, it's assumed throughout.
- **Pauli set**: 𝑃𝑎𝑢𝑙𝑖 denotes the set of all 𝑛-qubit tensor products of {𝑋,𝑌,𝑍,𝐼} with phase factors ±1, ±𝑖 (used for stabilizer formalism).
- Gate symbols used consistently: 𝐼 (identity), 𝑋, 𝑌, 𝑍 (Pauli/bit-flip etc.), 𝐻 (Hadamard), CNOT and CNOT′ (control/target swapped), 𝑆, 𝑇, 𝑅ₓ(𝜃)/𝑅_𝑌(𝜃)/𝑅_𝑍(𝜃) (rotation gates), Toffoli.

## Answer Format Expectations

- When two computed results (e.g. two post-measurement-states, or two unitaries) differ only by a global phase factor 𝑐 (|𝑐| = 1), state this explicitly and treat them as equivalent rather than as a contradiction — the notes do this every time it comes up.
- Keep "observing" (probabilistic) and "measuring" (quantum) terminologically separate — they are analogous but not interchangeable, and the notes deliberately use different verbs for the two cases.
- When writing a probability distribution or quantum state as a vector, state (or assume) an explicit ordering of the possibilities first, since the vector's meaning depends on it.
- For circuit/algorithm derivations, the notes' convention is to number intermediate states as |𝜓₁⟩, |𝜓₂⟩, … (or 𝜙₁, 𝜙₂, … for non-normalized states) step by step and show the unitary applied at each step.

## Common Mistakes / Warnings

- "Measuring a quantum state changes the system!" — explicitly flagged as a common point of confusion, since the parallel definition for observing a probabilistic system has *no* effect on the system.
- Naively running an existing classical algorithm on a quantum computer via superposition does **not** give a speedup — a measurement collapses to one random result and the rest of the computed information is lost. Quantum speedups require deliberately engineered interference.
- Two Pauli matrices are *not* enough to build a universal gate set, and the Pauli gates alone can never entangle qubits — a common but incorrect intuition the notes explicitly rule out.
- In Shor's algorithm post-processing, the fraction recovered from a convergent may not have the true period 𝑟 in its denominator if numerator/denominator share a common factor during simplification — flagged as a (small-probability) failure mode already absorbed into the stated success probability.
- The bit-flip/phase-flip/Shor code constructions only work if the measurement of the error syndrome (𝑚₁, 𝑚₂) is done *without* directly measuring the data qubits — otherwise the superposition being protected is destroyed.

## Source Log

- Introduction-to-Quantum-Computing.pdf (lecture notes, RWTH Aachen, summer term 2025) — processed 2026-08-10

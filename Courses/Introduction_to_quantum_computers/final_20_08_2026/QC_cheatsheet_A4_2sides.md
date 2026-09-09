# QC CHEAT SHEET — 2 sides A4 (handwrite)
*Ranked by marks on the SS2024 paper. Side 1 = compute. Side 2 = recall.*
*Golden rule: answer EVERY sub-part. Post-measurement state + normalisation are where you leak marks.*

---

## ▌SIDE 1 — MACHINERY

### 1. Basis order (everything depends on this)
2 qubits: index = binary → `|00⟩ |01⟩ |10⟩ |11⟩` = e₀ e₁ e₂ e₃.
n qubits → 2ⁿ entries. Top wire = LEFT/most significant bit.

### 2. Valid state & norm  *(5+3 mk)*
- Valid ⟺ Σ|aᵢ|² = 1.  **|a+bi|² = a²+b²**  (not (a+bi)²).  |i/√2|² = ½.
- Missing entry: **? = √(1 − Σ|others|²)**. Any complex number of that modulus is accepted.
- ‖v‖ = √(Σ|vᵢ|²).  ‖(1,1)‖=√2 · ‖ |0⟩+|1⟩ ‖=**√2** (unnormalised!) · ‖ |0⟩ ‖=1 · ‖0‖=**0** (scalar zero).
- TRAP: `‖0‖` vs `‖ |0⟩ ‖` — read the bars.

### 3. Tensor product A⊗B  *(5 mk)*
Each entry of **A** scales a **whole copy of B**, in order.
(a₀,a₁)⊗(b₀..b₃) = (a₀b₀,a₀b₁,a₀b₂,a₀b₃, a₁b₀,a₁b₁,a₁b₂,a₁b₃) — 2·4 = 8 entries.
Matrices: (n·p)×(m·q), each aᵢⱼ scales a full copy of B.
TRAPS: A⊗B ≠ B⊗A (order = the classic loss) · write the zeros too.

### 4. Circuit tracing  *(8 mk)*
Write the full vector, apply gates **strictly left→right**, write the state after **each** gate, stop **exactly** at the named marker (ψ₁/ψ₂/ψ₃ are graded separately).
Gates: X=[[0,1],[1,0]] · Z=[[1,0],[0,−1]] · Y=[[0,−i],[i,0]] · H=1/√2[[1,1],[1,−1]] · S=diag(1,i) · T=diag(1,e^{iπ/4})
H|0⟩=(|0⟩+|1⟩)/√2 · H|1⟩=(|0⟩−|1⟩)/√2 · H|+⟩=|0⟩ · X|+⟩=|+⟩ · Z|+⟩=|−⟩
CNOT(c→t): flips t iff c=1. Toffoli(a,b→t): flips t iff a=b=1.
**Worked (the 2024 one):** |00⟩ –H(top)→ (|00⟩+|10⟩)/√2 –CNOT(top→bot)→ (|00⟩+|11⟩)/√2 –X(top)→ (|10⟩+|01⟩)/√2.
TRAP: keep the 2^(−n/2); Hⁿ on |0ⁿ⟩ gives 2ⁿ terms.

### 5. Measurement — FULL  *(4 mk)*
P(outcome b) = |a_b|². Post-state = |b⟩ (drop the phase, it's normalised already).
Ex: ψ=(−i/2, 1/√2, 0, i/2) → P(00)=|−i/2|²=**¼**, post = **(1,0,0,0)**.

### 6. Measurement — PARTIAL  *(4 mk)*
Outcome set A: 1) **zero out** every component not in A → unnormalised v.
2) P(A) = ‖v‖² = Σ_{i∈A}|aᵢ|².  3) post-state = **v/‖v‖**.
Ex: same ψ, A₂={01,10} → P=|1/√2|²+0=**½**, post = **(0,1,0,0)**.
TRAPS: ALWAYS write the post-measurement state · normalise it · if asked for both, give both.
Two measurements: "without knowing the 1st" = sum over both (marginalise); "knowing the 1st" = collapse THEN square.

### 7. Entanglement test (2 qubits)  *(in T/F)*
(a₀,a₁,a₂,a₃) is a **product state ⟺ a₀a₃ − a₁a₂ = 0**. Non-zero ⇒ entangled.
Ex: ½(1,−1,1,−1): (½)(−½)−(−½)(½)=0 → **NOT entangled** (= |+⟩⊗|−⟩).

### 8. Hamiltonian → gate  *(8 mk)*
Solve time-independent Schrödinger: Ĥψ=Eψ → E = eigenvalues, E₀ ≤ E₁.
Ĥ = X = [[0,1],[1,0]] → **E₀ = −1, E₁ = +1** (eigvecs |−⟩,|+⟩).
U(t) = e^{−iĤt}. If Ĥ² = I: **e^{−iĤt} = cos(t)·I − i·sin(t)·Ĥ**.
→ X gate (up to global phase) when sin t = ±1 ⇒ **t = π/2**.
General: diagonalise Ĥ=PDP†, U = P·e^{−iDt}·P† — exponentiate the **diagonal only**.
TRAPS: the minus in e^{−iĤt} is load-bearing · global phase ≠ different gate, factor it out.

### 9. Oracle circuit → f  *(5 mk)*
Track the **aux** wire. Each CNOT(a→aux) XORs `a`; each Toffoli(a,b→aux) XORs `a·b`.
f = whatever aux holds **at the moment of CNOT(aux→y)**. Everything after that is **uncomputation — ignore it**.
Ex: CNOT(x₁→aux), Tof(x₂,x₃→aux), CNOT(aux→y), then mirror ⇒ **f = x₁ ⊕ (x₂ ∧ x₃)**.

---

## ▌SIDE 2 — ALGORITHMS & FORMALISM

### 10. Bernstein–Vazirani  *(8 + 4 mk)*
Circuit: |0ⁿ⟩–H^⊗n–U_f–H^⊗n–measure **s** ; |1⟩–H–U_f. f(x) = x·s.
**Read s from a truth table:** sᵢ = f(eᵢ), i.e. evaluate f on 100…, 010…, 001….
Ex: f(100)=1, f(010)=1, f(001)=0 ⇒ **s = 110**.
f ≡ 0 → s=0ⁿ. f ≡ 1 → s=0ⁿ (global −1 only). f = ¬(x·s) → still s.
**Which modifications keep s?**
- Measure bottom wire **AFTER** U_f → **YES** (bottom is |−⟩, already unentangled from the answer).
- Measure bottom wire **BEFORE** U_f → **NO** (kills |−⟩ ⇒ no phase kickback).
- Replace **1st** H^⊗n by DFT_{2ⁿ} → **YES** (both make the uniform superposition from |0ⁿ⟩).
- Replace **2nd** H^⊗n by DFT_{2ⁿ} → **NO** (the 2nd layer must *undo* the 1st; DFT ≠ H^⊗n for n>1).
TRAP: an *ignored* measurement still collapses. The two H layers do different jobs.

### 11. DFT  *(3 mk)*
DFT_N |0⟩ = uniform superposition (= H^⊗n on |0ⁿ⟩, **not** entangled).
Input comb with a non-zero every **r**-th slot in C^N ⇒ DFT is a comb of period **t = N/r**.
Ex: nonzero every 4th entry, N=32 ⇒ **t = 8**. TRAP: periods are **inverse**; count the input spacing carefully.

### 12. Shor  *(8 mk)*
f(x)=aˣ mod N, r = ord(a) mod N = smallest r>0 with aʳ ≡ 1.
Compute by hand: 5¹=5, 5²=25, 5³=125≡1 (mod 124) ⇒ **ord(5) mod 124 = 3**. (124 mod 5 = 4; 4²=16≡1 ⇒ ord = 2.)
**Upper-register outcome c ≈ a multiple of 2ⁿ/r.** (n=100, r=3 ⇒ 2¹⁰⁰/3.)
Then continued fractions on c/2ⁿ → r. Factor: if r even and a^{r/2} ≢ −1, take gcd(a^{r/2}∓1, N); else retry.

### 13. Grover  *(in T/F)*
t_opt ≈ (π/4)√(N/M), N=2ⁿ, M = #solutions. Queries O(√N) = 2^{n/2} — **√ of the search space, not of n**.
- More iterations does **NOT** monotonically help — success **oscillates**. (F)
- Success prob is **not exactly 1** in general. (F)
- t tuned for 1 solution is **wrong** for 2 solutions (overshoots). (F)
- An O(n²) oracle multiplies total time, not the query count.

### 14. Stabilisers  *(6 + 4 mk)*
**Set → state:** each generator is a +1 eigenvalue constraint. ZI ⇒ qubit1 = |0⟩; −IZ ⇒ qubit2 = |1⟩ ⇒ **|01⟩**.
(Z: |0⟩=+1, |1⟩=−1. X: |+⟩=+1, |−⟩=−1.)
**Unitary → new set:** conjugate every generator, **S → U S U†** (not US). Only on the factors U touches. Carry signs.
Clifford table: **H:** X↔Z, Y→−Y · **S:** X→Y, Y→−X, Z→Z · **CNOT(c→t):** XI→XX, IZ→ZZ, IX→IX, ZI→ZI.
Ex: {XX, −YZ} under H⊗I → XX→ZX ; −YZ→ −(−Y)Z = **+YZ** ⇒ **{ZX, YZ}**.

### 15. Error correction  *(3 mk)*
Shor code = 9 qubits, corrects **any single-qubit error**. Correcting X, Y, Z ⇒ correcting **all** 1-qubit errors (every 1-qubit op is a lin. comb. of I,X,Y,Z — error discretisation). So "corrects X,Y,Z but not H" is **FALSE**.
**Transversal gate** acts qubit-wise ⇒ maps product states to product states ⇒ Gψ non-entangled if ψ non-entangled: **TRUE**. Also: no code has a universal transversal gate set (Eastin–Knill).

### 16. Gate sets / universality  *(4 mk)*
Q: can this set build **SWAP**? SWAP = **3 CNOTs** ⇒ you need an **entangling 2-qubit gate**.
✔ Clifford (CNOT,H,S) ✔ Clifford+T ✔ {Toffoli, H} (universal; Toffoli with |1⟩ aux = CNOT)
✘ {X,Y,Z,S,T,H} — all single-qubit, no entangler ⇒ never.
Universality: finite 1-qubit sets like {X,Y,Z} are **not** dense ⇒ not universal even on 1 qubit. {CNOT,H,T} = universal.

### 17. Uniform superposition Σ_x 2^{−n/2}|x⟩  *(4 mk)*
Need **every** basis state, equal amplitude **and equal sign**.
✔ H^⊗n on |0ⁿ⟩ ✔ DFT_{2ⁿ} on |0ⁿ⟩ ✘ X^⊗n on |0ⁿ⟩ (just permutes to |1ⁿ⟩)
✘ H on one wire of |+⟩^⊗n (H|+⟩=|0⟩ — kills it) ✘ Z on one wire (|+⟩→|−⟩, sign breaks uniformity)
Note X|+⟩ = |+⟩ (harmless); H and Z are the ones that break it.

### 18. Fact bank for T/F  *(7 + 7 mk)*
- U valid ⟺ **unitary** (U†U=I, orthonormal columns). All-1/√2 matrix: columns equal ⇒ **not** unitary. **F**
- Two identical consecutive measurements → same outcome. **T** (state already collapsed)
- …with **Z** in between → still same. **T** (Z is diagonal in the computational basis, phase only)
- …with **X** in between → **F** (X flips the outcome)
- A finite continued fraction is always rational. **T**
- DFT_{2ⁿ}|0ⁿ⟩ entangled? **F** (it's |+⟩^⊗n, a product state)
- Global phase never changes a measurement outcome.
- Measurement is irreversible; an ignored outcome still collapses.

---
**Before you submit each question:** re-read it and check that *every* asked quantity has an answer, is normalised, and is in the demanded notation (ket, no |+⟩/|−⟩, no ⊗).

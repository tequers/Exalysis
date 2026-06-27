# Tutor Feedback Log

A living record of tutor mistakes, near-misses, and the rules that prevent them.
Updated during sessions whenever a protocol violation is caught.

---

## 2026-06-27 — Loci encoding triggered before concept retrieval

**What happened:**
After rung 1 PASS on weight sharing (CNNs), the tutor correctly ran the loci encoding flow for station 5.1 (already encoded — confirmed solid). Then it immediately proposed encoding station 5.2 (pooling) even though pooling had not yet been introduced, questioned, or answered by the user. The user caught this.

**Rule violated:**
> "After I pass rung 1 or you first explain a concept: check `loci_encodings.md` for that concept's station. If status is ❌, run the encoding flow."

The trigger is **rung 1 PASS on that specific concept**, not "rung 1 PASS on the topic in general." Proposing an encoding for a concept the user hasn't encountered yet is backwards — it front-loads the mnemonic before any understanding exists, which defeats the purpose of the encoding.

**Rule to enforce going forward:**
- Only run the loci encoding flow for a concept **after the user has attempted and passed at least rung 1 on that specific concept**.
- Encoding order follows rung order. If rung 2 introduces a new concept (e.g. pooling), encode pooling only after rung 2 passes.
- Never scan ahead in `loci_encodings.md` and propose ❌ stations for concepts not yet covered in the ramp.

**Check:** Before proposing any loci encoding, ask: "Has the user answered at least one question on this specific concept?" If no → wait.

---

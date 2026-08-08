# Session Notes / Pending Tasks

## Loci encoding updates needed (end of session)

### 4.3 Piano — Cross-entropy loss
Current encoding captures the single-example formula correctly, but needs to clarify the per-example summation:
- The full formula sums over n examples: L = −(1/n) · Σᵢ Σ_c yᵢ_c · log(pᵢ_c)
- The piano scene works for one example; add note that the piano screams once per example and you average all screams
- User learned this the hard way: thought n divided by number of classes, not number of examples

### CNN parameter counting — known failure mode (encode in loci or concept map)
User made this mistake twice: thought bias is per input channel, not per output channel.

**Rule to encode:** number of kernels (and biases) is determined by **output channels**, not input channels.
- One filter → one output channel → covers ALL input channels → 1 bias
- Formula: (k × k × C_in + 1) × C_out
- The kernel spans all input channels; the bias is one per output channel (per filter)

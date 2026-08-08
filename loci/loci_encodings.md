# Loci Encodings — Living Room Palace

Tracks which concept is encoded at each station, the bizarre image used, and encoding status.
Status: ✅ solid | ⚠️ needs sharpening | ❌ empty

---

## Subsection 1 — Entry / Palisandro Wall
*(Topic: Canny Edge Detection)*

| # | Station | Concept | Bizarre Image | Status |
|---|---------|---------|---------------|--------|
| 1.1 | Roomba | Gaussian filter — smooths/blurs image before gradient | Roomba glides across the floor over expensive paintings (the Mona Lisa). Irreversibly blurs them. Smug Roomba says "I'm the Gaussian filter, looks cool right?" — owner is horrified. | ✅ |
| 1.2 | Palisandro (3 drawers) | Gradient computation: Cx (horizontal), Cy (vertical), magnitude √(Cx²+Cy²) | Swan crushes Cx (moustache detective) and Cy (afro detective) — they curse at it (squaring = Cx², Cy²). They crawl under the rifle (√ symbol) to escape the chaos above. A Mangus ice cream sticks out of the middle drawer — bigger detectives = more ice cream sticking out (magnitude). | ✅ |
| 1.3 | Xiaomi vaporizer | Non-maximum suppression — keep only local gradient peaks; ties = implementation-dependent | Nun on ice skates on top of the vaporizer, skating along the gradient direction. Holds a ruler — flames the lower tile. On a tie she collapses, then pulls out a small rusty emergency note explaining what to do (implementation-dependent, can change). | ✅ |
| 1.4 | Flower pot | Gradient direction θ = atan2(Cy, Cx) — angle fed to NMS | Tanga-bow throws Afro detective (Cy) and Moustache detective (Cx) at the flower pot lid → lid flies off → angel with θ-halo rockets out and whispers the skating direction to the nun. | ✅ |
| 1.5 | Mirror | Hysteresis thresholding — strong edges stay, weak edges stay only if connected to strong | Mirror with cracks. Cracks below T_low vanish. Cracks above T_high stay (strong edges). Cracks in between stay only if touching a T_high crack (connected weak edges) | ✅ |

---

## Subsection 2 — Sofa Area
*(Topic: Feature Detection & Description — Harris + SIFT)*

| # | Station | Concept | Bizarre Image | Status |
|---|---------|---------|---------------|--------|
| 2.1 | Footrest | Harris: structure tensor M — sliding window, intensity change in all directions | Two detectives visit every pixel: Afro (tall, black, vertical = Cy) and Moustache (short, bald, chubby, huge horizontal moustache = Cx). A pink swan (²) grabs Afro by the hair and Moustache by the moustache — squaring them. They wrap their chains together (IxIy cross term), stuff everything in a briefcase (M), kick it down a hatch under the footrest into an underground lab. Scientist stamps: CORNER (R positive), EDGE (R negative), FLAT (R≈0). | ✅ |
| 2.2 | Inside sofa / cushion rails | Harris: eigenvalue cases (flat/edge/corner) — λ₁,λ₂ small=flat, one large=edge, both large=corner | Plusle (green, vertical arrow = λ₁) and Minun (orange, horizontal arrow = λ₂) inside the sofa. Flat: both tiny and shriveled, collapse on cushions, no tent. Edge: one giant raging, one tiny baby — lopsided tent falls over in one direction. Corner: both huge and roaring — massive glowing blanket tent fills the whole sofa cavity. | ✅ |
| 2.3 | Countryside painting | Harris: corner response R = det(M) - k·trace(M)² | Kite carrying the police suitcase (det(M)) crashes through the countryside painting. Kevin in wheelchair fires a Breath of the Wild ice arrow at the suitcase (k × subtraction). The ice arrow is tied to a trace rope (λ₁+λ₂), and a red swan grabs the rope and squares it (trace²). R = kite-crash − Kevin's ice arrow · red-swan². | ✅ |
| 2.4 | Hook picture lamp | SIFT: local descriptor — 16×16 patch → 4×4 grid of cells → 8-direction histogram per cell → 128-number fingerprint. Matching = Euclidean distance between fingerprint vectors. | Lamp points at wall. Shoe×shoe (16×16 patch). Inside: door×door grid (4×4 cells). Each door-cell has a cake stretched in 8 directions (cross + diagonals). Mangus white chocolate stretches the cake (gradient magnitude weights the bins). Giant finger crashes in and leaves its fingerprint on the glowing hot lamp (= 128-number descriptor output). | ✅ |
| 2.5 | Ceiling light | SIFT: scale invariance + rotation invariance — Gaussian blur at multiple scales (scale-space), keypoint stable across blur levels and orientations | The giant finger from 2.4 reaches up and spins the ceiling light (rotation invariance). Then slaps a massive painting-sized fingerprint on one side and a tiny stamp-sized fingerprint on the other — the frosted lamp recognizes them as the same keypoint (scale invariance). Same fingerprint, two scales, one lamp. | ✅ |

---

## Subsection 3 — Door & Table Area
*(Topic: Clustering & Mixture Models)*

| # | Station | Concept | Bizarre Image | Status |
|---|---------|---------|---------------|--------|
| 3.1 | Crystal rainbow door | k-Means: steps — random init once, then assign to nearest center, recompute center as group mean, repeat until stable | N dummies pour through the crystal rainbow door. One-time lottery picks k kings (random init). Each dummy runs to nearest king. Kings glow average color of their group. Then crowns become magnetic — fly off and reattach to the true mean dummy each round. Repeat until no dummy switches. | ✅ |
| 3.2 | Upside-down chair | k-Means: properties — always converges ✓, never globally optimal ✗ (local min), finding global optimum is NP-hard | Chair climbs a small hill and shouts "I FOUND THE HIGHEST POINT!" — opens eyes and sees a massive golden peak on the other side (global optimum). Chair shrugs: "I never gave you a warranty." Napoleon stands guard at the golden peak — to find the global optimum you must defeat Napoleon (NP-hard). | ✅ |
| 3.3 | Dining table | k-Means: weaknesses — needs k upfront, sensitive to init, assumes spherical clusters; k-means++ fix | Porter at door demands K before entry. Centers placed too close → civil war explodes. Lamp god above table descends with magnets on each center — repels nearby points so next center must be far from all existing ones (k-means++, distance² probability). Peace restored. But clusters form a dolphin shape → centers totally confused → HUGE FAIL (non-spherical clusters). | ✅ |
| 3.4 | Windows | Mean-Shift: steps — compute mean of points within radius r, shift toward it, repeat until convergence | Magic compass obsessed with Kirito. Draws circle (radius r) on the floor-image, Kirito teleports to the exact mean position of all points inside (densest spot, not nearest point). Repeats. When the circle fires up at the same spot twice → cluster center found. | ✅ |
| 3.5 | Translucent blinds | Mean-Shift: properties — no k needed, finds arbitrary shapes, slow, bandwidth r-sensitive | Hippie at the blinds asks for no K ("no k needed, my fella"). Dolphin shape appears — hippie grabs magic compass and finds its center perfectly (arbitrary shapes ✅). Small compass = tiny r → hippie hallucinates, finds a tiny bump instead of the real cluster (over-segments). You stuff the joint into the compass band → stretches larger r → merges everything together (under-segments). | ✅ |

---

## Subsection 4 — Shelf & AC Wall
*(Topic: Neural Network Training & Loss Functions)*

| # | Station | Concept | Bizarre Image | Status |
|---|---------|---------|---------------|--------|
| 4.1 | Air conditioning unit | Neuron: weighted sum (w·x) + bias + activation function (ReLU) | Conveyor belt feeds items with price tags (weights × inputs) onto a scale. Bias brick already sits on the scale. Below threshold → AC stays off (ReLU = 0). Above threshold → AC blasts proportionally harder the more the scale tips (ReLU output = excess above zero). | ✅ |
| 4.2 | Shelf (guitar + books merged) | Forward pass: input → layers → output | Shelf = neural network canvas. Air conditioners drilled in as neurons per layer. Fire = excitatory connections, ice = inhibitory. Each AC explodes after passing its output forward — sequential explosions left-to-right encode directionality. Reset between inputs. | ✅ |
| 4.3 | Piano | Loss function: cross-entropy — L = −(1/n)·Σᵢ Σ_c y·log(p). One scream per example, averaged over n examples. Only the ground-truth key matters (others are zero). | Piano keys = ground truth (fixed). Neural network outputs = wild animals shot from the Clash Royale Log card. Log rolls across piano, animals crash into keys. Discrepancy = loss (piano screams). **One full piano performance per training example** — you average the screaming volume across all n performances. Perfect prediction = silence. The 1/n is averaging screams across the crowd of examples, NOT across the keys. | ✅ |
| 4.4 | Vertical floor lamp | Backpropagation: gradient of loss flows backward through layers | ❌ |
| 4.5 | Transparent cabinet — porcelain | Gradient descent: update weights in direction of steepest loss decrease | ❌ |

---

## Subsection 5 — TV & Entertainment Unit
*(Topic: Convolutional Neural Networks)*

| # | Station | Concept | Bizarre Image | Status |
|---|---------|---------|---------------|--------|
| 5.1 | Left drawer — Wii accessories | CNN: local receptive fields + weight sharing — one kernel slides across image, same weights at every patch | Square bloated oruga (caterpillar) that ate a painter — paint splatters everywhere. Each leg has a weight stamped on it. Slides across Wii accessories patch by patch, legs press a weighted imprint at each local area. Same oruga, same legs, same weights every patch = weight sharing. Local = legs only touch a small patch at once. | ✅ |
| 5.2 | Console gap — Wii/Switch/PS4 | Feature maps — C_out kernels each slide the full input, each leaving one 2D activation trail (feature map). Bias = one brick per console. | Three colored caterpillars (white=Wii, blue=PS4, red=Switch) slide the full length of the console gap. Each has its own bias brick. Each leaves a colored splatter trail — bright where the feature is strong, faint where weak. Three caterpillars → three feature maps. They detect features everywhere, not just "their" console. | ✅ |
| 5.3 | Samsung TV | MaxPooling — takes max per 2×2 window, halves spatial size, saves index (ember mark) for unpooling. Conv layer (Kamek) grows values back. | Samsung TV shows a YouTube video of the encoder-decoder. At each pooling layer: trees grow across the image. Tallest tree = max, survives. Others explode into fire and ash. A **glowing ember** marks exactly where the max tree stood (= saved index). Decoder: seed planted on each glowing ember → **Kamek** (Mario Bros wizard) waves his wand → seeds grow back into full feature maps (conv layer fills the gaps). Repeat per layer until full resolution restored. | ✅ |
| 5.4 | Transparent drawer — painting stickers | TBD | ❌ |
| 5.5 | Subwoofer — **END** | TBD | ❌ |

---

## Encoding progress
- Subsection 1: 5/5 solid ✅ | 0 ⚠️ | 0 ❌  (Canny Edge Detection — all walked & confirmed 2026-06-28)
- Subsection 2: 5/5 solid ✅ | 0 ⚠️ | 0 ❌  (Feature Detection & Description — all walked & confirmed 2026-06-28)
- Subsection 3: 5/5 solid ✅ | 0 ⚠️ | 0 ❌  (Clustering & Mixture Models — all walked & confirmed 2026-06-28)
- Subsection 4: 3/5 solid ✅ | 0 ⚠️ | 2 ❌  (NN Training: 4.1–4.3 ✅, 4.4 backprop ❌, 4.5 gradient descent ❌)
- Subsection 5: 1/5 solid ✅ | 0 ⚠️ | 4 ❌  (CNNs: 5.1 weight sharing ✅, 5.2–5.5 pending)

# -*- coding: utf-8 -*-
"""
Computer Vision, final_26_08_2026 - ARCHETYPE MAP (judgement layer).

This file holds only decisions a person had to make: which question belongs to which
archetype, and what the playbook for that archetype says. It contains NO arithmetic.
Every number in archetypes.json - marks, mark shares, budgets, ROI ordering - is computed
by archetypes_postprocess.py from this map plus parsed/*.json.

That split is deliberate. On the quantum-computing port the budgets were derived by hand
and came out wrong three times running, because a hand-typed number has nothing to check it.

WHY THIS COURSE NEEDED A DIFFERENT PLAYBOOK SHAPE
-------------------------------------------------
58% of the marks here (128/220) are `explain_derive`, and the real 2023 paper averages
2.0 marks per question. The marks count *distinct scorable statements*, not steps of a
calculation. So a playbook carries:

  trigger       - what you see on the page that fires this archetype
  why           - ONE sentence of causal intuition. Not a derivation. On an explain-heavy
                  paper the question literally asks "why", so a recipe without this fails.
  answer_shape  - the shape of a full-mark answer, e.g. "2 methods x (1 adv + 1 disadv)"
  steps         - the scorable points, roughly one per mark
  traps         - named failure modes; these accumulate from drills and feed /cheat-sheet

RECALL ARCHETYPES vs DERIVATION ARCHETYPES
------------------------------------------
For recall-type archetypes (`algorithm-steps-recall`, `concept-brief-explain`) the playbook
carries the answer SHAPE and the instances cycle the content - no single set of steps covers
Canny and k-Means at once. For derivation-type archetypes (`derive-epipolar-constraint`) the
playbook carries the actual derivation, because there is only one and it is the whole value.
"""

# Paper weights for marks_at_stake. Only 2023_Exam is a genuine single sitting.
PAPER_WEIGHT = {
    "2023_Exam":        1.00,   # real past paper, 94 marks / 47 q - also the budget basis
    "Old_Exam_Tasks":   0.85,   # = the SS 2022 paper (same PDF as cv_ss_2022.pdf). A real
                                # sitting after all, but the oldest one and so the most exposed
                                # to the content change staff flagged on 2026-08-21.
    "mockup_exam_2023": 0.60,   # practice; PROJECT_NOTES excludes it from the 175 total
}

# Load factor on time budgets. Marks already encode expected time, so this corrects only the
# two places where they systematically don't: drawing is slower than writing, recall faster.
LOAD = {"recall": 0.85, "normal": 1.00, "slow": 1.15}

# Topics whose deep-mode status is `mastered` as of 2026-06-29 (7 weeks stale at build time).
# Used ONLY to discount estimated drill minutes - never to set exam_ready, which is a
# different criterion earned by drilling.
DEEP_MASTERED = {
    "Image Filtering and Convolution", "Feature Detection and Description",
    "Clustering and Mixture Models", "Convolutional Neural Networks", "Edge Detection",
    "Neural Network Training and Loss Functions", "Boosting and Ensemble Classifiers",
    "Semantic Segmentation with Deep Learning",
}
STALE_DISCOUNT = 0.70   # a decayed trace is cheaper to re-fire than to build; k_drill corrects this

# (exam_id, q_id) -> archetype id.  All 105 parsed questions appear exactly once;
# archetypes_postprocess.py asserts that and fails loudly if this drifts.
ASSIGN = {
 ("2023_Exam", "Q1a"): "def-formula-gloss",
 ("2023_Exam", "Q1b"): "separable-filters",
 ("2023_Exam", "Q1c"): "separable-filters",
 ("2023_Exam", "Q1d"): "conv-correlation-properties",
 ("2023_Exam", "Q1e"): "algorithm-steps-recall",
 ("2023_Exam", "Q1f"): "why-design-choice",
 ("2023_Exam", "Q1g"): "failure-mode-and-fix",
 ("2023_Exam", "Q2a"): "harris-hessian-mechanics",
 ("2023_Exam", "Q2b"): "harris-hessian-mechanics",
 ("2023_Exam", "Q2ci"): "invariance-properties-check",
 ("2023_Exam", "Q2cii"): "invariance-properties-check",
 ("2023_Exam", "Q2d"): "feature-vector-size-count",
 ("2023_Exam", "Q2ei"): "derive-homography-A",
 ("2023_Exam", "Q2eii"): "derive-homography-A",
 ("2023_Exam", "Q3ai"): "def-formula-gloss",
 ("2023_Exam", "Q3aii"): "mrf-graphcut-mechanics",
 ("2023_Exam", "Q3bi"): "mrf-graphcut-mechanics",
 ("2023_Exam", "Q3bii"): "mrf-graphcut-mechanics",
 ("2023_Exam", "Q3ci"): "algorithm-steps-recall",
 ("2023_Exam", "Q3cii"): "feasibility-judgement",
 ("2023_Exam", "Q3ciii1"): "why-method-unsuitable",
 ("2023_Exam", "Q3ciii2"): "why-method-unsuitable",
 ("2023_Exam", "Q3ciii3"): "why-method-unsuitable",
 ("2023_Exam", "Q4a"): "algorithm-steps-recall",
 ("2023_Exam", "Q4b"): "concept-brief-explain",
 ("2023_Exam", "Q4c"): "concept-brief-explain",
 ("2023_Exam", "Q4d"): "feasibility-judgement",
 ("2023_Exam", "Q4e"): "boosting-mechanics",
 ("2023_Exam", "Q4f"): "viola-jones-mechanics",
 ("2023_Exam", "Q4g"): "enumerate-and-describe",
 ("2023_Exam", "Q5a"): "compare-two-methods",
 ("2023_Exam", "Q5bi"): "cnn-parameter-count",
 ("2023_Exam", "Q5bii"): "cnn-parameter-count",
 ("2023_Exam", "Q5biii"): "receptive-field",
 ("2023_Exam", "Q5biv"): "receptive-field",
 ("2023_Exam", "Q5c"): "apply-on-given-grid",
 ("2023_Exam", "Q5di"): "read-figure-identify",
 ("2023_Exam", "Q5dii"): "read-figure-identify",
 ("2023_Exam", "Q5diii"): "read-figure-identify",
 ("2023_Exam", "Q5e"): "def-formula-gloss",
 ("2023_Exam", "Q5f"): "feasibility-judgement",
 ("2023_Exam", "Q5g"): "why-design-choice",
 ("2023_Exam", "Q6a"): "code-vision-function",
 ("2023_Exam", "Q6b"): "read-figure-identify",
 ("2023_Exam", "Q6c"): "derive-epipolar-constraint",
 ("2023_Exam", "Q6d"): "derive-ransac-iterations",
 ("2023_Exam", "Q6e"): "derive-sfm-dof",

 ("Old_Exam_Tasks", "Q1a"): "def-formula-gloss",
 ("Old_Exam_Tasks", "Q1b"): "conv-correlation-properties",
 ("Old_Exam_Tasks", "Q1c"): "enumerate-and-describe",
 ("Old_Exam_Tasks", "Q1d"): "invariance-properties-check",
 ("Old_Exam_Tasks", "Q1e"): "pyramid-mechanics",
 ("Old_Exam_Tasks", "Q1f"): "why-design-choice",
 ("Old_Exam_Tasks", "Q1g"): "pyramid-mechanics",
 ("Old_Exam_Tasks", "Q2a"): "algorithm-steps-recall",
 ("Old_Exam_Tasks", "Q2b"): "sketch-or-draw",
 ("Old_Exam_Tasks", "Q2c"): "concept-brief-explain",
 ("Old_Exam_Tasks", "Q2d"): "enumerate-and-describe",
 ("Old_Exam_Tasks", "Q2e"): "segmentation-via-clustering",
 ("Old_Exam_Tasks", "Q3a"): "algorithm-steps-recall",
 ("Old_Exam_Tasks", "Q3b"): "invariance-properties-check",
 ("Old_Exam_Tasks", "Q3c"): "sketch-or-draw",
 ("Old_Exam_Tasks", "Q3d"): "enumerate-and-describe",
 ("Old_Exam_Tasks", "Q3e"): "segmentation-via-clustering",
 ("Old_Exam_Tasks", "Q4a"): "code-vision-function",
 ("Old_Exam_Tasks", "Q4b"): "code-vision-function",
 ("Old_Exam_Tasks", "Q4ci"): "compare-two-methods",
 ("Old_Exam_Tasks", "Q4cii"): "invariance-properties-check",
 ("Old_Exam_Tasks", "Q4ciii"): "harris-hessian-mechanics",
 ("Old_Exam_Tasks", "Q5ai"): "boosting-mechanics",
 ("Old_Exam_Tasks", "Q5aii"): "algorithm-steps-recall",
 ("Old_Exam_Tasks", "Q5b"): "boosting-mechanics",
 ("Old_Exam_Tasks", "Q5c"): "boosting-mechanics",
 ("Old_Exam_Tasks", "Q5d"): "viola-jones-mechanics",
 ("Old_Exam_Tasks", "Q5ei"): "viola-jones-mechanics",
 ("Old_Exam_Tasks", "Q5eii"): "viola-jones-mechanics",
 ("Old_Exam_Tasks", "Q5f"): "viola-jones-mechanics",
 ("Old_Exam_Tasks", "Q6ai"): "epipolar-glossary",
 ("Old_Exam_Tasks", "Q6aii"): "epipolar-glossary",
 ("Old_Exam_Tasks", "Q6aiii"): "epipolar-glossary",
 ("Old_Exam_Tasks", "Q6aiv"): "epipolar-glossary",
 ("Old_Exam_Tasks", "Q6bi"): "derive-eight-point",
 ("Old_Exam_Tasks", "Q6bii"): "derive-eight-point",
 ("Old_Exam_Tasks", "Q6biii"): "failure-mode-and-fix",
 ("Old_Exam_Tasks", "Q6biv"): "failure-mode-and-fix",
 ("Old_Exam_Tasks", "Q6ci"): "fundamental-matrix-rank",
 ("Old_Exam_Tasks", "Q6cii"): "fundamental-matrix-rank",
 ("Old_Exam_Tasks", "Q6ciii"): "fundamental-matrix-rank",

 ("mockup_exam_2023", "Q1a"): "apply-on-given-grid",
 ("mockup_exam_2023", "Q1b"): "algorithm-steps-recall",
 ("mockup_exam_2023", "Q2a"): "code-vision-function",
 ("mockup_exam_2023", "Q2b"): "feasibility-judgement",
 ("mockup_exam_2023", "Q2c"): "feasibility-judgement",
 ("mockup_exam_2023", "Q3a"): "sketch-or-draw",
 ("mockup_exam_2023", "Q3b"): "mrf-graphcut-mechanics",
 ("mockup_exam_2023", "Q4a"): "compare-two-methods",
 ("mockup_exam_2023", "Q4b"): "why-design-choice",
 ("mockup_exam_2023", "Q4ci"): "feature-vector-size-count",
 ("mockup_exam_2023", "Q4cii"): "feature-vector-size-count",
 ("mockup_exam_2023", "Q4ciii"): "feature-vector-size-count",
 ("mockup_exam_2023", "Q5a"): "cnn-parameter-count",
 ("mockup_exam_2023", "Q5b"): "enumerate-and-describe",
 ("mockup_exam_2023", "Q5c"): "def-formula-gloss",
 ("mockup_exam_2023", "Q6a"): "def-formula-gloss",
 ("mockup_exam_2023", "Q6b"): "derive-triangulation",
}

# archetype id -> playbook + metadata.
#   load          key into LOAD
#   figure        True if at least one exemplar depends on a figure the parsed JSON lacks
#   kind          "recall" | "derive" | "compute" | "judge" - drives how a drill is graded
#   uses          archetypes that are genuine prerequisites (the dependency graph)
PLAYBOOKS = {

 "def-formula-gloss": dict(
   load="normal", figure=False, kind="derive", uses=[],
   trigger="'How is X defined ... give/write the formula' or 'write the formula for L and explain the variables'.",
   why="The examiner is checking you can move between the name of an operation and its indexed algebraic form - the gloss is where the marks hide, because anyone can memorise a formula and not know what the indices range over.",
   answer_shape="formula on its own line + one line per symbol. Marks ~= 1 for the formula + 1 per symbol group glossed.",
   steps=[
     "Write the formula with explicit index ranges - do not leave a bare sum sign.",
     "Gloss EVERY symbol you wrote, including the index bounds and what they run over.",
     "If the question says 'explain the variables', that is a separate mark from the formula: never skip it even when the formula is obviously right.",
     "State the role of each term when the formula has more than one (e.g. unary vs pairwise in an MRF energy).",
   ],
   traps=[
     "writing the formula and stopping - the gloss is typically half the marks",
     "cross-correlation vs convolution: convolution flips the kernel, F[i,j] (x) H[i,j] = F[i,j] * H[-i,-j]",
     "omitting the index bounds on the sum",
   ]),

 "conv-correlation-properties": dict(
   load="recall", figure=False, kind="recall", uses=["def-formula-gloss"],
   trigger="'How do you modify a cross-correlation filter to represent convolution?' or a true/false list of filtering properties.",
   why="Correlation and convolution differ by a 180-degree flip of the kernel, which is why symmetric kernels make the two identical and why the distinction is invisible until it isn't.",
   answer_shape="one sentence per property, each with a yes/no AND a reason.",
   steps=[
     "Convolution = correlation with the kernel rotated 180 degrees (flip both axes).",
     "For a symmetric kernel the two coincide - say so if asked why it often doesn't matter.",
     "Linearity holds for both; shift-invariance holds for both.",
     "On a true/false list, justify each item in a clause - an unjustified answer usually scores zero.",
   ],
   traps=[
     "flipping only one axis",
     "answering true/false with no justification when the question says 'state if ... always valid'",
   ]),

 "separable-filters": dict(
   load="normal", figure=False, kind="compute", uses=["def-formula-gloss"],
   trigger="'Write two 1D filters equivalent to this 2D filter' or 'how many operations for two 1D filters vs one 2D'.",
   why="A separable 2D kernel is an outer product of two 1D kernels, so applying them in sequence costs 2k instead of k-squared operations per pixel - this is the entire reason Sobel and Gaussian filters are implemented separably.",
   answer_shape="the two vectors written out + one operation count per case.",
   steps=[
     "Factor the 2D kernel as a column vector times a row vector (outer product).",
     "Check by multiplying back out - one multiplication verifies all nine entries.",
     "2D k x k: k^2 multiplications + (k^2 - 1) additions per pixel.",
     "Two 1D 1 x k: 2k multiplications + 2(k-1) additions per pixel.",
     "State the counts per pixel, as asked, not per image.",
   ],
   traps=[
     "giving multiplications but not additions when the question says 'addition, multiplication'",
     "reporting per-image instead of per-pixel counts",
     "sign/order error: for Sobel the [-1,0,1] row pairs with the [1,2,1] column, not the reverse",
   ]),

 "algorithm-steps-recall": dict(
   load="recall", figure=False, kind="recall", uses=[],
   trigger="'List/write down/describe the steps of <algorithm>' - Canny, RANSAC, Mean-Shift, k-Means, Adaboost, Hough, sliding-window.",
   why="These are the course's named pipelines, and the examiner is testing that you hold the ordered sequence, not that you can derive it - the order carries the marks because a pipeline out of order is a pipeline that doesn't work.",
   answer_shape="a numbered list. MARKS = NUMBER OF STEPS. A 4-mark question wants 4 steps, not a paragraph.",
   steps=[
     "Count the marks first; that is your step count and your stopping rule.",
     "Number the steps. Never write a prose paragraph for a 'list the steps' question.",
     "Name the operation in each step using the course's term.",
     "Include the termination/convergence condition for iterative algorithms - it is nearly always a scoring step.",
     "One clause of purpose per step at most; extra prose earns nothing and costs time.",
   ],
   traps=[
     "writing 3 steps for 4 marks - always match count to marks",
     "Canny: forgetting non-maximum suppression, or forgetting hysteresis is the LAST step",
     "k-Means / Mean-Shift: omitting the convergence criterion",
     "RANSAC: omitting the final re-fit on all inliers",
     "Adaboost: omitting the re-weighting of misclassified samples",
   ]),

 "enumerate-and-describe": dict(
   load="recall", figure=False, kind="recall", uses=[],
   trigger="'List two advantages and two disadvantages', 'describe two methods and name one advantage and one disadvantage for each', 'name two and describe them briefly'.",
   why="Enumeration questions are pure mark-counting: the examiner has a checklist, and each named item with its qualifier ticks one box.",
   answer_shape="EXACTLY the number asked, as a labelled list. '2 methods x (1 adv + 1 disadv)' = 4 scorable items even though it is 2 marks.",
   steps=[
     "Re-read the count in the question and write that many. No more, no fewer.",
     "Label each item explicitly ('Advantage:', 'Disadvantage:') so the marker cannot miss it.",
     "Each item is one clause. Do not explain at length - the mark is for naming, not defending.",
     "If asked for a method AND its trade-off, both halves must appear or the pair scores half.",
   ],
   traps=[
     "listing three advantages and one disadvantage when asked for two and two",
     "giving advantages that are restatements of each other - the marker counts DISTINCT points",
     "border handling: zero-padding is excluded by the question, so name wrap/clamp/mirror instead",
   ]),

 "cnn-parameter-count": dict(
   load="normal", figure=False, kind="compute", uses=[],
   trigger="'How many learned parameters does this block/layer have?' with kernel size, input depth, output depth, bias, stride, padding all given.",
   why="Parameter count is independent of spatial input size because a convolution kernel is shared across every position - that is the entire weight-sharing argument for CNNs, and the exam tests it by changing the image size and seeing if your number moves.",
   answer_shape="one arithmetic line per component + a total. Show the multiplication.",
   steps=[
     "Conv weights = k * k * C_in * C_out.",
     "Add bias = C_out (only if the question says bias).",
     "Add BatchNorm = 2 * C_out (scale and shift) when a BatchNorm is in the block.",
     "ReLU has zero parameters. Say so explicitly - it is often a scoring point.",
     "Sum, and state the total.",
     "If asked for output SIZE: floor((i + 2p - k)/s) + 1 per spatial dim, times C_out.",
   ],
   traps=[
     "CHANGING THE ANSWER WHEN THE IMAGE SIZE CHANGES - parameter count does not depend on H x W",
     "forgetting C_in: RGBD is 4 channels, not 3",
     "forgetting BatchNorm's 2*C_out",
     "counting ReLU as having parameters",
   ]),

 "receptive-field": dict(
   load="normal", figure=False, kind="compute", uses=["cnn-parameter-count"],
   trigger="'What is the receptive field of a pixel in the Nth layer?' or 'how do we improve the receptive field without more convolutions?'",
   why="Each 3x3 layer widens the receptive field by 2 because the kernel reaches one pixel either side, so depth grows it linearly while stride and dilation grow it multiplicatively - which is why architectures buy reach with pooling rather than depth.",
   answer_shape="one number, with the accumulation shown.",
   steps=[
     "Stride-1 stack: RF grows by (k - 1) per layer. n layers of 3x3 gives RF = 2n + 1.",
     "State the arithmetic, not just the number.",
     "To widen without more convolutions: pooling/downsampling, dilated (atrous) convolutions, larger stride.",
     "BatchNorm and ReLU do not change the receptive field - say so if they are in the block.",
   ],
   traps=[
     "counting the block itself as adding 2 twice because it contains Conv+ReLU+BN",
     "off-by-one: 4 layers of 3x3 gives 9, not 8",
   ]),

 "feature-vector-size-count": dict(
   load="normal", figure=False, kind="compute", uses=[],
   trigger="'What is the dimension/size of a <SIFT/HOG> descriptor?' or 'how many learnable parameters does the linear SVM have?' or 'how many feature vectors from N images?'",
   why="Every descriptor is a grid of cells times a histogram per cell, so its length is a product you can rebuild from the geometry rather than memorise.",
   answer_shape="the product written out, then the number. 'Explain how you get to this number in words' = the product IS the answer.",
   steps=[
     "SIFT: 4 x 4 spatial cells x 8 orientation bins = 128.",
     "HOG: (W/cell) x (H/cell) x bins. CURRENT SLIDES: 8x8 cells, 9 orientation bins. "
     "Worked example from the mockup paper (200x100, 10x10 cells, 8 bins): 20 x 10 x 8 = 1600 - "
     "but read the cell size and bin count off the question, never from memory.",
     "Linear SVM: one weight per feature dimension + 1 bias.",
     "Number of training vectors = number of images (one descriptor per window/image), so 1000 + 1000 = 2000.",
     "Always write the product before the total - the derivation is the marked part.",
   ],
   traps=[
     "giving 128 for SIFT with no breakdown when asked to 'explain how you get to this number'",
     "HOG: dividing image dims by bins instead of by cell size",
     "HOG bin count: the current slides use 9 orientation bins (the old mockup question used 8) - "
     "take both cell size and bin count from the question text",
     "forgetting the SVM bias term",
   ]),

 "invariance-properties-check": dict(
   load="recall", figure=False, kind="judge", uses=[],
   trigger="'To which transformations is X invariant? Justify' or a true/false property list (k-Means, Fourier, Hessian).",
   why="Invariance follows from what the operator actually measures: a detector built on image gradients is unchanged by rotation and translation but not by scaling, because scaling changes the gradient magnitudes it thresholds.",
   answer_shape="yes/no PER ITEM, each with a one-clause reason. Justification is always a separate mark.",
   steps=[
     "Answer each item separately; never give one verdict for a list.",
     "Give the reason in a clause - 'invariant because the response depends only on gradient ratios'.",
     "Harris: invariant to rotation and translation (Euclidean), NOT to scaling, NOT to general affine.",
     "Hessian: translation- and rotation-invariant, NOT scale-invariant.",
     "k-Means: always converges; does NOT always find the global optimum; the optimal problem is NP-hard.",
     "Fourier: FT of a Gaussian is a Gaussian; FT of a box is a sinc (NOT a box); Gaussian emphasises low frequencies; truncating the spectrum causes ringing, not aliasing.",
   ],
   traps=[
     "answering yes/no with no justification when the question says 'justify your answer'",
     "claiming Harris is affine-invariant because it is rotation-invariant",
     "FT of a box filter is a sinc - a very common false 'true'",
   ]),

 "derive-homography-A": dict(
   load="slow", figure=False, kind="derive", uses=["def-formula-gloss"],
   trigger="'To estimate a homography H we solve Ah = 0. Derive the entries of A given a correspondence pair' or 'how many correspondence pairs are needed?'",
   why="A homography has 8 degrees of freedom (9 entries up to scale), each point pair gives 2 independent equations, so 4 pairs is the minimum - the derivation is just the cross-product trick that removes the unknown scale factor.",
   answer_shape="the two rows of A written out in full, symbolically, + the DOF count. 6 marks = show every algebraic step.",
   steps=[
     "Write p_r = H p_l in homogeneous coordinates with an unknown scale: lambda * p_r = H p_l.",
     "Eliminate lambda by taking the cross product: p_r x (H p_l) = 0.",
     "Expand into three scalar equations; only two are linearly independent.",
     "Rearrange each into the form (row of A) . h = 0 where h is H flattened to 9x1.",
     "Write both rows explicitly with x_l, y_l, x_r, y_r.",
     "DOF: 9 entries - 1 for scale = 8; 2 equations per pair; so 4 pairs minimum.",
   ],
   traps=[
     "forgetting the unknown scale factor lambda and getting an inconsistent system",
     "claiming 3 independent equations from the cross product - only 2 are independent",
     "answering '4 pairs' without the 8-DOF / 2-equations justification when it says 'justify'",
   ]),

 "derive-epipolar-constraint": dict(
   load="slow", figure=False, kind="derive", uses=["epipolar-glossary"],
   trigger="'Derive the epipolar constraint given R and T. Explicitly give the equation for the essential matrix E.'",
   why="The constraint says the two camera centres and the 3D point are coplanar, and the triple product of three coplanar vectors is zero - E is just that coplanarity written as a matrix.",
   answer_shape="a chain of equations ending in x'^T E x = 0 with E named. 6 marks = every line shown.",
   steps=[
     "Relate the two camera frames: X' = R X + T.",
     "Write the coplanarity of X', T and RX as a scalar triple product: X' . (T x R X) = 0.",
     "Replace the cross product with the skew-symmetric matrix [T]_x, giving X'^T [T]_x R X = 0.",
     "Define E = [T]_x R. State this explicitly - it is its own mark.",
     "Conclude X'^T E X = 0 and say it holds for normalised/calibrated coordinates.",
     "If asked for F rather than E: F = K'^-T E K^-1 for pixel coordinates.",
   ],
   traps=[
     "getting E = R [T]_x instead of [T]_x R - the order matters",
     "not stating E explicitly when the question says 'explicitly give the equation for E'",
     "confusing E (calibrated) with F (pixel coordinates)",
   ]),

 "derive-eight-point": dict(
   load="slow", figure=False, kind="derive", uses=["derive-epipolar-constraint"],
   trigger="'Fill in the first row of the matrix to complete the Eight-point algorithm' + follow-ups on how it is solved.",
   why="Writing out x'^T F x = 0 for one correspondence gives one linear equation in the nine entries of F, so stacking eight of them determines F up to scale - the row is literally the expanded product.",
   answer_shape="the 9-entry row written out + the solution method named.",
   steps=[
     "Expand y^T F x = 0 with x = (x1, x2, 1), y = (y1, y2, 1).",
     "The row is [x1*y1, x2*y1, y1, x1*y2, x2*y2, y2, x1, x2, 1] against f = F flattened.",
     "Solve Af = 0 by SVD: the solution is the singular vector for the smallest singular value.",
     "The solution is defined only up to scale - say so.",
     "Enforce rank 2 afterwards by zeroing the smallest singular value of the recovered F.",
   ],
   traps=[
     "ordering the row entries wrong - derive it from the product, never recall it",
     "saying 'solve the linear system' without naming SVD / smallest singular vector",
     "forgetting that the raw solution violates the rank-2 constraint",
   ]),

 "derive-triangulation": dict(
   load="slow", figure=False, kind="derive", uses=["derive-epipolar-constraint"],
   trigger="'Given two projection matrices and a correspondence, triangulate the 3D point using the linear algebraic approach.'",
   why="Each image point says the 3D point lies on a ray, and the cross product x cross (PX) = 0 turns 'lies on that ray' into linear equations you can stack and solve.",
   answer_shape="the stacked matrix + the SVD solution + dehomogenisation.",
   steps=[
     "For each view write x_i x (P_i X) = 0 - the cross product removes the unknown depth.",
     "Each view contributes 2 independent rows built from rows of P_i.",
     "Stack into A X = 0 (4 rows for 2 views).",
     "Solve by SVD - smallest singular vector.",
     "Dehomogenise: divide by the 4th component to get (a, b, c).",
   ],
   traps=[
     "forgetting to dehomogenise and reporting a 4-vector",
     "using all 3 cross-product rows per view instead of 2 independent ones",
   ]),

 "derive-ransac-iterations": dict(
   load="normal", figure=False, kind="derive", uses=["algorithm-steps-recall"],
   trigger="'Given outlier proportion delta, derive the minimum number of iterations k so that P(all iterations fail) < epsilon.'",
   why="One iteration succeeds only if all s sampled points are inliers, so failure compounds geometrically and k comes straight out of taking a logarithm.",
   answer_shape="a short chain of 4 lines ending in an explicit k >= ... expression.",
   steps=[
     "P(one sample all inliers) = (1 - delta)^s, where s is the sample size (4 for a homography).",
     "P(one iteration fails) = 1 - (1 - delta)^s.",
     "P(all k fail) = (1 - (1 - delta)^s)^k < epsilon.",
     "k > log(epsilon) / log(1 - (1 - delta)^s).",
     "State s explicitly for the model being fitted.",
   ],
   traps=[
     "using delta as the inlier rate instead of the outlier rate",
     "forgetting the inequality flips when dividing by a negative logarithm",
     "not stating s for the specific model",
   ]),

 "derive-sfm-dof": dict(
   load="normal", figure=False, kind="derive", uses=[],
   trigger="'Projective SfM is solvable when 2mn >= 11m + 3n - 15. Explain the reasoning behind the terms.'",
   why="It is a counting argument: measurements on the left, unknowns on the right, minus the projective ambiguity you can never recover.",
   answer_shape="one sentence per term. 3 terms = the marks.",
   steps=[
     "2mn: each of n points in each of m images gives 2 image measurements.",
     "11m: each projective camera matrix has 12 entries, defined up to scale, so 11 unknowns per camera.",
     "3n: each 3D point has 3 unknown coordinates.",
     "-15: the whole reconstruction is only determined up to a projective transformation of space, a 4x4 homography with 16 entries up to scale = 15 DOF that can be fixed arbitrarily.",
   ],
   traps=[
     "explaining the inequality but not the -15, which is the term the mark is really for",
     "saying 12 per camera instead of 11 (forgetting the scale ambiguity)",
   ]),

 "concept-brief-explain": dict(
   load="recall", figure=False, kind="recall", uses=[],
   trigger="'Briefly describe/explain X', 'what is X, how does it work and why is it useful?' - kernel trick, linear SVM, Mean-Shift speedup, automatic scale selection.",
   why="Two marks means the examiner wants two things: what it is, and what it buys you - the second half is the one people drop.",
   answer_shape="one sentence WHAT + one sentence WHY/HOW. 2 marks = 2 sentences.",
   steps=[
     "Sentence 1: what the thing is, in the course's vocabulary.",
     "Sentence 2: what problem it solves or what it buys you.",
     "If the question has three clauses ('what, how, why'), write three sentences.",
     "Use the technical term at least once - markers scan for it.",
     "Do not derive. 'Briefly' is an instruction about marks, not politeness.",
   ],
   traps=[
     "writing what it is and never why it is useful",
     "kernel trick: must say inner products in a high-dimensional space are computed WITHOUT the explicit mapping",
     "linear SVM: 'maximise the margin between classes' - the word margin must appear",
     "answering at derivation length and losing the time elsewhere",
   ]),

 "why-method-unsuitable": dict(
   load="normal", figure=False, kind="judge", uses=[],
   trigger="'Explain why <k-Means / MaxFlow / Mixture of Gaussians> would be a poor choice given these constraints.'",
   why="Every algorithm encodes an assumption about the data, and these questions are testing whether you know which assumption breaks - not whether you dislike the method.",
   answer_shape="name the assumption + say how the given scenario violates it. 1 mark, 1 tight sentence, but BOTH halves.",
   steps=[
     "Identify the algorithm's built-in assumption (k-Means: isotropic compact clusters and a known k; MoG: a chosen number of Gaussian components; MaxFlow: a graph with meaningful pairwise terms and a labelling task).",
     "Point at the specific feature of the scenario that violates it.",
     "Say what goes wrong as a result.",
     "Never answer with a generic weakness that would apply to any dataset.",
   ],
   traps=[
     "listing a generic disadvantage instead of the one relevant to THIS scenario",
     "answering with only the assumption and never the consequence",
     "for the ground-plane case: the point is that a plane is not a compact blob, so distance-based clustering cannot represent it",
   ]),

 "why-design-choice": dict(
   load="normal", figure=False, kind="judge", uses=[],
   trigger="'Why is X better than Y?', 'why do we want to use X?', 'what would happen without this step?' - hysteresis, Gaussian in a pyramid, skip connections, HOG for pedestrians.",
   why="A design-choice question always has the same shape: name the failure of the naive alternative, then say how the choice removes it.",
   answer_shape="failure of the alternative + mechanism of the fix. 2 marks = 2 clauses.",
   steps=[
     "State what the simpler alternative does wrong.",
     "State the mechanism by which the chosen method avoids that.",
     "If the question asks 'what would happen without it', describe the concrete artefact by name (aliasing, broken edges, loss of spatial detail).",
     "Name the artefact - vague 'worse results' scores nothing.",
   ],
   traps=[
     "hysteresis: must mention TWO thresholds and that weak edges are kept only if connected to strong ones",
     "Gaussian before subsampling: without it you get ALIASING - name it",
     "skip connections: recover spatial detail lost to downsampling, not 'help gradients' alone",
     "asserting a method is better without saying what the alternative fails at",
   ]),

 "failure-mode-and-fix": dict(
   load="normal", figure=False, kind="judge", uses=[],
   trigger="'What problem(s) might we face when ...? What might be a possible approach to mitigate it?' - salt-and-pepper before Canny, noise in the eight-point algorithm.",
   why="These test whether you know an algorithm's sensitivity, and the fix is always a preprocessing or conditioning step rather than a change to the algorithm itself.",
   answer_shape="problem named + mechanism of the problem + the fix. Always answer BOTH halves.",
   steps=[
     "Name the problem in the course's vocabulary.",
     "Say why the algorithm is sensitive to it (the mechanism).",
     "Give the standard fix.",
     "Check the question for a second sub-question - these almost always have two halves and one is commonly skipped.",
   ],
   traps=[
     "answering the problem and never the mitigation - half the marks gone",
     "salt-and-pepper + Canny: Gaussian smoothing does NOT remove impulse noise; the fix is a MEDIAN filter",
     "eight-point noise: the fix is normalising/conditioning the coordinates (Hartley normalisation)",
   ]),

 "compare-two-methods": dict(
   load="recall", figure=False, kind="recall", uses=[],
   trigger="'What is the difference between X and Y?', 'main difference and advantage of X over Y' - CNN vs MLP, Hessian vs Harris, classifier vs detector.",
   why="A comparison question wants the axis of difference, not two separate descriptions.",
   answer_shape="state the axis, then both sides of it. 2 marks = difference + consequence.",
   steps=[
     "Name the single axis on which they differ.",
     "Say where each one sits on that axis.",
     "State the consequence - what the difference buys or costs.",
     "Do not describe both methods from scratch; the marks are for the contrast.",
   ],
   traps=[
     "describing X, then describing Y, and never stating the difference",
     "CNN vs MLP: weight sharing and local connectivity -> far fewer parameters and translation equivariance",
     "classifier vs detector: a detector also LOCALISES (and must handle many windows / no-object)",
     "Hessian vs Harris: second derivatives vs first-derivative second-moment matrix",
   ]),

 "apply-on-given-grid": dict(
   load="slow", figure=True, kind="compute", uses=["def-formula-gloss"],
   trigger="A small numeric image/matrix is given and you must produce the output of correlation, max-pooling, or unpooling.",
   why="These are the only questions where a careless arithmetic slip costs full marks, and they are graded on the output grid alone.",
   answer_shape="the output grid, written as a grid.",
   steps=[
     "Write the output grid dimensions first from the stride and padding.",
     "For correlation: slide WITHOUT flipping. For convolution: flip the kernel first.",
     "Same-padding with zeros means the output is the same size as the input.",
     "Max-pool 2x2 stride 2: take the max of each disjoint 2x2 block.",
     "Max-UNpool: put each value back at the ARGMAX position recorded during pooling, zeros elsewhere.",
     "Plain unpooling has no memory of positions - it fills a fixed position or replicates.",
   ],
   traps=[
     "flipping the kernel for a correlation question",
     "max-unpooling into the top-left of each block instead of the remembered argmax",
     "getting the output size wrong because padding was ignored",
   ]),

 "sketch-or-draw": dict(
   load="slow", figure=True, kind="judge", uses=[],
   trigger="'Sketch the cluster boundaries', 'draw the corresponding flow-graph'.",
   why="A drawing question is graded on labelled structure, not artistry - the marks are on the nodes, edges and weights you name.",
   answer_shape="a labelled diagram. Every node/edge/boundary that carries a mark must be annotated.",
   steps=[
     "Draw the structure, then LABEL every element - unlabelled diagrams score poorly.",
     "Graph cuts: source and sink terminals, one node per pixel, t-links weighted by unary potentials, n-links by pairwise potentials.",
     "To force a pixel to a label, set its t-link to that terminal to infinity.",
     "Mean-Shift with radius r: points within r of each other merge into one mode - larger r means fewer clusters.",
     "k-Means with given initial means: boundaries are perpendicular bisectors between final means.",
     "State any assumption you make about ties.",
   ],
   traps=[
     "drawing without labelling weights",
     "forgetting the source/sink terminals in a flow graph",
     "for constrained graph cuts: the answer is an INFINITE-weight edge, not a modified potential",
   ]),

 "read-figure-identify": dict(
   load="normal", figure=True, kind="recall", uses=[],
   trigger="Images of a convolution operation to name (with k, i, s, p), or a stereo diagram whose elements must be labelled.",
   why="These test vocabulary recognition against a picture, so the marks are entirely in using the exact course term.",
   answer_shape="one term per blank. No sentences.",
   steps=[
     "Read the output size relative to the input: larger output means transposed/fractionally-strided convolution; smaller means strided; equal means padded stride-1.",
     "Count grid cells to read off k, i, s, p rather than guessing.",
     "Standard stereo labels: image plane, optical centre, focal length, baseline, epipole, epipolar line, epipolar plane, projected point, disparity.",
     "Use the exact course term - synonyms often are not accepted.",
   ],
   traps=[
     "'deconvolution' instead of 'transposed convolution'",
     "confusing baseline (between optical centres) with disparity (between image points)",
     "writing an explanation where a single term was asked for",
   ]),

 "code-vision-function": dict(
   load="slow", figure=False, kind="compute", uses=["harris-hessian-mechanics"],
   trigger="'Write a function that computes X using numpy / fill in the Matlab fragment / what steps are missing?'",
   why="The code questions test the same pipeline knowledge as the prose ones, expressed as operations - the marks are on the sequence of operations, not on syntax.",
   answer_shape="short vectorised code, one operation per marked step. Comments count.",
   steps=[
     "Write the pipeline as comments first, then fill in - a correct commented skeleton scores most of the marks.",
     "Harris: gradients Ix, Iy -> products Ix2, Iy2, IxIy -> Gaussian-smooth each -> R = det(M) - k*trace(M)^2.",
     "Hessian: second derivatives Ixx, Iyy, Ixy -> score = Ixx*Iyy - Ixy^2.",
     "Camera centre: C is the null space of P, i.e. the right singular vector of P for the smallest singular value; dehomogenise.",
     "'Loops are not allowed' means vectorise - use array ops and SVD, never nested indexing.",
     "Commonly-missing steps: smoothing the derivative products, and non-maximum suppression / thresholding at the end.",
   ],
   traps=[
     "forgetting to smooth the gradient products before forming M - the single most common missing step",
     "forgetting non-maximum suppression / thresholding as the final step",
     "writing loops when the question forbids them",
   ]),

 "feasibility-judgement": dict(
   load="normal", figure=False, kind="judge", uses=[],
   trigger="'Is it possible to ...? Justify your answer.' / 'If yes, explain the approach. If not, provide a justification.'",
   why="The verdict is worth almost nothing; the justification is the mark, and the examiner wants the specific technical reason.",
   answer_shape="verdict + reason. NEVER a bare yes/no.",
   steps=[
     "Give the verdict in the first word.",
     "Give the technical reason immediately after.",
     "If yes, sketch the approach in one clause. If no, name what is missing.",
     "Watch for the hidden catch - these questions usually turn on one omitted requirement (e.g. a detector needs NEGATIVE training samples, not just 1000 positives).",
   ],
   traps=[
     "answering yes/no with no justification - scores zero even when correct",
     "SVM+HOG on 1000 pedestrian images: the catch is the absence of negative examples",
     "cross-entropy for segmentation: yes, applied PER PIXEL - the catch is per-pixel, not that it fails",
     "raw pixels as descriptors under pure translation: they do work, which is the surprise",
   ]),

 "epipolar-glossary": dict(
   load="recall", figure=False, kind="recall", uses=[],
   trigger="'Briefly explain the Essential Matrix / Fundamental Matrix / Epipolar line / Epipolar plane.' Typically four 1-mark parts in a row.",
   why="These four terms describe one geometric picture from four angles, so learning the picture once answers all of them.",
   answer_shape="ONE sentence each. 1 mark = 1 sentence. Do not over-write.",
   steps=[
     "Essential matrix E: relates corresponding points in two CALIBRATED views, x'^T E x = 0; E = [T]_x R; 5 DOF.",
     "Fundamental matrix F: the same for UNCALIBRATED (pixel) coordinates, x'^T F x = 0; F = K'^-T E K^-1; 7 DOF, rank 2.",
     "Epipolar line: the image in one view of the ray through a point in the other view - the search line for the match.",
     "Epipolar plane: the plane through the 3D point and both camera centres.",
     "Give the defining equation where there is one - it is usually half the mark.",
   ],
   traps=[
     "swapping E and F - E is calibrated, F is pixel coordinates",
     "writing a paragraph for a 1-mark part and losing time on the 6-mark derivation later",
   ]),

 "fundamental-matrix-rank": dict(
   load="normal", figure=False, kind="judge", uses=["epipolar-glossary"],
   trigger="'What is the rank of the Fundamental matrix? Why?' / 'What if F had full rank?' / 'How do we enforce the rank constraint?'",
   why="F maps every point to a line, and all those lines meet at the epipole - a matrix with a non-trivial null space cannot have full rank.",
   answer_shape="the number + the reason. Both halves always.",
   steps=[
     "Rank is 2.",
     "Reason: all epipolar lines pass through the epipole, so the epipole is a non-trivial null vector (F e = 0), forcing rank < 3.",
     "If F had full rank: no epipole would exist, epipolar lines would not intersect in a common point, and the geometry would be inconsistent.",
     "Enforce it by SVD: decompose F = U S V^T, set the smallest singular value to zero, recompose.",
   ],
   traps=[
     "saying 'rank 2' with no reason - the 'why' is the mark",
     "confusing the rank-2 constraint with the 8-point normalisation step",
   ]),

 "boosting-mechanics": dict(
   load="recall", figure=False, kind="recall", uses=["algorithm-steps-recall"],
   trigger="'What values do we adjust after training a weak classifier and in which direction?' / 'what property must weak classifiers have?' / 'how is a test point classified?' / 'input and output of Adaboost?'",
   why="Boosting works by making the next weak learner focus on what the previous ones got wrong, which is why misclassified samples gain weight and accurate classifiers gain influence.",
   answer_shape="named quantity + DIRECTION of change. The direction is the mark.",
   steps=[
     "Sample weights: INCREASE for misclassified samples, decrease for correctly classified.",
     "Classifier weight alpha_m: HIGHER for a weak classifier with lower error.",
     "Weak classifier requirement: better than chance (error < 0.5).",
     "Classification: H(x) = sign(sum_m alpha_m h_m(x)) - a weighted vote.",
     "Adaboost input: labelled training set + a weak learner. Output: the set of weak classifiers with their weights alpha_m.",
   ],
   traps=[
     "naming the quantity but not the direction",
     "saying weak classifiers must be 'weak' rather than 'better than chance'",
     "omitting alpha from the test-time equation and giving an unweighted vote",
   ]),

 "viola-jones-mechanics": dict(
   load="recall", figure=False, kind="recall", uses=["boosting-mechanics"],
   trigger="'What are the weak classifiers in Viola-Jones?' / 'what is an integral image?' / 'why and how are integral images used?' / 'explain cascading classifiers'.",
   why="Viola-Jones is fast because each feature is a difference of rectangle sums, and an integral image makes any rectangle sum cost four lookups regardless of its size.",
   answer_shape="mechanism + the speed consequence. 2 marks = both.",
   steps=[
     "Weak classifiers: Haar-like features - the difference between sums of pixels in adjacent rectangles, thresholded.",
     "Integral image: each entry holds the sum of all pixels above and to the left.",
     "Any rectangle sum = 4 array lookups, in constant time regardless of rectangle size.",
     "Cascade: a sequence of stages; each stage rejects clear negatives immediately and only survivors reach the next.",
     "Cascade payoff: most windows are background and are discarded after one or two cheap stages.",
   ],
   traps=[
     "describing the integral image but never saying '4 lookups / constant time', which is the point",
     "describing a cascade as just 'several classifiers in a row' without the early-rejection argument",
     "calling Haar features 'edges' instead of differences of rectangle sums",
   ]),

 "mrf-graphcut-mechanics": dict(
   load="normal", figure=False, kind="recall", uses=["def-formula-gloss"],
   trigger="'What is the optimisation objective?' / 'expand the posterior' / 'what parameters are updated each iteration and why?' / 'how do we adapt the flow-graph to constrain a label?'",
   why="An MRF splits segmentation into what a pixel looks like (unary) and what its neighbours say (pairwise), and graph cuts find the global minimum of that sum exactly for two labels.",
   answer_shape="objective as an argmin/argmax + one sentence of role per term.",
   steps=[
     "Objective: x_hat = argmin_x E(x, y) - the minimum-energy labelling, found by min-cut/max-flow.",
     "Unary term: cost of assigning a label given that pixel's own appearance (from the colour model).",
     "Pairwise term: smoothness - penalises neighbouring pixels taking different labels.",
     "Posterior: p(c | r,g,b) proportional to p(r,g,b | c) * p(c), from Bayes.",
     "Iterating: the colour/appearance models per class are re-estimated from the current mask, which sharpens the unary terms.",
     "Hard constraint: set the t-link to the desired terminal to infinity.",
     "s-t graph cuts are exact only for TWO labels. For more, use alpha-expansion: repeatedly "
     "solve a binary problem 'keep current label or switch to alpha' over each label alpha.",
     "Max-flow is computed by augmenting-path algorithms.",
   ],
   traps=[
     "writing argmax where the energy formulation needs argmin",
     "swapping which term is unary and which is pairwise",
     "saying 'everything is updated' rather than naming the appearance model",
   ]),

 "pyramid-mechanics": dict(
   load="recall", figure=False, kind="recall", uses=["def-formula-gloss"],
   trigger="'What is a Gaussian/Laplacian pyramid and how is it created?' / 'how are they connected?'",
   why="Smoothing before subsampling removes the high frequencies that would otherwise alias, and the Laplacian pyramid stores exactly what that smoothing threw away - which is why it reconstructs perfectly.",
   answer_shape="construction procedure + the relationship. 2 marks = both.",
   steps=[
     "Gaussian pyramid: repeatedly Gaussian-smooth, then subsample by 2. Each level is half the resolution.",
     "Laplacian level i = Gaussian level i minus the upsampled Gaussian level i+1.",
     "So the Laplacian pyramid stores the band-pass detail lost between levels.",
     "The original is reconstructed exactly by adding the Laplacian levels back to the smallest Gaussian level.",
     "The smoothing exists to prevent aliasing - name aliasing explicitly.",
   ],
   traps=[
     "subsample-then-smooth (wrong order - the aliasing has already happened)",
     "saying the Gaussian 'removes noise' rather than 'prevents aliasing' when asked why",
     "defining the Laplacian level without saying which Gaussian levels it differences",
   ]),

 "harris-hessian-mechanics": dict(
   load="normal", figure=False, kind="recall", uses=[],
   trigger="'Explain the influence of image content on the eigenvalues' / 'what is automatic scale selection and how does it work?' / 'how can Harris be extended to arbitrary scale?'",
   why="The second-moment matrix summarises how the image gradient varies in a window, so its two eigenvalues say how many independent directions of change exist - which is exactly what separates a corner from an edge from flat texture.",
   answer_shape="all three cases named for eigenvalue questions; mechanism + selection rule for scale questions.",
   steps=[
     "Both eigenvalues small -> flat, uniform region.",
     "One large, one small -> edge (variation in one direction only).",
     "Both large -> corner / interest point.",
     "R = det(M) - k * trace(M)^2 encodes this without computing eigenvalues explicitly.",
     "Automatic scale selection: evaluate a scale-normalised response (e.g. LoG) over a range of sigma and take the sigma at which it is a local MAXIMUM.",
     "Extending Harris to scale: run it over a scale-space and select the characteristic scale per keypoint by the LoG extremum.",
   ],
   traps=[
     "giving two eigenvalue cases and forgetting flat regions",
     "saying 'pick the best scale' without naming the local maximum of a scale-normalised response",
     "forgetting the scale normalisation, without which the response always decays with sigma",
   ]),

 "segmentation-via-clustering": dict(
   load="recall", figure=False, kind="recall", uses=["algorithm-steps-recall"],
   trigger="'Briefly describe how Mean-Shift / k-Means can be used for image segmentation.'",
   why="Segmentation by clustering works by treating each pixel as a point in a feature space and letting cluster membership become the segment label.",
   answer_shape="feature space + clustering + label mapping. 'In detail' means include the feature vector definition.",
   steps=[
     "Represent each pixel as a feature vector - colour, or colour plus (x, y) position.",
     "Run the clustering algorithm in that feature space.",
     "Assign each pixel the label of its cluster; the labels are the segments.",
     "Note the consequence of including position: it enforces spatial coherence.",
     "Mean-Shift finds the number of segments itself; k-Means needs k in advance.",
   ],
   traps=[
     "never saying what the feature vector is - that is the substance of the answer",
     "for 'describe in detail', giving the same short answer as for 'briefly describe'",
   ]),
}


# ---------------------------------------------------------------------------------------
# SYLLABUS-DERIVED ARCHETYPES (the blind spots)
# ---------------------------------------------------------------------------------------
# These cover material named in the CURRENT official slides that appears in NO past paper.
# They exist because the alternative is worse: the 2023 paper allots 15-19 marks per block,
# and a named sub-area of a block with zero drill coverage is unprotected marks.
#
# They break this mode's usual rule that archetypes must come from real papers. That rule
# guards against guessing the examiner where evidence exists. Here it does not: the content is
# named by the course itself, and the FORM is independently confirmed (90 min, closed book,
# explain_derive dominant, marks = distinct scorable statements). So the content comes from the
# slides and the shape from the measured form - neither half is invented.
#
# `est_marks` is an ESTIMATE and is flagged as such in the output so it can never be mistaken
# for a measured mark. Basis: the block's question total in the 2023 paper spread across the
# sub-areas the slides name. Block 4 (Q5) = 19 marks over ~6 areas; Block 3 (Q4) = 15 over ~5;
# Block 2 (Q3) = 15 over ~4.
SYLLABUS_ARCHETYPES = {

 "triplet-loss-and-metric-learning": dict(
   topic="Metric Learning and Triplet Embeddings", block=4, est_marks=4.0,
   load="normal", kind="derive", uses=["def-formula-gloss"],
   trigger="Siamese networks, triplet loss, anchor/positive/negative, embedding distance, or hard mining.",
   why="Classification needs a fixed label set but matching and retrieval do not, so instead of predicting a class you learn an embedding where distance itself means similarity - and the triplet loss is the cheapest way to say 'closer to the positive than to the negative'.",
   answer_shape="formula + gloss of every symbol, or WHAT/WHY sentences. 2 marks = 2 statements.",
   steps=[
     "Triplet loss: L = max(0, d(a,p) - d(a,n) + margin), over anchor a, positive p, negative n.",
     "Gloss it: d is a distance in embedding space (usually Euclidean on L2-normalised vectors); the margin forces a gap rather than a mere ordering.",
     "The max(0, .) means a triplet already satisfying the margin contributes zero gradient - which is exactly why mining is needed.",
     "Siamese network: two (or three) branches with SHARED weights producing the embeddings.",
     "Batch hard: per anchor, take the hardest positive (farthest) and hardest negative (closest) in the batch.",
     "Batch all: average the loss over every valid triplet in the batch.",
     "Why mine at all: random triplets are mostly already easy, contribute no gradient, and training stalls.",
   ],
   traps=[
     "omitting the margin - without it the trivial all-zero embedding is a perfect solution",
     "omitting max(0, .) and presenting the loss as a plain difference",
     "sign flip: anchor-positive distance is MINIMISED, anchor-negative MAXIMISED",
     "describing Siamese branches without saying the weights are SHARED - that is the defining property",
     "confusing batch hard (hardest per anchor) with batch all (average over all triplets)",
   ]),

 "em-for-mixture-models": dict(
   topic="Expectation-Maximization for Mixture Models", block=2, est_marks=4.0,
   load="recall", kind="recall", uses=["algorithm-steps-recall"],
   trigger="'List the steps of EM', 'how is a Mixture of Gaussians fitted?', or EM compared with k-Means.",
   why="You cannot fit a mixture directly because you do not know which component generated each point, so EM alternates between softly guessing that assignment and re-fitting the components to it, each pass raising the likelihood.",
   answer_shape="numbered steps. MARKS = NUMBER OF STEPS - a 4-mark question wants 4.",
   steps=[
     "Initialise the component means, covariances and mixing weights.",
     "E-step: compute the RESPONSIBILITY of each component for each point - the posterior probability that component k generated point n.",
     "M-step: re-estimate each component's mean, covariance and mixing weight as responsibility-weighted averages over all points.",
     "Repeat until the log-likelihood converges.",
     "Contrast with k-Means: EM assigns SOFTLY (a probability per component), k-Means hard; k-Means is the limiting case with spherical equal-variance components.",
   ],
   traps=[
     "swapping the E and M steps",
     "saying EM 'assigns points to clusters' - the E-step assigns PROBABILITIES, not clusters",
     "omitting the mixing weights from the M-step (means and covariances alone is incomplete)",
     "omitting the convergence criterion, as with every 'list the steps' question",
     "claiming EM finds the global optimum - it converges to a local one, like k-Means",
   ]),

 "deformable-part-models": dict(
   topic="Deformable Part-based Models", block=3, est_marks=3.0,
   load="normal", kind="recall", uses=["concept-brief-explain"],
   trigger="DPM, root filter, part filters, deformation cost, or 'how are intra-class shape variations handled?'",
   why="A single rigid HOG template cannot match an object whose parts move relative to each other, so DPM scores a coarse whole-object filter plus movable higher-resolution part filters and charges a penalty for how far each part has shifted.",
   answer_shape="component + component + how they combine. 2-3 marks = 2-3 statements.",
   steps=[
     "Root filter: a coarse HOG template over the whole object.",
     "Part filters: several HOG templates, one per part, at TWICE the root's resolution.",
     "Deformation cost: a penalty on each part's displacement from its anchor position relative to the root.",
     "Score = root response + sum of part responses - sum of deformation costs, MAXIMISED over part placements.",
     "The maximisation over placements is made tractable by the GENERALIZED DISTANCE TRANSFORM.",
     "The payoff: tolerance to intra-category shape variation that one rigid template cannot express.",
   ],
   traps=[
     "describing root and parts but omitting the deformation cost - it is the 'deformable' in the name",
     "putting parts at the same resolution as the root; they are higher",
     "forgetting the score maximises over part placements rather than using fixed positions",
   ]),

 "multiscale-dense-prediction": dict(
   topic="Multi-scale Dense Prediction (FPN, ASPP)", block=4, est_marks=3.0,
   load="normal", kind="recall", uses=["why-design-choice"],
   trigger="FPN, Feature Pyramid Network, ASPP, Atrous Spatial Pyramid Pooling, dilated/atrous convolution, multi-scale dense prediction.",
   why="Objects appear at many sizes but one feature map has one effective receptive field, so both designs give the network several receptive fields at once - FPN by combining depths, ASPP by varying dilation at a single depth.",
   answer_shape="mechanism + what it buys. 2 marks = 2 statements.",
   steps=[
     "FPN: a top-down pathway upsampling deep, semantically strong, low-resolution features and merging them by LATERAL connections with shallow high-resolution ones - strong features at every scale.",
     "ASPP: several PARALLEL atrous convolutions with different dilation rates on the same feature map, concatenated - several receptive-field sizes at one depth.",
     "Atrous/dilated convolution: gaps between kernel taps enlarge the receptive field WITHOUT extra parameters and WITHOUT losing resolution.",
     "Both exist because dense prediction needs high output resolution AND large context, which plain downsampling trades against each other.",
     "Same problem as encoder-decoder skip connections (detail lost to downsampling), different remedy.",
   ],
   traps=[
     "saying dilated convolutions add parameters - they do not, which is the whole point",
     "describing FPN as only upsampling and omitting the lateral connections",
     "confusing ASPP's parallel branches with a sequential stack",
   ]),
}

# ---- Added 2026-08-21 from the EXERCISE NOTEBOOKS (exercises/*.ipynb) ------------------
# The exercises are programming tasks, but their markdown cells carry conceptual questions in
# exactly the exam's voice - "Which network has more parameters?", "What is the size of the
# receptive field?", "Why do we use addition instead of concatenation?", "provide formulas to
# compute T and D". Those are the exam-shaped part and the source for these playbooks.
#
# Exercise 4 covers Vision Transformers in real depth. That area appears in NO past paper and
# was absent from the slide block summaries too - it surfaced only from the exercises, which is
# precisely why staff named slides AND exercises as the study basis.

SYLLABUS_ARCHETYPES.update({

 "vit-and-self-attention": dict(
   topic="Vision Transformers and Self-Attention", block=4, est_marks=5.0,
   load="normal", kind="derive", uses=["def-formula-gloss", "cnn-parameter-count"],
   trigger="Self-attention, Q/K/V, positional encoding, patchify, tokens, transformer block, ViT, class token.",
   why="A CNN has spatial structure built into its kernels, but a transformer sees an unordered set of tokens - so a ViT has to cut the image into patches, ADD a positional encoding to say where each came from, and let attention learn which patches should influence which.",
   answer_shape="formula + gloss, or mechanism + reason. 2 marks = 2 statements.",
   steps=[
     "Self-attention: softmax(Q K^T / sqrt(d)) V, where Q, K, V come from dense layers on the input and d is the feature dimension.",
     "The sqrt(d) scaling keeps the dot products from growing with dimension and saturating the softmax.",
     "Patchify: images (N x C x H x W) -> tokens (N x T x D), with T = H_n x W_n (number of patches) and D = C x H_p x W_p (pixels per patch x channels).",
     "Positional encoding: p[i,j] = sin(i / 10000^(j/d)) for even j, cos(i / 10000^((j-1)/d)) for odd j.",
     "It is ADDED to the tokens, not concatenated - addition lets the model choose how much positional signal to keep, by scaling image features up or down against it.",
     "Transformer block: z' = MSA(LN(z)) + z, then z_out = MLP(LN(z')) + z'. Note LayerNorm BEFORE each sub-layer and a residual connection around each.",
     "ViT end to end: patchify -> add positional encoding -> transformer blocks -> take the CLASS token -> classification MLP -> logits.",
     "Multi-head: attention is computed in head_dim dimensions per head, and the heads are combined.",
   ],
   traps=[
     "omitting the 1/sqrt(d) scaling from the attention formula",
     "saying positional encoding is CONCATENATED - it is added, and the reason is examinable",
     "getting T and D backwards: T counts patches, D is the size of one patch (C x H_p x W_p)",
     "putting LayerNorm after the sub-layer instead of before it",
     "forgetting the residual connections in the transformer block",
     "forgetting that classification reads the CLASS token, not a pooled average",
   ]),

 "resnet-and-training-practices": dict(
   topic="Residual Networks and Training Practices", block=4, est_marks=3.0,
   load="normal", kind="recall", uses=["cnn-parameter-count", "why-design-choice"],
   trigger="Residual block, ResNet, identity shortcut, global average pooling, learning-rate decay, weight decay / L2, Adam, data augmentation.",
   why="Deep plain networks get harder to optimise as they grow, so a residual block learns only the CHANGE to its input and passes the input through untouched - which means adding layers can never make the function harder to represent.",
   answer_shape="mechanism + what it buys. 2 marks = 2 statements.",
   steps=[
     "Residual block: output = F(x) + x. The block predicts only the residual - the leftover correction to its input.",
     "Why it helps: the identity path lets gradients and signal skip layers, so depth stops degrading optimisation.",
     "Global average pooling: average over the spatial dimensions, giving [batch, channels] from [batch, channels, H, W].",
     "Its payoff: a fixed-size output regardless of input image size, and far fewer parameters than flatten + dense.",
     "Its cost: units before it need a large enough receptive field, or the model underperforms.",
     "L2 regularisation / weight decay: add (lambda/2) * sum(w^2) to the loss to penalise large weights and combat overfitting.",
     "Learning-rate decay: reduce the learning rate as training progresses, e.g. by a factor of 10 at set milestones.",
     "Receptive field with stride: stride multiplies the growth. 3x3 convs at stride 2 give 3, then 7, then 15 - not 3, 5, 7.",
   ],
   traps=[
     "describing a residual block as 'a skip connection' without saying the block learns the RESIDUAL",
     "computing receptive field as if stride were 1 when the convolutions are strided - the exercise's own worked answer is 3 -> 7 -> 15",
     "confusing global average pooling with max pooling",
     "claiming global average pooling adds parameters - it has none",
   ]),
})

# ---- Added 2026-08-21 from the LECTURE SUMMARIES (lectures/_summaries/*.txt) -----------
# Slide-level summaries of the actual deck. They show the course has shifted decisively toward
# transformers: 7_reconstruction.txt (24KB, the largest summary, and misleadingly named) runs
# attention -> ViT -> DETR/Mask2Former/EoMT -> CLIP/self-supervised learning. None of that
# appears in any past paper, and only part of it appeared in the block summaries.
#
# `vit-and-self-attention` is superseded here: one archetype could not hold this much, and the
# slides examine the mechanics and the architecture-level trade-offs as different question types.

del SYLLABUS_ARCHETYPES["vit-and-self-attention"]

SYLLABUS_ARCHETYPES.update({

 "attention-mechanics": dict(
   topic="Attention Mechanisms", block=4, est_marks=5.0,
   load="normal", kind="derive", uses=["def-formula-gloss"],
   trigger="Scaled dot-product attention, Q/K/V, alignment matrix, masked attention, multi-head, self- vs cross-attention.",
   why="Attention is a differentiable key-value lookup: a query is compared against every key to produce weights, and the output is the weighted average of the values - which is why it aggregates globally where a convolution only reaches its kernel.",
   answer_shape="formula + gloss of every symbol, or mechanism + reason. 2 marks = 2 statements.",
   steps=[
     "Scaled dot-product attention: softmax(Q K^T / sqrt(d)) V.",
     "Alignment: E = Q K^T, giving an N x N matrix of query-key similarities.",
     "The sqrt(d) scaling exists to stabilise training - unscaled dot products grow with dimension and saturate the softmax.",
     "Self-attention: Q, K and V all come from the SAME input by linear projection - Q = X W_q, K = X W_k, V = X W_v.",
     "Cross-attention: queries from one input, keys and values from ANOTHER (Q = X W_q, K = Y W_k, V = Y W_v). The two inputs may have different token counts; output length follows the QUERY.",
     "Masked attention: a lower-triangular mask before the softmax restricts each token to current and past positions. Used for language modelling and time series.",
     "Multi-head: split tokens along the feature dimension, run heads in parallel, concatenate. Head dims sum to d, so it costs no extra computation and learns diverse representations.",
     "Why an MLP between attention layers: stacked self-attention has NO nonlinearity - it just re-averages value vectors. The MLP supplies it.",
   ],
   traps=[
     "omitting the 1/sqrt(d) scaling, or not knowing WHY it is there (softmax saturation)",
     "confusing self- and cross-attention: the difference is where K and V come from",
     "saying multi-head attention increases computation - it does not, the dimension is split",
     "forgetting that output token count follows the QUERY in cross-attention",
     "not knowing why an MLP is needed between attention layers - a favourite 'why' question",
   ]),

 "vit-architecture-and-tradeoffs": dict(
   topic="Vision Transformers and Self-Attention", block=4, est_marks=5.0,
   load="normal", kind="recall", uses=["attention-mechanics", "cnn-parameter-count"],
   trigger="ViT, patchify, CLS token, positional embedding, 'ViT vs CNN', inductive bias.",
   why="A transformer sees an unordered set of tokens, so a ViT must cut the image into patches and add positional information - and because it lacks the CNN's built-in locality assumptions it must learn them from far more data.",
   answer_shape="pipeline steps, or an advantage/limitation list. Match the count to the marks.",
   steps=[
     "ViT pipeline: split image into patches -> flatten -> linear embedding -> add learnable positional embedding -> prepend CLS token -> transformer encoder (self-attention only) -> MLP head reads the CLS token -> logits.",
     "Patchify sizes: tokens T = H_n x W_n; feature dim D = C x H_p x W_p.",
     "The CLS token is a LEARNED parameter that aggregates global information for classification.",
     "Positional encoding is ADDED not concatenated - addition lets the model scale image features against positional ones and decide the proportion itself.",
     "Sinusoidal encoding: p[i,j] = sin(i / 10000^(j/d)) for even j, cos(...) for odd j. RoPE is the rotary alternative.",
     "CNN advantages: efficient on small datasets and low resolution; strong on traditional CV tasks.",
     "CNN limitation: the receptive field caps long-range dependencies.",
     "ViT advantages: global context and long-range dependencies; scales to large datasets and high resolution.",
     "ViT limitation: needs large datasets and heavy compute.",
     "CNN inductive biases - name all three: LOCALITY (small kernels), EQUIVARIANCE (weight tying), INVARIANCE (pooling). ViTs lack these and must learn them.",
   ],
   traps=[
     "saying ViT uses convolutions - it does not; it is encoder-only self-attention",
     "forgetting the CLS token, or saying classification uses average pooling instead",
     "listing only one CNN inductive bias when the question asks for the built-in biases - there are three",
     "T and D backwards: T counts patches, D is one patch's size (C x H_p x W_p)",
   ]),

 "transformers-for-dense-tasks": dict(
   topic="Transformers for Detection and Segmentation", block=4, est_marks=4.0,
   load="normal", kind="recall", uses=["vit-architecture-and-tradeoffs"],
   trigger="DETR, Mask2Former, EoMT, DynaMITe, mask transformers, query-based detection or segmentation.",
   why="Detection and segmentation used to need hand-built stages like anchor boxes and non-maximum suppression; casting the output as a fixed set of learned QUERIES lets a transformer predict objects or masks directly and removes those stages.",
   answer_shape="mechanism + what it replaces. 2 marks = 2 statements.",
   steps=[
     "DETR: object detection as direct SET prediction. A fixed number of learned object queries cross-attend to image features; each emits one box and class.",
     "Its payoff: no anchor boxes and no non-maximum suppression, because set prediction with bipartite matching already forbids duplicates.",
     "Mask2Former: unifies semantic, instance and panoptic segmentation with mask queries attending to image features - one architecture for all three.",
     "EoMT (encoder-only mask transformer): drops the separate decoder, showing a plain ViT encoder suffices; mask annealing phases the mask supervision in during training.",
     "DynaMITe: interactive segmentation, where user clicks become queries.",
     "The common thread: QUERIES replace hand-designed output structure (anchors, NMS, per-task heads).",
   ],
   traps=[
     "describing DETR as a CNN detector with attention bolted on - it is set prediction, and removing NMS is the headline",
     "not naming what each method REPLACES; these questions are about what the transformer makes unnecessary",
     "confusing Mask2Former (unified segmentation) with DETR (detection)",
   ]),

 "self-supervised-and-multimodal": dict(
   topic="Self-Supervised and Multimodal Learning", block=4, est_marks=3.0,
   load="recall", kind="recall", uses=["attention-mechanics"],
   trigger="Pretext tasks, self-supervised learning, contrastive learning, CLIP, shared embedding space, multimodal tokens.",
   why="Labels are expensive but raw images and their captions are abundant, so these methods invent a supervision signal from the data itself - and once text and images land in one embedding space, similarity across modalities becomes a dot product.",
   answer_shape="mechanism + what it buys. 2 marks = 2 statements.",
   steps=[
     "Pretext task: a task whose labels come free from the data (predicting rotation, inpainting, patch order), used to learn representations without annotation.",
     "Contrastive learning: pull representations of matching pairs together and push non-matching ones apart - the same principle as triplet loss, applied at batch scale.",
     "CLIP: trains an image encoder and a text encoder jointly so matching image-caption pairs land close in a SHARED embedding space.",
     "Its payoff: zero-shot classification - compare an image embedding against embeddings of candidate class names, no task-specific training.",
     "Multimodal token streams: once every modality is a set of tokens, one transformer can consume them together.",
   ],
   traps=[
     "confusing self-supervised with unsupervised - self-supervised INVENTS labels from the data, it does not do without the notion",
     "describing CLIP without the shared embedding space, which is the whole mechanism",
     "not naming zero-shot transfer as the payoff",
   ]),
})

# --- corrections to existing syllabus archetypes, forced by the slide summaries -----------
# ASPP and atrous/dilated convolution appear in NO lecture summary, while FPN does. The block
# summary named both; the slides support only FPN. Narrowed rather than deleted.
SYLLABUS_ARCHETYPES["multiscale-dense-prediction"]["est_marks"] = 2.0
SYLLABUS_ARCHETYPES["multiscale-dense-prediction"]["trigger"] = (
    "FPN, Feature Pyramid Network, multi-scale dense prediction, combining features across depths.")
SYLLABUS_ARCHETYPES["multiscale-dense-prediction"]["traps"].append(
    "ASPP/atrous convolution appears in the block summary but in NO lecture summary - do not "
    "spend drill time on it unless the slide deck proves otherwise")

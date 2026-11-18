# Pilot validity by condition (C1; A1.10 primary rule, top-up applied)

Cells (model x paradigm x format): 84. Cells whose Newcombe 95% interval for the difference in valid share (x = 1 minus x = 0) excludes zero: 16. Cells with an absolute difference of at least 2 points: 19. Largest absolute difference: 0.3094.

| model | paradigm | format | valid x0 | valid x1 | difference (95% Newcombe) |
|---|---|---|---|---|---|
| granite-3.3-2b-instruct | P2d | F0 | 275/404 | 400/404 | +0.309 (+0.263 to +0.357) |
| olmo2-1b-instruct | P2b | F0 | 327/404 | 253/404 | -0.183 (-0.243 to -0.122) |
| olmo2-1b-instruct | P2c | F0 | 296/404 | 369/404 | +0.181 (+0.129 to +0.232) |
| granite-3.3-8b-instruct | P4 | F1 | 339/404 | 285/404 | -0.134 (-0.190 to -0.076) |
| olmo2-1b-instruct | P2d | F0 | 388/404 | 341/404 | -0.116 (-0.158 to -0.076) |
| granite-3.3-2b-instruct | P2d | F1 | 365/404 | 394/404 | +0.072 (+0.040 to +0.106) |
| qwen2.5-1.5b-instruct | P4 | F0 | 286/404 | 258/404 | -0.069 (-0.133 to -0.005) |
| qwen2.5-1.5b-instruct | P2a | F1 | 210/404 | 228/404 | +0.045 (-0.024 to +0.113) |
| qwen2.5-1.5b-instruct | P2d | F0 | 402/404 | 387/404 | -0.037 (-0.062 to -0.017) |
| granite-3.3-2b-instruct | P2a | F0 | 400/404 | 386/404 | -0.035 (-0.060 to -0.012) |
| olmo2-1b-instruct | P2d | F1 | 386/404 | 372/404 | -0.035 (-0.069 to -0.001) |
| olmo2-1b-instruct | P2c | F1 | 399/404 | 387/404 | -0.030 (-0.055 to -0.007) |
| qwen2.5-1.5b-instruct | P2d | F1 | 205/404 | 217/404 | +0.030 (-0.039 to +0.098) |
| granite-3.3-2b-instruct | P4 | F1 | 263/404 | 274/404 | +0.027 (-0.038 to +0.092) |
| olmo2-7b-instruct | P2d | F0 | 386/404 | 397/404 | +0.027 (+0.003 to +0.053) |
| olmo2-7b-instruct | P4 | F0 | 393/404 | 382/404 | -0.027 (-0.056 to +0.001) |
| olmo2-7b-instruct | P2a | F1 | 402/404 | 392/404 | -0.025 (-0.046 to -0.007) |
| olmo2-1b-instruct | P1 | F0 | 777/808 | 796/808 | +0.024 (+0.008 to +0.040) |
| qwen2.5-1.5b-instruct | P2a | F0 | 380/404 | 389/404 | +0.022 (-0.008 to +0.053) |
| olmo2-1b-instruct | P2a | F0 | 303/404 | 295/404 | -0.020 (-0.080 to +0.041) |

(20 cells with the largest absolute difference; all cells in validity_by_condition.csv.)

Parsed-but-unfinished F0 responses (primary-invalid; valid under sensitivity a): 592. Blind sample: 121 (proportional by model, seed 20261016): granite-3.3-2b-instruct 33, granite-3.3-8b-instruct 72, olmo2-1b-instruct 11, olmo2-7b-instruct 3, qwen2.5-1.5b-instruct 1, qwen2.5-7b-instruct 1.


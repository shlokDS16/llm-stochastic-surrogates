# Pilot results, primary metric (analysis tag 'primary'; A1 + A1.10 rules)

| model | paradigm | metric | validity | cells | dbar [95% CI] | S [95% TI] | S2 lower > 0 | sign stability |
|---|---|---|---|---|---|---|---|---|
| granite-3.3-2b-instruct | P1 | log OR (sure option), gain vs loss | 0.999 | 32/32 | 0.649 [0.330, 0.969] | 1.137 [0.640, 1.500] | True | 0.25 |
| granite-3.3-2b-instruct | P2a | Hedges g on log (A1.2) | 0.953 | 16/16 | 1.033 [0.926, 1.141] | 0.727 [0.615, 0.829] | True | 0.75 |
| granite-3.3-2b-instruct | P2b | Hedges g on log (A1.2) | 0.931 | 16/16 | 0.555 [0.345, 0.766] | 0.359 [0.000, 0.727] | False | 0.50 |
| granite-3.3-2b-instruct | P2c | Hedges g on log (A1.2) | 0.984 | 16/16 | 1.113 [0.956, 1.271] | 0.803 [0.426, 1.002] | True | 0.69 |
| granite-3.3-2b-instruct | P2d | Hedges g on log (A1.2) | 0.883 | 16/16 | 7.938 [7.317, 8.559] | 8.955 [8.428, 9.274] | True | 1.00 |
| granite-3.3-2b-instruct | P3 | Hedges g | 1.000 | 16/16 | 0.132 [0.044, 0.221] | 0.123 [0.000, 0.236] | False | 0.19 |
| granite-3.3-2b-instruct | P4 | Hedges g on log(1+x) | 0.826 | 16/16 | -0.325 [-0.430, -0.220] | 0.521 [0.412, 0.631] | True | 0.12 |
| granite-3.3-8b-instruct | P1 | log OR (sure option), gain vs loss | 0.989 | 32/32 | 0.857 [0.433, 1.280] | 4.975 [4.490, 5.455] | True | 0.44 |
| granite-3.3-8b-instruct | P2a | Hedges g on log (A1.2) | 0.959 | 16/16 | -0.030 [-0.085, 0.025] | 0.121 [0.036, 0.185] | True | 0.12 |
| granite-3.3-8b-instruct | P2b | Hedges g on log (A1.2) | 0.912 | 16/16 | 0.320 [0.236, 0.404] | 1.041 [0.887, 1.159] | True | 0.75 |
| granite-3.3-8b-instruct | P2c | Hedges g on log (A1.2) | 0.949 | 16/16 | -0.073 [-0.263, 0.118] | 1.446 [1.032, 1.817] | True | 0.31 |
| granite-3.3-8b-instruct | P2d | Hedges g on log (A1.2) | 0.901 | 16/16 | 0.371 [0.228, 0.515] | 0.489 [0.000, 0.679] | False | 0.38 |
| granite-3.3-8b-instruct | P3 | Hedges g | 0.996 | 16/16 | -0.037 [-0.150, 0.075] | 1.122 [0.961, 1.256] | True | 0.25 |
| granite-3.3-8b-instruct | P4 | Hedges g on log(1+x) | 0.840 | 16/16 | -0.046 [-0.176, 0.085] | 0.718 [0.530, 0.878] | True | 0.31 |
| olmo2-1b-instruct | P1 | log OR (sure option), gain vs loss | 0.975 | 32/32 | 0.229 [-0.024, 0.482] | 1.548 [1.231, 1.871] | True | 0.34 |
| olmo2-1b-instruct | P2a | Hedges g on log (A1.2) | 0.848 | 16/16 | -0.992 [-1.327, -0.657] | 1.735 [0.808, 2.624] | True | 0.00 |
| olmo2-1b-instruct | P2b | Hedges g on log (A1.2) | 0.797 | 16/16 | 0.152 [-0.049, 0.354] | 0.311 [0.000, 0.604] | False | 0.19 |
| olmo2-1b-instruct | P2c | Hedges g on log (A1.2) | 0.887 | 16/16 | 0.055 [-0.070, 0.180] | 0.308 [0.081, 0.468] | True | 0.12 |
| olmo2-1b-instruct | P2d | Hedges g on log (A1.2) | 0.913 | 16/16 | 0.738 [0.605, 0.872] | 0.806 [0.623, 0.958] | True | 0.75 |
| olmo2-1b-instruct | P3 | Hedges g | 0.981 | 16/16 | 0.028 [-0.071, 0.126] | 0.000 [0.000, 0.104] | False | 0.00 |
| olmo2-1b-instruct | P4 | Hedges g on log(1+x) | 0.917 | 16/16 | 0.029 [-0.085, 0.143] | 0.087 [0.000, 0.247] | False | 0.06 |
| olmo2-7b-instruct | P1 | log OR (sure option), gain vs loss | 0.998 | 32/32 | 2.505 [2.163, 2.846] | 2.102 [1.669, 2.520] | True | 0.69 |
| olmo2-7b-instruct | P2a | Hedges g on log (A1.2) | 0.981 | 16/16 | 0.259 [0.161, 0.357] | 0.690 [0.595, 0.779] | True | 0.50 |
| olmo2-7b-instruct | P2b | Hedges g on log (A1.2) | 0.988 | 16/16 | 0.232 [0.110, 0.354] | 0.831 [0.664, 0.960] | True | 0.44 |
| olmo2-7b-instruct | P2c | Hedges g on log (A1.2) | 0.994 | 16/16 | 0.286 [0.193, 0.379] | 0.352 [0.238, 0.463] | True | 0.31 |
| olmo2-7b-instruct | P2d | Hedges g on log (A1.2) | 0.976 | 16/16 | 2.109 [1.769, 2.450] | 2.207 [1.507, 2.687] | True | 0.75 |
| olmo2-7b-instruct | P3 | Hedges g | 0.988 | 16/16 | 0.147 [0.048, 0.245] | 0.096 [0.000, 0.229] | False | 0.12 |
| olmo2-7b-instruct | P4 | Hedges g on log(1+x) | 0.852 | 16/16 | -0.211 [-0.354, -0.068] | 1.363 [1.180, 1.548] | True | 0.50 |
| qwen2.5-1.5b-instruct | P1 | log OR (sure option), gain vs loss | 0.984 | 32/32 | 1.486 [1.181, 1.792] | 0.852 [0.000, 1.247] | False | 0.50 |
| qwen2.5-1.5b-instruct | P2a | Hedges g on log (A1.2) | 0.747 | 16/16 | 1.061 [0.841, 1.281] | 1.410 [1.242, 1.595] | True | 0.44 |
| qwen2.5-1.5b-instruct | P2b | Hedges g on log (A1.2) | 0.751 | 16/16 | 1.075 [0.248, 1.903] | 2.397 [0.690, 4.583] | True | 0.06 |
| qwen2.5-1.5b-instruct | P2c | Hedges g on log (A1.2) | 0.822 | 16/16 | 0.706 [0.027, 1.385] | 0.000 [0.000, 1.565] | False | 0.50 |
| qwen2.5-1.5b-instruct | P2d | Hedges g on log (A1.2) | 0.750 | 16/16 | 2.273 [1.789, 2.757] | 1.260 [0.000, 1.874] | False | 0.88 |
| qwen2.5-1.5b-instruct | P3 | Hedges g | 0.981 | 16/16 | -0.135 [-0.235, -0.035] | 0.179 [0.000, 0.296] | False | 0.00 |
| qwen2.5-1.5b-instruct | P4 | Hedges g on log(1+x) | 0.594 | 16/16 | 0.162 [0.022, 0.302] | 0.242 [0.000, 0.430] | False | 0.19 |
| qwen2.5-7b-instruct | P1 | log OR (sure option), gain vs loss | 1.000 | 32/32 | 6.769 [6.206, 7.332] | 2.123 [1.471, 2.701] | True | 0.94 |
| qwen2.5-7b-instruct | P2a | Hedges g on log (A1.2) | 1.000 | 16/16 | 1.161 [1.093, 1.229] | 0.773 [0.671, 0.861] | True | 1.00 |
| qwen2.5-7b-instruct | P2b | Hedges g on log (A1.2) | 0.998 | 16/16 | 0.020 [-0.074, 0.113] | 0.541 [0.422, 0.651] | True | 0.31 |
| qwen2.5-7b-instruct | P2c | Hedges g on log (A1.2) | 1.000 | 16/16 | 0.048 [0.010, 0.085] | 0.057 [0.000, 0.140] | False | 0.12 |
| qwen2.5-7b-instruct | P2d | Hedges g on log (A1.2) | 0.987 | 16/16 | 3.586 [3.151, 4.021] | 1.843 [0.858, 2.328] | True | 0.94 |
| qwen2.5-7b-instruct | P3 | Hedges g | 1.000 | 16/16 | 0.451 [0.337, 0.565] | 0.454 [0.275, 0.610] | True | 0.56 |
| qwen2.5-7b-instruct | P4 | Hedges g on log(1+x) | 0.994 | 16/16 | -0.587 [-0.685, -0.489] | 0.979 [0.892, 1.077] | True | 0.06 |

| model | system role | system text kept | BOS in render | double BOS if add_special | A-D,Yes/No,1-9 single (no space) | same with space | digits split | prompt tokens |
|---|---|---|---|---|---|---|---|---|
| qwen2.5-0.5b-instruct | ok | True | False | False | 15/15 | 6/15 | True | 41 |
| qwen2.5-1.5b-instruct | ok | True | False | False | 15/15 | 6/15 | True | 41 |
| qwen2.5-7b-instruct | ok | True | False | False | 15/15 | 6/15 | True | 41 |
| qwen2.5-14b-instruct | ok | True | False | False | 15/15 | 6/15 | True | 41 |
| olmo2-1b-instruct | ok | True | True | False | 15/15 | 6/15 | False | 44 |
| olmo2-1b-sft | ok | True | True | False | 15/15 | 6/15 | False | 44 |
| olmo2-1b-dpo | ok | True | True | False | 15/15 | 6/15 | False | 44 |
| olmo2-7b-instruct | ok | True | True | False | 15/15 | 6/15 | False | 44 |
| olmo2-13b-instruct | ok | True | True | False | 15/15 | 6/15 | False | 44 |
| granite-3.3-2b-instruct | ok | True | False | False | 15/15 | 6/15 | True | 43 |
| granite-3.3-8b-instruct | ok | True | False | False | 15/15 | 6/15 | True | 43 |
| smollm2-1.7b-instruct | ok | True | True | False | 15/15 | 6/15 | True | 44 |
| phi4-mini-instruct | ok | True | False | False | 15/15 | 15/15 | False | 33 |
| mistral-7b-instruct-v0.3 | ok | True | True | True | 15/15 | 6/15 | True | 36 |

OLMo-2 1B ladder parity: {"models": ["olmo2-1b-sft", "olmo2-1b-dpo", "olmo2-1b-instruct"], "template_hashes": {"olmo2-1b-sft": "fe689ffbd6a4e2d0", "olmo2-1b-dpo": "fe689ffbd6a4e2d0", "olmo2-1b-instruct": "fe689ffbd6a4e2d0"}, "rendered_hashes": {"olmo2-1b-sft": "1148d87a3162f1af", "olmo2-1b-dpo": "1148d87a3162f1af", "olmo2-1b-instruct": "1148d87a3162f1af"}, "rendered_identical": true, "answer_tokens_identical": true, "vocab_identical": true}

### qwen2.5-0.5b-instruct
```
<|im_start|>system
You are taking part in a short study. Answer the question as yourself.<|im_end|>
<|im_start|>user
Which program would you choose?

Answer with only the program letter.<|im_end|>
<|im_start|>assistant

```

### qwen2.5-1.5b-instruct
```
<|im_start|>system
You are taking part in a short study. Answer the question as yourself.<|im_end|>
<|im_start|>user
Which program would you choose?

Answer with only the program letter.<|im_end|>
<|im_start|>assistant

```

### qwen2.5-7b-instruct
```
<|im_start|>system
You are taking part in a short study. Answer the question as yourself.<|im_end|>
<|im_start|>user
Which program would you choose?

Answer with only the program letter.<|im_end|>
<|im_start|>assistant

```

### qwen2.5-14b-instruct
```
<|im_start|>system
You are taking part in a short study. Answer the question as yourself.<|im_end|>
<|im_start|>user
Which program would you choose?

Answer with only the program letter.<|im_end|>
<|im_start|>assistant

```

### olmo2-1b-instruct
```
<|endoftext|><|system|>
You are taking part in a short study. Answer the question as yourself.
<|user|>
Which program would you choose?

Answer with only the program letter.
<|assistant|>

```

### olmo2-1b-sft
```
<|endoftext|><|system|>
You are taking part in a short study. Answer the question as yourself.
<|user|>
Which program would you choose?

Answer with only the program letter.
<|assistant|>

```

### olmo2-1b-dpo
```
<|endoftext|><|system|>
You are taking part in a short study. Answer the question as yourself.
<|user|>
Which program would you choose?

Answer with only the program letter.
<|assistant|>

```

### olmo2-7b-instruct
```
<|endoftext|><|system|>
You are taking part in a short study. Answer the question as yourself.
<|user|>
Which program would you choose?

Answer with only the program letter.
<|assistant|>

```

### olmo2-13b-instruct
```
<|endoftext|><|system|>
You are taking part in a short study. Answer the question as yourself.
<|user|>
Which program would you choose?

Answer with only the program letter.
<|assistant|>

```

### granite-3.3-2b-instruct
```
<|start_of_role|>system<|end_of_role|>You are taking part in a short study. Answer the question as yourself.<|end_of_text|>
<|start_of_role|>user<|end_of_role|>Which program would you choose?

Answer with only the program letter.<|end_of_text|>
<|start_of_role|>assistant<|end_of_role|>
```

### granite-3.3-8b-instruct
```
<|start_of_role|>system<|end_of_role|>You are taking part in a short study. Answer the question as yourself.<|end_of_text|>
<|start_of_role|>user<|end_of_role|>Which program would you choose?

Answer with only the program letter.<|end_of_text|>
<|start_of_role|>assistant<|end_of_role|>
```

### smollm2-1.7b-instruct
```
<|im_start|>system
You are taking part in a short study. Answer the question as yourself.<|im_end|>
<|im_start|>user
Which program would you choose?

Answer with only the program letter.<|im_end|>
<|im_start|>assistant

```

### phi4-mini-instruct
```
<|system|>You are taking part in a short study. Answer the question as yourself.<|end|><|user|>Which program would you choose?

Answer with only the program letter.<|end|><|assistant|>
```

### mistral-7b-instruct-v0.3
```
<s>[INST] You are taking part in a short study. Answer the question as yourself.

Which program would you choose?

Answer with only the program letter.[/INST]
```

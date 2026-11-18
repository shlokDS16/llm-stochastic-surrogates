"""Run local_screen.py and report wall time and peak VRAM. Usage: python run_wrapped.py <local_screen args...>"""
import runpy, sys, time
import torch
sys.argv = ["local_screen.py"] + sys.argv[1:]
t = time.time()
try:
    runpy.run_path("analysis/screening/local_screen.py", run_name="__main__")
finally:
    print(f"WALL {time.time() - t:.1f}s PEAK_VRAM_GiB {torch.cuda.max_memory_allocated() / 2**30:.2f} RESERVED_GiB {torch.cuda.max_memory_reserved() / 2**30:.2f}", flush=True)

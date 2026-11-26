"""Deterministic mutations of owned DLLs, bounded static inspection only."""
from pathlib import Path
import random
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pecheck import Rejected
from peexports import inspect_dll

rng = random.Random(27112026)
seeds = [Path('build/dependency.dll').read_bytes(), Path('build/export_cases.dll').read_bytes()]
counts = [0, 0]
def check(raw):
    try:
        assert inspect_dll(raw)['execution_allowed'] is False
        counts[0] += 1
    except Rejected:
        counts[1] += 1
for seed in seeds:
    for n in range(len(seed)):
        check(seed[:n])
for _ in range(10000):
    b = bytearray(rng.choice(seeds))
    for __ in range(rng.randrange(1,9)):
        p = rng.randrange(len(b))
        b[p] ^= rng.randrange(1,256)
    check(bytes(b))
print(f'Export fuzz: {sum(counts)} cases; accepted={counts[0]}, rejected={counts[1]}, 0 unexpected exceptions')

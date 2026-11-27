"""Bounded deterministic mutations of owned inputs, no execution."""
import random
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pecheck import Rejected
from pemap import model
from peresolve import plan

rng = random.Random(2026112703)
exe = Path('build/import_reloc.exe').read_bytes()
root = Path('build/bridge_root.exe').read_bytes()
dep = Path('build/dependency.dll').read_bytes()
bridge = Path('build/bridge.dll').read_bytes()
counts = {'layout':[0,0], 'resolver':[0,0]}

def mutate(raw):
    b = bytearray(raw)
    for _ in range(rng.randrange(1,9)):
        b[rng.randrange(len(b))] ^= rng.randrange(1,256)
    if rng.randrange(7)==0:
        del b[rng.randrange(len(b)):]
    return bytes(b)

def check_layout(raw):
    try:
        out = model(raw)
        assert out.execution_allowed is False and type(out.data) is bytes
        assert 0 <= out.entry_rva < len(out.data)
        counts['layout'][0] += 1
    except Rejected:
        counts['layout'][1] += 1

def check_graph(raw, dll1, dll2):
    try:
        out = plan(raw, {'bridge.dll':dll1,'dependency.dll':dll2})
        assert out.execution_allowed is False
        assert len(set(out.modules))==len(out.modules)
        assert all(b.target_module in out.modules and b.target_rva>0 for b in out.bindings)
        counts['resolver'][0] += 1
    except Rejected:
        counts['resolver'][1] += 1

for n in range(len(exe)):
    check_layout(exe[:n])
for _ in range(1000):
    check_layout(mutate(exe))
for which, raw in enumerate((root,bridge,dep)):
    for n in range(len(raw)):
        inputs=[root,bridge,dep]
        inputs[which]=raw[:n]
        check_graph(*inputs)
for _ in range(2000):
    inputs=[root,bridge,dep]
    i=rng.randrange(3)
    inputs[i]=mutate(inputs[i])
    check_graph(*inputs)
for name,(good,bad) in counts.items():
    print(f'{name} fuzz: {good+bad} cases; accepted={good}, rejected={bad}, 0 unexpected exceptions')

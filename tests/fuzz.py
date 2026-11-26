from pathlib import Path
import sys,random
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pecheck import Image,Rejected
rng=random.Random(20261127)
seeds=[Path('ws01/build/fixture.exe').read_bytes(),Path('build/import_reloc.exe').read_bytes()]
counts={'accepted_static':0,'rejected_or_unsupported':0}
def test(b):
    try:
        assert Image(b).report()['execution_allowed'] is False
        counts['accepted_static']+=1
    except Rejected: counts['rejected_or_unsupported']+=1
for seed in seeds:
    for n in range(len(seed)): test(seed[:n])
for i in range(20000):
    b=bytearray(rng.choice(seeds))
    for _ in range(rng.randrange(1,12)):
        j=rng.randrange(len(b)); b[j]^=rng.randrange(1,256)
    if i%7==0: del b[rng.randrange(len(b)):]
    test(bytes(b))
for i in range(2000): test(rng.randbytes(rng.randrange(1024)))
print('Deterministic fuzz:',sum(counts.values()),'cases;',counts,'; 0 unexpected exceptions; execution always disabled')

"""Static graph checks using owned linked PE fixtures."""
import unittest
from pathlib import Path
from unittest.mock import patch
from pecheck import Image, Rejected
from peresolve import Resolver, plan, MAX_FORWARDERS
from peexports import inspect_dll

DEP = Path('build/dependency.dll').read_bytes()
BRIDGE = Path('build/bridge.dll').read_bytes()
ROOT = Path('build/bridge_root.exe').read_bytes()
CHAIN = Path('build/chain.dll').read_bytes()
CAT = {'bridge.dll': BRIDGE, 'dependency.dll': DEP}
DEMO = next(e for e in inspect_dll(DEP)['exports'] if 'demo' in e['names'])
WRAP = next(e for e in inspect_dll(BRIDGE)['exports'] if 'wrap' in e['names'])

def chain_to(index):
    """Replace only the forwarder string with an equal-length module name."""
    img = Image(CHAIN, allow_dll=True)
    entry = next(x for x in inspect_dll(CHAIN)['exports'] if 'next' in x['names'])
    old = b'module00.next\0'
    off = img.rva(entry['rva'], len(old))
    assert CHAIN[off:off+len(old)] == old
    return CHAIN[:off] + f'module{index:02d}.next'.encode() + b'\0' + CHAIN[off+len(old):]

class Graph(unittest.TestCase):
    def test_transitive(self):
        result = plan(ROOT, CAT)
        self.assertEqual(result.modules, ('bridge.dll','dependency.dll'))
        self.assertEqual([(b.owner,b.symbol,b.target_module,b.target_rva) for b in result.bindings],
                         [('<exe>','wrap','bridge.dll',WRAP['rva']),
                          ('bridge.dll','demo','dependency.dll',DEMO['rva'])])
        self.assertFalse(result.execution_allowed)
    def test_transitive_missing(self):
        with self.assertRaisesRegex(Rejected,'missing DLL: dependency.dll'):
            plan(ROOT, {'bridge.dll':BRIDGE})
    def test_unused_not_parsed(self):
        self.assertEqual(plan(ROOT,{**CAT,'unused.dll':b'invalid'}).modules,
                         ('bridge.dll','dependency.dll'))
    def test_independent_plans(self):
        self.assertEqual(plan(ROOT,CAT),plan(ROOT,dict(reversed(list(CAT.items())))))
    def test_forwarder_depth(self):
        catalog={f'module{i:02d}.dll':chain_to(i+1) for i in range(MAX_FORWARDERS+1)}
        with self.assertRaisesRegex(Rejected,'forwarder depth limit'):
            Resolver(catalog).resolve('module00.dll','next')
    def test_cross_module_forwarder_cycle(self):
        catalog={'module00.dll':chain_to(1),'module01.dll':chain_to(0)}
        with self.assertRaisesRegex(Rejected,'forwarder cycle'):
            Resolver(catalog).resolve('module00.dll','next')
    def test_module_budget(self):
        with self.assertRaisesRegex(Rejected,'catalog limit'):
            Resolver({f'm{i}.dll':DEP for i in range(65)})
    def test_catalog_byte_budget(self):
        # Exercise the actual budget guard without allocating 128 MiB in a test.
        with patch('peresolve.MAX_CATALOG_BYTES',len(DEP)-1):
            with self.assertRaisesRegex(Rejected,'catalog byte limit'):
                Resolver({'dependency.dll':DEP})

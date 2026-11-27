import struct
import unittest
from pathlib import Path
from pecheck import Image, Rejected
from peexports import inspect_dll
from peresolve import Resolver, plan, module_key, MAX_WORK

EXE = Path('build/import_reloc.exe').read_bytes()
DEP = Path('build/dependency.dll').read_bytes()
CASES = Path('build/export_cases.dll').read_bytes()
CYCLE = Path('build/cycle.dll').read_bytes()
CATALOG = {'dependency.dll': DEP, 'export_cases.dll': CASES, 'cycle.dll': CYCLE}
DEMO = next(x for x in inspect_dll(DEP)['exports'] if 'demo' in x['names'])

class Resolve(unittest.TestCase):
    def test_only_needed(self):
        result = plan(EXE, {**CATALOG, 'unused.dll': b'bad'})
        self.assertEqual(result.modules, ('dependency.dll',))
        self.assertEqual(len(result.bindings), 1)
        self.assertEqual(result.bindings[0].target_rva, DEMO['rva'])
        self.assertFalse(result.execution_allowed)
    def test_name(self):
        self.assertEqual(Resolver(CATALOG).resolve('DEPENDENCY.DLL', 'demo'), ('dependency.dll', DEMO['rva']))
    def test_ordinal(self):
        self.assertEqual(Resolver(CATALOG).resolve('dependency.dll', DEMO['ordinal']), ('dependency.dll', DEMO['rva']))
    def test_forward_name(self):
        self.assertEqual(Resolver(CATALOG).resolve('export_cases.dll', 'redirected'), ('dependency.dll', DEMO['rva']))
    def test_forward_ordinal(self):
        self.assertEqual(Resolver(CATALOG).resolve('export_cases.dll', 'ordinal_redirect'), ('dependency.dll', DEMO['rva']))
    def test_forward_cycle(self):
        with self.assertRaisesRegex(Rejected, 'forwarder cycle'):
            Resolver(CATALOG).resolve('cycle.dll', 'a')
    def test_missing_library(self):
        with self.assertRaisesRegex(Rejected, 'missing DLL'):
            plan(EXE, {})
    def test_missing_export(self):
        with self.assertRaisesRegex(Rejected, 'missing export'):
            Resolver(CATALOG).resolve('dependency.dll', 'Demo')
    def test_literal_hash_not_ordinal(self):
        with self.assertRaisesRegex(Rejected, 'missing export'):
            Resolver(CATALOG).resolve('dependency.dll', '#1')
    def test_ordinal_import(self):
        img = Image(EXE)
        r, _ = img.directory(1)
        ilt = img.u32(img.rva(r, 4))
        raw = bytearray(EXE)
        struct.pack_into('<Q', raw, img.rva(ilt, 8), (1<<63)|DEMO['ordinal'])
        result = plan(bytes(raw), CATALOG)
        self.assertEqual(result.bindings[0].symbol, DEMO['ordinal'])
    def test_duplicate_catalog(self):
        with self.assertRaisesRegex(Rejected, 'duplicate'):
            Resolver({'dependency.dll': DEP, 'DEPENDENCY.DLL': DEP})
    def test_paths_rejected(self):
        for name in ('../a.dll','x/y.dll','C:a.dll','x\\a.dll','a..dll'):
            with self.subTest(name=name), self.assertRaises(Rejected):
                module_key(name)
    def test_work_limit(self):
        resolver = Resolver(CATALOG)
        resolver.work = MAX_WORK
        with self.assertRaisesRegex(Rejected, 'work limit'):
            resolver.resolve('dependency.dll', 'demo')
    def test_invalid_dll(self):
        with self.assertRaises(Rejected):
            plan(EXE, {'dependency.dll': b'bad'})
    def test_immutable(self):
        with self.assertRaises(Rejected):
            plan(bytearray(EXE), CATALOG)
    def test_missing_forward_target(self):
        with self.assertRaisesRegex(Rejected, 'missing DLL'):
            Resolver({'export_cases.dll': CASES}).resolve('export_cases.dll', 'redirected')

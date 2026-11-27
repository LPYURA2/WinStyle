"""Real linked DLLs, independent GNU objdump comparison; no execution."""
import os
import re
import subprocess
import unittest
from pathlib import Path
from peexports import inspect_dll

PATH = Path('build/export_cases.dll')
RAW = PATH.read_bytes()
ITEMS = {x['ordinal']: x for x in inspect_dll(RAW)['exports']}

def parse_objdump(out):
    addresses, names = {}, {}
    base = None
    in_names = False
    for line in out.splitlines():
        m = re.match(r'\s*Ordinal Base\s+(\d+)\s*$', line)
        if m:
            base = int(m[1])
        if '[Ordinal/Name Pointer] Table' in line:
            in_names = True
            continue
        m = re.search(r'\+base\[\s*(\d+)\]\s+([0-9a-fA-F]+) (?:Export RVA|Forwarder RVA -- (\S+))\s*$', line)
        if m:
            addresses[int(m[1])] = (int(m[2],16), m[3])
        if in_names:
            m = re.fullmatch(r'\s*\[\s*(\d+)\]\s+(?:\+base\[\s*(\d+)\]\s+[0-9a-fA-F]+\s+)?(\S+)\s*', line)
            if m:
                if base is None:
                    raise ValueError('missing ordinal base')
                ordinal = base + int(m[1])
                if m[2] is not None and int(m[2]) != ordinal:
                    raise ValueError('inconsistent ordinal')
                names.setdefault(ordinal, []).append(m[3])
            elif line.strip():
                in_names = False
    return addresses, names

class RealExports(unittest.TestCase):
    def test_noname_and_holes(self):
        self.assertEqual(ITEMS[9]['names'], [])
        self.assertNotIn(4, ITEMS)
        self.assertNotIn(6, ITEMS)
    def test_same_target(self):
        self.assertEqual(ITEMS[3]['names'], ['alpha'])
        self.assertEqual(ITEMS[5]['names'], ['beta'])
        self.assertEqual(ITEMS[3]['rva'], ITEMS[5]['rva'])
    def test_forwarders(self):
        by_name = {name: item for item in ITEMS.values() for name in item['names']}
        self.assertEqual(by_name['redirected']['forwarder'], 'dependency.demo')
        self.assertEqual(by_name['ordinal_redirect']['forwarder'], 'dependency.#1')
        self.assertNotEqual(by_name['redirected']['ordinal'], by_name['ordinal_redirect']['ordinal'])
    def test_no_execution(self):
        self.assertFalse(inspect_dll(RAW)['execution_allowed'])
    def test_independent_objdump(self):
        out = subprocess.check_output(['objdump','-p',str(PATH)], text=True,
                                      env={**os.environ, 'LC_ALL':'C'})
        addresses, names = parse_objdump(out)
        self.assertTrue(addresses)
        self.assertEqual(addresses, {k:(v['rva'],v['forwarder']) for k,v in ITEMS.items()})
        self.assertEqual(names, {k:v['names'] for k,v in ITEMS.items() if v['names']})
    def test_objdump_legacy_names(self):
        out = 'Ordinal Base 3\n[Ordinal/Name Pointer] Table\n\t[  0] alpha\n\t[  2] beta\n'
        self.assertEqual(parse_objdump(out)[1], {3:['alpha'],5:['beta']})
    def test_objdump_extended_names(self):
        out = 'Ordinal Base 3\n[Ordinal/Name Pointer] Table\n\t[  0] +base[ 3] 00001000 alpha\n\t[  2] +base[ 5] 00001000 beta\n'
        self.assertEqual(parse_objdump(out)[1], {3:['alpha'],5:['beta']})

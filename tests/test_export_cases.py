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
        self.assertEqual(ITEMS[11]['forwarder'], 'dependency.demo')
        self.assertEqual(ITEMS[12]['forwarder'], 'dependency.#1')
    def test_no_execution(self):
        self.assertFalse(inspect_dll(RAW)['execution_allowed'])
    def test_independent_objdump(self):
        out = subprocess.check_output(['objdump','-p',str(PATH)], text=True,
                                      env={**os.environ, 'LC_ALL':'C'})
        addresses, names = {}, {}
        for line in out.splitlines():
            m = re.search(r'\+base\[\s*(\d+)\]\s+([0-9a-fA-F]+) (?:Export RVA|Forwarder RVA -- (\S+))$', line)
            if m:
                addresses[int(m[1])] = (int(m[2],16), m[3])
            m = re.search(r'\+base\[\s*(\d+)\]\s+[0-9a-fA-F]+\s+(\S+)$',line)
            if m:
                names.setdefault(int(m[1]),[]).append(m[2])
        self.assertTrue(addresses)
        self.assertEqual(addresses, {k:(v['rva'],v['forwarder']) for k,v in ITEMS.items()})
        self.assertEqual(names, {k:v['names'] for k,v in ITEMS.items() if v['names']})

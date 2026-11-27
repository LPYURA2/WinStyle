import re
import struct
import subprocess
import unittest
from pathlib import Path
from pecheck import Image, Rejected
from ws03b.embed import inspect_fixture

RAW=Path('build/ws03b/fixture.exe').read_bytes()
I=Image(RAW)

class FirstAPI(unittest.TestCase):
    def test_real_import(self):
        self.assertEqual(I.import_refs,[('kernel32.dll',('GetCurrentProcessId',))])
        self.assertEqual(len(I.import_slots),1)
    def test_fixture_profile(self):
        image,entry,slot,code,span=inspect_fixture(RAW)
        self.assertEqual(len(image),I.size)
        self.assertEqual(entry,I.entry)
        self.assertEqual(slot,I.import_slots[0][2])
        self.assertTrue(code<=entry<code+span)
    def test_api_call(self):
        child=subprocess.Popen(['build/ws03b/child'],stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                               env={'LC_ALL':'C'})
        try:
            out,err=child.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
            child.communicate()
            self.fail('trusted child timed out')
        self.assertEqual(child.returncode,0,err)
        match=re.fullmatch(rb'PID=(\d+) RESULT=(\d+) CALLS=(\d+)\n',out)
        self.assertIsNotNone(match,out)
        pid,result,calls=map(int,match.groups())
        self.assertEqual(pid,child.pid)
        self.assertEqual(result,pid+7)
        self.assertEqual(calls,1)
    def test_wrong_api(self):
        bad=RAW.replace(b'GetCurrentProcessId\0',b'GetCurrentProcessXX\0')
        self.assertNotEqual(bad,RAW)
        with self.assertRaisesRegex(Rejected,'unexpected API'):
            inspect_fixture(bad)
    def test_wrong_library(self):
        bad=RAW.replace(b'kernel32.dll\0',b'unknown0.dll\0')
        self.assertNotEqual(bad,RAW)
        with self.assertRaisesRegex(Rejected,'unexpected API'):
            inspect_fixture(bad)
    def test_bad_iat(self):
        b=bytearray(RAW)
        slot=I.import_slots[0][2]
        struct.pack_into('<Q',b,I.rva(slot,8),123)
        with self.assertRaisesRegex(Rejected,'IAT differs'):
            inspect_fixture(bytes(b))
    def test_truncated(self):
        with self.assertRaises(Rejected):
            inspect_fixture(RAW[:64])

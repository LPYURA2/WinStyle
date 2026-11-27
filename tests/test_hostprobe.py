import signal
import unittest
from hostprobe import run, MAX_OUTPUT

class TrustedHostProbe(unittest.TestCase):
    def test_native_pe_result(self):
        r=run('normal')
        self.assertEqual((r.status,r.returncode,r.output),('OK',0,b'RESULT=22\n'))
    def test_guest_machine_fault(self):
        r=run('fault')
        self.assertEqual(r.status,'SIGNAL')
        self.assertEqual(r.returncode,-signal.SIGILL)
    def test_guest_hang(self):
        r=run('hang')
        self.assertEqual(r.status,'TIMEOUT')
        self.assertEqual(r.returncode,-signal.SIGKILL)
    def test_output_limit(self):
        r=run('output')
        self.assertEqual(r.status,'OUTPUT_LIMIT')
        self.assertLessEqual(len(r.output),MAX_OUTPUT)
        self.assertEqual(r.returncode,-signal.SIGXFSZ)
    def test_recovery(self):
        self.assertEqual(run('fault').status,'SIGNAL')
        self.assertEqual(run('normal').status,'OK')
    def test_no_arbitrary_command(self):
        for v in ('/bin/sh','normal; echo x','',None):
            with self.subTest(v=v),self.assertRaises(ValueError):
                run(v)

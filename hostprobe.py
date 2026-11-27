"""Supervise a fixed owned PE experiment. Not an untrusted-code sandbox."""
from dataclasses import dataclass
from pathlib import Path
import os
import signal
import subprocess
import tempfile

CHILD=Path(__file__).resolve().parent/'build/ws03a/child'
MODES=frozenset(('normal','fault','hang','output'))
MAX_OUTPUT=4096

@dataclass(frozen=True)
class Result:
    status: str
    returncode: int
    output: bytes

def run(mode):
    if type(mode) is not str or mode not in MODES:
        raise ValueError('owned fixture mode required')
    # Fixed build artifact, no external executable or guest filename accepted.
    # Only trusted build inputs; the binary itself must not be substituted.
    with tempfile.TemporaryFile() as out:
        proc=subprocess.Popen([str(CHILD),mode],stdin=subprocess.DEVNULL,
                              stdout=out,stderr=out,close_fds=True,
                              start_new_session=True,
                              env={'LC_ALL':'C'})
        timeout=False
        try:
            proc.wait(timeout=1.5)
        except subprocess.TimeoutExpired:
            timeout=True
            try:
                os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait()
        out.seek(0)
        data=out.read(MAX_OUTPUT+1)
        if timeout:
            status='TIMEOUT'
        elif proc.returncode==-signal.SIGXFSZ or len(data)>=MAX_OUTPUT:
            status='OUTPUT_LIMIT'
        elif proc.returncode<0:
            status='SIGNAL'
        elif proc.returncode==0:
            status='OK'
        else:
            status='ERROR'
        return Result(status,proc.returncode,data[:MAX_OUTPUT])

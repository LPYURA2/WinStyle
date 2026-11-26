#!/bin/sh
set -eu
cd "$(dirname "$0")"
[ "$(uname -m)" = x86_64 ] || { echo 'Requires Linux x86_64'; exit 1; }
mkdir -p build
clang --target=x86_64-pc-windows-msvc -O2 -ffreestanding -fno-stack-protector -c fixture.c -o build/fixture.obj
lld-link /entry:entry /subsystem:console /nodefaultlib /fixed /machine:x64 /out:build/fixture.exe build/fixture.obj
python3 - <<'PY'
from pathlib import Path
b=Path('build/fixture.exe').read_bytes()
Path('build/fixture.h').write_text('static const unsigned char fixture[] = {'+','.join(map(str,b))+'};\n')
PY
cc -std=gnu11 -O2 -Wall -Wextra -Werror -Ibuild probe.c -o build/probe
./build/probe

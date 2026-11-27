#!/bin/sh
set -eu
cd "$(dirname "$0")"
sh ws01/run.sh
mkdir -p build
clang --target=x86_64-pc-windows-msvc -O2 -ffreestanding -fno-stack-protector -c tests/dependency.c -o build/dependency.obj
lld-link /dll /noentry /nodefaultlib /machine:x64 /out:build/dependency.dll /implib:build/dependency.lib build/dependency.obj
clang --target=x86_64-pc-windows-msvc -O2 -ffreestanding -fno-stack-protector -c tests/import_reloc.c -o build/import_reloc.obj
lld-link /entry:entry /subsystem:console /nodefaultlib /machine:x64 /dynamicbase /out:build/import_reloc.exe build/import_reloc.obj build/dependency.lib
lld-link /dll /noentry /nodefaultlib /machine:x64 /out:build/export_cases.dll /def:tests/exports.def build/dependency.obj
lld-link /dll /noentry /nodefaultlib /machine:x64 /out:build/cycle.dll /def:tests/cycle.def build/dependency.obj
# Own DLL that imports another DLL, and an EXE importing that DLL.
clang --target=x86_64-pc-windows-msvc -O2 -ffreestanding -fno-stack-protector -c tests/bridge.c -o build/bridge.obj
lld-link /dll /noentry /nodefaultlib /machine:x64 /base:0x180100000 /out:build/bridge.dll /implib:build/bridge.lib build/bridge.obj build/dependency.lib
clang --target=x86_64-pc-windows-msvc -O2 -ffreestanding -fno-stack-protector -c tests/bridge_root.c -o build/bridge_root.obj
lld-link /entry:entry /subsystem:console /nodefaultlib /machine:x64 /out:build/bridge_root.exe build/bridge_root.obj build/bridge.lib
lld-link /dll /noentry /nodefaultlib /machine:x64 /out:build/chain.dll /def:tests/chain.def build/dependency.obj
# Bootstrap B's import library, then link real A <-> B, without executing either.
clang --target=x86_64-pc-windows-msvc -O2 -ffreestanding -fno-stack-protector -c tests/ring_b_stub.c -o build/ring_b_stub.obj
lld-link /dll /noentry /nodefaultlib /machine:x64 /base:0x180300000 /out:build/ring_b.dll /implib:build/ring_b.lib build/ring_b_stub.obj
clang --target=x86_64-pc-windows-msvc -O2 -ffreestanding -fno-stack-protector -c tests/ring_a.c -o build/ring_a.obj
lld-link /dll /noentry /nodefaultlib /machine:x64 /base:0x180200000 /out:build/ring_a.dll /implib:build/ring_a.lib build/ring_a.obj build/ring_b.lib
clang --target=x86_64-pc-windows-msvc -O2 -ffreestanding -fno-stack-protector -c tests/ring_b.c -o build/ring_b.obj
lld-link /dll /noentry /nodefaultlib /machine:x64 /base:0x180300000 /out:build/ring_b.dll /implib:build/ring_b.lib build/ring_b.obj build/ring_a.lib
clang --target=x86_64-pc-windows-msvc -O2 -ffreestanding -fno-stack-protector -c tests/ring_root.c -o build/ring_root.obj
lld-link /entry:entry /subsystem:console /nodefaultlib /machine:x64 /out:build/ring_root.exe build/ring_root.obj build/ring_a.lib
sh ws03a/build.sh
python3 -m unittest discover -s tests -v
python3 tests/fuzz.py
python3 tests/fuzz_exports.py
python3 tests/fuzz_models.py
python3 tests/fuzz_bind.py

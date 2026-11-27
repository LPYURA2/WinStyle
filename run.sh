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
python3 -m unittest discover -s tests -v
python3 tests/fuzz.py
python3 tests/fuzz_exports.py

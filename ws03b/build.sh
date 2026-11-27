#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
[ "$(uname -m)" = x86_64 ]
mkdir -p build/ws03b
clang --target=x86_64-pc-windows-msvc -O2 -ffreestanding -fno-stack-protector -c ws03b/import_stub.c -o build/ws03b/import_stub.obj
lld-link /dll /noentry /nodefaultlib /machine:x64 /out:build/ws03b/kernel32.dll /implib:build/ws03b/kernel32.lib build/ws03b/import_stub.obj
clang --target=x86_64-pc-windows-msvc -O2 -ffreestanding -fno-stack-protector -c ws03b/fixture.c -o build/ws03b/fixture.obj
lld-link /entry:entry /subsystem:console /nodefaultlib /fixed /machine:x64 /out:build/ws03b/fixture.exe build/ws03b/fixture.obj build/ws03b/kernel32.lib
PYTHONPATH=. python3 ws03b/embed.py
cc -std=gnu11 -O2 -Wall -Wextra -Werror -Ibuild/ws03b ws03b/child.c -o build/ws03b/child

#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
[ "$(uname -m)" = x86_64 ]
mkdir -p build/ws03a
clang --target=x86_64-pc-windows-msvc -O2 -ffreestanding -fno-stack-protector -c ws03a/fixture.c -o build/ws03a/fixture.obj
lld-link /entry:entry /subsystem:console /nodefaultlib /fixed /machine:x64 /out:build/ws03a/fixture.exe build/ws03a/fixture.obj
PYTHONPATH=. python3 ws03a/embed.py
cc -std=gnu11 -O2 -Wall -Wextra -Werror -Ibuild/ws03a ws03a/child.c -o build/ws03a/child

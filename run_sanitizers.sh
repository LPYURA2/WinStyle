#!/bin/sh
set -eu
cd "$(dirname "$0")"
sh ws01/run.sh
# The mapped foreign code lacks Clang's function-type metadata. Keep other checks.
clang -std=gnu11 -g -O1 -Wall -Wextra -Werror -fsanitize=address,undefined -fno-sanitize=function -fno-omit-frame-pointer -Iws01/build ws01/probe.c -o ws01/build/probe_san
./ws01/build/probe_san
gcc -std=gnu11 -g -O1 -Wall -Wextra -Werror -fsanitize=address,undefined -fno-omit-frame-pointer -Iws01/build ws01/probe.c -o ws01/build/probe_gcc_san
./ws01/build/probe_gcc_san

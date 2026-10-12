#!/usr/bin/env bash
# Public tools only. Never downloads firmware, reads serials or registers MCP.
set -euo pipefail
umask 077
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
root=/tmp/ep7-re-tools
providers=yes
dry=no
while (($#)); do
  case "$1" in
    --root) root="$2"; shift 2;;
    --core-only) providers=no; shift;;
    --dry-run) dry=yes; shift;;
    --help) printf '%s\n' 'Usage: setup_re_environment.sh [--root /tmp/NAME] [--core-only] [--dry-run]' 'Linux x86_64; Python3, curl, tar, unzip, C/C++ compiler and make required.' 'Pinned public GNU tools; default also installs pinned Node/JDK/Ghidra/REA.' 'No firmware download, camera operation, user-level registration or secrets.'; exit 0;;
    *) printf '%s\n' 'Unknown option' >&2; exit 2;;
  esac
done
[[ "$root" == /tmp/* && "$root" != /tmp/ && "$root" != *[[:space:]]* ]] || { printf '%s\n' 'STOP: root must be a non-root /tmp directory without whitespace' >&2; exit 2; }
[[ "$(uname -s)" == Linux && "$(uname -m)" == x86_64 ]] || { printf '%s\n' 'STOP: this pinned bootstrap supports Linux x86_64 only' >&2; exit 2; }
if [[ "$dry" == yes ]]; then
  printf 'Plan: root=%s, GNU2.44, providers=%s; public downloads only; no changes\n' "$root" "$providers"
  exit 0
fi
missing=no
for dependency in python3 curl tar gcc g++ make sha256sum cmp xz; do
  command -v "$dependency" >/dev/null || missing=yes
done
if [[ "$providers" == yes ]] && ! command -v unzip >/dev/null; then missing=yes; fi
if [[ "$missing" == yes ]]; then
  # Codex Debian/Ubuntu bootstrap only. Preserve injected proxy/CA settings.
  command -v apt-get >/dev/null || { printf '%s\n' 'STOP: missing prerequisites and no apt-get; unsupported base image' >&2; exit 2; }
  elevate=()
  if [[ "$(id -u)" != 0 ]]; then
    command -v sudo >/dev/null && sudo -n true || { printf '%s\n' 'STOP: prerequisite installation needs root or noninteractive sudo in Cloud Setup' >&2; exit 2; }
    elevate=(sudo -n)
  fi
  "${elevate[@]}" apt-get update -qq
  "${elevate[@]}" apt-get install -y --no-install-recommends build-essential python3 curl ca-certificates tar xz-utils unzip coreutils
fi
mkdir -p "$root/cache" "$root/logs"
chmod 700 "$root" "$root/cache" "$root/logs"
pin() { python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))[sys.argv[2]][sys.argv[3]])' "$repo_dir/tools/re_environment/pins.json" "$1" "$2"; }
fetch() {
  local name="$1" suffix="$2" archive="$root/cache/$1.$2"
  if [[ ! -f "$archive" ]]; then
    curl --fail --location --silent --show-error --max-time 300 "$(pin "$name" url)" --output "$archive.part" || { rm -f "$archive.part"; return 1; }
    mv "$archive.part" "$archive"
  fi
  printf '%s  %s\n' "$(pin "$name" sha256)" "$archive" | sha256sum --check --status || { printf 'STOP: %s archive hash mismatch\n' "$name" >&2; return 1; }
}
if [[ ! -x "$root/binutils/binutils/objdump" || ! -x "$root/binutils/gas/as-new" || ! -x "$root/binutils/ld/ld-new" ]]; then
  fetch binutils tar.xz
  mkdir -p "$root/binutils-source" "$root/binutils"
  tar -xf "$root/cache/binutils.tar.xz" -C "$root/binutils-source" --strip-components=1
  (cd "$root/binutils"; "$root/binutils-source/configure" --target=mn10300-elf --disable-nls --disable-werror --disable-gdb --disable-gdbserver --disable-gprofng --disable-gold --without-debuginfod > "$root/logs/configure.log" 2>&1
   make -j2 MAKEINFO=true all-binutils all-gas all-ld > "$root/logs/build.log" 2>&1) || { printf 'STOP: build failed; see %s/logs\n' "$root" >&2; exit 2; }
fi
if [[ "$providers" == yes ]]; then
  for name in node jdk; do
    if [[ ! -f "$root/$name/.archive-sha256" || "$(cat "$root/$name/.archive-sha256")" != "$(pin "$name" sha256)" ]]; then
      suffix=tar.xz; [[ "$name" == jdk ]] && suffix=tar.gz
      fetch "$name" "$suffix"
      mkdir -p "$root/$name"
      tar -xf "$root/cache/$name.$suffix" -C "$root/$name" --strip-components=1
      pin "$name" sha256 > "$root/$name/.archive-sha256"
    fi
  done
  if [[ ! -f "$root/ghidra_12.1.4_PUBLIC/.archive-sha256" ]]; then
    fetch ghidra zip
    unzip -q -o "$root/cache/ghidra.zip" -d "$root"
    pin ghidra sha256 > "$root/ghidra_12.1.4_PUBLIC/.archive-sha256"
  fi
  export PATH="$root/node/bin:$PATH"
  mkdir -p "$root/rea"
  if ! cmp -s "$repo_dir/tools/re_environment/package-lock.json" "$root/rea/.installed-lock.json"; then
    cp "$repo_dir/tools/re_environment/"package*.json "$root/rea/"
    npm_config_cache="$root/cache/npm" npm ci --prefix "$root/rea" --ignore-scripts --omit=dev --no-audit --no-fund > "$root/logs/npm.log" 2>&1 || { printf 'STOP: npm install failed; see %s/logs/npm.log\n' "$root" >&2; exit 2; }
    cp "$root/rea/package-lock.json" "$root/rea/.installed-lock.json"
  fi
fi
python3 - "$root" "$providers" <<'PY'
from pathlib import Path
import shlex, sys
root, providers = Path(sys.argv[1]), sys.argv[2]
values = {'EP7_RE_ROOT':str(root), 'EP7_OBJDUMP':str(root/'binutils/binutils/objdump'), 'EP7_AS':str(root/'binutils/gas/as-new')}
if providers == 'yes':
    values.update(JAVA_HOME=str(root/'jdk'), GHIDRA_INSTALL_DIR=str(root/'ghidra_12.1.4_PUBLIC'))
text = ''.join('export '+key+'='+shlex.quote(value)+'\n' for key,value in values.items())
if providers == 'yes':
    text += 'export PATH='+shlex.quote(str(root/'node/bin')+':'+str(root/'rea/node_modules/.bin'))+':"$PATH"\n'
(root/'env.sh').write_text(text)
PY
source "$root/env.sh"
python3 "$repo_dir/tools/check_re_environment.py" --root "$root"
printf 'Ready. In each task shell: source %s/env.sh\n' "$root"

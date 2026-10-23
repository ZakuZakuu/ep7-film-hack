#!/usr/bin/env bash
# Original public-tool bootstrap for T20. No firmware, serial or device access.
set -euo pipefail
umask 077
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
upstream="$project_dir/work/upstream/oly_fw_analysis"
cache_root=/tmp/ep7-t20
reference=/tmp/bgdb-ref
if [[ "${1:-}" == --dry-run ]]; then
  printf '%s\n' 'Public sources: github.com/fishcu/oly_fw_analysis@539fcf1; sourceware.org exact GNU commit; gnu.googlesource.com archive; ftp.gnu.org binutils2.45.' 'Complete-tree/source-file validation before external preparation/build. No OEM data or devices.'
  exit 0
fi
for dependency in python3 git curl tar make gcc g++ sha256sum; do
  command -v "$dependency" >/dev/null || { printf 'STOP: missing tool %s\n' "$dependency" >&2; exit 2; }
done
mkdir -p "$cache_root/cache" "$project_dir/work/upstream"
if [[ ! -d "$upstream/.git" ]]; then
  git clone https://github.com/fishcu/oly_fw_analysis.git "$upstream"
  git -C "$upstream" checkout --detach 539fcf1fa9eda5fdef8ede4deeab94a4691d94c3
fi
[[ "$(git -C "$upstream" rev-parse HEAD)" == 539fcf1fa9eda5fdef8ede4deeab94a4691d94c3 ]] || { printf '%s\n' 'STOP: unexpected upstream revision; no automatic change' >&2; exit 2; }
if [[ ! -d "$reference/.git" ]]; then
  git init -q "$reference"
fi
if ! git -C "$reference" rev-parse --verify FETCH_HEAD >/dev/null 2>&1; then
  git -C "$reference" fetch --depth 1 https://sourceware.org/git/binutils-gdb.git 87ffb882e0f4d73401a0746177ffabb8e8bbe4ac
fi
snapshot="$cache_root/cache/binutils-gdb-87ffb882.tar.gz"
if [[ ! -f "$snapshot" ]]; then
  curl --fail --location --silent --show-error --max-time 180 \
    https://gnu.googlesource.com/binutils-gdb/+archive/87ffb882e0f4d73401a0746177ffabb8e8bbe4ac.tar.gz \
    --output "$snapshot"
fi
python3 "$project_dir/tools/build_upstream_mn103_sim.py" --upstream "$upstream" \
  --archive "$snapshot" --reference "$reference" --jobs 2
archive="$cache_root/cache/binutils-2.45.tar.xz"
if [[ ! -f "$archive" ]]; then
  curl --fail --location --silent --show-error --max-time 180 \
    https://ftp.gnu.org/gnu/binutils/binutils-2.45.tar.xz --output "$archive"
fi
printf '%s  %s\n' c50c0e7f9cb188980e2cc97e4537626b1672441815587f1eab69d2a1bfbef5d2 "$archive" | sha256sum --check --status
source_dir="$cache_root/binutils-source"
build_dir="$upstream/toolchains/mn103-patch-build"
mkdir -p "$source_dir" "$build_dir"
if [[ ! -f "$source_dir/configure" ]]; then
  tar -xf "$archive" -C "$source_dir" --strip-components=1
fi
if [[ ! -f "$build_dir/Makefile" ]]; then
  (cd "$build_dir"; "$source_dir/configure" --target=mn10300-elf \
    --disable-nls --disable-werror --disable-gdb --disable-sim --disable-gprof \
    --disable-gold --disable-libctf --with-system-zlib --disable-shared > configure.log 2>&1)
fi
(cd "$build_dir"; make -j2 all-gas all-ld all-binutils MAKEINFO=true > build.log 2>&1)
for tool in gas/as-new ld/ld-new binutils/objcopy binutils/objdump; do
  "$build_dir/$tool" --version | head -n 1
done
printf '%s\n' 'T20 tools ready. Existing legacy Setup may remain; invoke this script for T20.'

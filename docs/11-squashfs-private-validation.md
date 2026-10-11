# 11｜复用 upstream squashfs-tools 的私有验证

这是 Issue #7 的复现说明，不是安装器或实机流程。真实样本已在私有环境取得并核对完整 size/SHA；OE、真实 -s/-ll 和七文件选择性提取成功。以下为复现步骤；不公开原厂数据。合成 integration 也已实际执行。

## 固定上游构建（已在本任务验证）

[源码快照](https://github.com/plougher/squashfs-tools/tree/d8cb82d9840330f9344ec37b992595b5d7b44184)、[Makefile](https://github.com/plougher/squashfs-tools/blob/d8cb82d9840330f9344ec37b992595b5d7b44184/squashfs-tools/Makefile)、[USAGE](https://github.com/plougher/squashfs-tools/blob/d8cb82d9840330f9344ec37b992595b5d7b44184/USAGE-4.6)、[COPYING](https://github.com/plougher/squashfs-tools/blob/d8cb82d9840330f9344ec37b992595b5d7b44184/COPYING)。上游 GPL 条款保留，运行独立工具不表示将上游源代码合并进本项目。

Linux 需要 gcc、make、pthread、zlib development、liblzo2 development。不要做系统更改也能构建：本轮在 Debian 13 amd64，系统已有 gcc/make/zlib；将以下 Debian 官方包下载到 `work/` 并 `dpkg-deb -x` 解到私有依赖目录，**不**运行 maintainer scripts 或系统安装：

| URL / 包 | 本轮下载 SHA-256 |
| --- | --- |
| [liblzo2-2_2.10-3+b1_amd64.deb](https://deb.debian.org/debian/pool/main/l/lzo2/liblzo2-2_2.10-3+b1_amd64.deb) | `f3032201fe2928a87e13f05ce256ff3ac2a7860c7e594dc51ae6d7348a4466ce` |
| [liblzo2-dev_2.10-3+b1_amd64.deb](https://deb.debian.org/debian/pool/main/l/lzo2/liblzo2-dev_2.10-3+b1_amd64.deb) | `d8d981ce661266211bed1e2c54ae525ff6f197f4e862530afc1d30eb38ea97e0` |

这些是 HTTPS 响应的实测哈希用于固定复现，不声称额外审计了 Debian 发布签名。其他 CPU/发行版需要其适用的 LZO 开发包，不用 amd64 binaries 跨平台。

```bash
# 在仓库根目录执行；所有第三方源码/构建产物均位于被忽略的 work/
mkdir -p work/squashfs-upstream
curl --fail --location --max-time 30 \
  'https://deb.debian.org/debian/pool/main/l/lzo2/liblzo2-2_2.10-3+b1_amd64.deb' \
  -o work/squashfs-upstream/liblzo2-2_2.10-3+b1_amd64.deb
curl --fail --location --max-time 30 \
  'https://deb.debian.org/debian/pool/main/l/lzo2/liblzo2-dev_2.10-3+b1_amd64.deb' \
  -o work/squashfs-upstream/liblzo2-dev_2.10-3+b1_amd64.deb
printf '%s\n' \
  'f3032201fe2928a87e13f05ce256ff3ac2a7860c7e594dc51ae6d7348a4466ce  work/squashfs-upstream/liblzo2-2_2.10-3+b1_amd64.deb' \
  'd8d981ce661266211bed1e2c54ae525ff6f197f4e862530afc1d30eb38ea97e0  work/squashfs-upstream/liblzo2-dev_2.10-3+b1_amd64.deb' | sha256sum -c -
dpkg-deb -x work/squashfs-upstream/liblzo2-2_2.10-3+b1_amd64.deb work/squashfs-upstream/lzo
dpkg-deb -x work/squashfs-upstream/liblzo2-dev_2.10-3+b1_amd64.deb work/squashfs-upstream/lzo
git clone --depth 1 --branch 4.6.1 \
  'https://github.com/plougher/squashfs-tools.git' work/squashfs-upstream/source
test "$(git -C work/squashfs-upstream/source rev-parse HEAD)" = \
  'd8cb82d9840330f9344ec37b992595b5d7b44184'
make -C work/squashfs-upstream/source/squashfs-tools -j2 unsquashfs mksquashfs \
  LZO_SUPPORT=1 XZ_SUPPORT=0 LZMA_XZ_SUPPORT=0 LZ4_SUPPORT=0 ZSTD_SUPPORT=0 \
  EXTRA_CFLAGS="-I$PWD/work/squashfs-upstream/lzo/usr/include" \
  EXTRA_LDFLAGS="-L$PWD/work/squashfs-upstream/lzo/usr/lib/x86_64-linux-gnu -Wl,-rpath,$PWD/work/squashfs-upstream/lzo/usr/lib/x86_64-linux-gnu"
work/squashfs-upstream/source/squashfs-tools/unsquashfs -version
work/squashfs-upstream/source/squashfs-tools/unsquashfs -help
SQUASHFS_TOOLS_DIR="$PWD/work/squashfs-upstream/source/squashfs-tools" \
  python3 -m unittest discover -s tests -v
```

本轮 help 的 `Decompressors available` 包含 gzip/lzo。integration 真实生成、列出并解压纯合成 LZO 数据；不同编译器的 build hash 可能不同。没有实现新 SquashFS parser。

## 官方只读下载入口（首次变量缺失，后续授权输入成功）

下载器新增 `--serial-env NAME` 读取任务注入的变量，缺失/空值在请求前返回 2；不用命令行传序列号，不打印值。首次以下授权命令因缺失 `EP7_SERIAL` 停止；用户随后提供授权输入，经不回显的临时进程变量完成一次下载，未存储序列号：

```bash
umask 077
python3 tools/ep7_firmware_fetch.py --serial-env EP7_SERIAL --output-dir /tmp/ep7-firmware
```

只有环境绑定恢复且命令成功后，才使用 `/tmp/ep7-firmware/E142_EP7_firmware_download.BIN` 核对完整 size/SHA。网络失败、大小/hash 不符或解包失败立即停止，不反复重试。可在下述提取命令中使用这个绝对输入路径，不必复制原厂数据到 checkout。

## OEM segment 的有 guard 私有提取

不要用 `sudo`，不要挂载镜像，不执行提取的文件，不把 stdout/目录列表交给 GitHub CI。`private_samples/`、`work/`、`*.squashfs` 被忽略；忽略规则不替代提交清单审查。

```bash
# 私有任务环境内：先把获授权且可读取的输入置于这个位置，不通过 Git 传送
umask 077
mkdir -p private_samples/t11
chmod 700 private_samples private_samples/t11
# 确认 111017984 bytes 和用户预期 SHA-256；任一不符就停止
wc -c < private_samples/E142_EP7_firmware_download.BIN
sha256sum private_samples/E142_EP7_firmware_download.BIN
python3 tools/inspect_olympus_oe.py \
  private_samples/E142_EP7_firmware_download.BIN --json \
  > private_samples/t11/container.json
# 本行自身也核对 SHA/size/所有块校验、唯一候选与 bounds；拒绝已存在的输出
python3 tools/inspect_olympus_oe.py \
  private_samples/E142_EP7_firmware_download.BIN \
  --extract-squashfs private_samples/t11/block2.squashfs \
  --allow-local-oem-output \
  --expected-size 111017984 \
  --expected-sha256 9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb \
  --block-index 2 --payload-offset 0x021367e0 --json \
  > private_samples/t11/carving.json
```

成功 carving 不表示内容被验证。下面依次运行；上一条非零即停，不屏蔽错误：

```bash
work/squashfs-upstream/source/squashfs-tools/unsquashfs \
  -s private_samples/t11/block2.squashfs > private_samples/t11/superblock.txt 2>&1
work/squashfs-upstream/source/squashfs-tools/unsquashfs \
  -ll private_samples/t11/block2.squashfs > private_samples/t11/listing.txt 2>&1
```

确认上面的真实目录后，才从私有 listing 中挑选少量**普通文件**。用 upstream `-strict-errors -no-xattrs -no-progress -processors 1 -no-wildcards -d PRIVATE_NEW_DEST IMAGE EXACT_FILE_PATH...` 选择性提取。不要选择设备节点、整棵根目录或未经审查的符号链接；不使用 `-force`、`-ignore-errors` 或 `-no-exit-code`。仅列表能读不证明文件压缩数据可解，记录真正文件读取的独立结果。

错误返回 1/2 都要停止并留在私有日志中。公开报告只包含脱敏错误、工具版本、文件系统 summary、少量一般路径/职责、样本哈希和有证据的 file offsets；没有原厂 file contents、完整目录列表、第三方源代码、凭据/序列号或逆向代码片段。不能把文件偏移写成运行时地址。

本轮真实 listing 确认后选择了 bin/am、bin/bsa_server、bin/linux_status、lib/libisc.so、lib/libper.so、sbin/lighttpd、share/udhcpc/default.script；严格提取 exit 0。对五个 ELF 使用 `readelf -h -d`，输出留在私有目录。对真实路径及七文件按报告所列 case-insensitive 关键词进行有界检查，公开仅计数/metadata；未提供猜测 ART 文件名或执行提取文件。完整结果与每文件 SHA 见 [实测报告](../research/e142-squashfs-validation.md)。

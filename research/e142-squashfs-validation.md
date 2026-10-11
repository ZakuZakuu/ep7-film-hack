# E-P7 T1.1：真实 SquashFS 验证与有界资源调查

日期 2026-10-11；[Issue #7](https://github.com/ZakuZakuu/ep7-film-hack/issues/7)。基线：[PR #6](https://github.com/ZakuZakuu/ep7-film-hack/pull/6)，`research/e142-container-validation` / `770960ba86da3d9ebd24963500cb264d8b53eae4`。仅私有环境只读静态分析，无设备连接、程序执行、repack 或写入。

**verified：官方下载文件的 size/SHA、五个 OE 块、真实 LZO SquashFS 目录及七个普通文件的选择性提取成功。unknown：ART 滤镜、色彩参数表及主成像处理器。** 没有把关键词或 ELF 架构升级为 ART/主 CPU 证据。

## 输入、复现与边界

用户授权官方只读下载；序列号仅临时输入进程，没有写入文件、报告或 Git，也未回显。下载器补齐 `--serial-env`；最初任务变量缺失，命令在请求前退出 2。用户提供授权输入后进行一次实际下载，官方 metadata 返回 host `dl01.om-digitalsolutions.net` 和 `OLY_E_142_1100_0000_0000.BIN`。附件 32 MiB 传输上限仍存在，但官方路线已解除本任务输入 blocker，见 [历史 blocker](blockers/BLOCKER-e142-attachment-access.md)。

- 机型/版本：E-P7，owner-reported v1.1；原厂文件名与此一致，未独立验证 OEM 数字签名。
- 原文件实测 **111017984 bytes**、SHA-256 **`9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb`**，与用户预期及 PR #6 完全相同。
- 独立 size/SHA 检查通过；默认 OE 检查及 carving 内全文件两次重验通过：5 个块覆盖全文件，每块 checksum residual 为零。加和校验不是数字签名或安装安全证明。
- 原文件、carved segment、完整 listing、提取文件和 readelf 输出都留在 `/tmp/ep7-firmware/`。不上传到 CI、GitHub 或第三方分析服务。

命令与固定工具构建见 [复现步骤](../docs/11-squashfs-private-validation.md)。已有 OE decoder/社区先例来自 PR #6；本轮只加 bounded carving 和 guards，不另写 SquashFS decoder。

## 真实文件系统：verified

block #2 原文件块起点 `0x03200000`，SquashFS 位于**解码 payload 内文件偏移** `0x021367e0`；不是运行时地址，也不是 ART 地址。复用 16-byte lane 变换后按 bytes_used 截取，不能直接用原始文件连续切片替代。

| 项目 | 本轮实测 |
| --- | --- |
| Carved segment | 3393511 bytes；SHA-256 `de0fe0b6ee12013d89f6c0bff455d8c03893f8bd05fc9d8ba5716076897c7f79` |
| 工具 | upstream squashfs-tools 4.6.1，commit `d8cb82d9840330f9344ec37b992595b5d7b44184`；LZO build |
| `unsquashfs -s` | exit 0；SquashFS 4.0、LZO、block size 131072、247 inodes、12 fragments、1 ID、无 xattrs |
| 内部 timestamp | 2020-10-21 14:08:33；文件系统记录，不代表固件发布日期 |
| `unsquashfs -ll` | exit 0；13 directories（含根）、159 symlinks、75 regular files；主要是 bin/lib/sbin/share |
| 选择性提取 | strict-errors、no-xattrs、processors 1、no-wildcards；7 个事先由 listing 确认的普通文件，exit 0；未提取设备节点或选择符号链接 |

目录名称包括 curl、hostapd、dnsmasq、lighttpd 及网络库；**hypothesized** 为 Linux 网络/辅助软件区域。目录名不能证明版本、许可证合规、服务运行状态或完整相机架构。未验证其余 68 个普通文件的数据解压，不声称所有文件都已读过。

以下是少量实际读取的文件 metadata，无原厂内容、完整目录或反汇编：

| 路径 | bytes | SHA-256 | 验证范围 |
| --- | ---: | --- | --- |
| bin/am | 4448 | `fd09e02821ed8695efedfe4c26603d39cd1ee356706a50d32a0d21dc061c82d9` | readelf: ELF32 LE ARM EXEC；NEEDED libisc.so/libc.so.6 |
| bin/bsa_server | 1416200 | `bc66595c4b2491e088ec0db9a9119ec6529ebedf205e497d31a2844277bda95f` | ELF32 LE ARM EXEC；存在 Bluetooth/A2DP/OBEX 字词 |
| bin/linux_status | 124 | `507a745a145c7ea2afccb6e3e3c36ec4fa4e464abe631f79541339c96f409d5e` | 实际解压/读取，非 ELF |
| lib/libisc.so | 8764 | `f9a3f7c003d4ab145b0c7c2ecf8ee33fe13a09ce5fb82da88c260340c85a3be9` | ELF32 LE ARM DYN；NEEDED libc.so.6 |
| lib/libper.so | 4204 | `6094742e8141925788a9a28197ed15db2449760387640313e70eb94c51ac820b` | ELF32 LE ARM DYN；NEEDED libisc.so/libpthread.so.0/libc.so.6 |
| sbin/lighttpd | 212908 | `daa46df12efd0ec0faed5f23c5cd5ff0450ad55bece1f4b6a2e57849b92307c5` | ELF32 LE ARM EXEC；NEEDED libpcre.so.1/libdl.so.2/libc.so.6 |
| share/udhcpc/default.script | 1611 | `0c99e8c051340fce021a2d3824d2e45d3dd29d7ca1b3105c524a3a172891238e` | 实际解压/读取，非 ELF；没有执行脚本 |

GNU readelf 2.44 的 `-h -d` 对五个 ELF 均 exit 0。这是真实文件的 ELF 证据，与 PR #6 原始 magic 扫描的伪阳性不同；**仅描述所选 Linux 文件，不推断 TruePic 主 CPU 或其他块 ISA**。

## ART 调查：有界负面结果，不能排除

两条有限检查：

1. 实际目录路径检查：case-insensitive `art.?filter`、whole-word `lut`、`gamma`、`colou?r.?profile`、`monochrome`、`sepia` 均无候选路径。未发现独立可识别 LUT/profile 文件名。
2. 上述七文件字节检查：whole-word ART/LUT、art[_ -]?filter、gamma、color/colour profile、monochrome、sepia 均 0 次命中。零关键词不排除二进制参数表、资源编号、压缩内容或其他块。`bin/bsa_server` 有 1 个 JPEG 字词，同时有 18 个 Bluetooth、2 个 A2DP、5 个 OBEX 字词；**只支持通信相关候选，不支持 ART 归属**。没有公开原始字符串或代码片段。

`bin/am` 依赖 `libisc.so`，`lib/libper.so` 也依赖 `libisc.so`；静态符号 metadata 有 mmap/ioctl 线索。**hypothesized** 为值得进一步核实的辅助控制边界；没有实证连接到滤镜、成像控制或实时预览。本轮不沿模糊名称扩大逆向。ART/ISP 表示位置仍 unknown，G2 未通过，见 [ART 证据 blocker](blockers/BLOCKER-e142-art-evidence.md)。

## 原创工具与合成验证

提取入口要求 explicit opt-in、expected SHA/size、block index、decoded payload offset；复用全块校验，核对唯一候选及 bounds；同一 read-only fd 再验输入，0600 临时输出、no-replace 发布、失败清理。Git checkout 内只允许 private_samples/，外部私有目录可用。忽略规则不代替发布审查。

**20 tests passed，0 skipped**：含基线测试、guards/跨 chunk/非 lane 对齐/失败清理、环境变量 mock-only 测试，以及 upstream mksquashfs 生成 LZO 树→synthetic OE→carve→-s/-ll→选择性提取的字节精确 integration。截断合成镜像由 upstream 拒绝。CI 仅合成输入。`git diff --check` 通过。上游 GPL 工具及 Debian LZO 依赖只在 work/ 构建，不 vendor 到本 MIT 项目。

## 推荐下一步（本轮不执行）

最有价值的是**版本限定的资源映射实验**：以这个已核对原文件 hash 的其他 decoded 块（尤其 PR #6 的 block #4 resource-like 候选）为范围，先复用已有社区资源格式先例，验证结构化记录/索引及其引用；把可解析资产与公开 ART 模式/资源 ID 对照。JPEG magic、名称或颜色外观单独都不够，必须证明引用链才可报告 ART。

若社区格式先例不足，先查同代 Olympus/TruePic VIII 已验证格式与公开软件通知，或单独提出 libisc/辅助控制边界的只读静态任务；不要凭猜测造资源 parser。可行的体验替代是评估官方 Color Profile 原生参数的表达能力，但需独立受控样张实验，不能承诺任意 LUT 或 ART 替换。G1 passed；G2 unknown；G3–G6 未推进，无设备操作。

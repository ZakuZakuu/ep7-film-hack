# E-P7 T1.2：非网络块资源布局与 ART 关联边界

2026-10-11；[Issue #10](https://github.com/ZakuZakuu/ep7-film-hack/issues/10)。基线是完成 PR 整理后的 main **`c274678f27c481fb2f015ec22237c8f1297d893b`**。机型 E-P7、owner-reported v1.1；相同候选 111017984 bytes，SHA-256 **`9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb`**。本轮复核完整 hash、五 OE 校验和最终输入不变，复用既有私有文件，未重新下载或使用序列号。

**结论：verified 的是 block #4 的规律性资产布局和两个可完整解码的 JPEG；未建立资源索引/记录语义、ART 菜单 ID 或处理调用关系。** 对继续版本限定的资源研究为 conditional，对 ART 实现/补丁为 no-go。两条有限结构假设未建立索引，依照 Issue 的停止条件结束；不以图片外观或字符串补足证据。

## 先处理依赖与评审

[PR #9 review](https://github.com/ZakuZakuu/ep7-film-hack/pull/9#pullrequestreview-5483469214) 的 README 阶段导航已修正，中英文对齐；复现输入/输出统一为 `/tmp/ep7-firmware/` 绝对私有路径。PR #5→#6→#9 按顺序 merge（非 squash，保留原提交）；合并时保留 #5 完整 F01–F15 账本、来源/许可复核、报告和两项测试，另加后续 T1/T1.1 证据及历史 blocker 状态。

#8 的非交互环境输入与缺失变量 guard 已由 #9 的更全面 mock-only 测试覆盖，独有配置/网络指导保留在 `docs/12-codex-cloud-private-download.md`；确认后关闭 #8，没有重复 merge 或删除历史分支。#9 同步 main/retarget 后 22 tests/CI 成功再 merge。详见 [整理记录](pr-reconciliation-2026-10-11.md)。

## Community-first：可复用到什么程度

| 来源 | 证据、适用范围与许可 | 本轮使用 / 不适用边界 |
| --- | --- | --- |
| [CHDK Olympus e/mju/stylus 原帖](https://chdk.setepontos.com/d/2471-olympus-emjustylus-series-fw-analysis) | 历史多个 OLY_E_049/052/059 等编号文件；公开 OE 变换/校验说明与作者的图片/语言块类别报告；不是 TruePic VIII 的验证 | OE decoder 已在 E-P7 独立验证；旧 block type 0x0102 的图片类别仅作对照。资源 extractor 附件被提及，但本轮未读到可复用实现/许可；直接 HTTP 读取返回 403，不重试/运行附件 |
| [DVXuser E-P1/E-P2/E-PL1，2010](https://www.dvxuser.com/threads/e-p1-e-p2-e-pl1-hack-research.217453/) | 作者描述 OlympusFwTool resource extraction 与 OSD/font 分析；例示 E-P1 旧文件编号 068，源代码附件声明可得，未确认本轮可得完整源代码/重用许可 | working-tool **author-reported**，讨论中的字体格式/加载地址不迁移到 E-P7；没有已验证的 ART 表或 TruePic VIII 索引格式 |
| [stv0g OM-D 协议](https://0l.de/projects/omd/) | 作者的 E-M10 1.2 网络协议描述、libqt-omd 链接；不是内部固件资源格式 | 能解释此前网络区研究方向，不能提供 ART firmware 索引；没有相机通信 |
| [固定社区矩阵](../docs/10-prior-art-matrix.md) | 保留原审阅 commit：Ricoh e0e0b69、Fuji 754acff、Nikon de8019e、Olympus Wi-Fi 364dfcd 等及许可边界 | 这些源码对应不同品牌/协议；未发现其中有可直接适用的 Olympus 内部资源格式。没有把 Ricoh addresses/Canon/Nikon 表移植或复制未授权代码 |

两组定向检索与上述原始资料复核未给出本轮可验证的近代 Olympus/TruePic VIII 索引实现；这是有限搜索结果，**不是断言全社区不存在**。因此只做 Issue 许可的两个小结构假设，不构建 proprietary parser。

## 四块真实汇总：verified metadata

以下偏移均为原文件块起点或 **decoded payload-relative offset**；不是运行时地址。熵对整个 decoded payload 计算，包含填充，不识别代码/加密/压缩或处理器架构。

| block | 原文件块偏移 | bytes | raw ID / LE 值 | whole entropy bits/byte | 零占比 | trailing run | 未验证 magic 计数 |
| --- | --- | ---: | --- | ---: | ---: | --- | --- |
| #0 | 0x00000000 | 26214336 | 0001 / 0x0100 | 5.652653 | 14.5374% | FF × 5122814 | JPEG 5、RIFF 59 |
| #1 | 0x01900000 | 26214336 | 0101 / 0x0101 | 4.519067 | 41.1789% | zero × 4123132 | 所查 7 类均 0 |
| #3 | 0x05d20000 | 262080 | 0e01 / 0x010e | 4.655204 | 23.0823% | zero × 41920 | 所查 7 类均 0 |
| #4 | 0x05d60000 | 13107136 | 0201 / 0x0102 | 5.867348 | 38.0893% | zero × 4689418 | JPEG 221、PNG 1 |

所查 magic：JPEG SOI+FF、PNG signature、RIFF、ELF、SquashFS、gzip、ZIP；未验证 PNG/RIFF 或 #0 的五个 JPEG-like 命中。#0 JPEG hits 在 mod16 分散，没有连续间隔对齐模式。#1/4 的 ID 与旧社区语言/图片类别一致只是 **hypothesized 类别对照**，不是 E-P7 block 功能定义。

#4 的 221 个 SOI-like starts 全部满足 `offset % 512 == 480`（0x1e0），亦为 16-byte aligned，220 个相邻 start gap 均为 512 的整数倍；最常见 gap 20992 bytes（18 次）。这是 **verified 布局规律**。hypothesized 为对齐资产打包；不证明 asset count=221、记录头长度、sector 意义或某个滤镜数量。210/221 个 start 的前 32 bytes 全零，反驳“每个 JPEG 前都有相同非空 32-byte 记录头”的简单解释。

## 两条独立结构假设与反证

### H1：每资产前存在简单 u32 长度记录

在 #4 全部 221 个 starts 前 4/8/16/32 bytes 检查 LE/BE u32，要求 numeric value 96–1000000 且不越出 payload。LE -4 候选 0，-8 为 2，-16/-32 各 1；BE 所有距离均 0。零星 numeric candidates 并没有组成 repeated count/length/next-offset 关系；两个独立验证的 JPEG 长度也未支持统一头。

**结果：该具体直接长度布局未建立。** 没有泛化成“无任何记录”；可能是固定槽位、索引在别处、短整数/相对单位或未知编码，但本轮不逐项扫猜。

### H2：块内有直接 u32 start offset/address 索引

仅在 #4 内搜索全部 SOI starts 的 4-byte aligned LE/BE 精确值，分别使用 decoded payload-relative offset 与 header load-candidate `0x467e0000` 加 offset。该 header field 没有运行时证据，测试它只是旧社区约定的可证伪候选。

只有 LE relative 单个命中：word 所在文件内 payload offset `0x003f03e4`，数值等于候选 start `0x000081e0`；其他三种形式 0。单个数值相等可能偶然，并没有 coherent table/order/count 或已验证调用；不能命名 pointer。#0 的五个 magic starts 同样四种搜索为 0，#1/3 无 targets。

**结果：没有建立 block-local 直接 start 索引。** 不排除索引引用 record start 而非 SOI、跨块索引、压缩/偏移单位或未证明的地址空间；这些是下一任务的候选，不能当结论。

## 两个资产独立检查，不做 ART 归属

只选择 #4 第一个、第二个候选；限至本候选后首次 EOI（非通用 JPEG parser），由成熟 **Pillow 12.3.0** `Image.open(...).verify()` 及重新 open 后 `.load()` 分别完成结构/像素解码检查，未写图片、未显示或按外观分类。

| #4 decoded payload start | end exclusive | bytes | mature decoder result |
| --- | --- | ---: | --- |
| 0x00002fe0 | 0x00008045 | 20581 | JPEG、640×480、RGB；verify/load 成功 |
| 0x000081e0 | 0x0000d252 | 20594 | JPEG、640×480、RGB；verify/load 成功 |

下一 start 分别 0x81e0 / 0xd3e0，与 end 之间间隔 411/398 bytes；只证明非重叠和布局，不自行把间隙定义为头/尾/padding。没有检查余下 219 个 SOI-like starts 或 PNG。

三个 milestone 严格分开：**asset identified = 两个；ART-linked = 0；image processing-linked = 0。** 没有菜单 ID、索引记录意义、版本限定调用引用或参数表。图像能解码和旧 ID 对照不能说明它是滤镜图标，更不能说明滤镜处理实现属于此块。

## 复现与发布范围

原创小工具 [probe_oe_resources.py](../tools/probe_oe_resources.py) 复用 OE 验证/变换；只读、预期 size/SHA guard、每块上限 64 MiB、JPEG-like 候选上限 1024、前后输入检查；内存解码，不写 blobs/raw strings/assets，只输出 aggregate metadata。精确命中只是 numeric coincidence，输出明确 unvalidated/no index。合成用例验证偏移单位/对齐 outlier、endianness、重复 targets、不对齐 false matches、u32 溢出、越界长度和 magic false positive。

```bash
umask 077
mkdir -p /tmp/ep7-firmware/t12
python3 tools/probe_oe_resources.py \
  /tmp/ep7-firmware/E142_EP7_firmware_download.BIN \
  --expected-size 111017984 \
  --expected-sha256 9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb \
  > /tmp/ep7-firmware/t12/resource-probes.json
SQUASHFS_TOOLS_DIR="$PWD/work/squashfs-upstream/source/squashfs-tools" \
  python3 -m unittest discover -s tests -v
```

独立图像检查命令算法：通过既有 `inspect/check_expected` 校验输入；read block #4 payload→`decode_chunk`；只对 offset 0x2fe0/0x81e0 截至 `find(b'\xff\xd9', start+3)+2`，内存 BytesIO 交给 Pillow verify/reopen/load；打印仅 format/dimensions/offset/byte length，无图片/像素/原始字符串。初步私有命令的 trailing-run 计数为 `len(data)-len(data.rstrip(b'\x00'))` 或 FF；没有区段 parser。

**26 tests passed，0 skipped**，包含 4 个新合成用例及既有 LZO integration；CLI 实际私有运行和输入再验证通过，`git diff --check` 通过。公开仅工具/合成测试/脱敏报告；原厂文件、图像、decoded payload、完整 candidate list 与公共页面缓存均不提交。

## 决策、blocker 与最小下一实验

G1 passed；G2 unknown；G3–G6 未推进。已有规律支持资源布局研究 **conditional**，不能授权资源修改或 ART patch。两个假设没有 coherent index，停止扩大扫描，见 [本轮 blocker](blockers/BLOCKER-e142-resource-index.md)。

最值得验证的下一实验：**先取得并审阅旧 Olympus resource extractor 的真实源代码与许可/格式说明**，确认它引用 SOI、record start 还是 slot-relative units；只在 E-P7 已观察的两个 offset 上测试那一明确关系，再到其他块查该已验证引用形式。若 source 不可得，先补证据，而不是对所有 base/stride/ISA 无限扫猜。单独的官方 Color Profile 表达能力/样张实验仍是保留机内 JPEG 的替代路线；它不等于 ART 替换。没有厂商数据上传、OEM code 执行、相机通信或固件修改。

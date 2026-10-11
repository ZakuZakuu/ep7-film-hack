# E-P7 T1.1：SquashFS 工具验证与真实样本访问状态

日期：2026-10-11；任务 [Issue #7](https://github.com/ZakuZakuu/ep7-film-hack/issues/7)。基线为 [PR #6](https://github.com/ZakuZakuu/ep7-film-hack/pull/6) 的 `research/e142-container-validation`，commit `770960ba86da3d9ebd24963500cb264d8b53eae4`。本轮仅只读静态工具研究，无设备通信或写入。

**当前结论：已完成 upstream LZO 工具与受保护的 OE→SquashFS 提取入口的合成验证；附件传输受限，且官方下载路径的 `EP7_SERIAL` 未注入当前进程；本轮未能读取真实 E-P7 输入，因此未验证真实文件系统目录/文件，也未开展 ART 资源调查。** 不用合成测试代替真实固件证据。Issue #7 的真实样本验收仍未完成。

## 真实输入与证据等级

用户授权私有静态分析的候选：E-P7 / owner-reported v1.1，111,017,984 bytes，SHA-256 `9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb`。这是本轮**预期值**，并非新测量值。PR #6 的结果是此前私有环境的实测记录，本轮只复核该报告/源码，不冒充重新跑过真实文件。

| 问题 | 可用证据 | 本轮判定 |
| --- | --- | --- |
| 真实原厂文件大小/哈希 | 用户及 PR #6 记录 | prior-session verified；本轮未读取/复测 |
| 五个 OE 块、历史 XOR/permutation、加和校验 | PR #6 的真实记录；复用其 decoder，原 8 项合成测试通过 | 本轮 verified on synthetic；真实重验待输入可访问 |
| block #2 的 SquashFS v4/LZO 候选 | PR #6：decoded payload+`0x021367e0`，247 inodes、block_size 131072、bytes_used 3393511 | 真实 superblock 是 prior-session verified；目录/内容仍 unknown |
| upstream unsquashfs 的 LZO 能力 | 固定上游源码构建；help 列 gzip/lzo；合成 LZO 树真实列出并选择性提取、逐字节匹配 | verified locally on synthetic filesystem |
| ART、Color Profile 或成像组件 | 无本轮真实目录/文件输出 | unknown；没有找到或排除 ART，未声称滤镜地址/参数表 |
| OEM 签名、安装、恢复 | 无证据 | unknown / no-go；加和校验不等于数字签名 |

`0x021367e0` 是 **block #2 解码 payload 内的文件偏移**，不是相机运行时地址，也不是 ART 地址。由于变换是 16-byte lane permutation，不能将解码位置简单当成一个可直接 memcpy 的原始连续文件切片。提取器先复用 lane decode，再按精确 bytes_used 截取。

## 当前为何不能读取真实内容

私有附件的受支持下载工具返回：`file exceeds the executor transfer limit of 32 MiB`。任务环境 `/workspace`、`/mnt` 没有该文件挂载，`/mnt/data` 不存在。没有可读文件，就无法计算新哈希/重验 OE 或运行真实 `unsquashfs -s/-ll`。完整失败、边界与可行替代见 [BLOCKER-e142-attachment-access](blockers/BLOCKER-e142-attachment-access.md)。用户随后授权官方下载器路径；补齐其 `--serial-env` 参数后，指定命令以退出码 2 停在请求之前：`Serial environment variable is unavailable or empty; no request made.` 当前进程的变量存在性检查为 false，未打印或记录序列号。没有官方服务响应或下载文件，因此不能判断网络、实际 hash 或文件系统是否有问题。缺失绑定已报告，未重试。

这是输入访问限制，**不是固件校验失败、SquashFS 损坏或 LZO 不支持**。

与 PR #6 不同，本轮已经解决成熟 LZO 工具缺失问题：不再用不支持 SquashFS 的 libarchive，不开发自制文件系统解码器。

## 本轮实现与已完成验证

1. `tools/inspect_olympus_oe.py` 默认依旧仅检查/输出 metadata。显式 `--extract-squashfs` 必须同时给出 local OEM output opt-in、期望 SHA-256/长度、块索引、decoded payload offset。
2. 复用原 OE 变换、全文件哈希与每块加和校验。输出前检查候选唯一性/bytes_used/边界，允许非 lane 对齐的 FS 起止；对同一个 read-only descriptor 再验证全输入，防止检测到输入变化后发布 artifact。
3. 只输出 bytes_used 的私有 SquashFS segment，不输出其他块、原厂代码片段或镜像安装包。临时输出权限 0600，失败清理；通过所有 guards 后以 no-replace link 发布，不覆盖文件/符号链接。Git checkout 内只允许 `private_samples/`，外部私有目录也可用。这些保护不能替代发布前逐项审核或防止人为 `git add -f`。
4. 提取只证明 bounded carving 成功，**目录/文件必须另由 upstream unsquashfs 检查**。没有 decoder/FS patch/repack/installer 功能。全部原创增量；没有复制历史社区或 GPL 上游实现到 MIT 项目。
5. 十二项新增测试（另含两项 `--serial-env` mock-only 用例：缺失/不合法值请求前停止，合成值不出现在输出中）（含空 OE 拒绝）包括 opt-in/hash/size/index/offset、越界、其他块损坏、已有输出/符号链接、Git 输出位置、跨 1 MiB 边界、输入不变/0600/失败清理、CLI，以及成熟工具 LZO integration。integration 在临时目录用 upstream mksquashfs 生成一个 131072 block size 的纯合成树，封装成两个合成 OE 块，再 carve、`-s`、`-ll`、选择性提取并比对两文件完整字节；截断镜像由 upstream 拒绝。

执行：

```bash
SQUASHFS_TOOLS_DIR="$PWD/work/squashfs-upstream/source/squashfs-tools" \
  python3 -m unittest discover -s tests -v
python3 tools/inspect_olympus_oe.py --help
git diff --check
```

结果：**20 tests passed，0 skipped**（包括 8 项基线测试），CLI 帮助及 diff check 通过。仅在没有 mksquashfs/unsquashfs 的环境，integration 有明确 skip；CI 安装 upstream squashfs-tools 对合成输入执行 integration，不访问 OEM 文件或私有附件。

## 成熟工具来源、许可和可重现步骤

实际使用 squashfs-tools **4.6.1**，tag `4.6.1` 解引用 commit **`d8cb82d9840330f9344ec37b992595b5d7b44184`**。版本、支持能力与固定构建方式见 [upstream setup and private validation](../docs/11-squashfs-private-validation.md)。上游 GPL-2.0-or-later（unsquashfs/mksquashfs version 输出及源码），仅在私有 work 中独立构建/运行，不 vendor、链接进或重许可到本仓库。LZO 依赖从 Debian 官方包取得，亦不提交。

本轮 build 输出的本地 binary SHA-256（不是 OEM/样本哈希，换编译器/路径会改变）：

- unsquashfs：`94117bee5d097dac3f9478be427c689ccc82218aa2d01126e3017e4003e39f04`
- mksquashfs：`bd4f435e45c2a228378e20902f4270b0af4fa88cb92bbfb9f554ba1747c0b3a1`

只启用 gzip/LZO；足以测试 PR #6 的 LZO 候选，不声称支持所有压缩器/未来格式。

## 后续最有价值的验证（当前未执行）

1. **先确认已授权的 `EP7_SERIAL` 在任务进程中的绑定，或恢复原始私有输入访问**，核对完整长度/哈希。两者任何一个不符立即停止；符合后检查五 OE blocks，并 carve 唯一候选。输入仅在私有环境保留，公开只报告 metadata。
2. **运行真实 `unsquashfs -s` 与 `-ll`**，确认 v4/LZO 和真实目录，metadata 能读取不等于所有压缩数据可读取。对 listing 中存在的少量普通文件选择性提取，核对读取成功、文件类型和一般职责；任一 corruption/incompatible 错误即记录并停止，不屏蔽错误。
3. **只沿实测目录产生的线索研究 ART**：先判断内容更像 Linux 启动/网络辅助文件还是成像资源；若出现明确 profile/filter 参数或成像模块，再记录其文件哈希、文件内偏移/结构和对照解释。关键词/名称只是候选，需资源 ID/调用引用才可关联 ART；未见命中也不证明 ART 不在其他块/封闭 ISP 中。不能盲猜地址、扫描构建完整补丁或运行提取的二进制/脚本。

最值得做的是步骤 2 的真实目录和少量实际文件读取，先确定这个 3.39 MB 候选究竟包含什么，而不是继续猜 ART 地址。当前 G2 未通过，G4/G5/G6 未推进。取得可访问输入后可直接在任务环境继续，不要求用户搭建本地 Codex。

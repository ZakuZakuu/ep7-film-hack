# BLOCKER：真实 E-P7 输入不可访问（附件上限与缺失环境变量）

日期 2026-10-11；Issue #7 / T1.1。目标：重新验证真实文件哈希/OE，进而用 mature unsquashfs 验证目录/实际文件和少量 ART 线索。原厂版本 owner-reported E-P7 1.1；期望 111,017,984 bytes / SHA-256 `9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb`。

## 有界访问检查与确切失败

1. 请求受支持的私有附件下载，工具返回 **`file exceeds the executor transfer limit of 32 MiB`**；此工具没有 Range/chunk 参数。约 106 MiB 的附件没有成功传入工作区。不能尝试自行拼造存储 URL 或绕过访问限制。
2. 检查当前 `/workspace`、`/mnt` 的候选文件/挂载与 `/mnt/data`；没有该固件，后者不存在。没有复用上一环境的假定文件路径或下载上游 proprietary 镜像代替用户样本。

3. 用户随后授权使用官方下载器及 `EP7_SERIAL`。当前进程仅检查变量是否存在，结果为不存在；未读取或输出任何序列号。原下载器没有 `--serial-env`，本轮补齐该参数与 mock-only 测试后执行用户指定的命令：

   ```bash
   python3 tools/ep7_firmware_fetch.py --serial-env EP7_SERIAL --output-dir /tmp/ep7-firmware
   ```

   **退出码 2：`Serial environment variable is unavailable or empty; no request made.`** 在创建输出目录、网络请求和真实数据下载之前停止。没有观察到网络错误或 hash mismatch，不能把变量缺失解释为官方服务器不可用。没有反复重试。

已请求确认任务环境的变量绑定，未索取变量值；未调用 OEM 更新后端或要求启动相机更新。

## 阻塞含义

PR #6 已在此前私有环境验证过候选的 OE/checksum/superblock，G1 的既有证据没有被这个失败推翻。但 **本轮访问缺失**，真实数据检查及目录/文件验收未完成，G2 ART 仍未知。

这是传输能力/挂载/环境变量绑定缺失，不是损坏、加密、非法获取或 SquashFS 不兼容的结论。上游 4.6.1 + LZO 的合成端到端验证已经成功，成熟工具缺失问题已解决；不重复尝试 unsupported libarchive，也不编造 ART 文件或写自制 FS decoder。

## 最小可行替代

- 优先将用户已授权的 `EP7_SERIAL` 绑定到当前任务进程（不要发送值或写入仓库），再执行上述命令；成功取得文件才开始 size/SHA 校验。缺失变量、网络失败、hash 不符或解包失败即停。
- 或让同一任务私有环境获得现有文件的可读路径，或提供有权使用的下载链接；完整下载后仍核对预期 size/SHA，任何不符停止。不要用 public GitHub repo/issue/Actions artifacts 中转。
- 若只能用当前私有附件工具，可由文件持有人拆成 **每段不超过 32 MiB** 的四个有序原始字节分片（例如每段 30 MiB），再在任务私有环境按顺序合并并核对完整 hash。使用系统 split/cat 等成熟工具；不用自制上传服务，不要求搭建本地 Codex。也可用标准归档分卷，但必须保证每个可传入分卷低于工具限制，完整复原后的 hash 与原文件一致。

等待可访问真实输入前，交付工具/合成测试/复现步骤与此 blocker；研究 PR 标 draft，Issue #7 的真实内容验收不声称完成。真实输入恢复后，最有价值的第一步仍是 `unsquashfs -s`、`-ll` 与少量选择性文件读取。无实机写入、安装镜像或自定义 LUT 开发。

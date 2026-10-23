# T20 · E-P7 COLOR 最小 H/L 挂钩：S0 阻塞

- **做了什么**：2026-10-23，初始基线为 main `362339e07a89`；机主合并 PR #50 后，已同步至 main `aebe5ca2274a`，完整读取新版 AGENTS.md，并重新核对 Issue #49 正文与评论。上游位于忽略目录 `work/upstream/oly_fw_analysis/`，HEAD 为 `539fcf1fa9eda5fdef8ede4deeab94a4691d94c3`、工作树干净。完整阅读该提交的 [EMULATOR.md](https://github.com/fishcu/oly_fw_analysis/blob/539fcf1fa9eda5fdef8ede4deeab94a4691d94c3/docs/tooling/EMULATOR.md) 与构建器，仅下载一次其指定的 GNU 源码包并离线检查，未复制上游代码、汇编或文档进入交付。

- **结果**：S0 **未通过**。[指定源码包](https://gnu.googlesource.com/binutils-gdb/+archive/87ffb882e0f4d73401a0746177ffabb8e8bbe4ac.tar.gz) 下载成功，大小 **69104663 bytes**，gzip 完整性通过；整包 SHA-256 预期 `a5e7cd02f844bb2873c25e0ac8e9a5b50a72c3e8e6570a6b7821d2e4c21178ad`，实得 `b0b06179b0aff88df98978552431d86f16045e2f993faa3d1f98350fb7429865`。离线读取包内 `sim/mn10300/interp.c`、`mn10300.igen`，其 SHA-256 分别与上游构建准备器的两个固定值相符，但不代表整个源码树通过校验。没有放宽检查、重新下载或换源。未构建 binutils 2.45 / 模拟器，未进入 S1–S7，未获取、执行或修改原厂固件，未生成测试/恢复 BIN，未操作相机。

- **风险与未知**：整包差异原因未知；压缩或归档元数据差异只是可能解释，不能据此接受。`github.com` 与 `gnu.googlesource.com` 本次均可访问，无证据表明需要新增域名放行；`ftp.gnu.org` 尚未测试。新版规则已生效，但 Issue #49 的 S0 要求以及固定上游文档的源码包校验值未变，此阻塞与旧 ART 闸门无关。没有完成工具链或 H/L 可行性验证，不能给出可执行实拍安装方案。

- **需要机主决定的事**：为 S0 提供与预期 SHA-256 匹配的固定源码包，或经独立来源核验后明确更新 Issue 的源码身份要求。当前包仅留在私有 `/tmp/ep7-t20/cache/`，未解包构建。解决后从 S0 继续；本 PR 只记录阻塞，不代表批准后续安装或应当放宽哈希要求。

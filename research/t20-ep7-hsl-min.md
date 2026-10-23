# T20 · E-P7 COLOR 最小 H/L 挂钩：S0 内容核验

- **做了什么**：2026-10-23，以 main `aebe5ca2274a` 的新版 AGENTS.md 为准，核对固定上游 `539fcf1fa9eda5fdef8ede4deeab94a4691d94c3`；按机主新指令尝试两处指定的 Git 来源；把已有压缩包安全解到全新私有目录，以 `git init`、`git add -A`、`git write-tree` 核对树，再离线核对差异文件和两个核心文件。没有重下压缩包、修改上游工具或制作来源标记。

- **结果**：S0 仍未通过指定的树哈希检查，依“任何一项不一致就停止并报告”未开始构建或 S1。GitHub 的 `bminor/binutils-gdb` 返回 Repository not found；授权的 Sourceware 备用来源成功，无需新增域名放行。取到的提交精确为 `87ffb882e0f4d73401a0746177ffabb8e8bbe4ac`，参考 tree 为 `059d50a3cc76bd13dc10f21023863674e6da515c`；归档目录经 `git add -A` 得到 `36c3f8c7cb6ec270586f05ee78e955cbf9e79fa2`。树差异仅为 10 个文件未入索引；它们都在归档中，且各自 Git blob 哈希与参考提交一致。两个指定文件的 SHA-256 也通过：`interp.c` 为 `f6c34c6c81ff67bda52d6b57d0ea47954587e36908923cd7e4e59a90424cd37b`，`mn10300.igen` 为 `355754c61879dc24bf6128bbba5a7931355731000e8cb213082b9b9cd4df0129`。

- **风险与未知**：本次树差异来自源码自带 `.gitignore` 使普通 `git add -A` 漏收文件，不能称为这些文件的内容不一致；但尚未生成包含所有文件并精确匹配的验证树，不能声称整树校验完成。源码包大小 69104663 bytes，实际 SHA-256 为 `b0b06179b0aff88df98978552431d86f16045e2f993faa3d1f98350fb7429865`，上游记录为 `a5e7cd02f844bb2873c25e0ac8e9a5b50a72c3e8e6570a6b7821d2e4c21178ad`；服务器动态归档的字节稳定性不再作为源码身份判据。未构建 binutils 2.45 / 模拟器，未获取、执行或修改原厂固件，未生成 BIN，未操作相机。

- **需要机主决定的事**：允许在临时验证目录使用 `git add -f -A`，把归档中已有的忽略文件完整入树，再要求 `git write-tree` 精确等于参考 tree；不改任何源码或忽略规则。只有这一检查通过才编写原创包装脚本、记录真实来源清单并继续 S0/S1。无需重新提供 E-P7 固件或另一个源码包。

## 核验细节

参考来源：<https://sourceware.org/git/binutils-gdb.git>。上游方法：[EMULATOR.md](https://github.com/fishcu/oly_fw_analysis/blob/539fcf1fa9eda5fdef8ede4deeab94a4691d94c3/docs/tooling/EMULATOR.md)、[prepare_mn103_sim.py](https://github.com/fishcu/oly_fw_analysis/blob/539fcf1fa9eda5fdef8ede4deeab94a4691d94c3/tools/prepare_mn103_sim.py)。仅阅读和引用，无第三方源码交付。

树比较：`GIT_ALTERNATE_OBJECT_DIRECTORIES=/tmp/bgdb-ref/.git/objects git -C /tmp/bgdb-archive diff --name-status 059d50a3cc76bd13dc10f21023863674e6da515c 36c3f8c7cb6ec270586f05ee78e955cbf9e79fa2`。结果仅 10 个 D，无其他差异。逐项用 `git hash-object --no-filters` 对比参考提交的 `git ls-tree` blob；10/10 相符。`git check-ignore -v` 确认全部被忽略。

| 未入索引的归档文件 | 命中的源码内忽略规则 | blob 核对 |
| --- | --- | --- |
| `binutils/sysroff.info` | 根目录 `*.info` | 一致 |
| `gdb/gdb-gdb.gdb` | `gdb/.gitignore` 的 `/gdb-gdb.gdb` | 一致 |
| `gdb/testsuite/gdb.base/gdbinit-history/unlimited/.gdbinit` | 根目录 `.gdbinit` | 一致 |
| `gdb/testsuite/gdb.base/gdbinit-history/zero/.gdbinit` | 根目录 `.gdbinit` | 一致 |
| `gprof/.gdbinit` | 根目录 `.gdbinit` | 一致 |
| `ld/testsuite/ld-scripts/libpr33265-1.a` | 根目录 `*.a` | 一致 |
| `ld/testsuite/ld-scripts/libpr33265-2.a` | 根目录 `*.a` | 一致 |
| `ld/testsuite/ld-scripts/libpr33265-3a.a` | 根目录 `*.a` | 一致 |
| `ld/testsuite/ld-scripts/libpr33265-3b.a` | 根目录 `*.a` | 一致 |
| `ld/testsuite/ld-scripts/libpr33265-3c.a` | 根目录 `*.a` | 一致 |

私有现场保留于 `/tmp/bgdb-ref/`、`/tmp/bgdb-archive/`、`/tmp/ep7-t20/cache/`；忽略目录 `work/t20/s0-tree-check.json` 记录逐项 blob 与规则。下一次应复用本次下载和 Git 参考，而非重新下载动态归档。建议的补齐索引步骤尚未执行。

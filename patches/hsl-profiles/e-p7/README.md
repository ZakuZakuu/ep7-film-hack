# E-P7 1.1 · T24 常量配方 v2（待审查，尚未实拍）

这是独立于 T20 的原创候选实现。参考方法只读/运行自 [fishcu/oly_fw_analysis@539fcf1](https://github.com/fishcu/oly_fw_analysis/tree/539fcf1fa9eda5fdef8ede4deeab94a4691d94c3)，没有复制其代码、汇编或文档。原厂输入严格固定为 111017984 字节，SHA-256 `9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb`。

`hook.s` 接管原厂选择器的调用点 `0x603b14f3`，完整调用原选择器后，只在默认 COLOR 且请求/操作记录/job/图像上下文关系通过检查时，选择编译常量。不会读取全局当前配置或设置存储，不会保存 H/L，也不会修改菜单。它不能与 T20 包叠加；输入必须是精确原厂文件，T20 文件和哈希保持不变。

| 配置 | 常量变化，其余 22 或 24 个 H/L 值显式写 0 |
| --- | --- |
| COLOR1 | 黄色关联色区 H +3 → 原生 −3000 |
| COLOR2 | 蓝色关联色区 L −5 → 原生 −200 |
| COLOR3 | 红色关联色区 H −3 → 原生 +3000；绿色关联色区 L +3 → 原生 +100 |
| COLOR4 | 全部为 0；对应相同原厂 COLOR4 设置的中性 H/L |

常量表是 4 × 24 个 i16，共 192 字节，按物理记录交错排列 H/L；轮盘顺序及换算沿用 T20 已核对的规则。色区名称是近似响应区域，不能当作严格 RGB 色相区间。不会改变原厂 S、LUT 或其他字段。

## 已验证边界

- 请求完成回调 `0x60355fd4`，嵌入请求 `job+11364`，操作记录 `job+14576+i*56`，`i=0…15`，记录的 parent 指回 job。
- 已核对的两种 job 头回调为 `0x603e7b83` 和 `0x603e9631`；`job+8 → 图像上下文+28 → 设置快照`。快照原始模式 +24053 必须为 11，配置 +24083 必须为 1…4。
- 紧凑构造调用点 `0x60321ea8` 及其他未知回调/布局保持原厂行为。第二种回调不自动等于已验证的 RAW 编辑工作流。**尚未证明所有预览、连拍与 RAW 编辑都满足上述关系，也未重放相同 S 下的菜单变更到新请求调度。**
- 相同 S 时原厂默认分支仍构造 HSL；原厂后续打包器无条件置系数上传位，两处 ISP 系数窗口均已模拟核对。无需修改 LUT 脏标志。
- 借用 32 字节临时栈，恢复所有借用寄存器和 PSW；不使用硬件循环或乘除法，保留 LIR/LAR。修复绕接调用的返回槽及可能保留进入调用地址的 MDR，实际与合成对照均检查全部模型寄存器和有效调用栈。
- 代码和常量共 460 字节，加载段 2 尾部前留 64 字节、后留 68 字节。原生加载/重载、12 个初始化回调及正向越界反证均通过；这不是完整 DMA/缓存/并发安全证明。

## 本轮复验：不输出更新包

Linux / WSL 的工具环境仍用 `bash tools/setup_t20_environment.sh`。原厂分析探针另需 Pillow（本环境已有），只用于排除代码空间字面量扫描中的已编码图像数据误报，不调查 ART。

```sh
umask 077
python3 tools/ep7_t24_probe.py \
  --upstream work/upstream/oly_fw_analysis \
  --stock /tmp/private-stock.BIN --out /tmp/ep7-t24-private-check
python3 patches/hsl-profiles/e-p7/build.py \
  --upstream work/upstream/oly_fw_analysis \
  --stock /tmp/private-stock.BIN --verify-only
```

`--verify-only` 校验原厂容器、原始修改范围、源码与汇编哈希，再分段计算“编码后的主组件 + 原厂未变尾部”的预期整包哈希；不创建安装/恢复 BIN。哈希及独立构建入口已提交，但**本轮不运行实际输出构建**。普通构建仍要求机主另行授权，并提供仓库外不存在的私有 `--out`；输出与 T20 一样分为 `install` / `restore-stock`，内部版本仍为 1.1。

所有适用范围、快照缺口、存储结论及机主 B2 方案见 [T24 报告](../../../research/t24-profiles-snapshot-storage.md)和[证据](../../../research/t24-profiles-snapshot-storage-evidence.json)。本轮不连接相机、不写设置、不生成或发送 v2 更新包、不进入 T25；是否实际构建和实拍由后续审查决定。

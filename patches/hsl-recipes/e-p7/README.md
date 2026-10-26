# E-P7 1.1 v4 · EP71 配方存储与逐值 Wi-Fi

v4 替代 v3 的常量数值来源，保留图像所有者配置快照及紧凑请求的当前配置身份规则。H/L 从原厂 COLOR 类型记录更新时发布的 RAM 镜像读取。相机端逐值应用，完整配方校验、备份、差异写入与回读由 T26b 负责；没有 40 值事务。

只适用原厂大小 111017984 字节、SHA-256 `9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb` 的 E142 1.1。来源参考固定 [fishcu@539fcf1](https://github.com/fishcu/oly_fw_analysis/tree/539fcf1fa9eda5fdef8ede4deeab94a4691d94c3)，实现为本仓库原创，未复制上游代码。

本轮没有安装文件。复现离线检查：

```bash
bash tools/setup_t20_environment.sh
python3 tools/ep7_t25_v4_probe.py --upstream work/upstream/oly_fw_analysis \
  --stock /tmp/private-stock.BIN --out /tmp/ep7-v4-check
python3 patches/hsl-recipes/e-p7/build.py --upstream work/upstream/oly_fw_analysis \
  --stock /tmp/private-stock.BIN --verify-only
```

原厂数据、执行窗口、调用桩及轨迹只进入私有 `/tmp`。放置引用分类复用了 Pillow，完整 SquashFS 数据与既有验证哈希核对，没有自行实现解压器。生产构建器仅使用固定上游的容器工具与 GNU 2.45；未更改 T20 setup。

预期 v4 整包 SHA-256：`719b57c4fa0b94da60d73f0ed70b0d5dcd536c970e44054152a63b55d30a59e6`。恢复原厂的预期哈希为上述输入哈希；T20/v2/v3 清单和源码均独立保留。生产构建器正常输出功能供机主另行授权本地使用，本轮只运行 `--verify-only`。

镜像初始化为零，使用 uncached 别名，每个 H/L 对以一个对齐 u32 发布。发布器只读经原厂元数据与 API 对照确认的 part 1 范围，精确检查 ACTIVE 基址；成像函数不读 ACTIVE。H/L **写入**仍调用原厂 part API，再经过原 S 的正常注册 setter、COLOR 刷新与通知；没有 raw setter 写 H/L。相机侧保存时机与 NVS 行为仍需 B4，HTTP 200 不代表持久化成功。

详细命令、范围、错误与超时语义见[正式协议](../../../docs/wifi-recipe-protocol.md)。模拟 RTOS 投递、HTTP 响应和部分 UI 消费者不能替代真实调度、无线或 ISP 像素验证；不承诺导入期间整槽快照或每帧一致性。

## B4 · 仅由机主审查后选择执行

1. 先保存需要的设置、备份照片、充满电，确认机身及原件是 1.1。机主另行决定是否本地构建/安装；核对清单哈希，不能混用 T20/v2/v3/v4。
2. 未写入时四档 H/L 应中性，原 S/影调/暗角保留。比较取景、拍后回看和最终 JPEG；同 S 切换也应重新使用正确槽。
3. 在 PASM、原厂私人 Wi-Fi 下，用 T26b 先 discover、读取四槽并保存备份，再向一槽导入明显但有界的 H/L、S、影调、暗角组合；完整回读 40 值，确认其他三槽没变。白平衡与曝光建议手动设置。
4. 比较 H 正负方向、L 的非线性档位、三段影调的区域以及暗角正负方向；使用中性对照和相同拍摄条件。观察镜像发布是否同时覆盖取景、回看及 JPEG。
5. 正常保存并关机重开后重新读取、拍照；再分别测试单项重置、全重置中性，Myset/自定义模式保存与召回。**不要主动断电测试设置写入**；这些项目尚未离线证明。
6. 如模拟 Wi-Fi 断连，只中断连接；工具应停止、不自动重试/回滚。机主重新连接后先只读核对，再明确决定还原备份；不能把迟到的写入误当已取消。
7. 机主最后选择是否恢复已验证原厂文件，核对残留 part 1 没有改变原厂显示/设置/成片。恢复固件不等于清空设置；异常、重启、错误回读、不同槽被改动时立即停止写入，保留私有日志并按既有原厂恢复流程处理。

以上是待验证清单，不是实拍成功报告。工具不会连接、控制或刷写相机。

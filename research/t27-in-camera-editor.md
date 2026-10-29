# T27：GUI 提交已贯通，编辑原型尚不能发布为 v5a

任务没有完成：缺的是新增代码空白区的可靠放置证明，没有可安装的 v5/v5a。
PR #76 的同步对象阻塞已解除，真实子控件能够经过原厂忙闲判断，把 H/L 写入 v4 的分部存储并发布。
删除键、轴文字及当前轴的编辑原型已实现；未改色轮生产路径，真实画面与按键手感没有验证。
本轮只交付可重放的研究原型，不提供安装文件，也不安排机主刷入该原型。

- 基线 `e011e054f519eafc85db9868010928381fd2d82a`，已合并 PR #76；遵循 [机主补充](https://github.com/ZakuZakuu/ep7-film-hack/issues/70#issuecomment-6470726983)。
- 输入仍为已验证的 E142 / 1100 原厂固件；全文件、OE 往返与解码主程序哈希重新核验。
- 只参考 [固定上游 PEN-F 设计及工具](https://github.com/fishcu/oly_fw_analysis/tree/539fcf1fa9eda5fdef8ede4deeab94a4691d94c3)，补丁与夹具原创，没有复制上游实现。
- 地址、哈希、实际通过项与未通过项见 [本轮证据](t27-gui-commit-evidence.json)；[PR #76 证据](t27-ui-flow-evidence.json) 保留。

| 环节 | 新增证据及边界 |
|---|---|
| GUI 同步及准入 | 显式拥有的资源 5 互斥对象、捕获状态四个字与最小原生接口；忙、闲及原厂覆盖分支均执行原代码，不替换准入或设置器 |
| H/L 提交 | 原厂子控件 → GUI → 原厂准入 → 标记值适配 → 未改 v4 应用入口 → 分部 RAM 记录写入、正常 S 刷新及同一 typed 发布点 |
| 原厂后处理 | H/L 标记保存在本次原厂 GUI 调用栈；原厂协调通知继续携带真实 S，未把 H/L 数字发送为 S；活动应用消息交付是明确的服务模型 |
| 删除键 | 只改 COLOR 编辑状态的查找查询，实际事件仍是删除键；未扩充或复制原厂事件表，旧路由对照见 JSON |
| 轴与枚举 | 独立、对齐的四个 u32 易失字段，不改原厂对象布局；原厂枚举构造器重建十二个子控件；S 仍用原厂十一值枚举 |
| 显示 | 原厂数值记录生产者附加 UTF-16 轴名、符号和数值；H/L 隐藏旧六帧数字，复用原生文字消费入口；没有执行字形或像素绘制 |
| 放置 | 三个相关组件的原厂加载、重载与初始化表边界可重放，但三项原始字节候选尚不能排除，故不满足发布条件 |

明确的停止点：

1. 复用既有指针、相对分支检查及 Pillow/zlib/文件系统分类，没有把字节命中直接叫作代码引用。
2. 三项候选未能分类，其中两项位于同一带 OE 头、描述符的范围；按已确认的外层描述符截取后，固定上游解析器报 checksum mismatch。
3. 头、结构和邻近 Linux 内容不能代替有效校验，也不能证明跨组件地址域隔离；第三项另属未分类范围，不能被该嵌套假设覆盖。
4. 按 [AGENTS.md](../AGENTS.md) 的“遇到阻塞时，最多尝试两种不同的方法，然后报告”，停止该放置路线；不绕过保护、不靠继续换地址凑一个可刷版本。

原型验证不等于系统验证：

- 锁为单线程、无竞争模型；消息接收方成功为显式输入。原厂状态读取、拒绝、设置转换、存储和发布执行真实代码。
- 所有实际访问逐条核对自然对齐；未声明对象和坏指针必须停止。未证明真实调度、缓存一致性或完整启动。
- 本轮没有执行 NVS 后端，不能声称机内编辑已经证明断电持久化；该部分仍依赖以后获准的 B5。
- INFO 改变光标后，夹具重放原厂数值记录生产者，再执行依赖其派生 ALL 状态的操作；没有把父控件单次调用冒充完整 GUI。
- 色轮仍是旧停止点，未重新扫描 C3d。拨盘的完整上层交付及实际绘制仍不能用旧路由不变来替代。
- 新增原型清单记录的是复现哈希，`owner_build_allowed: false`；验证脚本只接受 `--verify-only`，不存在安装文件写入器。
- T20、v2、v3、v4 的源码、清单与预期哈希未改变，完整包哈希仅通过流式输入复算；未生成任何安装文件。

私有复现：

```sh
bash tools/setup_t20_environment.sh
python3 tools/ep7_t27_v5_probe.py --upstream work/upstream/oly_fw_analysis \
  --stock /tmp/ep7-stock/E142_EP7_firmware_download.BIN --out /tmp/t27-native
python3 tools/ep7_t27_editor_aux_probe.py --upstream work/upstream/oly_fw_analysis \
  --stock /tmp/ep7-stock/E142_EP7_firmware_download.BIN --out /tmp/t27-aux
python3 patches/hsl-editor/e-p7/build.py --upstream work/upstream/oly_fw_analysis \
  --stock /tmp/ep7-stock/E142_EP7_firmware_download.BIN --verify-only
python3 -m unittest discover -s tests -p 'test_ep7_hsl*.py'
```

原厂输入、解码镜像、反汇编、目标文件与执行记录全部留在私有 `/tmp`，没有公开。
复现结果的 `placement.qualified` 必须仍为 `false`；验证脚本计算出稳定哈希不代表可刷。
完整四配置交互重放可能较慢；`summary.json` 持续记录阶段，异常不转换为成功。

下一步只建议审查本轮程序证据，然后决定是否单独解决三项放置候选及对应装载所有权；不应再次从冷 GUI 同步对象或单值提交起步。
可直接继续：沿用本分支及固定输入，先阅读本轮 JSON 的 `placement` 和 `validation_status`，不要解除构建禁令或重新扫描色轮。
若私有环境重建，按上述脚本重新产生 `/tmp` 证据；无需机主提供序列号、操作相机或导出设置。
B5 仅在放置和剩余交互验收完成、另行审查通过后考虑；届时检查三轴、共享光标、ALL、长按重置、Wi-Fi 双向可见、重启及取景/JPEG，并保留回退 v4/原厂方案。

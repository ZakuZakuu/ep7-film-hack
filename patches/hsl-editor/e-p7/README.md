# E142 / 1100 机内编辑原型（尚非 v5a）

**放置审查尚未通过，禁止据此生成安装文件或安排 B5。**
`build.py` 只接受 `--verify-only`，没有安装文件写入器。

这是本仓库原创的有限原型：在未改动的 v4 设置、发布及成像扩展上，
加入 COLOR 专属的 S → L → H 枚举、原厂 GUI 准入后的标记提交、轴文字、
ALL 边界适配。未实现色轮的 H/L 显示重定向；尚未达到“其他全部验收完成”的 v5a 标准。
参考 [PEN-F 设计](https://github.com/fishcu/oly_fw_analysis/blob/539fcf1fa9eda5fdef8ede4deeab94a4691d94c3/docs/color/pen-f/EDITOR.md)，
只阅读、运行固定上游工具，没有复制其实现或地址。

原型的适配层、枚举重建和原厂提交链必须结合真实 E142 固件在 GNU 引擎中复现。
同步对象为明确拥有的单线程、无竞争夹具；应用消息的接收成功为外部输入。
未知地址与未声明服务均停止，不能将模拟通过视为真实 RTOS、缓存或画面安全证明。

GUI 提交入口：`tools/ep7_t27_v5_probe.py`。
本轮拨盘输入复现：`tools/ep7_t27_dial_probe.py`；放置复核：`tools/ep7_t27_placement_review.py`。
`ep7_t27_editor_aux_probe.py` 保留历史冷夹具反证，不代表修正后的拨盘验收。
放置尚未闭合，不更新本目录的补丁源码或原型哈希，不生成 v5 发布清单。
所有输入、解码镜像、汇编产物和原厂执行记录仅允许留在私有 `/tmp`。
详细成功项、未通过项及可直接继续的步骤见研究报告和证据 JSON。

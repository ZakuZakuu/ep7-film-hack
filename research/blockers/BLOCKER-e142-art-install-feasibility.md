# T2 blocker：ART ownership 与可恢复安装均缺证据

2026-10-11 / Issue #13；E-P7 owner-reported 1.1，111017984 bytes，SHA-256 `9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb`。

| Gate | 两条有界证据路径与结果 | 缺失要求 / 最小前提 |
| --- | --- | --- |
| G2 | 官方跨型号 ART 更新已核实，但无前后 binaries/consumer；两条本地探针找到名称、未找到 direct reference/处理归属 | 合法同型号版本对及适用容器工具，先验证 ART ID→参数/consumer，再另证 E-P7 映射；缺前提暂停 |
| G4/G5 | 私有 OE 验证再次通过，仅完整性；历史社区/当前原厂升级资料没有提供 E-P7 修改包接受及独立恢复证明，官方还警告中断失效及不提供旧版回退 | E-P7 checker/trust/model-version 证据，覆盖启动失败的独立恢复、可恢复额外平台、单独设备授权，缺一不做修改包尝试 |

不是技术不可能或“签名已证实”的结论。厂商新增 ART 不公开其实现或第三方信任权限；图像/音频资产可读不等于 camera-tested customization。未生成修改包、私有更新服务器、绕过/伪造签名、USB/SD 实验、降级或设备 I/O。

暂停固件修改投入。只保留有合法 paired inputs 前提的版本差分研究；目前输入不足，未执行。现实替代是另行授权的手动 OEM Color Profile 样张表达能力测量，可保留预览与机内 JPEG，但不能增加隐藏色彩自由度/自定义 ART。E-P7 作为官方 OI.Share/Workspace Profile Load 写入目标不受支持，JPEG 作为来源与目的机不同。

[决策备忘录](../art-update-feasibility.md)与[来源/精确探针边界](../t2-art-update-evidence.md)。无需为本任务接相机或提供序列号。

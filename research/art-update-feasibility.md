# T2 决策备忘录：E-P7 ART 与修改固件的可行性

2026-10-11，[Issue #13](https://github.com/ZakuZakuu/ep7-film-hack/issues/13)。最新 main 基线 `efed91b1d9aeb3315cf2b8c3b5d3b2771418b6f9`，已含 #11/#12。E-P7 owner-reported 1.1 私有原文件 **111017984 bytes / SHA-256 `9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb`**。本轮再验 size/hash、五 OE 校验、输入不变；没有下载其他机型固件、生成修改镜像或设备操作。

**后续范围澄清：**下文“唯一条件性下一实验”是 T2 当轮提案，不是所有离线逆向的前置闸门。[T3 / Issue #15](e142-executable-map.md)已在同一真实样本上建立 MN103 代码与静态引用证据，可独立继续有限函数分析；旧版 binary 对是可选证据。T3 还确认三处 BleachBypass 名称位于 OI.Share XML，不是处理代码。

**建议：暂停固件修改方向的工程投入。保留一个有前置条件的离线研究机会；当前不能承诺机内自建 ART、任意 LUT、修改包安装或恢复。unknown 不等于技术上已证明不可能。**

| 必要闸门 | 已证明的事实 / 缺失的关键证据 | 判定与停止理由 |
| --- | --- | --- |
| **G2：ART 处理定位与可修改性** | **verified**：官方曾新增 ART；E-P7 已有 Bleach Bypass，私有样本出现相应名称。未建立 E-P7 ART ID→参数/算法/处理调用或 ISP ownership；未证明编辑参数能产生目标 look | **unknown & no-go for implementation**；跨机型研究仅 **conditional**。两条定向探针用尽，不能把名称、Exif ID 或 JPEG 当作处理表 |
| **G4/G5：修改包接受、安装与独立恢复** | **verified**：外层 OE 加和完整性及官方原厂升级说明；未验证 E-P7 修改包接受、内部签名/boot trust、版本检查或独立救援入口。没有覆盖启动失败的恢复证据 | **unknown & no-go for any modified-image attempt**；禁止以“可解码/校验通过/原厂能升级”代替安全安装证明 |

## 新增 Bleach Bypass 的官方先例：改变研究价值，不解除闸门

[Olympus 2018-02-28 公告](https://www.olympus-global.com/news/2018/nr00715.html)及[详细发布说明](https://www.olympus-global.com/news/2018/contents/nr00715/nr00715_00001.pdf)确认 **PEN-F 3.0、E-M1 Mark II 2.0、E-M5 Mark II 4.0** 都新增 Bleach Bypass I/II；此前 E-M10 Mark III 已提供该效果。[PEN-F 更新手册 p.182](https://learnandsupport.getolympus.com/sites/default/files/media/files/2018/03/PEN-F_ENU_02_FW3_0.pdf)独立确认新增菜单功能。

这证明 **OEM 更新可扩展这些型号的 ART 功能**；不能确定更新是新算法、既有处理单元的参数组合、开放已有功能，还是混合改动。没有前后私有 binary 对，不做差分归因。PEN-F 为 [TruePic VII](https://learnandsupport.getolympus.com/support/pen-f)，E-M1 II 为 [TruePic VIII](https://www.olympus-global.com/news/2016/nr161102em1mk2e.html)；后者与 E-P7 品牌代际相近，仍不证明相同 ISA、地址、参数格式、信任链或允许第三方写入。

同一公告提供的 Flat→BT.709 LUT 是 **DaVinci Resolve 的离线视频调色文件**，不是 E-P7 机内 LUT 导入接口。PEN-F 3.0 的 Profile Load 是另一项原厂功能，不能当作 ART 算法替换。

## E-P7 定向证据与安装边界

两条预定义探针只检查官方 ART 名称及一个有界字符串的直接引用：#0 的 `BleachBypass` ASCII 有 4 处，#1 的 UTF-16LE 名称有 54 处；仅一个 #0 候选有完整的 ±256-byte NUL 边界，直接 aligned u32 offset/header-load-candidate 引用为 0。**这是文本线索，未建立处理归属**；没有扩大 ISA/base/stride 猜测或重复资源扫描。精确 payload offsets、字节序歧义与复现见 [证据页](t2-art-update-evidence.md)。ExifTool 的公开照片 metadata 42/43 也不能直接作为 E-P7 固件 dispatch ID。

必须区分传输入口、外层 integrity、内部签名、boot trust、型号/版本接受、独立恢复。已验证五 OE blocks 的 additive residual 为零；没有设备侧 checker、签名/公钥或启动链验证结果，**不能断言有某种签名，也不能因未识别而断言没有**。[官方 USB 更新说明](https://explore.omsystem.com/c/en/firmware-update-instructions)警告中断可能使相机失效，并不提供旧版回退；原厂流程、历史 E-P1 updater 模拟或 SD 更新原厂包的社区报告都不是 E-P7 修改包接受/恢复证明。BIN 也不是完整 flash/bootloader 备份；不在唯一日常机身做“无害刷一下”。

## 项目投入与功能成本

| 用户希望的功能 | 当前可行范围 / 增量成本 |
| --- | --- |
| 原厂 COLOR/MONO 机内预览/JPEG、4 组原生配置 | **官方可用**；目标负片 look 的表达能力尚未测量。手动设置可作低成本基线，不增加参数自由度 |
| UI 图片/音效定制 | 图片可离线解码；调用/索引未知，WAVE spans 重叠、并非已证实快门音；仍需 G4/G5。更容易读取资产不等于更安全安装 |
| 修改原生 look 参数或 ART | 需真实参数 schema、ID→consumer 和效果响应；不能从图标/名字推出，成本明显高于资产读取 |
| 添加任意新图像处理代码/LUT runtime | 再需执行环境、ISP/frame access、性能与实时预览证据；当前无依据投入 |

**容易导入配方的路线也有明确边界：**官方 [FAQ 007489（2026-09-25）](https://digital-faq.jp.omsystem.com/faq/public/app/servlet/qadoc?QID=007489)明示 E-P7/PEN-F 不支持 OI.Share Profile Library 写入；[FAQ 007407（2025-10-07）](https://digital-faq.jp.omsystem.com/faq/public/app/servlet/qadoc?QID=007407)的 Workspace Profile Load 写入目标为 OM-3/PEN-F 3.0+。E-P7 JPEG 可以作为配置读取来源，不等于 E-P7 可接收；普通设置 backup 也不能替代这一接口。这里的 no-go 是**这些官方功能不支持 E-P7 作为目标**，不是断言所有未知协议永远不可能。

## 唯一条件性下一实验与停止决定

**仅在有合法、型号一致的前后原厂 binary 对时**，以 E-M1 Mark II 1.x→2.0（TruePic VIII）或 PEN-F 2.1→3.0 的官方 Bleach Bypass 变更为 oracle，用已证明适用的容器工具私下做版本/hash 限定差分，寻找明确 ID/参数/consumer 关系。须先验证两版格式、来源/size/SHA；release 还有多项其他改动，diff 命中不能单独归因 ART。只有真实 linkage 成立且另证 E-P7 映射，才值得另起定位任务；仍不触碰安装。**本轮没有这些 paired inputs，实验未执行。**

现阶段推荐暂停风险固件路线；另行授权后，用原厂 Color Profile 手动配置和固定 WB/曝光、灰阶/肤色/留出光照拍摄，判断它能否达到目标 look，保留真实机内 JPEG。这是非侵入基线，不是假称自定义 ART 已实现。安装路线重新开启前还须同型号 checker/trust 证据、独立失败启动恢复、可恢复测试平台和单独设备授权，详见 [blocker](blockers/BLOCKER-e142-art-install-feasibility.md)。

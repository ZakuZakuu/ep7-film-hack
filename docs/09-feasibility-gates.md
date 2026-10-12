# 09｜可行性闸门与硬性阻塞

**不是所有能在另一台相机上完成的改机，都能在 E-P7 上完成。** 我们要求“跨品牌社区实现先例 + E-P7 专属证据 + 最小验证”。

| Gate | 继续推进必须具备 | 如果证据不足 |
| --- | --- | --- |
| G0 社区先例 | 有公开实现及其精确机型、版本、许可和验证范围 | 仅作研究问题，不进入产品开发 |
| G1 可研究介质 | 合规的 E-P7 固件样本或经过确认的只读协议入口 | 停止虚构固件解包，调查合法获取与替代路径 |
| G2 原生成像路径定位 | E-P7 特定版本下风格选择 → 配置/参数记录 → 实际预览/JPEG consumer 的证据，区分持久化与菜单/诊断/协议描述；不限 ART | 不造补丁、不把字符串/诊断读取当成成像算法、不宣称已找到 LUT |
| G3 风格表达能力 | 目标胶片风格在原生/已验证处理能力上有可重复的效果证据；采用 LUT 拟合时还需量化拟合 | 列出不可表达或未测量之处，不承诺 1:1 理光/富士/胶片色彩 |
| G4 可重复离线修改 | 版本限定、原始字节 guard、校验/签名约束、差分和合成测试 | 仅保留离线研究成果 |
| G5 实机安全 | 可独立验证的升级接受与恢复方案、单独用户授权 | **禁止真实相机写入** |
| G6 用户体验 | 在 E-P7 上可切换、取景预览与 JPEG 实际呈现目标效果 | 不宣称“机内直出已实现” |

## 硬性 Blocker 处理流程

写入 `research/blockers/BLOCKER-<topic>.md`，包含：(1) 被阻塞的目标和 gate；(2) 原始证据、型号版本；(3) 已试过的两条不同、有限的验证路径；(4) 是技术不可能还是证据暂缺；(5) 备用路线及其对“机内直出”体验的损失；(6) 需要用户决定或提供的最小信息。

**按证据停止，不按 token/迭代数硬熬。** 有新的实证再恢复。

## 先例不能直接迁移

- [GR4-LUTSmith](https://github.com/lemonadesaltbagel/GR4-LUTSmith) 把创意 LUT 拟合到 GR IV 自带的色彩参数，非通用的任意 LUT 运行时。E-P7 的色彩表达自由度可能更低。
- [GR Custom Tool](https://github.com/DoYitNow/gr-custom-tool) 的原生 profile 描述符、getter/setter、保存/加载方法可供研究；公开版明确缺少独立完整实机验收，GPL-2.0-only 代码和 GR4 地址不能直接移植。见 [T4 方法复核](14-native-profile-private-validation.md)。
- [GR IV firmware research](https://github.com/radium-wang/ricoh-gr4-firmware-analysis-and-feature-expansion) 的工厂脚本及写入接口为理光特有。
- [Magic Lantern](https://github.com/reticulatedpines/magiclantern_simplified) / [FujiHack](https://github.com/fujihack/fujihack) 的加载器、CPU/OS 和地址映射不能直接复制。
- [NikonHacker](https://github.com/simeonpilgrim/nikon-firmware-tools) 的固件校验/补丁只针对其支持的尼康机型。

一项可复现的 E-P7 证据，胜过大量看似完整但无法验证的代码。

[Issue #18](../research/e142-native-profile-chain.md) 找到真实 Picture Mode 诊断字段与部分选择/地址链，尚未定位 COLOR 槽持久化或成像 consumer；G2 未通过，G4/G5 仍 NO-GO。官方四槽手动编辑不等于自动导入，也不等于本项目已验证自定义机内效果。

[Issue #21](../research/e142-picturemode-producers-and-remote-controls.md) 新增真实字段生产者和复合键/标志分支消费者，超出了诊断读取，但尚未建立 COLOR 选择→持久化记录→真实预览/JPEG 链。OI.Share 描述与社区接口不提供已验证自定义导入路线。**G2 仍未通过，G4/G5 不变**；新证据支持一次具体下游调用研究，不支持修改工程。

[Issue #23](../research/e142-picturemode-handoff-verdict.md) 完成该下游研究，仅确认选项/group/标志门控及未定性条件调用，未建立真实成像 consumer。**停止这条逐函数路线，G2 未通过，G4/G5 NO-GO。** 原生 COLOR 受控测量可独立检验 G3/原厂控件的产品价值；即使颜色可接受，也不证明二进制调用链或自动导入。测量只作为另行授权提案，手动路线不适用时优先暂停。

[Issue #25](../research/e142-system-boundary-map.md) 的自主四轮研究新增可复现的分段地址归属、方法名称查找、拍摄软件请求与通用设置描述边界，满足有限架构图的独立结构/反证要求。**不等于 G2 通过**：没有自定义色彩记录→真实预览/JPEG 消费者，也没有导入入口。拍摄标签1007与设置ID53…56不能命名为 ISP/ART/COLOR 操作。当前暂停进一步固件静态追踪，等待能区分存储/控制与成像的独立机型相关驱动/接口或具体版本变更证据；不自动安排 T8，也不开发补丁/导入器。G3 未测量，G4/G5 NO-GO。

[Issue #27](../research/e142-public-interface-evidence.md) 按新授权独立调查公开资料，未恢复固件追踪。源码申请说明、其他型号的处理核分工、通用 Linux/ISA 支持和原始专利均未提供 E-P7 的成像接口对应。**保持暂停，G2 未通过，G3 未测量，G4/G5 NO-GO。** 接收源码也不是自动 GO：先确认型号/版本/许可及相关驱动定义，再要求两项独立不变量支持一次有界离线验证。厂商联系与相机实验均未执行、未授权。

[Issue #29](../research/e142-native-style-workflows.md)区分文档已支持的原生工作流与新增二进制工程：可以继续有限的保存/切换/可观察性研究，不能因 G2 未通过而否认原厂功能，也不能用手册代替成像代码或实机验收。**G2 仍未通过，G3/G6 未验收，G4/G5 NO-GO。** 自动传输与自由效果组合仍缺关键接口/兼容/安全证据；MONO 颗粒预览例外必须显式呈现。本轮没有相机操作授权，后续最小召回审计需用户单独选择；不自动开发 UI、上传器或补丁。

[Issue #31](../research/e142-cross-model-style-entrypoints.md)按新授权进行了两个既有控制层锚点的有限复核：独立效果子字段转换有字节/诊断依据，selector/editor 写入者仍未绑定，A/B 收敛和持久化未证明。四机型官方 UI、Myset/Custom 与命名/备份能力必须逐型号逐版本区分；菜单相似不是 ABI/补丁兼容。**A 选择器/B 受限编辑器可继续有界状态研究，优先支持机型的原生配置槽召回；E-P7 实现仍暂停。** 文档支持与机主的 Profile 明暗切换观察范围有分歧，不承诺原子召回。G2 未通过/G3G6 未验收/G4G5 NO-GO；无新界面 writer 就不安排自动下一个函数。

[T17 / Issue43](../research/e142-longrun-architecture-and-deployment.md)新增可复现的子对象返回调整、完整/直接调用双入口约定，以及两个独立的 ART 命名控制入口；一个只绑定到 u16 控制字，另一个属于拍后 RAW ART BKT 工作流，未证明滤镜参数或预览/JPEG consumer。独立安装审计区分外层加和、内部认证、正常升级与启动失败恢复；当前官方不支持旧版回退，历史同厂修改先例不能作为 E-P7 独立恢复。**G2 未完成，G3/G6 未验收，G4/G5 NO-GO。** 暂停泛化分派追踪和安装/UI/补丁工程；新 ART 参数/消费锚点与独立机型信任/恢复证据是不同的恢复研究条件，不要求旧版对照或当前相机操作。

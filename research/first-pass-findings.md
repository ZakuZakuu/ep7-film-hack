# T0｜证据复核与可研究性预检

日期：2026-10-11；任务：[GitHub Issue #1](https://github.com/ZakuZakuu/ep7-film-hack/issues/1)。本轮止于 T0，没有推进 T1–T5。

**结论：已有可信跨品牌方法先例，但尚没有 E-P7 研究介质或参数实现证据。固件研究 G1 BLOCKED；原生配置与协议路线 CONDITIONAL，仅允许后续经过评审的研究，不进入补丁/产品实现。T0 报告完成不等于可行性 gate 已通过。**

未取得/分析任何 E-P7 固件样本，未连接相机，无设备读取/写入、改包、LUT 应用、固件编译或生成可刷镜像。所有 E-P7 binary offsets/runtime addresses 均 N/A；用户机身实际固件版本 unknown。

## Confirmed facts：本轮核实的事实

- **official**：产品/FAQ 列 TruePic VIII、16 ART、内置预览/部分效果微调、Color/Mono 各 4 组。官方手册印刷页 51–53 说明 Color1–4、12 色饱和度 ±5、shading、highlight/shadow/midtone，以及 sharpness/contrast。第 52 页 “Set the hue using the front dial” 处于 **Saturation Level** 操作，不能据这句话推导独立色相偏移或 GR IV 同等的矩阵自由度。
- **official**：手册 70–73 页列 ART 与不同附加效果；72 页明确 ART 加在 JPEG 副本，RAW 保留。这支持原厂 JPEG SOOC，不证明可导入任意 LUT 或替换算法。
- **official**：官方索引及对应更新说明列 E-P7 **v1.1 / 2022-02-28**，改进单焦距镜头对焦精度。说明是 HTML；本轮未取得完整固件。
- **official**：E-P7 软件通知索引列 Linux、Expat 1.95.5；E-P7 Linux PDF 有 GPL v2 和按型号/购买日期申请相关源码的说明。没有内核版本/ISA/加载地址/ART 用户态实现证据；源码通知不是完整固件，也不授权分发 OEM payload。本轮没有联系厂商。
- **verified locally（公开源码）**：GR4-LUTSmith main `0f0856e246524ccd435bb93aaf1ede29cd338aa6` 的 VERSION=2.1.0，目标 GR IV **1.11**。实现拟合 LUT 到原生矩阵/曲线/12 hue sectors，有 ΔE00 均值/p95、灰阶和 ColorChecker 评估；构建检查精确输入 SHA-256/长度、原字节、改动范围/重叠以及重解码一致性。未执行其构建器或读取 Ricoh 固件。
- **author-reported**：GR4-LUTSmith 的机内效果与恢复在 GR IV 1.11 上报告测试；hue sectors 实测仅覆盖日光绿/黄场景 ISO 200 RAW Development，不能扩展为全光照/肤色验证。after-curves 尚无机身结果，公开 latest release 是 v2.0.2；main 功能与 release 分开。未找到本轮所审阅来源中的独立 E-P7 复现。
- **verified locally（许可）**：GR4-LUTSmith 未见项目自身明确许可证；GR IV research 的新材料是 noncommercial source license，旧 Apache grant 保留；FujiHack GPL v3、Magic Lantern COPYING GPL v2、olympus-wifi MIT；其余项目的统一授权不充分。依赖许可证不授权项目源码。本轮没有复制第三方实现，详见 [固定版本与许可矩阵](../docs/10-prior-art-matrix.md)。
- **verified locally（协议源码）**：olympus-wifi 提供 command-list/model/property 查询先例，但 `OlympusCamera.__init__` 会 `switch_cammode(rec)` 后再切回 play。不能把其 CLI/相机对象初始化当无副作用只读查询。文档设备示例 TG-5 3.10，E-P7 支持情况 unknown。

关键事实与限制逐条登记于 [evidence-ledger](evidence-ledger.md)，公开响应及复核命令见 [source-access-review](source-access-review.md)。HTTP 200 与内容验证分开：2019 Reddit 和非官方 updater 返回中间页，不能据此复核实际功能。

## Open questions 与 gate 决策

| 路线 / Gate | 判定 | 尚缺的 E-P7 专属证据 |
| --- | --- | --- |
| G0 跨品牌社区先例 | CONDITIONAL | 已有作者报告及可读实现；没有 E-P7 同型号实机先例，受限许可不能跳过 |
| 固件介质 G1 | BLOCKED / 本轮 NO-GO | 合法完整 E-P7 文件、确切版本、来源、长度、SHA-256；两条有限官方获取调查未建立可用路径 |
| 只读协议 G1 替代 | CONDITIONAL research；当前设备执行 NO-GO | E-P7 实际型号/版本/能力响应，且每个查询无副作用、有单独授权；现有库默认初始化不符合 |
| ART 路径 G2 | UNKNOWN / NO-GO implementation | 精确版本的 ID、资源/调用/参数与真实处理路径；表、代码、封闭 ISP、混合实现均未排除 |
| 原生表达能力 G3 | CONDITIONAL research | 12 色饱和度不等于 hue-sector 矩阵；需 E-P7 真实响应模型与目标 look 的可量化误差 |
| 离线修改 G4 | UNKNOWN / NO-GO | 格式、校验、签名、可重打包与原字节 guards 的 E-P7 证据 |
| 安全安装/恢复 G5 | NO-GO | 同型号验证的接受/恢复路径和单独授权；官方更新能力不能充当修改包/救砖证据 |
| 用户体验 G6 | UNKNOWN | 自建风格在机内切换、取景预览和实际 JPEG 匹配；没有实机样片或性能测量 |

**没有样本绝对不能得出**：E-P7 用何种 ISA/OS 分工、容器已解包、某字节为 LUT/ART 参数、存在固定偏移/加载基址、签名可绕过、可安全 downgrade/recovery、Wi-Fi 可写配方、实时性能可用。官方软件通知及其他机型的工具都不能补足这些证据。

## GR4-LUTSmith 方法在 E-P7 上的前置条件

优先复用其研究方法，不移植地址或受限源码。要先证明：

1. **表达力**：E-P7 实际可控参数及处理顺序/输入空间；是否存在独立 hue rotation、通道混合、每通道曲线、亮度/饱和度依赖色彩。官方只证明菜单参数，未证明隐藏自由度。需要实测拟合残差与留出场景，不把 GR IV 的 ΔE 阈值直接当 E-P7 已达成质量。
2. **固件结构**：准确样本中识别与这些参数/ART ID 关联的数据、代码或 ISP 命令，验证读写布局/定点值/长度/共享槽位；字符串命中、相似 TruePic 品牌或旧 Olympus 格式均不足。
3. **持久化与安全**：已知格式不等于可安装，校验成功不等于签名/型号/版本接受。离线验证、恢复实证、单独授权都在后续 gate；本轮不写补丁。

## 三个最有价值且可证伪的后续实验（仅提案，未执行）

| 顺序 / 假设 | 复用先例与最小输入 | 最小观察 / 可证伪结果 | 前置条件与停止边界 |
| --- | --- | --- | --- |
| **E1：存在可依法取得的独立完整 E-P7 1.1 样本** | 复用 GR IV 样本 provenance/inventory 方法及本仓库 inspect_blob。先获得官方明确的仅下载/本地保留方式或用户已有合法本地文件，不要求开启更新 | 本地验证来源、完整长度、版本依据、SHA-256、读取前后 hash 相同。若只有 HTML/源码通知/分段缓存，或流程必须启动设备写入，则不足以满足 G1 | 后续另立任务；OEM 文件留在用户私有本地环境，仅提交元数据。没有合法路径便维持 blocker；不猜 URL、不绕过鉴权、不借获取样本启动更新 |
| **E2：E-P7 原生参数足以逼近一个指定负片 look** | GR4-LUTSmith 的原生参数拟合/ΔE 评估方法；官方 51–53 页参数范围。用户先选一个有使用权、明确 sRGB 输入的目标 look；自有色卡/RAW+JPEG，不需改固件 | 用原厂菜单的有限参数扰动验证是否出现所需 hue/chroma/tone 响应，固定 WB/曝光并留出日光/钨丝/肤色场景。预先与用户定义误差和视觉接受阈值；若所有允许参数组合仍有系统性绿/肤色偏差，拒绝“原生参数足够”的假设，不加入未证实的隐藏矩阵 | 需独立授权的标准拍摄/设置实验（L2），不是当前 T0。先排除表达力不足，再花精力研究修改结构；不开发 LUT fitter/App，不因一张图相似宣称成功 |
| **E3：E-P7 暴露可查询的配置能力清单** | MIT olympus-wifi 中 command-list/model 查询方法；作者文档 TG-5 3.10，仅为协议先例 | 在先审查命令及副作用、单独授权后，由用户本地仅查询已确认的能力/型号字段，输出脱敏摘要。若清单没有 profile/ART 配置相关属性，停止这条公开接口预设路线；即使有 setter 名称也不调用，不据此认定 LUT/配方可写 | 禁止默认构造器、模式切换、remote shutter、delete、setters、扫描未知命令。若查询无法在无副作用条件下完成立即停止；未公开入口不证明内部绝无能力 |

**推荐先做 E1 的官方获取方式确认；若仍阻塞，以 E2 判定原厂参数路线是否值得投入。E3 是提升切换便利性的条件路线，不能解决已证实的颜色表达不足。** 三个实验不是自动获得的下一轮授权。

## Blocker、可行替代路线与所需用户输入

[BLOCKER-firmware-acquisition](blockers/BLOCKER-firmware-acquisition.md) 记录官方静态页面与 Workspace 两条调查、缺少的输入、技术不可能与证据暂缺的区别，以及方案排序。

- **原厂 Color1–4 优化**：保留机内预览/原厂 JPEG 及切换；无法承诺复杂 hue mapping、新颗粒/空间效果或任意 LUT，是最现实的低风险替代方向。
- **条件性的远程预设管理**：仅在 E-P7 属性/写入路径另行验证并授权后考虑；最多改善操作，色彩自由度仍受原厂控制。
- **外部 RAW/JPEG 处理**：复用 RawTherapee/darktable 等成熟工具可作为目标 look/颜色误差基线；没有自定义风格机内预览/JPEG SOOC。需用户明确选择，未在本轮开始 T5。

**当前无需用户插相机、上传固件或提供设备身份信息。** 若评审选择 E1，所需的是合法文件获取依据与本地版本/长度/哈希；选择 E2 则先明确一个目标 look 和可接受误差；选择 E3 才需要机身菜单型号/版本及单独只读计划授权。所有原厂镜像/私有样片/完整设备响应均不进入公开仓库或云端分享。

## 本轮验证与停止记录

复用 `tools/inspect_blob.py`，没有增加解析器/补丁框架；补充空/短文件和跨 4 KiB 初始读取、多个 1 MiB 块及独特尾部的 CLI JSON 测试，验证完整 SHA-256、采样位置和输入不变。

```bash
python3 -m unittest discover -s tests -v
python3 tools/inspect_blob.py --help
git diff --check
```

结果见 [validation](validation-t0.md)。这些测试只验证通用只读 inventory，不识别 E-P7 格式、不验证硬件或修改包接受。

T0 到此停止；本轮没有任何未报告的 firmware unpack/patch、实机通信或后续阶段实现。

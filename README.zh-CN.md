# Olympus PEN E-P7 · Film Simulation Reverse Engineering Research

**当前软件进展 — 2026-10-27**

当前按 [AGENTS.md](AGENTS.md) 复用原生 COLOR HSL，ART 路线暂停。机主报告 T20 效果及 v2 四档 JPEG 实拍通过（[#49](https://github.com/ZakuZakuu/ep7-film-hack/issues/49)、[#58](https://github.com/ZakuZakuu/ep7-film-hack/issues/58)）；v4 与电脑工具已做离线验证，仍待 B4 实拍，不是生产安全保证。

- [Recipe Studio](tools/recipe_studio/README.md)：离线配方编辑与近似预览。
- [v4 / EP71 协议](docs/wifi-recipe-protocol.md)：原厂逐值设置、H/L 发布镜像和 ISP 系数证据；持久性、无线、Myset 与缓存列入 B4。
- [电脑 Wi-Fi 工具](tools/ep7_wifi/README.md)：Windows/macOS/WSL 的读取、自动备份、差异写入、完整回读和还原；原厂固件拒绝写入，超时后不自动重试或回滚。

本仓库不提供原厂数据或安装文件。Agent 未连接或操作相机；机主在审查后另行决定本地构建、安装和 B4。

## T0–T19 历史记录

下文保留当时的结论与停点，不代表当前任务规则；当前以 AGENTS.md 与授权 Issue 为准。

**历史 T19：[Issue #47 原生 ART 消费者](research/e142-art-native-consumers.md)。** 已将原生附加效果字段连接到真实32字节参数构造器和既有效果接收器，并交叉验证逐变体参数与 bracketing 记录的共用关系。这条构造路径清除 FilmNoise；另一组半字标签与 ExifTool 元数据格式吻合，不能当成 ISP 接口。仍未验证像素处理、独立命名风格和永久保存。见[复现与 handoff](docs/25-t19-private-validation.md)，G2 未完成/G4G5 NO-GO。

**上一轮：[Issue #45 ART 参数图](research/e142-art-parameter-graph.md)。** 原生控件缓存、注册回调及156字节参数包是本轮基线，历史成果保留。

**已有基础：[Issue #43 多方向自主研究](research/e142-longrun-architecture-and-deployment.md)。** 子对象返回调整、同体双入口及 ART 命名根；修改包接受和独立恢复审计仍适用。

**已有基础：[Issue #41 系统架构研究](research/e142-art-architecture-sprint.md)。** 已绑定创建路径下的代理与返回字节控制映射；不是 ART 参数写入或渲染证据，GNU UDF 语义仍未准入。

**已有基础：[Issue #39 GNU 模拟器与复制循环准入](research/e142-mn103-semantics.md)。** 优先复用现成 GNU sim，原创合成调用/数据/分支/复制测试通过，并保留 LIR 缓存反例。两处真实复制循环已有条件性静态证明，私有 CFG 能越过首个循环；没有执行原厂代码、制作反编译器或实现 ART 修改。[运行命令](docs/21-mn103-semantics.md)。

**已有基础：[Issue #37 系统逆向工作台](research/e142-system-re-workbench.md)。** 已有可复现的工具初始化脚本和经过真实固件校验的私有 GNU/SQLite 索引；可直接复制的 [Cloud Setup 内容与运行命令](docs/20-re-workbench.md)。Ghidra 无界面合成 ELF 验证成功，但 MN103 语言/反编译尚未准入，REA 实际调用受云运行时阻塞。尚未实现自定义 ART 或修改固件。

**已有 ART 证据：[Issue #33 ART 颗粒门控与自定义项目边界](research/e142-art-host-gates.md)。** 新代码关系确认三个复合键强制 MonoEnable，以及独立的 Type 条件清除 FilmNoise、保留 MonoEnable。局部条件下保留颗粒位不等于相机接受彩色颗粒，更不等于真实处理或预览。**当时 ART 是第一候选；该路线现已暂停。** 新项目注册、独立保存、实际处理及名称/图标/预览映射仍有阻塞。见[精确复现](docs/19-art-gates-private-validation.md)。机主已确认专用 ART 的 Add Effects 无法从普通 P/A/S/M Picture Mode 调用，旧跨入口实验不再提议。[T10 对比](research/e142-cross-model-style-entrypoints.md)、[T9 原生能力](research/e142-native-style-workflows.md)保留为历史证据。

**状态：已验证 OE、LZO SquashFS、MN103 代码及部分系统结构；尚未找到自定义色彩参数的真实预览/JPEG 消费者；未连接或修改相机。** [Issue #25 系统边界研究](research/e142-system-boundary-map.md)在四轮有依据的离线实验中恢复了初始化数据与辅助代码的搬移关系、三层方法名称查找、带类型的单次拍摄请求，以及通用自定义设置路径。原先未定位的复制/填充辅助函数已在 #0 找到；这些发现仍属于架构和控制层，没有证明 COLOR 槽记录、成像实现或外部风格导入。见[有限数值索引](research/e142-system-boundary-map.json)和[私有复现](docs/16-system-map-private-validation.md)。**该轮停止逐函数追踪；T14 现已建立有证据的离线工作台，仍未解锁成像消费者或固件修改。** G2 未通过，G4/G5 NO-GO；不自动开启下一项 callee 任务，也不要求用户做相机测量。

[Issue #15 程序级成果](research/e142-executable-map.md)中的 `payload offset + 0x60020020` 只适用于已核对锚点，T7 新增不同范围的搬移映射；均未经过实机观测。三处 BleachBypass 名称属于 OI.Share XML 接口描述。[Issue #13 可行性决策](research/art-update-feasibility.md)中的修改包接受/恢复阻塞仍在，暂停修改与安装工程。下列历史研究保留原结论，T9 当前决策区分可继续的原生工作流与仍暂停的固件工程。

## 一句话目标

让 Olympus PEN E-P7 像一台好用的数码胶片相机：历史路线首选 ART 生态，复用原厂彩色风格与兼容效果，研究可保存、快速切换的自建风格，最终争取保留原厂滤镜并增加自定义名称、原创图标和预览。彩色颗粒、柔焦组合须有真实处理依据；不要求任意 LUT 运行时。手动原厂编辑是有限基线，不是自动导入或已实现的命名风格库；不能隐瞒 WB 等全局状态或预览例外。

[Issue #18 原生配置研究](research/e142-native-profile-chain.md)已验证两种 Picture Mode 诊断结构的字段读取，以及选择相关的地址辅助函数；尚未找到 COLOR1–4 持久化布局、上传接口或预览/JPEG 消费者。两条有限假设均已停止，四个官方 COLOR 槽仍是证据最强的条件性路线。[当前 blocker](research/blockers/BLOCKER-e142-native-profile-consumer.md)与[私有复现](docs/14-native-profile-private-validation.md)记录了下一项字段写入者实验；39 项合成测试通过，未操作相机或公开原厂数据。

[Issue #21 后续研究](research/e142-picturemode-producers-and-remote-controls.md)已找到 CREATE_PARAM 的真实 caller、group/type/mode 字段的临时对象写入，以及将这些字段组成键并选择标志位分支的非格式化消费者。这比诊断读取前进了一步，但仍未证明 COLOR 槽身份、持久化和预览/JPEG 处理链。OI.Share 固定描述列出原厂 ART 控制属性，没有证明自定义配置导入；官方 Profile Library 仍排除 E-P7 写入目标。见[完整复现](docs/15-picturemode-and-schema-private-validation.md)。最值得继续的是一个已观察到的下游调用；G2 未通过，G4/G5 仍 NO-GO。

[Issue #23 调用判定](research/e142-picturemode-handoff-verdict.md)已完成该实验：`0x334780` 读取 group、选项和标志，进行条件调用；没有确认实际成像消费者，两个新 callee 也没有满足独立成像依据要求，因此停止这条逐函数研究链。G2 未通过，G4/G5 不变。建议另行授权一个原生 COLOR 色彩表达能力测量；若手动控件路线已不符合需求，则暂停项目等待新证据。报告包含路线成本/价值比较和私有复现，本轮未操作相机。

## 别误会当前状态

T0 复核结果见 [首轮报告](research/first-pass-findings.md)、[固件获取 blocker](research/blockers/BLOCKER-firmware-acquisition.md)、[来源核对](research/source-access-review.md) 与 [合成测试记录](research/validation-t0.md)。该历史 G1 获取阻塞已由 T1/T1.1 解除；原生参数/只读协议路线仍为条件性后续研究。

**这不是现成的 E-P7 破解包、刷机工具或已验证的自定义 LUT 方案。** 官方确认 E-P7 有 16 种 ART 滤镜、4 组彩色配置、TruePic VIII，且产品的软件通知涉及 Linux；但没有公开资料证明 E-P7 的 ART 算法可以通过修改某张 LUT 表直接替换。理光目前还出现了 GR4-LUTSmith，可以将创意 LUT 拟合到 GR IV 原生调色参数并替换滤镜槽，但这不意味着 E-P7 具备对应参数和固件写入路径。理光逆向、早期奥林巴斯固件改动和其他相机项目可借鉴的是*研究方法*，不是可直接移植的补丁。

## 建议阅读顺序

1. `docs/01-product-and-scope.md` — 用户真实需求、可接受体验、验收标准。
2. `docs/02-facts-unknowns.md` — 已核实事实、推测与误区。
3. `docs/03-technical-playbook.md` — 固件/成像流水线逆向策略与分叉决策。
4. `docs/04-reference-projects.md` — 理光 GR4-LUTSmith、奥林巴斯、FujiHack、Magic Lantern、NikonHacker、Wi-Fi 工程参考。
5. `docs/05-execution-plan.md` — Codex Cloud 主力、ChatGPT 审核、本地验证的任务拆分。
6. `docs/06-validation-and-safety.md` — 不变砖原则、首次实机实验门槛。
7. `docs/07-image-science-and-backup.md` — 色彩模拟验证方法及失败备选。
8. `docs/08-sources.md` — 带链接的来源与局限（2026-10-11 核查）。
9. `docs/09-feasibility-gates.md` — 分阶段可行性判定、硬阻塞与替代路线。
10. `CODEX_START.md` — 历史 T0 启动指令；当前任务以 Issue 的授权范围为准。
11. `AGENTS.md` — Codex 在仓库内应自动遵循的执行规则。

## 阶段目标不是写出一个假插件

- **优先解答**：原生风格选择如何连接参数记录、保存操作和真实预览/JPEG 处理？既有固件与 MN103 映射已验证，按具体字段追踪，不反复扫描 ART 名称。
- **并行低风险调查**：E-P7 Wi-Fi/USB 是否暴露只读的能力列表或预设读写接口？仅在证据充足时考虑预设写入。
- **第一道成功门槛**：提交带原始证据、偏移/哈希/版本的结构分析，或诚实给出证据不足的结论。
- **不做**：未授权刷机、破解来源不明固件、盲猜偏移进行补丁、在云端声称做了实机验证。

## 仓库内提供的小工具

`python3 tools/inspect_blob.py <本地固件文件> --json` 只做只读元数据采集：长度、SHA-256、开头文件标记和抽样熵。它**不具备** E-P7 固件解包能力，不能替代真实格式分析。运行 `python3 -m unittest discover -s tests -v` 可执行离线合成样本测试。

原厂固件、解包固件、相机照片、抓包记录可能含版权或个人数据，不应上传公开仓库；参见 `.gitignore` 和安全文档。

## 跳转

[Issue #10 资源布局成果](research/e142-resource-mapping.md) · [T0 研究基线](research/first-pass-findings.md) · [T1 容器成果](research/e142-first-sample-analysis.md) · [T1.1 文件系统成果](research/e142-squashfs-validation.md) · [技术路线](docs/03-technical-playbook.md) · [完整资源](docs/08-sources.md)

公开发布约束：本仓库不包含原厂固件、提取代码或安装文件；实拍证据与未验证边界见本页开头。详见 [English README](README.md)、[可行性闸门](docs/09-feasibility-gates.md) 及 [研究政策](RESEARCH_POLICY.md)。

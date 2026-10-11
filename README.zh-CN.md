# Olympus PEN E-P7 · Film Simulation Reverse Engineering Research

**公开研究仓库启动稿 v1.1 — 2026-10-11**  
**状态：已在私有环境验证真实 OE 容器、LZO SquashFS 目录及七个选择性提取文件；ART 仍未知；未连接或修改相机。** [Issue #7 实测报告](research/e142-squashfs-validation.md)。

## 一句话目标

让 Olympus PEN E-P7 像一台好用的数码胶片相机：从 ART 菜单选风格，实时预览，拍摄 JPEG 直接获得自己喜欢的负片 / 复古胶片质感；最好能拥有可更换的预设库，而不是反复手调 12 色饱和度。

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

- **优先解答**：E-P7 官方固件样本是否可合法获得？解析是否可行？ART 图像效果属于资源/参数表、程序代码、硬件流水线，还是几者组合？
- **并行低风险调查**：E-P7 Wi-Fi/USB 是否暴露只读的能力列表或预设读写接口？仅在证据充足时考虑预设写入。
- **第一道成功门槛**：提交带原始证据、偏移/哈希/版本的结构分析，或诚实给出证据不足的结论。
- **不做**：未授权刷机、破解来源不明固件、盲猜偏移进行补丁、在云端声称做了实机验证。

## 仓库内提供的小工具

`python3 tools/inspect_blob.py <本地固件文件> --json` 只做只读元数据采集：长度、SHA-256、开头文件标记和抽样熵。它**不具备** E-P7 固件解包能力，不能替代真实格式分析。运行 `python3 -m unittest discover -s tests -v` 可执行离线合成样本测试。

原厂固件、解包固件、相机照片、抓包记录可能含版权或个人数据，不应上传公开仓库；参见 `.gitignore` 和安全文档。

## 跳转

[当前任务 Issue #10](https://github.com/ZakuZakuu/ep7-film-hack/issues/10) · [T0 研究基线](research/first-pass-findings.md) · [T1 容器成果](research/e142-first-sample-analysis.md) · [T1.1 文件系统成果](research/e142-squashfs-validation.md) · [技术路线](docs/03-technical-playbook.md) · [完整资源](docs/08-sources.md)

公开发布约束：本仓库不包含原厂固件或提取代码，也尚无已验证 E-P7 实机改造功能。详见 [English README](README.md)、[可行性闸门](docs/09-feasibility-gates.md) 及 [研究政策](RESEARCH_POLICY.md)。

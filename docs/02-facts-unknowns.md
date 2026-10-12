# 02｜证据盘点（2026-10-11）

标记规则：**F 官方已证实**；**P 公开项目作者/社区证实但机型可能不同**；**H 假设、必须测试**；**N 尚未发现证据**。

| 论断 | 状态 | 来源 / 说明 |
|---|---|---|
| E-P7 使用 TruePic VIII、20MP 传感器、有 Wi-Fi/蓝牙 | F | [OM 官方产品页](https://explore.omsystem.com/c/en/e-p7) |
| E-P7 有 16 种 ART 滤镜，支持实时预览及局部微调 | F | [E-P7 官方 FAQ](https://support.jp.omsystem.com/en/support/imsg/digicamera/qa/products/ep7/) |
| 彩色及黑白配置可各保存 4 组 | F | [E-P7 官方 FAQ](https://support.jp.omsystem.com/en/support/imsg/digicamera/qa/products/ep7/) |
| 官方最新列出的 E-P7 固件为 v1.1，发布于 2022-02-28 | F | [官方固件索引](https://support.jp.omsystem.com/en/support/imsg/digicamera/download/software/firm/e1/) |
| 官方 E-P7 相关软件通知列有 Linux 与 Expat | F | [官方软件版权信息](https://support.jp.omsystem.com/en/support/imsg/digicamera/download/notice/notice.html)；**不证明全部 ART 算法运行于 Linux 用户态** |
| ART 包含颜色和非颜色的处理，RAW+JPEG 仅 JPEG 加入 ART 效果 | F | [相机说明书在线内容](https://manualzz.com/doc/59292907/olympus-e-p7-user-manual)；[官方 FAQ](https://support.jp.omsystem.com/en/support/imsg/digicamera/qa/products/ep7/) |
| 过去有人针对旧 Olympus 机型解包/修改固件，涉及录像限制/镜头白名单 | P | [2010 年固件格式工具研究](https://www.dvxuser.com/threads/e-p1-e-p2-e-pl1-hack-research.217453/)、[2019 M43 社区链接](https://www.reddit.com/r/M43/comments/bnhfb5/modified_olympus_firmware_removes_30minute/)、[原论坛讨论](https://micro43club.pro/forum/threads/modifikacija-proshivki-kamer-olympus.22086/)；**不可推出 E-P7 已可刷自制固件** |
| GR IV 有解包器、只读探针、通过工厂脚本替换关机画面案例 | P | [GR IV 研究仓库](https://github.com/radium-wang/ricoh-gr4-firmware-analysis-and-feature-expansion) |
| GR IV research 仓库提供任意 3D LUT 运行时 | N | 此处特指 radium-wang 研究仓库，不能泛指所有 GR IV 项目。GR4-LUTSmith 是另一个项目，公开源码拟合 creative LUT 到原生参数并修改槽位，非任意 LUT 运行时；范围/许可见 [T0 矩阵](10-prior-art-matrix.md) |
| E-P7 的 ART 滤镜存在可换的 LUT/资源表 | H | 已验证容器与 ART 名称线索，未建立参数/算法归属；见 [T2 决策](../research/art-update-feasibility.md) |
| E-P7 可以运行自定义 ARM/Linux 插件直接处理实时 JPEG | H | Linux 组件存在不意味着访问 ISP 或任意代码执行 |
| Wi-Fi 可发现 E-P7 的配方写入命令 | H | 公开 OPC 工具只证明**某些 Olympus 机型**有远程控制/部分设置能力；未见 E-P7 配方写入验证 |
| E-P7 可安全降级、恢复损坏启动分区 | N | 未见 E-P7 可靠的独立恢复路径；禁止假设 |

## 三个最重要的推理边界

1. **相同 TruePic VIII ≠ 相同固件地址、签名密钥或成像算子实现。** E-M10 III / E-PL9 仅供交叉参考。
2. **能够解包 ≠ 能重打包/刷机。** 可能存在签名、CRC、型号绑定、加密或 anti-rollback。
3. **菜单项 ≠ 独立滤镜文件。** ART 可能由颜色参数、固定程序、ISP/DSP 专用逻辑组合实现。

## 未确认事项（优先补证）

- E-P7 v1.1 候选已通过授权官方路线取得并核对 size/SHA；修改包接受的型号/版本/信任校验仍未知。
- 官方 Linux 软件组件在相机中的具体职责是什么？是否有可提取的设备树、文件系统和 ELF？
- ART 滤镜名称/标识符/参数在哪里存储？是否存在多组数据表和 shared processing routines？
- USB、PTP/MTP 和 Wi-Fi 的 E-P7 能力列表到底有哪些？其中是否存在配置只读、配置写入接口？
- 官方 ART 子效果已有何种**允许的**组合？不能把 UI 的所有限制都归因于“一个简单锁”。

## T2 官方新增证据

2018 原厂更新为 PEN-F 3.0、E-M1 II 2.0、E-M5 II 4.0 新增 Bleach Bypass；厂家扩展 ART 的先例不证明 E-P7 第三方算法修改。官方 FAQ 007489 / 007407 区分 E-P7 JPEG 作为 profile 来源与写入目标，E-P7 不支持这两项官方 Profile Load 目的机功能。来源及限制见 [决策](../research/art-update-feasibility.md)。

## T3 程序级证据

同一 owner-reported v1.1 / SHA-256 `9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb` 中，GNU binutils 验证 #0 的 MN10300-family 小程序调用与返回，并由八个具名常量的落点支持静态映射 `payload offset + 0x60020020`；具体 CPU 子型、OS、硬件运行地址和 ART consumer 仍未知。#3 也有 MN103 代码，职责与基址未知；辅助 ARM ELF 不代表主程序架构。三处 BleachBypass 名称在合法 `oishare` XML 中，仅是接口描述。见 [完整程序图与反证](../research/e142-executable-map.md)；G2 未通过，安装/恢复闸门没有变化。

## T4 原生 Picture Mode 证据与产品边界

[Issue #18](../research/e142-native-profile-chain.md) 在同一哈希的 #0 中验证了诊断入口 0x13be62f 的六个 byte 字段（工作缓冲 +0x124…0x129），以及 CREATE_PARAM 入口 0x13c1f98 的 group/type/mode 字段（输入对象 +8/+9/+0xa，mode 为 halfword）。选择辅助函数 0x2e9e99 有四个地址选择分支，但没有证据对应 COLOR1–4；未知 `udfu01` 语义与外部调用 0x47001052 阻止把它当成已解码配置记录。持久化与预览/JPEG consumer 仍 N/unknown。

官方说明书 pp.51–53、103、130 支持四个 COLOR 槽的编辑/保存、屏幕效果和 Picture Mode 的原生处理；未证明任意 XMP/LUT 的导入、拟合质量或更多槽。优先沿已有字段找 producer/consumer，手动配方仅是产品的部分能力，非完整导入成果。两条假设已停止，见 [blocker](../research/blockers/BLOCKER-e142-native-profile-consumer.md)。

## T5 字段生产与非格式化消费

[Issue #21](../research/e142-picturemode-producers-and-remote-controls.md) 在同一哈希的 #0 中验证真实调用链 0x301e7b → 0x2e4e58 → 0x2e4e75（callsite0x2e50eb）→ CREATE_PARAM0x13c1f98。生产者0x301d16 将源对象 +16/+17/+18 的 byte/byte/halfword 复制到临时对象 +8/+9/+0xa；同一对象还经 0x301e88 传入0x3337cb。后者形成 `(group<<24)|(type<<16)|mode`，保存在上下文 +0x2c2c，使用函数内键→代码分支表并改变标志。这是 **verified 静态程序数据使用**，不是仅凭日志名称推断；但源对象上游、COLOR1–4 身份、保存函数及实际成像 consumer 仍 unknown，G2 未通过。

固定 `oishare` XML 的 GET desc/get 分别列出33/31个属性，POST set列出23个属性，含 ART 与子效果控制，没有明确 COLOR/PictureMode/profile 上传项，也没有允许值响应。`colorphase` 的名称不能证明十二色配置能力；社区枚举设置方法不证明 E-P7 可导入任意风格。已观察到下游调用0x333c72→0x334780，适合下一项有界离线实验；本轮未追踪其函数体、未连接设备。

# 10｜跨品牌先例矩阵（2026-10-11）

| 项目 | 公开实现/作者报告 | 可以参考 | 不可照搬 | 优先级 |
| --- | --- | --- | --- | --- |
| [GR4-LUTSmith](https://github.com/lemonadesaltbagel/GR4-LUTSmith) | 将 creative .cube LUT 拟合到 GR IV 原生调色参数并修改既有 Image Control 槽位；带误差评估和桌面工具；存在 v2.0.2 release | 原生参数拟合、ΔE 色差测量、精确目标版本的补丁护栏、UI 槽位 | 固件偏移、调色参数的自由度、刷机路径 | P0 |
| [GR IV Research](https://github.com/radium-wang/ricoh-gr4-firmware-analysis-and-feature-expansion) | 固件容器解析、只读探针和部分机型关机图片替换 | 可复现的偏移/结构调查、实验证据记录 | Ricoh TTL/工厂菜单/资源地址 | P0 |
| [Olympus legacy work](https://www.dvxuser.com/threads/e-p1-e-p2-e-pl1-hack-research.217453/) | 旧奥林巴斯固件封装格式调查；部分后续社区功能改动报告 | 可能有历史结构线索 | E-P7 新固件与信任链 | P0 |
| [gr3x-fw-hack](https://github.com/hhornbacher/gr3x-fw-hack) | 部分环境仿真与静态分析 | 环境限制、可重复研究 | 不可当作 E-P7 ISP 模拟器 | P1 |
| [FujiHack](https://github.com/fujihack/fujihack) | 富士特定机型调试、补丁、模块研究 | 渐进验证、只读探测、后期插件架构 | Fuji CPU、接口、签名、救砖路径 | P1 |
| [Magic Lantern](https://github.com/reticulatedpines/magiclantern_simplified) | 佳能特定型号扩展 | 机型特定加载器、测试框架 | 佳能引导方式与内存布局 | P2 |
| [NikonHacker](https://github.com/simeonpilgrim/nikon-firmware-tools) | 旧尼康逆向与精确固件版本补丁 | 原字节断言、格式研究 | Nikon 加解密与偏移 | P1 |
| [olympus-wifi](https://github.com/joergmlpts/olympus-wifi) | 部分 Olympus 机型的 Wi-Fi 协议 | E-P7 只读能力探测（待证明） | 不代表 ART 写入能力 | P1 |

本表的“公开实现”可能仅是作者验证，不代表第三方复现。公开仓库不等于允许重用源码；导入前逐一检查许可证和归属。

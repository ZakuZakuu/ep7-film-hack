# 08｜经核对的参考来源（2026-10-11）

以下来源公开可读，但网站和仓库会变化。后续 Codex 在使用时应重新核对页面状态与修订时间，并在 `evidence-ledger.md` 里注明。公开项目源码的引用要单独核对 license。

## OM SYSTEM 官方（高优先级）

1. [E-P7 产品页](https://explore.omsystem.com/c/en/e-p7) — TruePic VIII、16 ART、Wi-Fi/Bluetooth、机内实时预览。
2. [E-P7 官方 FAQ](https://support.jp.omsystem.com/en/support/imsg/digicamera/qa/products/ep7/) — 16 ART 滤镜名称、子变体/微调、Color/Mono 各 4 组、拍摄模式。
3. [E-P7 正式用户手册 PDF](https://my.omsystem.com/consumer/manuals/cameras/E-P7_MANUAL_EN.pdf) — 色彩配置、ART 效果列表、JPEG/RAW 规则、Film Grain Effect（主要与黑白配置相关）。
4. [E-P7 用户手册 HTML 镜像](https://manualzz.com/doc/59292907/olympus-e-p7-user-manual) — 方便文本检索，但应以官方手册核实分歧。
5. [官方固件索引](https://support.jp.omsystem.com/en/support/imsg/digicamera/download/software/firm/e1/) — E-P7 v1.1 发布 2022-02-28；是版本记录，不是直接二进制下载链接。
6. [OM Workspace 官方更新方式与提醒](https://learnandsupport.getolympus.com/ca-en/updating-your-digital-camera-or-lens) — 更新注意事项、可能无法回退等。
7. [OM 官方第三方软件版权声明](https://support.jp.omsystem.com/en/support/imsg/digicamera/download/notice/notice.html) — E-P7 明确列 Linux、Expat；**不能证明图像 ISP 的完整实现**。

## 已核实的开源研究

8. [GR IV Firmware Analysis — radium-wang](https://github.com/radium-wang/ricoh-gr4-firmware-analysis-and-feature-expansion) — 固件封装、只读探针和关机画面实验；未公开成熟任意 LUT 管理器；新内容非商业 source license。
9. [GR IIIx Firmware Exploration — hhornbacher](https://github.com/hhornbacher/gr3x-fw-hack) — 解包、Docker 模拟、硬件依赖局限。
10. [FujiHack](https://github.com/fujihack/fujihack) — 固件修改、USB 调试、自定义代码和模块设计；另一个品牌，技术不兼容。
11. [Olympus 2010 Firmware Tool 研究](https://www.dvxuser.com/threads/e-p1-e-p2-e-pl1-hack-research.217453/) — 早期奥林巴斯固件格式/工具，过于久远不可假设适配 E-P7。
12. [Olympus 固件修改历史社区讨论](https://micro43club.pro/forum/threads/modifikacija-proshivki-kamer-olympus.22086/) — 旧机型的有限功能解除，实机范围以原作者/使用者报告为准。
13. [2019 M43 社区记录](https://www.reddit.com/r/M43/comments/bnhfb5/modified_olympus_firmware_removes_30minute/) — 指向录像时长与镜头白名单补丁。历史链接可能失效。

## 旁路：协议与低风险可观测性

14. [olympus-wifi (Python)](https://github.com/joergmlpts/olympus-wifi) — 支持多个 Olympus 机型的 Wi-Fi 连接、查询、拍摄和设置；**E-P7 具体命令能力待证**。
15. [olympus-wifi 开发文档](https://olympus-wifi.readthedocs.io/en/stable/api.html) — 模型间命令能力会不同。
16. [Olympus View](https://github.com/dpolarov/olympus-view-and-delete) — OPC 读图/删图/连接管理参考；注意删除接口有副作用，第一轮禁止调用。
17. [公开存档 OPC Communication Protocol PDF](https://raw.githubusercontent.com/ccrome/olympus-omd-remote-control/master/OPC_Communication_Protocol_EN_1.0a/OPC_Communication_Protocol_EN_1.0a.pdf) — 2015 年规范，有版权及授权约束，仅供阅读参考。

## 固件样本现实限制

18. [2026 年 5 月第三方对 OM 固件下载状态的分析](https://marcrphoto.wordpress.com/2026/05/11/olympus-om-system-firmware-updates-the-situation-changed-again-may-2026/) — 报告不少旧直链不可用，**非官方消息，不可作为确认的下载入口**。

## 资料准确性特别提醒

- 一些 2026 新 PEN / OM-3 的色彩配方导入说明并不适用老款 E-P7，不应偷换机型。
- GR IV 的特定脚本、路径或引导手势与 E-P7 没有已验证兼容性。
- 在社区里看到的「LUT」可能只是 Lightroom 中对 RAW/JPEG 的后期套用，必须找机内 JPEG 或可复现实机证据。
- 请更新这些来源的状态，而不是把本文件当成永远正确的技术事实。

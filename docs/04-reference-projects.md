# 04｜参考项目如何使用

## 1. Ricoh GR IV：过程方法（最优先）

https://github.com/radium-wang/ricoh-gr4-firmware-analysis-and-feature-expansion

仓库明确记载：固件容器解码、版本/校验、RTOS 映射、设备树、USB/MTP 的只读枚举、工厂/调试接口和通过脚本定制关机图像。最值得借鉴：

- 按 **model + firmware version + SHA-256** 做每条结论的索引。
- 研究日志含实验和纠错；把只读实验、风险写入实验分开。
- 工具、文档、样本与测试分层；没有固件样本时运行 host-side tests，且不把 mock 当硬件模拟。
- 许可证要注意：2026-10-11 仓库 README 表明新增内容采用**非商业源代码许可证，非 OSI 开源**；不要整段复制工具或源码到本项目，优先读方法、独立实现。

**不可迁移**：GR IV 的特定固件头、脚本语法、存储路径、工厂模式进入方法与 ARM/RTOS 映射。也不要把网上的“自定义 LUT 成功”说法当成已发布的通用工具。

## 2. Ricoh GR IIIx firmware exploration：镜像仿真限制

https://github.com/hhornbacher/gr3x-fw-hack

研究过固件提取、Docker 中运行部分用户态软件、模拟共享内存/IPC，项目说明**无法完整启动相机系统、QEMU 内核启动未成功**。启示：即使有 Linux 根文件系统，ISP、硬件驱动和共享内存依赖仍可能让纯云端模拟停步。

## 3. Olympus 历史固件逆向：格式线索，不是兼容承诺

- 早期格式工具：https://www.dvxuser.com/threads/e-p1-e-p2-e-pl1-hack-research.217453/
- 历史社区讨论：https://micro43club.pro/forum/threads/modifikacija-proshivki-kamer-olympus.22086/
- M43 用户讨论：https://www.reddit.com/r/M43/comments/bnhfb5/modified_olympus_firmware_removes_30minute/

有早期 OlympusFwTool 的使用示例和社区修改旧机型录像限制/白名单的案例。但早期 E-P1 系列与 2021 年 E-P7 可能隔了多代打包机制；不允许直接采用旧解密/刷写流程。

## 4. FujiHack：长期扩展架构参考

https://github.com/fujihack/fujihack

它有 PTP/USB 调试器、固件补丁、RTOS API、模块和 UI 等项目经验，也明确风险及部分机型差异。**方法参考**：先得到安全的只读可观测性，再讨论注入。FujiHack 的可用工具链和补丁绝不可直接用于 Olympus。

## 5. Olympus Wi-Fi：预设管理器的较低风险平行线

- Python：https://github.com/joergmlpts/olympus-wifi
- 参考文档：https://olympus-wifi.readthedocs.io/en/stable/api.html
- 独立相机文件管理器：https://github.com/dpolarov/olympus-view-and-delete
- 早期 OPC 协议规范（需尊重原版权/许可）：https://raw.githubusercontent.com/ccrome/olympus-omd-remote-control/master/OPC_Communication_Protocol_EN_1.0a/OPC_Communication_Protocol_EN_1.0a.pdf

这些项目可证明若干 Olympus 机型存在网络远程控制、能力查询或照片管理。**并不验证 E-P7 支持 ART 配方写入或自定义 LUT**。用户核心诉求仍是机内预览/直出；仅有手机滤镜不算主线成果。

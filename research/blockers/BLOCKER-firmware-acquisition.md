> Historical T0 blocker; access resolved for the hash-verified E-P7 candidate by [T1](../e142-first-sample-analysis.md) / [T1.1](../e142-squashfs-validation.md). Remaining ART/signature/recovery gates are not implied passed.

# BLOCKER｜E-P7 完整固件研究介质尚未建立

日期：2026-10-11；范围：T0 / Issue #1；型号：Olympus PEN E-P7；目标官方版本：1.1（并非用户机身版本）。

## 被阻塞的目标与 gate

G1：建立可合法取得、来源明确、完整的 E-P7 样本及 SHA-256。没有样本，不能进入 E-P7 容器/资源/架构研究，更不能产生 ART 补丁。G2–G6 也尚无通过证据；本报告不将未知的加密/签名/ISP 限制判定为已经发生的技术阻塞。

## 原始证据与两条独立、有限的调查

1. **静态官网获取路径**：GET [官方固件索引](https://support.jp.omsystem.com/en/support/imsg/digicamera/download/software/firm/e1/)，E-P7 行给出 1.1 / 2022-02-28。沿该行明确链接 GET [更新说明](https://dl01.om-digitalsolutions.net/ww/ud2/ENU/0001/1420/index01a.html)，结果为 2,324-byte HTML，对焦精度修正，没有完整镜像链接。响应 SHA-256 `db7c5707bd005903b05422e6af56a9b2b88ee3c0f1074b1dd678c30f9469e2bc` **仅为 HTML 哈希**。未猜测二进制 URL 或向后端枚举。
2. **官方更新器中介路径**：读取 [OM Workspace 更新说明](https://learnandsupport.getolympus.com/ca-en/updating-your-digital-camera-or-lens)。文件传送属于 USB 连接相机、同意软件协议并开始更新的流程；资料没有建立一个本轮可执行、保证不写设备的 E-P7 完整镜像导出/仅下载路径。云端没有相机或已取得样本，未安装/运行更新器，也不要求用户启动更新。

两条官方路线结束后未得到样本，按停止条件结束获取调查。另对已有第三方文章中明确链接的 updater 只做一次公开 GET，收到 JavaScript/cookie challenge，未得到内容/来源/授权；这是访问限制，不能作为官网样本不可获取的独立证明。[来源记录](../source-access-review.md) 给出命令和响应元数据。

## 是技术不可能，还是证据暂缺？

**证据暂缺，BLOCKED for this task；不宣称 E-P7 无法破解、固件必然加密、签名必然阻止修改或全部下载不可用。** 未取得完整固件，故 firmware SHA-256、字节大小、头部、文件偏移、加载地址、ISA、签名/CRC 与 ART 资源结构全为 unknown。只取得公开版本记录不能满足 G1。

风险：把更新流程误作只读采集可能触发设备写入；官方提醒中断可导致不可用且不能回退旧版。这也是不能用唯一日常机身做未经审查获取实验的理由。

## 替代路线与体验代价（按优先级）

1. **既有原生 Color1–4 参数方案**：厂家文档支持保存和切换，并维持机内预览/JPEG；没有任意 LUT、独立 hue-sector 矩阵或新 ART 算子的证据。只能在原厂参数边界内改进，目标复杂负片偏色能否表达尚未测试。
2. **单独授权的只读能力调查**：研究 E-P7 是否暴露配置读取/枚举能力。若有，也只证明接口存在；远程预设管理需另证写入能力并另授权，不会增加参数表达范围。不能直接实例化 olympus-wifi 相机类，构造器会切换相机模式。
3. **外部 RAW/JPEG 流程**：复用成熟 RAW 工具做视觉目标基线，牺牲自定义风格机内预览和 JPEG SOOC；应由用户明确选择，不当作主目标完成。

自定义处理算子、交叉编译、固件移植均延期，无执行环境/帧访问/性能/安全安装证据时不开发。

## 恢复该路线所需最小输入

当前 T0 不需要用户提供文件、插相机或分享任何设备身份信息。评审后若选择固件路线，先取得厂商明确的合法完整 E-P7 镜像获取/本地保存方式；样本仅保存在用户私有本地环境，向仓库提供来源、版本、长度、SHA-256 的脱敏记录。取得文件本身不自动通过 G2–G5。若改走本地只读路线，先提供机身菜单中的型号/固件版本（无需序列号），再单独评审实际命令与授权。

# 09｜可行性闸门与硬性阻塞

**不是所有能在另一台相机上完成的改机，都能在 E-P7 上完成。** 我们要求“跨品牌社区实现先例 + E-P7 专属证据 + 最小验证”。

| Gate | 继续推进必须具备 | 如果证据不足 |
| --- | --- | --- |
| G0 社区先例 | 有公开实现及其精确机型、版本、许可和验证范围 | 仅作研究问题，不进入产品开发 |
| G1 可研究介质 | 合规的 E-P7 固件样本或经过确认的只读协议入口 | 停止虚构固件解包，调查合法获取与替代路径 |
| G2 ART 路径定位 | E-P7 特定版本下真实的滤镜 ID、数据表、调用或 ISP 参数的证据 | 不造补丁、不宣称已找到 LUT |
| G3 色彩表达能力 | 目标 LUT 在原生可控参数上具有可量化的拟合效果 | 列出不可表达之处，不承诺 1:1 胶片色彩 |
| G4 可重复离线修改 | 版本限定、原始字节 guard、校验/签名约束、差分和合成测试 | 仅保留离线研究成果 |
| G5 实机安全 | 可独立验证的升级接受与恢复方案、单独用户授权 | **禁止真实相机写入** |
| G6 用户体验 | 在 E-P7 上可切换、取景预览与 JPEG 实际呈现目标效果 | 不宣称“机内直出已实现” |

## 硬性 Blocker 处理流程

写入 `research/blockers/BLOCKER-<topic>.md`，包含：(1) 被阻塞的目标和 gate；(2) 原始证据、型号版本；(3) 已试过的两条不同、有限的验证路径；(4) 是技术不可能还是证据暂缺；(5) 备用路线及其对“机内直出”体验的损失；(6) 需要用户决定或提供的最小信息。

**按证据停止，不按 token/迭代数硬熬。** 有新的实证再恢复。

## 先例不能直接迁移

- [GR4-LUTSmith](https://github.com/lemonadesaltbagel/GR4-LUTSmith) 把创意 LUT 拟合到 GR IV 自带的色彩参数，非通用的任意 LUT 运行时。E-P7 的色彩表达自由度可能更低。
- [GR IV firmware research](https://github.com/radium-wang/ricoh-gr4-firmware-analysis-and-feature-expansion) 的工厂脚本及写入接口为理光特有。
- [Magic Lantern](https://github.com/reticulatedpines/magiclantern_simplified) / [FujiHack](https://github.com/fujihack/fujihack) 的加载器、CPU/OS 和地址映射不能直接复制。
- [NikonHacker](https://github.com/simeonpilgrim/nikon-firmware-tools) 的固件校验/补丁只针对其支持的尼康机型。

一项可复现的 E-P7 证据，胜过大量看似完整但无法验证的代码。

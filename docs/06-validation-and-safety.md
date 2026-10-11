# 06｜实验边界、设备安全与数据管理

## 研究安全等级

- **L0（允许立即执行）**：公开文献与开源许可核对；离线代码库阅读；自制合成固件的解析器测试。
- **L1（有合法文件才执行）**：原厂升级固件样本的只读分析、解包和哈希；合成数据的离线 patch 试验。
- **L2（须用户另行授权）**：物理 E-P7 的只读 USB/Wi-Fi 枚举、拍摄基线样片、采集带隐私信息的设备响应。所有实际命令必须事先审查是否真正无副作用。
- **L3（默认禁止）**：用修改固件升级/降级、写入内部闪存、调用未知工程模式写入接口、直接更改硬件 ISP 寄存器、调试器接线。**即使有用户泛泛同意“开发”，也不代表批准 L3；须有单独的安全方案、恢复途径和具体确认。**

## 进入 L3 的最低前置要求（缺一不可）

1. E-P7 **同型号、同固件版本**验证的镜像与目标偏移。
2. 证明升级链路接受此类修改（签名、CRC、型号与版本约束）；不能只看打包工具输出成功。
3. 真实、已验证的恢复/回滚途径，明确是否可能不可恢复变砖，且不依赖未证实的论坛传言。
4. 样片、设置和存储介质数据完整备份；电源和操作中断风险已评估。
5. 明确说明是否会影响保修、法规或许可证；用户知悉并逐项批准。
6. 先在额外测试机或可恢复仿真平台验证（若可用），而不是首选唯一日常使用的机身。

官方升级说明特别提醒中断更新可使相机不能使用，也提醒部分型号不能回退旧版本。出处：https://learnandsupport.getolympus.com/ca-en/updating-your-digital-camera-or-lens

## 本地硬件任务的输入输出格式

任务卡必须包含：

```
Purpose:
Model: Olympus PEN E-P7
Firmware version: (read from camera; never guess)
Commands to run: (explicit command list)
Side effects: none / list known risks
Data collected: (fields, not full sensitive payload)
Local-only paths: (not synced to public repo)
Expected response: ...
Abort conditions: ...
How to sanitize report: ...
```

首次只读操作不在本包内预先提供 Wi-Fi 请求脚本，因为 E-P7 的实际控制协议和可用端点尚未经过实机验证。

## 隐私和版权

- 官方固件 / 解包系统文件 / proprietary LUT / RAW 与照片样本：默认 `private_samples/`，不可入库。
- 任何 USB/Wi-Fi 日志：删去 serial、MAC、SSID、设备 ID、定位、图像和个人目录路径。
- 如果使用第三方源码，核对逐文件许可证；尤其 GR IV 仓库近期的非商业许可，**不能按宽松 MIT/Apache 假定直接复制**。
- 公开发布的技术发现优先用结构描述、示意/合成数据，谨慎对待可能含第三方版权的数据段。

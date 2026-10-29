# Workspace HSL 阶段原创模型

结论：HSL 阶段已原创实现并接入默认预览；350 套配方、1,486,100 个 RGB / YCbCr 像素与原生输出完全一致。
这仅证明指定软件阶段一致，不代表 RAW 显影或相机 JPEG 逐像素一致；影调、暗角仍为明确标注的近似。

## 范围与来源

- 本阶段从 main `e2c62b3` 新建 `codex/workspace-hsl-exact`，不再推送旧研究分支。
- 对象为 Workspace 程序 2.3.0.22 内的 Acacia DLL 1.0.3.1；DLL 完整 SHA-256 仅在私有资格报告。
- 参考 [fishcu 固定提交 `539fcf1`](https://github.com/fishcu/oly_fw_analysis/tree/539fcf1) 的表结构与色区研究；代码为本仓库原创。
- 本地 Ghidra / Capstone 证据及原生 ctypes 调用核实了对象工厂、表展开、参数转换和像素回调 ABI。
- 原厂 DLL、反编译、照片及详细数据只放私有任务临时目录，均不提交；源码不嵌入任何原厂 LUT。

## 算法与数据边界

`workspace_hsl.py` 实现 8 位 RGB / YCbCr 阶段，所有系数表和 LUT 在运行时从已核验 DLL 读取。
共享 3028 字节表的 SHA-256 为 `a33d64bdb78ac41ba24ccbff820380f563211a095ac08a12a7c37a51b5c00531`。
处理链为 RGB → 8 位 YCbCr → 10 位亮度 / 有符号色度 → 定点极坐标 → HSL → YCbCr → RGB。
极角一圈为 32768 单位；色度半径用已穷举验证的 `workspace_polar.py`，不使用 HSV 近似。
12 个记录按偶数轮盘项、奇数轮盘项分成两组，每组 6 个；分别选区后将两组 H/S/L 增量相加。
选区同时考察循环角度、半径和亮度范围；保留原生的独立命中标志、归一化、舍入和限幅。
LUT 的 7 位有符号基值 / 斜率展开为 14 组权重曲线，每色区 16 段，按 4 位小数坐标插值。
H/S 权重由角度、半径和亮度门相乘；L 的角度门使用 H 调整后的角度，因此 H/L 并非独立相加。
S 使用每色区、正负不同的固定点转换；负整数除法向零截断，乘积和右移的次序与原生一致。
相机配方 H 的正方向与桌面隐藏 H 参数相反；适配层和原生验证器均显式转换符号。
L 使用本机隐藏参数表；最终极角循环、半径 / 亮度限幅后，使用本机三角 LUT 回写色度。
RGB 通道转换保留原生双精度运算顺序、截断和 8 位限幅，不擅自替换成标准库矩阵。
本阶段内部没有新增 gamma；它在完整 Workspace RAW 管线中相对 gamma 的位置仍未证明。
中性阶段也会经历 8 位 RGB / YCbCr 往返，可能有微小量化差，不用强制恒等掩盖原生行为。

## 原生一致性验证

`workspace_native_check.py` 只在 64 位 Windows 运行，先核对 DLL 版本、机主提供的 SHA-256 和表哈希。
通过本机导出工厂创建类型 4 对象，展开 LUT，设置三组参数，调用实际 HSL 阶段，最后释放对象。
缓冲区、像素步长、行宽、位深与格式按反编译核实的 ABI 构造；没有调用、连接或刷写相机。
每色区 H/S/L 分别覆盖 −7、−5、+5、+7；另含全中性和固定种子 74 的 30 套随机组合。
每套输入包含 150 个边界 / 极端像素和 4096 个随机像素，两种通道格式共 350 套调用。
结果：系数逐项相同；1,486,100 个输出像素零差异，最大通道误差为 0 个 8 位码值。
资格报告只有全部调用通过后才生成，绑定 DLL 哈希及实现源码哈希；任何差异立即失败。
CI 只运行原创合成数据测试，不依赖厂商软件；本机真实 DLL 验证与 CI 合成验证分开报告。

## 默认模型与后备

CLI / 浏览器默认优先已验证 Workspace HSL；`model.py` 保留旧近似模型，不改写其校准参数含义。
私有资格报告缺失时显示“近似后备”；显式指定的报告缺失、过期或 DLL 哈希不符则报错，不静默降级。
资格报告路径可由 `--workspace-qualification` 或 `EP7_WORKSPACE_QUALIFICATION` 指定。
`EP7_WORKSPACE_DLL` 可在 WSL / Windows 路径不同的情况下覆盖 DLL 位置，但仍须通过相同哈希检查。
默认也识别本任务私有 `hsl-qualified.json`；临时目录重置后需重新验证，不假装模型仍已加载。
`--model approximate` / `EP7_RECIPE_MODEL=approximate` 可显式选择旧模型。
预览分块执行向量化内核；约 126 万像素在本机约需 1.2–1.5 秒，支持采样点和整图输入。
连续优化器只用旧模型提出起点；整数配方打磨、保留像素验证和最终报告使用当前选定模型。
影调、暗角保留旧近似尾部，仅应用一次；UI / API / 拟合报告均标明此混合范围，不称其为精确模型。

## 现有实拍复核

采用已有 B2 原厂 / v2 JPEG，先小位姿配准，再在固定参照区域比较；没有要求机主补拍。
| 项目 | 实拍 | 新 HSL 模型 |
| --- | --- | --- |
| 红色 H −3，色相差中位数 | +11.25° | +12.07° |
| 手机黄色跨目录，色相差中位数 | −13.79° | −15.58° |
| 蓝色 L −5，ΔL* 中位数 | −2.44 | −4.18 |
| S 全 −5，红色最终 C* | 6.95 | 8.01（旧模型约 38.00） |
| S 全 −5，红色 ΔL* | −5.15 | −5.75（旧模型约 +10.81） |
手机目录的固件身份仍未从文件确认；这里只比较既有区域变化，不把它当独立固件身份验证。
蓝色幅度仍偏强，零 H/L 对照也有 8 位往返差异；已显影 JPEG 后再应用软件阶段不等同相机 ISP 中间域。
因此不宣称相机实拍幅度精确，也不将相机区域误差冒充软件原生逐像素误差。

## 复现

在仓库外的 Python 环境安装 `tools/recipe_studio/requirements-research.txt`，确认使用上述 DLL 版本。
Windows 下先从私有清单核对 DLL SHA-256；以下 `$dll` / `$sha` 为机主本机路径和已确认的指纹。
```powershell
python -m tools.recipe_studio.workspace_native_check --dll "$dll" --expected-sha256 "$sha" --report "\\wsl.localhost\Ubuntu\tmp\ep7-workspace-research\hsl-qualified.json"
python -m tools.recipe_studio --workspace-qualification "\\wsl.localhost\Ubuntu\tmp\ep7-workspace-research\hsl-qualified.json" serve
python -m tools.recipe_studio --model approximate serve
```
影调和暗角未开展新一轮逆向；当前无需机主补文件、补拍或安装额外分析工具。

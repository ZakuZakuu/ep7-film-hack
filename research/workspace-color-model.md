# Workspace COLOR 软件模型研究

结论：已找到 COLOR 表和 H/S/L 候选接口，并用现有实拍确认 H/L 变化；精确软件模型尚未闭合。
实拍还证明当前近似模型有结构性偏差：降低饱和度时，其红色区域亮度预测方向与相机相反。
本次保留近似模型，不把这些区域观测冒充 Workspace 的精确像素公式。

## 软件侧证据与阻塞
- 基线为 main `e0a4d86`；参考固定为 [fishcu `539fcf1`](https://github.com/fishcu/oly_fw_analysis/tree/539fcf1)。
- 本机为 `F:\Program Files (x86)\OMDS\OM Workspace`，程序文件版本 2.3.0.22。
- 93 个 DLL 的 SHA-256、地址及指令证据仅存私有 `/tmp/ep7-workspace-research/`，不入库。
- Acacia 和 Lilac 均含完整 3028 字节表，SHA-256 为 `a33d64bdb78ac41ba24ccbff820380f563211a095ac08a12a7c37a51b5c00531`。
- Acacia 的 `OlyGetAcaciaInstance` 类型 4 分支复制此表；虚表 / 成员引用连接到候选消费者。
- 消费者可见扇区选择、固定点乘法、算术右移和限幅；另一接口接收并重排三组 12 项参数。
- Capstone 静态追踪已由 Ghidra 11.0.3 反编译补充确认，工具链阻塞已解除。
- 已确认 8 位回调包含 RGB / YCbCr 转换、定点极坐标、两组 6 区 HSL 处理及像素写回。
- 原创 `workspace_polar.py` 与 Acacia 原生极坐标函数穷举 1,048,576 组输入，角度 / 半径零差异。
- 新增 3 项纯合成测试通过；该内核不代表完整 HSL 模型，未替换现有 RGB 预览模型。
- 已受控调用 HSL 阶段：中性及自定义黄色 H / 蓝色 L 三组各 100 个合成 YCbCr 像素正常返回。
- 完整色区 / 系数 / LUT 及 RGB 写回仍待原创实现和原生对照；gamma 顺序、影调和暗角仍未闭合。
- 原生调用脚本、私有 DLL 哈希及逐项报告仅在任务环境，未复制原厂源码或表数据。

## 已用现有照片完成的验证
全部 35 张 JPEG 已核对元数据，14 个 ORF 已用相同 LibRaw 设置显影；无照片、EXIF 或派生图入库。
B2 前 4 对的 ISO 均为 800、快门均为 1/25 秒，配对 S / 影调一致，自动白平衡系数略有差别。
原厂第 5 张实际为 COLOR1 全区 S −5 / 影调 0，而非 Natural；据此与第 1 张 S 全 0 配对。
建立 19 组几何比较：15 组通过小位姿配准，4 组位移超门槛拒绝；不放宽门槛保留不可靠结果。
另对 2 组跨目录手机图用第二种方法 SIFT 单应性配准，仅比较声明的屏幕平面，两组均通过。
7 张无合适配对的 JPEG 用于元数据 / 场景归类；另 28 张参与区域比较。详细报告及派生图只存私有 `/tmp`。

| 观测 | 实拍结果 | 当前近似模型 |
| --- | --- | --- |
| 手机黄色，跨目录同 S / 影调 | HSV 色相 49.94° → 36.40° | 未作独立精度验收 |
| B2 COLOR3 红色 H −3 | 像素色相差中位数 +11.25° | +9.95° |
| B2 COLOR2 蓝色 L −5 | ΔL* 中位数 −2.44；C* 29.28 → 28.34 | ΔL* −3.36；C* → 19.62 |
| 原厂全区 S −5，红色 | C* 67.47 → 6.94；ΔL* −5.15 | C* → 37.94；ΔL* +10.91 |
| B2 COLOR4，全 H/L 为 0 | 蓝 / 红 / 灰 ΔL* 为 −0.12 / −0.20 / +0.05 | 中性恒等 |

表中 Δ 为匹配像素差的中位数；前后 C* 为各自中位数。HSV 色相、HSL 亮度、Lab L* 不混用。
B2 在最长边 1296 像素的代理图上配准，内点重投影误差中位数约 0.65–0.75 像素。
将变换额外扰动 ±1 个代理像素，蓝 ΔL* 为 −2.47…−2.43，红 ΔH 为 +11.18°…+11.29°。
固定白平衡 RAW 对照中，对应蓝 ΔL* 约 −0.06、红 ΔH 约 +0.02°；支持 JPEG 变化主要来自处理。
RAW 使用同一参考 WB、`no_auto_bright=True`、`half_size=True`、16 位 sRGB、`gamma=(2.4,12.92)`。
这不是 Workspace 显影，RAW / JPEG 的输入域与区域掩码不同，不将两者差值直接相减校正。
上述内点残差不是独立配准精度；以区域扰动分析补充检查，不报告虚构置信区间。
手机配准内点为 506 / 547、565 / 591，95% 重投影残差分别约 1.36、1.24 个代理像素。
B2 的 H/L 配方依据 [#58](https://github.com/ZakuZakuu/ep7-film-hack/issues/58#issuecomment-6416835422) 的机主记录。
两个手机目录的固件身份尚未从文件中确认，只报告跨目录变化，不据此拟合 H 步长。
其他手机重复组存在屏幕内容、曝光或白平衡变化；不用它们估算严格的相机重复性误差。
深蓝的零 R 通道保留并记录限幅比例；区域只按参照图选择，低色度不报告无意义色相。
B2 COLOR2 蓝区和 COLOR3 红区的单通道限幅较多，幅度依赖场景；绿色 L 尚无充分覆盖。
这些是局部实拍证据；Workspace 精确逐像素误差仍未测，影调 / 暗角未被单独隔离验证。

## 原创工具与复现

在仓库外的 venv 安装 `tools/recipe_studio/requirements-research.txt`；报告只能放系统临时目录。

```sh
python -m tools.recipe_studio.workspace_probe '/mnt/f/Program Files (x86)/OMDS/OM Workspace' --report /tmp/ep7-workspace-research/inspection.json
python -m tools.recipe_studio.photo_validation /tmp/ep7-workspace-research/photo-pairs.json --report /tmp/ep7-workspace-research/photo-observations.json
python -m tools.recipe_studio.workspace_compare /tmp/ep7-workspace-research/model.tif /tmp/ep7-workspace-research/workspace.tif --report /tmp/ep7-workspace-research/error.json
python -m unittest discover -s tests -p test_workspace_research.py -v
```

私有 photo manifest 含 `format: ep7-photo-observations-v1` 和 `pairs`；每对有 `id/reference/moving/regions`。
每个 region 有归一化 `box: [left,top,right,bottom]`，可选 `min_saturation/max_saturation/hue_degrees`。
平面配准另设 `registration: planar`、`plane_box`；默认 ORB 小位姿。拒绝记录显式保留，不填零。
区域工具使用最长边 1296 像素代理、按 ICC / sRGB 解读，无曝光或 WB 拟合；输出不称为精确像素误差。
TIFF 比较器保留 8 / 16 位码值，只接受同尺寸、位深、非空 ICC 的单页 RGB TIFF，不缩放 / 配准。
定位器不执行 DLL、不导出原厂字节；直接引用仅覆盖 PE 异常表范围，不能保证找全间接引用。
全部代码原创；上游工具、汇编、文档及原厂数据未复制。合成测试仅验证工具，不证明像素算法。

## 后续对照准备（当前无需追加拍摄）

现有 ORF 足够；后续从同一个 B2 原厂 ORF 导出中性及单项效果图，可消除拍摄间差异。
中性设 COLOR1、12 区 S 全 0、三段影调 0、创意暗角 0，固定曝光 / WB / 降噪 / 镜头校正 / 裁切。
导出原尺寸 sRGB RGB TIFF，优先 16 位、无压缩并嵌入 ICC；如仅支持 8 位则全部统一，不用 JPEG。
每次从中性重置：各色区 S −5 / +5；各影调 −7 / +7（以 UI 实际范围为准）；创意暗角 −5 / +5。
再次导出中性检查重复性；私下保留原始设置记录。若处理发生于 gamma 前，应比较相同中间缓冲区。
接续先闭合 HSL 输入域 / ABI 与原生对照，再实现公式；本次未追加其他阶段，也未要求机主补拍。

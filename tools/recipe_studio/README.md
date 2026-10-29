# E-P7 配方工作室

电脑端近似预览与拟合工具，不读取固件、不连接相机、不上传照片。实际机内效果必须用 E-P7 拍摄校准；RAW 的 LibRaw 显影尤其不等于原厂 Natural。建议从固定白平衡、曝光的 Natural 或默认 COLOR JPEG 开始。

## 安装与启动（Python 3.12）

在仓库根目录运行。Windows 推荐直接调用虚拟环境的 Python，不需要修改 PowerShell 执行策略：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r tools/recipe_studio/requirements.txt
.\.venv\Scripts\python.exe -m tools.recipe_studio serve
```

macOS / Linux / WSL：

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r tools/recipe_studio/requirements.txt
.venv/bin/python -m tools.recipe_studio serve
```

打开 <http://127.0.0.1:8765>。载入基准图，拖动 12 色 H/S/L、影调与暗角滑块；对比分界左侧为原图，右侧为效果。配方支持导入、导出和归零。自动拟合先选择方式，再载入对应目标文件。拟合通常数秒；预算内停止，并报告未收敛或未覆盖色区。修改输入时不会自动覆盖正在编辑的配方。

所有照片只进入本机进程内存，关闭服务后释放；浏览器无第三方脚本、字体或服务。只监听 loopback，禁止外部 Host、跨源写入与无令牌写入。不要改为公网监听或通过共享代理开放此服务。`Ctrl+C` 停止。

Windows 后续命令把 `python` 替换为 `.\.venv\Scripts\python.exe`；macOS/Linux 替换为 `.venv/bin/python`。路径带空格请加引号。CLI 的输出目录必须在仓库外，如 `C:/Users/你的用户名/ep7-recipes/`、`~/ep7-recipes/`；Cloud 使用私有 `/tmp`。不在仓库保存照片、预览或校准数据。

## CLI

```sh
python -m tools.recipe_studio preview /private/base.ORF /private/recipe.json --output /private/preview.png
python -m tools.recipe_studio fit /private/base.jpg --lut /private/look.cube --output /private/fit.json --report /private/error.json
python -m tools.recipe_studio fit /private/base.jpg --target /private/aligned.jpg --output /private/fit.json --report /private/error.json
python -m tools.recipe_studio fit /private/base.jpg --reference /private/other-scene.jpg --output /private/start.json --report /private/error.json
```

预览长边最多 1600 像素；浏览器显示长边最多 900，拟合代理最多 1024。成对图先检查原始尺寸，再缩小；不自动配准。支持带 RGB ICC 的 JPEG/PNG/TIFF（转 sRGB）；无标记图像按 sRGB，缺 ICC 的 Adobe RGB 标记拒绝。ORF 采用 LibRaw，相机白平衡、禁用自动提亮、16 位 sRGB；生成预览为 8 位 sRGB PNG，不复制 EXIF。

LUT 只接受以已显影 sRGB 为输入的 3D `.cube`（边长 2…128、R 最快，含 DOMAIN）或无损 8 位 RGB Hald PNG/TIFF（level 2…12）。不支持 1D/shaper、Log、ACES 或自动识别 LUT 输入域。Hald 按数值读取、不做 ICC 转换；超出显示域的 LUT 输出裁切并提示。

成对/LUT 拟合使用 CIEDE2000，报告整数化配方的保留像素误差和各色区误差。异场景模式只比较共同色区的 H 圆均值、S/V 分位统计，报告的是统计色块误差，最高评为“近似”，不是照片配准或风格分离。没有覆盖的参数保持初值，不把它们解释为已验证的零。`--initial` 可指定初值；`--max-nfev` 5…300、`--samples` 64…4096 可调整预算（异场景不使用 samples）。

## 用私人 RAW+JPEG 校准

在仓库外创建 `pairs.json`。`raw` / `jpeg` / `recipe` 均相对此清单，照片须同场景、曝光、WB、镜头和裁切。至少一对中性训练数据；Natural 与 COLOR 默认不是同一个基线，请分开建立校准文件。示例中的裁切尺寸是格式演示，必须用你自己的图像核实，不能照抄：

```json
{
  "format": "ep7-calibration-pairs-v1",
  "pairs": [
    {"raw": "neutral.ORF", "jpeg": "neutral.jpg", "split": "train", "raw_crop": [8, 8, 5184, 3888]},
    {"raw": "known-style.ORF", "jpeg": "known-style.jpg", "recipe": "known-style.json", "split": "train", "raw_crop": [8, 8, 5184, 3888]},
    {"raw": "held-out.ORF", "jpeg": "held-out.jpg", "recipe": "known-style.json", "split": "validation", "raw_crop": [8, 8, 5184, 3888]}
  ]
}
```

可选 `raw_crop` / `jpeg_crop` 为解码并转正方向后的 `[left, top, width, height]` 像素整数。裁切后仍须完全同尺寸和对齐；不接受用缩放掩盖差异。省略 `recipe` 只表示你明确声明该对数据是当前模型的中性基准，工具无法验证机内实际设置。

```sh
python -m tools.recipe_studio calibrate --pairs /private/pairs.json --output /private/calibration.json --report /private/calibration-report.json
python -m tools.recipe_studio --calibration /private/calibration.json serve
```

命令拟合 RAW→JPEG 的 RGB 增益与 gamma，并仅对有已知非零配方的效果拟合全局增益；没有相应配方不会校准该效果。不会自动恢复 ISP、相机色彩矩阵、色区边界或任意曲线。不同镜头、ISO、WB、场景需检查独立 validation 误差；没有 validation 会明确提示。只有训练误差下降不证明模型准确。现阶段没有用户实拍校准数据；附带模型仍为未校准近似。

校准文件集中定义色区中心、平滑宽度、H/S/L 增益、L 原生换算、影调基函数强度、暗角几何、RAW 基线和质量阈值。S 范围默认 5；可显式改为 7 用于后续能力确认后的配方设计，不代表原厂相机支持扩展范围。

配方协议见 [docs/recipe-format.md](../../docs/recipe-format.md)，模型证据与限制见 [T26 报告](../../research/t26-recipe-studio.md)。参考固定版本 [fishcu/oly_fw_analysis@539fcf1](https://github.com/fishcu/oly_fw_analysis/tree/539fcf1fa9eda5fdef8ede4deeab94a4691d94c3) 的参数事实与思路；本工具原创实现，未复制上游代码、汇编、文档、原厂表或曲线。

## 测试

```sh
python -m unittest discover -s tests -p test_recipe_studio.py -v
```

测试全部生成合成数组，不下载照片或访问相机；专用 CI 安装所需依赖。真实公开样片仅在私有目录手动验证，来源、CC0 许可和哈希记录在研究证据中。依赖使用 NumPy、SciPy、scikit-image、Pillow、rawpy/LibRaw 和 Flask，许可由各自发行包提供；不需要 GNU 模拟器、上游源码或固件环境初始化。

## 给 LUT → 得到配方 JSON → ep7wifi

无需照片，先运行：

```sh
python -m tools.recipe_studio fit --lut /private/ep7-recipes/luts/look.cube --output /private/ep7-recipes/compare/look.json --report /private/ep7-recipes/compare/look.report.json
```

可加 `--photo /private/photo.jpg`；生成同名 `.compare.png`（原图 / LUT / 配方加近似白平衡）。
网页“自动拟合”选“仅 LUT”，载入 LUT 后直接开始；基准照片可选。可下载对比图，或采用不拆分白平衡的版本。
配方 JSON 之后才交给现有 ep7wifi 流程；白平衡建议须手动设置，不由工具自动写入。
报告含质量、整体及 12 色区 ΔE00、实际模型、白平衡近似建议、不拆分配方和不可表达效果。
无本机 Workspace 资格时明确使用近似后备。白平衡每档幅度未经标定，影调仍近似。
支持 .cube 边长 2 至 128、8 位 Hald level 2 至 12；不支持 Log/RAW/混合 shaper。
权重与误差解释见 [研究说明](../../research/lut-only-fit.md)。

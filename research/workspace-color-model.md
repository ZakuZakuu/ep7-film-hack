# Workspace COLOR 软件模型研究

结论：已在本机找到完整 COLOR 表及使用它的 H/S/L 候选函数；尚未还原、验证精确像素模型。
本次未替换 Recipe Studio 的近似模型，不能声称预览已经等同 Workspace 或相机 JPEG。

## 已确认的事实

- 基线为 main `e0a4d86`；参考固定为 [fishcu `539fcf1`](https://github.com/fishcu/oly_fw_analysis/tree/539fcf1)。
- 本机路径为 `F:\Program Files (x86)\OMDS\OM Workspace`，程序文件版本为 2.3.0.22。
- 递归清点 93 个 DLL；版本、全部 DLL 的 SHA-256、地址与指令证据仅存任务私有 `/tmp/ep7-workspace-research/`。
- `OlyAcacia.dll` 和 `OlyLilac.dll` 均含完整 3028 字节表，逐字节相同。
- 表的 SHA-256 为 `a33d64bdb78ac41ba24ccbff820380f563211a095ac08a12a7c37a51b5c00531`。
- Acacia 是 PE x64；导出 `OlyGetAcaciaInstance` 的类型 4 分支复制该表到新对象。
- 从该对象虚表和成员引用追到表消费者：包含扇区选择、固定点乘法、算术右移和限幅。
- 另有接口接收三组指针；后续按 12 项读取并重排，分别更新记录内的三个系数字段。
- 这些是静态数据流证据，尚无受控 DLL 调用或原生像素对照，不把候选方法命名为完整渲染器。

## 未闭合与停止点

1. 第一种方法为 Capstone：按 PE 异常表的函数边界解码，并追踪 RIP 引用、虚表和对象成员。
2. 第二种方法尝试 Ghidra headless：下载 NSA 官方 11.0.3 及独立 Linux Java 17。
   Adoptium API 返回 403；官方 GitHub 下载亦持续缓慢，停止时工具仍不完整，未运行反编译。
3. 按 AGENTS.md 的两种方法上限停止；未绕过检查，未尝试未知调用约定的 DLL 调用。
4. 尚未确定色彩空间的标准定义、色区边界及所有插值公式、全部 LUT 用途、gamma 前后顺序。
   三段影调、创意暗角的实际像素入口也未闭合，不能用固件 CPU 配置顺序推断软件执行顺序。
5. 模型替换、精确 H/L 调用与逐像素误差均未完成；当前误差为“未测”，不是 0。

## 可复现工具

所有代码原创；没有复制上游工具、汇编或文档，没有提交 DLL、表数据、反汇编或照片。
在仓库外建立 Python venv 并安装 `tools/recipe_studio/requirements-research.txt`。
以下从 WSL 仓库根目录执行；报告必须保存在系统临时目录且不能位于仓库中。

```sh
python -m tools.recipe_studio.workspace_probe '/mnt/f/Program Files (x86)/OMDS/OM Workspace' --report /tmp/ep7-workspace-research/inspection.json
python -m tools.recipe_studio.workspace_compare /tmp/ep7-workspace-research/model.tif /tmp/ep7-workspace-research/workspace.tif --report /tmp/ep7-workspace-research/error.json
python -m unittest discover -s tests -p test_workspace_research.py -v
```

定位器只读本机安装、完整校验表哈希、记录直接引用；不提取或导出原厂字节，不执行 DLL。
直接引用扫描仅覆盖 PE 异常表列出的函数范围，不保证找全叶函数或间接引用。
比较器只接受同尺寸、同位深、相同非空 ICC 的单页 RGB TIFF，保留 8 / 16 位码值。
报告 MAE、RMSE、最大绝对误差、各通道偏差和完全相同像素比例；不缩放、不配准、不隐式转换颜色。
这些合成测试只能证明工具行为，不能证明尚未实现的 Workspace 算法精确。

## 机主对照图准备方案（尚未执行）

尚未收到具体 ORF 路径；请选一张 E-P7 ORF，含黄、蓝、红、绿、灰阶，并覆盖画面四角。
建议优先选 #58 的原始场景；#49 的截图测量不能充当逐像素参照图。
在 Workspace 中对同一张 ORF 编辑：选 COLOR 配置 1，12 区 S 全 0，三段影调全 0，暗角 0。
固定白平衡、曝光、锐度、降噪、镜头校正、色彩空间、裁切和方向；关闭自动调整并记录设置。
先导出 `neutral.tif`：原始尺寸、sRGB、16 位 RGB TIFF、嵌入 ICC、无损且优先无压缩。
若此版本无法输出 16 位，则所有对照统一用 8 位 RGB TIFF，并记录实际位深；不用 JPEG。
每张都从此中性设置重新开始，每次只变一个控制，文件名记录参数，其余设置保持相同：
- 饱和度：分别把 12 个色区各设 S −5 / +5，得到 24 张，再做全区 −5 / +5 两张。
- 三段影调：阴影 / 中间调 / 高光各设 −7 / +7，得到 6 张；若 UI 不支持某值，记录实际上限。
- 创意暗角：使用创意配置内的暗角控制，分别设 −5 / +5 两张，避免误用镜头阴影校正。
最后再次导出中性图作为重复性对照；全部保存在机主私有目录，不提交或上传照片。
后续实现须声明输入域，使用同一中性图产生候选 TIFF；若效果发生在中性导出的 gamma / tone 之前，
需改为在相同中间缓冲区比较，或重建 RAW 管线，不能把普通 sRGB 后处理误差视为独立算法误差。

## 实机证据与后续需要

[#49](https://github.com/ZakuZakuu/ep7-film-hack/issues/49#issuecomment-6395587169) 报告黄 50.9° → 36.6°、深蓝亮度 0.30 → 0.12；属于截图测量。
[#58](https://github.com/ZakuZakuu/ep7-film-hack/issues/58#issuecomment-6416835422) 报告蓝色 L* 16.2 → 12.1；L* 与前述 HSL 亮度不是同一单位。
[#65](https://github.com/ZakuZakuu/ep7-film-hack/issues/65#issuecomment-6440964392) 确认配方保存及生效，未给独立像素公式。
这些支持方向和局部幅度，尚无本次可读取的原始配对照片，未做模型数值核对。
需要机主提供上述原始文件路径和对照导出；继续还原还需要可运行的本地 Ghidra / Java 工具链。
接续任务应先闭合 HSL 函数 ABI、输入域与原生调用，再实现并验证公式；本次不开启下一阶段。

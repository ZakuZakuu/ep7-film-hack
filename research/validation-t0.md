# T0｜合成测试与发布范围检查

日期：2026-10-11；工作基线 `b9afe900296c41d29bccff04f5113160ed6ee040`（origin/main）。无 E-P7 样本或相机连接。

## 复用与最小增量

`tools/inspect_blob.py` 原实现保持不变，没有发现需要修改的 inventory 行为。复用标准库测试，仅补充两个风险相关场景：

- 空/短合成文件：完整 SHA-256、长度、header、边界采样以及读取后输入字节不变。
- 真实 CLI `--json`：3 MiB 均匀字节数据加独特尾部，跨越初始 4 KiB 和多个 1 MiB 读取；验证完整哈希、合法 JSON、头部、起始熵、中/尾采样位置、4096-byte 样本及输入不变。

原有三项测试仍覆盖空/单值熵、二值均匀熵、只读 inventory 与哈希。所有输入在临时目录即时生成；没有伪造 E-P7 容器或上传 OEM 数据。测试不是相机仿真，也不能推出不存在并发修改/来源真实性等额外保证。

## 实际执行结果

```text
python3 -m unittest discover -s tests -v
  test_balanced_bits ... ok
  test_cli_hashes_all_chunks_without_changing_input ... ok
  test_empty_and_short_files ... ok
  test_empty_entropy ... ok
  test_preserves_input_and_hash ... ok
  Ran 5 tests — OK

python3 tools/inspect_blob.py --help
  exit 0; Read-only generic blob inventory. NOT an Olympus firmware decoder.

git diff --check
  exit 0; no whitespace errors
```

PR 只包含原创研究文字、公开响应元数据、原测试增量、导航/事实措辞修正和 `work/` 忽略规则。检查提交文件清单，不包含固件、上游源码、PDF/HTML 缓存、私有照片或设备标识。`work/` 用于参考缓存/检索脚本/临时 checkout，不属于研究结论，不进入提交。

未执行：上游 GR/Ricoh/Fuji/Canon/Nikon 补丁工具、Ghidra/binwalk、Docker 构建、Workspace 更新器、Wi-Fi/USB 探针、任何相机写入。到此结束 T0。

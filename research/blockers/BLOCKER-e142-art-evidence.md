# BLOCKER：E-P7 ART 资源归属仍缺证据

2026-10-11；Issue #7，G2。E-P7 owner-reported 1.1；完整固件 SHA-256 `9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb`。输入/OE/SquashFS 已验证，不再是 G1 访问阻塞。

两条有限路径：真实 SquashFS 全目录路径的 ART/LUT/gamma/profile 关键词检查无候选；七个选择性提取普通文件的有界字节关键词检查无直接 ART 命中。五个有效 ELF 只证明该辅助区域包含 ARM Linux 软件；JPEG 字词同时伴随 Bluetooth/OBEX，不构成滤镜归属。

缺失的是版本限定的资源记录、filter ID/参数表及调用或 ISP 引用链。不是技术不可能结论，也不能据此排除其他块、无字符串二进制表或封闭 ISP。没有地址猜测、自造 LUT parser 或设备写入。

下一任务优先研究其他块的社区已验证资源格式，然后在本 hash 上验证索引/引用；先例不足先补研究，不猜测开发。辅助 libisc 依赖可作为单独静态边界调查，但功能未知。体验替代是公开 Color Profile 原生参数及受控样张表达能力实验；可保留官方机内直出，却不证明 ART 槽替换或任意 LUT。

本轮到真实 FS 验证及初步调查为止；G2 未通过，G3–G6 不推进。详细实测、范围与反证见 [报告](../e142-squashfs-validation.md)。

**T3 后续状态（同一 hash）：**[Issue #15](../e142-executable-map.md)已验证 #0 MN103 代码、实际调用/返回与有静态引用支持的执行地址映射。缺少可执行程序基础不再阻塞有限离线函数分析，旧版 binary 对也不是其必要条件；仍缺真实 selector→参数/算法/ISP consumer。三处既有 BleachBypass 锚点属于 `oishare` 接口 XML。下一步用已验证 ISA/引用形式追踪一条明确处理链，替代再次普通字符串或资源扫描；G2 仍 unknown，G4/G5 仍禁止实现/安装尝试。

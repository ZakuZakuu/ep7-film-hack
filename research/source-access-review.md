# T0｜公开来源访问与复核记录

核对日期：2026-10-11。范围：Issue #1、仓库研究包列出的公开资料及少量页面内明确链接。只做公开 GET、源码阅读和本仓库合成测试，没有运行上游程序、更新器、相机命令或刷机流程。

## 可重现记录

[source-access.json](source-access.json) 记录 27 个公开响应的 URL、最终 URL、HTTP 状态、字节数及 SHA-256。这些哈希是**网页/文档响应哈希，不是 E-P7 固件哈希**。原始 HTML/PDF、第三方源码与工作缓存不入 Git。官方手册的最终完整响应为 **16,862,659 bytes**，SHA-256 `54b139500c2f4192bc678b10427309d1ead22c8455550b6d235d467c2eea83f8`；首次读取受 12 MiB 上限截断，未用其哈希作为完整手册证据，最终记录已替换为完整响应。

公开站点是动态内容，之后响应哈希可能改变；哈希用于标识本轮阅读快照，不能证明 OEM 二进制真实性或法律许可。源码 commit 与逐文件引用固定在 [先例矩阵](../docs/10-prior-art-matrix.md)。未评估下载的跨品牌仓库每个文件的授权；只研究所引用文本与代码，不重分发第三方材料。

```bash
# 仅复核公开页面；所有下载放临时工作区，不加入 Git
mkdir -p work/reference-check
curl --fail --location --max-time 30 \
  'https://support.jp.omsystem.com/en/support/imsg/digicamera/download/software/firm/e1/' \
  -o work/reference-check/firmware-index.html
sha256sum work/reference-check/firmware-index.html
rg -n -A 4 -B 1 'E-P7' work/reference-check/firmware-index.html

curl --fail --location --max-time 30 \
  'https://my.omsystem.com/consumer/manuals/cameras/E-P7_MANUAL_EN.pdf' \
  -o work/reference-check/manual.pdf
sha256sum work/reference-check/manual.pdf
pdftotext -layout work/reference-check/manual.pdf work/reference-check/manual.txt
rg -n 'twelve different colors|JPEG copy only' work/reference-check/manual.txt

# 对源码采用固定 commit，阅读，不安装或执行上游工具
 git clone --no-checkout 'https://github.com/lemonadesaltbagel/GR4-LUTSmith.git' work/reference-check/lutsmith
 git -C work/reference-check/lutsmith show 0f0856e246524ccd435bb93aaf1ede29cd338aa6:README.md
 git -C work/reference-check/lutsmith show 0f0856e246524ccd435bb93aaf1ede29cd338aa6:gr4_lutsmith.py
 git -C work/reference-check/lutsmith ls-tree -r --name-only 0f0856e246524ccd435bb93aaf1ede29cd338aa6
```

以上为复核命令；实际本轮通过 Python 标准库 `urllib.request.urlopen` 定向 GET（25 秒超时，官方手册最终完整读取），通过 `git clone --depth 1` 阅读八个仓库并记录 `git rev-parse HEAD`。初次沙箱未允许网络，授权的网络模式下完成公开检索；本地命令失败不能据此称来源失效。没有猜测固件文件名/URL、枚举 OEM 更新后端或绕过鉴权。

## 关键来源及内容结果

| 来源 | 本轮结果 | 支持的事实 / 边界 |
| --- | --- | --- |
| [E-P7 产品](https://explore.omsystem.com/c/en/e-p7) | HTTP 200，产品内容可读 | TruePic VIII、16 ART、微调/触屏预览、Wi-Fi/Bluetooth；不是 CPU ISA 或 ART 内部实现 |
| [E-P7 FAQ](https://support.jp.omsystem.com/en/support/imsg/digicamera/qa/products/ep7/) | HTTP 200，内容可读 | ART 名称与部分滤镜微调；Color/Mono 各 4 组 |
| [官方手册](https://my.omsystem.com/consumer/manuals/cameras/E-P7_MANUAL_EN.pdf) | 完整 PDF，成功 pdftotext | 印刷页 51–53：Color1–4、12 色饱和度 ±5、shading、highlight/shadow/midtone、sharpness/contrast；70–73：ART 操作/效果；72：ART 只影响 JPEG 副本 |
| [官方固件索引](https://support.jp.omsystem.com/en/support/imsg/digicamera/download/software/firm/e1/) | HTTP 200，读取 E-P7 行 | 1.1、2022-02-28；链接是更新说明 HTML |
| [E-P7 1.1 更新说明](https://dl01.om-digitalsolutions.net/ww/ud2/ENU/0001/1420/index01a.html) | HTTP 200，2,324 bytes HTML | 单焦距镜头对焦精度改进，没有固件二进制下载链接；不把 URL 中 1420 当作已验证硬件 ID |
| [软件通知索引](https://support.jp.omsystem.com/en/support/imsg/digicamera/download/notice/notice.html) | HTTP 200，读取 E-P7 专属行 | Linux、Expat 1.95.5 |
| [E-P7 Linux 软件通知](https://support.jp.omsystem.com/en/support/imsg/digicamera/download/notice/pdf/Software_Notice_ep7_linux.pdf) | HTTP 200，完整 PDF 可读 | Linux/GPL v2 通知及按型号/购买日期请求相关源码的说明；不是完整固件、CPU 型号、ISP 源码或执行入口 |
| [官方通用更新流程](https://learnandsupport.getolympus.com/ca-en/updating-your-digital-camera-or-lens) | HTTP 200，内容可读 | Workspace + USB + 接受协议 + 传送/相机更新；未见独立的仅下载完整 E-P7 镜像功能；中断可能不可用，官方警告不能回退旧版本 |
| [Workspace backup FAQ](https://support.jp.omsystem.com/en/support/imsg/digicamera/qa/contents/ow/ow_a1.html) / [OM-1 FAQ](https://support.jp.omsystem.com/en/support/imsg/digicamera/qa/contents/omw/omw_a1.html) | HTTP 200，内容可读 | 前者针对列出的 backup 机型，后者 OM-1；不能作为 E-P7 设置备份/恢复的保证 |
| 八个 GitHub 先例仓库 / olympus-wifi API 文档 | HTTP 200，源码与文档可读 | 许可和效果范围逐项见先例矩阵；没有执行硬件复现 |
| [DVXuser legacy 帖](https://www.dvxuser.com/threads/e-p1-e-p2-e-pl1-hack-research.217453/) / [micro43club 帖](https://micro43club.pro/forum/threads/modifikacija-proshivki-kamer-olympus.22086/) | HTTP 200，讨论内容可读 | 保留历史 community/author-reported；不是 E-P7 兼容性证明 |
| [Manualzz 镜像](https://manualzz.com/doc/59292907/olympus-e-p7-user-manual) | HTTP 200，可读 | 可检索镜像；关键事实改以完整官方手册核对 |
| [OPC 1.0a PDF](https://raw.githubusercontent.com/ccrome/olympus-omd-remote-control/master/OPC_Communication_Protocol_EN_1.0a/OPC_Communication_Protocol_EN_1.0a.pdf) | HTTP 200，PDF 可获取 | 仅登记存档可得性，未据其证明 E-P7 命令或许可，不提交 PDF |
| [2019 Reddit 帖](https://www.reddit.com/r/M43/comments/bnhfb5/modified_olympus_firmware_removes_30minute/) | HTTP 200，但只有 Reddit 中间页 | 内容未复核；不能标作本轮验证的社区结果 |
| [2026 年 5 月第三方文章](https://marcrphoto.wordpress.com/2026/05/11/olympus-om-system-firmware-updates-the-situation-changed-again-may-2026/) | HTTP 200，内容可读 | 既报告旧直链不稳定，也链接一个非官方 updater；不能只摘前半段就声称所有下载路径已关闭 |
| [文章明确链接的 updater](https://ofu.infinityfreeapp.com/?utm_source=chatgpt.com) | HTTP 200，873 bytes，仅 JavaScript/cookie challenge | 没有看到 E-P7 列表、文件来源或授权条款；未运行脚本/工具、未下载固件。**访问受限不证明该站不存在合法样本** |
| [GR4-LUTSmith release API](https://api.github.com/repos/lemonadesaltbagel/GR4-LUTSmith/releases/latest) | HTTP 200，latest 返回 v2.0.2 | 审阅的 main 源码 VERSION=2.1.0；两者明确分开 |

来源的 HTTP 200 只表示传输成功。内容可读、许可证和设备结果必须分别核对。

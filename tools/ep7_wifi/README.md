# E-P7 EP71 电脑端 Wi-Fi 配方工具

Python 3.12，**仅标准库**；复用仓库 Recipe Studio 的 JSON 校验，无需安装它的图像依赖。本工具按 [T25 正式协议](../../docs/wifi-recipe-protocol.md) 实现，依赖已审查的 v4 / EP71。原厂或标识不符时拒绝写入，不提供刷机或无标记降级路径。

已通过回环模拟测试，**尚未连接 E-P7 实测**。相机端是逐值写入，不能保证中断时整套配方一致。实机安装和 B4 由机主另行决定。

## 连接与运行

先把仓库保存到电脑。在相机原厂菜单启动私人 Wi-Fi；Windows：设置 → 网络和 Internet → Wi-Fi，选择相机 SSID；macOS：系统设置 → Wi-Fi，选择相机 SSID。使用相机显示的密码/二维码流程，网络没有互联网是正常现象。关闭其他正在改设置的相机 App；本工具不读取 SSID、密码、序列号或 MAC。

在仓库根目录打开终端。Windows 使用 `py -3.12`；macOS、Linux、WSL 使用 `python3.12`，下列命令将前者替换即可。WSL 可能受 Windows 网络路由影响；连接失败时先核对系统 Wi-Fi 与相机地址，不要改为公网地址。

```powershell
py -3.12 -m tools.ep7_wifi discover
py -3.12 -m tools.ep7_wifi read --slot 1 --out "$HOME/COLOR1-backup.json"
py -3.12 -m tools.ep7_wifi write --slot 1 "$HOME/my-recipe.json" --dry-run
py -3.12 -m tools.ep7_wifi write --slot 1 "$HOME/my-recipe.json"
py -3.12 -m tools.ep7_wifi restore --slot 1 "$HOME/COLOR1-backup.json" --dry-run
py -3.12 -m tools.ep7_wifi restore --slot 1 "$HOME/COLOR1-backup.json"
```

`my-recipe.json` 是 Recipe Studio 导出的完整 `ep7-film-recipe-v1`。所有字段先校验，S 限于 −5…+5；非法配方不会连接相机。dry-run 不连接，也不创建状态文件。restore 明确标识为还原，但同样会先备份当前槽。

默认 `192.168.0.10:80`；全局参数放在命令前，例如：

```powershell
py -3.12 -m tools.ep7_wifi --host 192.168.0.10 --timeout 3 --gap 0.05 discover
```

只接受 RFC1918 私网 IP 或测试用回环 IP；不接受域名、公网、链路本地地址或 URL，不跟随跳转。相机只在原厂遥控模式（rec）下接受 `get_mcon` / `set_mcon`，否则返回 HTTP 520（错误码 1004），这是 B4 实测结果。所以 discover、read、write、restore 在确认型号后都会先请求 rec 模式，再查询 EP71 能力；write/restore 随后读取备份、只写差异、核对全部 40 值。切换 rec 模式不启动实时流、不按快门、不改设置。

输出的白平衡、WB 偏移、曝光建议**仅提醒手动设置**，不上传。目标是当前应用上下文中的 COLOR 槽，不直接操作内部 bank；Myset 等行为仍待 B4。

## 备份和不确定结果

默认备份：`~/.ep7-film-hack/backups/`；Windows 位于用户目录下同名文件夹，完整路径打印在结果中。备份文件不覆盖旧文件，可直接用于 restore。`--state-dir` 可指定其他仓库外目录。默认文件/目录在 Unix 上使用 0600 / 0700；Windows 使用用户目录继承的访问控制。

写入前先保存备份和本地意图标记。任何 HTTP 错误、超时、断连、回读不同都会停止，不重试写入、不自动回滚；尽力只读全部当前值并以退出码 3 报告实际结果。不确定标记会阻止下次写入，即使一次回读碰巧与目标相同，也不假定迟到编辑已取消。

1. 保留输出与备份，手动重新连接相机 Wi-Fi；不要把再次请求 rec 当成通用取消命令。
2. 用 `read` 只读核对需要的槽。完成手动重连后，执行下面的显式确认；工具仍会再次读取完整槽，报告与旧目标是否相同，**不会写入**：

```powershell
py -3.12 -m tools.ep7_wifi acknowledge-reconnect --after-manual-reconnect
```

3. 根据实际读取结果，再明确决定 write 或 restore。冷启动后保留与否必须另测；`verified_current_values` 只表示本轮完整回读一致。

本地 `write.lock` 只协调使用同一状态目录的客户端，不能锁住相机菜单或其他 App。进程异常退出后若遗留锁，先确认没有写入进程，再手动删除该目录的 `write.lock`；**不要删除 `uncertain.json` 来绕过核对**。本地状态损坏时保留文件并停止写入。

退出码：0 当前操作完成；2 校验/连接/本地文件错误；3 写入结果不确定；4 型号或协议不兼容。错误不打印原始 HTTP 响应；不保存设备身份字段。

## 仅回环模拟

模拟器是原创协议合同模型，没有原厂字节，不模拟 ISP、RTOS 或 NVS。它只监听 `127.0.0.1`，不访问相机：

```powershell
py -3.12 -m tools.ep7_wifi.simulator --port 8765
py -3.12 -m tools.ep7_wifi --host 127.0.0.1 --port 8765 --gap 0 discover
py -3.12 -m unittest discover -s tests -p test_ep7_wifi.py -v
```

`--stock` 模拟原厂能力查询为 0；`--drop-at 3` 模拟第三次标记写入已应用但回复断开；`--mismatch-at 1` 模拟未应用第一次写入。模拟器不实现普通 raw writer 或设备功能，测试通过不等于 E-P7 实测成功。CI 在 Windows、macOS、Ubuntu 上运行这些无相机测试。

设计参考：[fishcu 固定提交客户端说明](https://github.com/fishcu/oly_fw_analysis/blob/539fcf1fa9eda5fdef8ede4deeab94a4691d94c3/camera_client/README.md)，仅借鉴“超时后不确定状态”的思路，未复制代码。

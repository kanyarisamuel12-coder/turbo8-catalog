# Connect Codex to Turbo8

[English](#english) · [中文](#中文) · [API provider setup](api-setup.md)

## English

Turbo8's **Codex** provider connects to a local Codex CLI process. Install the
dependencies on the **same computer** running Turbo8. Node.js is also required
for Turbo8's local tools adapter, even when Codex itself was installed without npm.
This integration is desktop-only; installing these tools on another computer does
not connect an Android device. Windows/Linux setup is described below, but is not
a claim of device validation for every Turbo8 release.

### 1. Install Node.js

Open the [official Node.js download page](https://nodejs.org/en/download), select
the current **LTS** release and your operating system/architecture, and follow
its installation instructions. Reopen Terminal / PowerShell afterwards:

```sh
node --version
npm --version
```

Both should print a version. If either command is missing, complete Node.js
installation and check PATH before continuing.

### 2. Install Codex CLI

One supported installation method is npm:

```sh
npm install -g @openai/codex@latest
codex --version
```

For alternative installers, follow the
[official Codex CLI guide](https://developers.openai.com/codex/cli/).
The npm update command is documented in OpenAI's
[CLI workflow guide](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex).
Do not install the unrelated `openai` npm package as a replacement for Codex.

### 3. Connect in Turbo8

1. Fully quit and reopen Turbo8 after installing the dependencies.
2. Open **Settings → AI settings**, select **Codex** if a provider selector is shown.
3. Select **CONNECT CHATGPT** and complete the browser sign-in yourself.
4. If needed, use **USE DEVICE CODE**, then **OPEN SIGN-IN** and **COPY CODE**.
5. Wait for **CONNECTED**, choose an available model and save your settings.

An eligible ChatGPT account and remaining Codex usage are required. Model access
and limits depend on the account; installation does not grant them. This Turbo8
provider uses ChatGPT sign-in, not an API key entered in Turbo8. See
[OpenAI authentication guidance](https://developers.openai.com/codex/auth/).

### Troubleshooting

- **“Install Codex CLI and Node.js…”**: Turbo8 cannot locate one of the executables.
  On macOS/Linux, run `command -v node` and `command -v codex`. On Windows, use
  `where.exe node` and `where.exe codex`. The locations must be visible to Turbo8's
  process, not only to a terminal startup script.
- **Works in Terminal, not in Turbo8**: GUI apps can inherit a different PATH.
  Restart Turbo8; on macOS, signing out and back in may be needed after changing
  the login environment. Version-manager installations may require launching
  Turbo8 from the configured shell. Never replace an existing executable blindly.
- **Windows npm shim**: the current Turbo8 launcher looks for `codex.exe`, not
  `codex.cmd` or a WSL command. If only a shim is present, use the Windows native
  installation method linked by the official CLI guide and ensure `codex.exe`
  is on the Windows PATH. Node.js must also be installed on Windows, not only WSL.
- **macOS lookup**: Turbo8 additionally checks `/opt/homebrew/bin/node` and
  `/usr/local/bin/node`; Codex installed elsewhere must be on the inherited PATH.
- **Server fails to start**: update Codex, check `codex app-server --help`, restart
  Turbo8 and retry. Don't manually start a competing app-server; Turbo8 starts its
  own local process. Security software may need to allow local loopback traffic.
- **Browser login fails**: try device-code login. Account or workspace policy may
  need to enable it. Follow the official authentication guide above.
- **CONNECTED but no models/usage**: check account access, network and account
  restrictions. Reconnecting cannot increase the account's allowance.
- **Permission error during npm installation**: use an installation location
  writable by your user or another official installation method. Do not solve it
  by disabling security controls or recursively changing system-directory permissions.

Never paste passwords, API keys, login codes or Codex credential files into a
GitHub issue. A useful report includes the OS, `node --version`, `codex --version`
and the Turbo8 status message with personal information removed.

## 中文

Turbo8 的 **Codex** 接入需要在运行 Turbo8 的**同一台电脑**安装 Codex CLI 和
Node.js。即使 Codex 使用独立安装方式，Turbo8 的本地工具适配器仍需要 Node.js。
这不是 Android 端远程连接方案；在电脑上安装不会自动连接手机。

### 安装与连接

1. 到 [Node.js 官网](https://nodejs.org/en/download)选择当前 **LTS** 版本，按系统和
   芯片架构安装。重新打开终端，用 `node --version` 和 `npm --version` 确认安装。
2. 在终端运行 `npm install -g @openai/codex@latest`，再运行 `codex --version`。
   也可选择 [Codex 官方安装页](https://developers.openai.com/codex/cli/)中的其他方式。
3. 完全退出并重新打开 Turbo8，进入 **Settings → AI settings**。如显示服务商选择，
   选 **Codex**，点击 **CONNECT CHATGPT**，自行在浏览器完成登录。
4. 浏览器回调不成功时，可试 **USE DEVICE CODE**；通过 **OPEN SIGN-IN** 打开页面，
   **COPY CODE** 复制验证码。账号或组织可能需要先允许设备码登录。
5. 显示 **CONNECTED** 后选择可用模型并保存设置。是否可用及额度取决于账号，
   安装工具本身不会提供额度。本接入使用 ChatGPT 登录，不是在 Turbo8 中填写 API Key。

### 装好了仍提示未安装？

先检查终端中两条版本命令是否成功。macOS/Linux 用 `command -v node`、
`command -v codex` 查看位置，Windows 用 `where.exe node`、`where.exe codex`。
图形界面应用的 PATH 可能与终端不同，尤其是 nvm 等版本管理器安装；请让 Turbo8
继承正确环境后重启。不要覆盖其他可执行文件或随意修改系统目录权限。

Windows 当前需要能直接找到 **codex.exe**；只有 npm 的 `codex.cmd` 或只装在 WSL
中并不足够。请按官方 CLI 页使用 Windows 原生安装方式，并把可执行文件目录放进
Windows PATH；Node.js 也需安装在 Windows 中。

启动失败可先更新 CLI，用 `codex app-server --help` 检查该命令是否可用，然后重启
Turbo8。Turbo8 会自行启动本地服务，无需手动常驻另一个 app-server。网络、账号限制
或剩余额度问题请参阅 [官方登录说明](https://developers.openai.com/codex/auth/)。

反馈时只提供系统、工具版本及去除个人信息的错误提示；不要上传登录凭据、验证码或密钥。

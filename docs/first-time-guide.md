# Turbo8 First-time Guide

[English](#english) · [中文](#中文)

## English

### Start with ChatGPT / Codex — recommended

For AI-assisted game creation, **ChatGPT / Codex is our first choice**. We
recommend **GPT-6 Astra** as our quality-first choice; **GPT-6.1 Sol** is also a
good option, **when available to your account**. This is a Turbo8 recommendation,
not a promise of access or a change to your saved model.

1. Open **CREATE WITH AI** or the editor's **AI** feature. If you have not set up
   AI, the **Choose how to connect** wizard opens with two direct choices.
   Choose **USE CODEX** in the recommended **Codex / ChatGPT** card, or
   **USE API KEY** for your own provider. Codex requires Codex App or Codex CLI
   installed on this computer; API mode does not. The **First-time Guide ↗**
   link lives in the header, separate from the navigation buttons.
2. Read the connection status. Turbo8 checks for a local Codex engine and Node.js,
   including supported copies bundled with Codex App / ChatGPT. If something is
   missing, follow the [Codex installation guide](codex-setup.md). Install only
   the missing dependency on the computer running Turbo8, then reopen Turbo8
   and choose **CHECK AGAIN**. The wizard does not install software for you.
3. Choose **SIGN IN WITH CHATGPT** and complete sign-in in your browser yourself.
   If needed, use **USE DEVICE CODE**, **OPEN SIGN-IN**, and **COPY CODE**.
4. Once signed in, choose **CONTINUE** to the model step and select a model returned for your account. We recommend GPT-6;
   the wizard prefers GPT-6 Astra, then GPT-6.1 Sol when offered for a new setup.
   Choose **START CREATING** to return to your game idea.

This route is desktop-only. It uses the local Codex connection, not remote
control of a Codex App chat. Account eligibility, model availability, sign-in
policies and usage limits depend on your account. Installing a tool does not
grant access. See [official OpenAI authentication guidance](https://learn.chatgpt.com/docs/auth).

### Alternative: use an API key

Choose **USE API KEY** if you prefer your own API provider or are on a device
without the desktop Codex connection. No Codex or Node.js installation is needed
for this route.

1. Choose **OpenAI** or **Custom**. Set the **BASE URL first**, then enter the
   **API KEY** and exact **MODEL** ID from your provider. Changing the URL clears
   the key to avoid sending it to a different endpoint by accident.
2. For OpenAI, our quality-first recommendation is GPT-6 Astra; GPT-6.1 Sol is
   also an option. Use a model your API account can access.
   Start with **Auto** protocol; open **Show advanced protocol** only if your
   provider requires a particular protocol. Use a base URL, not a final
   `/responses` or `/chat/completions` route.
3. Optionally choose **TEST CONNECTION**. This explicitly sends one small real
   request to the displayed endpoint and may consume paid API quota. It does not
   send your game, chat history or attachments. A successful text response is
   not proof of full game-editing/tool compatibility. Failure is not success.
4. Choose **SAVE & FINISH**. Saving without testing configures the connection;
   it does not verify it. API keys are saved locally in Turbo8's settings file,
   not uploaded to this guide. Protect your user-data folder and do not share it.

For key creation, billing, exact model IDs, compatible endpoints and protocol
troubleshooting, see [API provider setup](api-setup.md). API billing is separate
from a ChatGPT subscription; check the provider's dashboard before sending requests.

### Skip, resume, or troubleshoot

- **LATER** (or the close button) returns to your draft without sending it. The wizard will not
  automatically interrupt you again after that choice is saved. In-progress
  wizard fields remain available during this app session; unsaved credentials
  are not promised to survive an app restart.
- Reopen it from **AI → SETTINGS → AI SETUP WIZARD**. Existing saved connections
  skip automatic onboarding, even when temporarily offline or signed out.
- Your game, conversation and unsent idea are not deleted by the wizard.
- All advanced provider/model controls remain in **AI → SETTINGS**. Experimental
  providers still require Developer Mode.
- A missing model is not automatically an installation problem. Check account
  access and use only model IDs actually supported by your provider.
- AI is optional: you can play cartridges and use the manual editor without it.

The wizard is included in the next Turbo8 build containing this change. If your
installed build has no wizard yet, use **AI → SETTINGS** with the linked detailed
guides; this documentation does not imply a new download has been published.

## 中文

### 首选 ChatGPT / Codex，推荐 GPT-6

对于 Turbo8 的 AI 游戏创作，我们**首选 ChatGPT / Codex 连接方式**，并推荐
**GPT-6 系列**：追求极致创作效果，首选 **GPT-6 Astra**；**GPT-6.1 Sol** 也是
可选方案。请以你账户实际返回的可用模型
为准；推荐不代表账户一定有权限，也不会替换已保存的模型。

1. 点击 **CREATE WITH AI** 或编辑器里的 **AI**。尚未配置时会出现
   **Choose how to connect** 向导，可以直接二选一。推荐的 **Codex / ChatGPT**
   卡片点击 **USE CODEX**；自己的 API 服务点击 **USE API KEY**。
   Codex 方式需要在本机安装 Codex App 或 Codex CLI；API 方式不需要。
   **First-time Guide ↗** 位于标题区，与底部导航操作分开。
2. 查看连接状态。Turbo8 会检查本机 Codex 引擎与 Node.js，也会查找支持的
   Codex App / ChatGPT 内置组件。缺什么才安装什么：按照
   [Codex 安装指南](codex-setup.md#中文)在**运行 Turbo8 的同一台电脑**安装，
   重开 Turbo8 后点击 **CHECK AGAIN**。向导不会自动安装软件。
3. 点击 **SIGN IN WITH CHATGPT**，由你本人在浏览器完成登录。需要时可以选
   **USE DEVICE CODE**，再用 **OPEN SIGN-IN** 和 **COPY CODE**。
4. 登录后点击 **CONTINUE** 进入模型选择步骤，从账户实际返回的列表选择模型。
   新配置优先推荐 GPT-6 Astra，其次 GPT-6.1 Sol。点击 **START CREATING**
   返回创作界面，继续原来的想法。

此方式仅适用于桌面端。Turbo8 使用本机 Codex 连接，不是遥控 Codex App 中的
聊天窗口。账户资格、模型权限、登录策略及用量限制以账户为准，安装工具并不会
获得额外权限。参考 [OpenAI 官方认证说明](https://learn.chatgpt.com/docs/auth)。

### 另一种方式：API 密钥

如果你希望使用自己的 API 服务，或设备不能使用桌面 Codex 连接，可以选择
**USE API KEY**。此方式不需要安装 Codex 或 Node.js。

1. 选择 **OpenAI** 或 **Custom**。**先填 BASE URL**，再填 **API KEY** 与服务商
   提供的准确 **MODEL** ID。修改 URL 会清空密钥，避免误发到另一个地址。
2. OpenAI 同样首选 GPT-6 Astra，GPT-6.1 Sol 也可以，请确认账户权限。
   协议先保持 **Auto**；只有服务商
   有特殊要求时，才打开 **Show advanced protocol**。填写基础地址，不要填最终
   的 `/responses` 或 `/chat/completions` 请求路径。
3. 可选点击 **TEST CONNECTION**：它会向显示的地址发送一次真实的小请求，可能
   消耗付费 API 额度，不会发送游戏、聊天历史或附件。文本响应成功并不代表完整
   的游戏编辑工具已验证；失败不会被当作成功。
4. 点击 **SAVE & FINISH** 保存。未测试也可以保存配置，但这不代表连接验证
   成功。密钥保存在本机 Turbo8 配置文件中，请保护用户数据目录，不要公开分享。

密钥创建、计费、模型 ID、地址和协议排错见 [API 配置指南](api-setup.md#中文)。
API 计费与 ChatGPT 订阅分开，请先在服务商后台确认权限和余额。

### 跳过、重新打开与排错

- **LATER**（或关闭按钮）返回原来的输入，不会发送消息；成功保存此选择后，不再自动
  弹出。未完成的向导表单会在当前应用会话中保留，未保存的密钥不保证重启后保留。
- 随时通过 **AI → SETTINGS → AI SETUP WIZARD** 重新打开。
- 已有保存配置的用户不会自动看到向导，即使暂时离线或退出了登录。
- 向导不会删除游戏、聊天记录或尚未发送的创作想法。
- 完整高级配置仍在 **AI → SETTINGS**；实验性服务商仍需开启 Developer Mode。
- 没有某个模型不一定是安装问题，请检查账户权限，不要猜测不存在的模型 ID。
- AI 不是必需的；不连接 AI 也可以玩游戏、使用手动编辑器。

向导会包含在纳入本次改动的后续 Turbo8 构建中。如果你安装的版本还没有向导，
请从 **AI → SETTINGS** 按详细指南配置；文档更新不代表新安装包已经发布。

## Share a cartridge · 发布卡带

In **PUBLISH**, open **Cartridge publishing guide** for official submission and author repository instructions. **ONLINE → SOURCE** opens the same guide at the author section, where you can save a starter template.

在 **PUBLISH** 点击 **Cartridge publishing guide**，可切换到简体中文，查看官方投稿和作者源发布步骤。在 **ONLINE → SOURCE** 点击同一指南，会直接打开作者源章节，可以保存建仓模板。

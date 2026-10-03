# Connect an API provider to Turbo8

[English](#english) · [中文](#中文) · [Codex / ChatGPT sign-in guide](codex-setup.md)

## English

Use an API provider when you want Turbo8 to send requests to an API endpoint
using your provider's credentials. This mode does **not** need Codex CLI or
Node.js. If you want ChatGPT sign-in instead, choose **Codex** and follow the
separate guide linked above.

### Quick setup

1. Obtain an API key from the provider's own dashboard. Confirm model access and
   API billing/credit before use; a ChatGPT subscription is not an API balance.
   [Subscription and API usage are separate](https://learn.chatgpt.com/docs/pricing).
   For OpenAI, start with the [official API quickstart](https://developers.openai.com/api/docs/quickstart)
   and [API key dashboard](https://platform.openai.com/api-keys).
2. In Turbo8, open **Settings → AI settings** and choose **OpenAI** or **Custom**.
   Additional provider presets are experimental and require Developer Mode in
   Turbo8. You do not need to enable it for OpenAI or Custom.
3. Set **ENDPOINT first**, then **API KEY**. Editing the endpoint clears the key
   field deliberately, to reduce accidental credential reuse on another host.
4. Click **FETCH MODELS**, then choose a model available to your account. If model
   listing is unsupported, use **MANUAL INPUT** and enter the exact provider model
   ID. Listing a model does not prove that your account can run it.
5. Start with **Auto (recommended)** under **API PROTOCOL**. Choose **Provider
   default** for reasoning effort if the model does not support reasoning controls.
6. Click **SAVE SETTINGS**, then **TEST CONNECTION / PROTOCOL**. The test sends a
   small real request and may incur charges. Review its response and protocol.
   A successful text test is not a full tool-calling/game-creation compatibility test.

### Base URLs and protocols

These are Turbo8's built-in preset values, not a promise that every model or
third-party gateway supports every feature. Confirm the provider's current
documentation and your account permissions.

| Turbo8 provider | Preset ENDPOINT | Auto selection |
| --- | --- | --- |
| OpenAI | `https://api.openai.com/v1` | Responses at this official URL |
| Custom | Your provider's documented base URL | Chat Completions, except recognized official URLs |
| Anthropic (experimental) | `https://api.anthropic.com/v1` | Anthropic Messages |
| DeepSeek (experimental) | `https://api.deepseek.com/v1` | Chat Completions |
| OpenRouter (experimental) | `https://openrouter.ai/api/v1` | Chat Completions |
| Ollama (experimental) | `http://localhost:11434/v1` | Chat Completions |

Supply a **base URL**, not the final request route. Turbo8 appends `/responses`,
`/chat/completions` or the Anthropic messages route. For example, do not enter
`https://api.openai.com/v1/responses` in ENDPOINT. Remote endpoints must use HTTPS;
plain HTTP is accepted only for loopback hosts. `localhost` means the device
running Turbo8, not another computer on the network.

Auto makes a deterministic protocol choice; it does not probe multiple protocols
or silently retry against another one. For a compatible gateway that supports
Responses, select **Responses** explicitly. Use **Anthropic Messages** only for
an endpoint implementing that protocol.

### Search, local models and costs

- **PROVIDER WEB SEARCH** is optional. Turbo8's Auto enables it only for the
  official OpenAI Responses endpoint. Other endpoints need compatible hosted
  `web_search` support and explicit configuration; search can add charges.
  **TEST WEB SEARCH** also makes a real request. Disable it if unsupported.
- A local server may not require a key, but it must already be running and expose
  the compatible API. Model installation and server configuration happen outside
  Turbo8. Local models still need adequate tool-calling capability for editing.
- Long conversations and repeated tool rounds can consume more quota. Check the
  provider's usage dashboard and budgets; Turbo8's connection test does not
  certify spending limits. Review [OpenAI API pricing](https://developers.openai.com/api/docs/pricing)
  or your chosen provider's pricing before use.

### Troubleshooting

| Symptom | Check |
| --- | --- |
| 401 / 403 | Correct provider key, project permissions and account/model access |
| 404 | Base URL, accidental duplicate route, exact model ID and selected protocol |
| 429 | Rate limit or exhausted credit/quota; inspect the provider message |
| Model list unavailable | Enter a documented model ID manually; do not guess an ID |
| Unsupported reasoning/search parameter | Use Provider default reasoning or disable search |
| Model mismatch | Turbo8 rejected a served model different from the requested one; check the gateway without silently substituting models |
| Timeout / TLS / cannot connect | Network, DNS, proxy, certificate and provider status; do not disable certificate verification |

Only send keys to a provider/endpoint you trust. The selected endpoint receives
your prompts and relevant editor/tool context. API keys belong in the settings
field, never in cartridge scripts, public GitHub issues or screenshots. Do not
share settings files containing credentials. If a key leaks, revoke it in the
provider dashboard. See [OpenAI API authentication and key safety](https://developers.openai.com/api/reference/overview).

## 中文

API 模式直接连接你选择的服务商，不需要安装 Codex CLI 或 Node.js。若要使用 ChatGPT
账号登录，请切到 **Codex**，参阅[另一份指引](codex-setup.md)。ChatGPT 订阅不是 API
余额；API 权限、计费和用量请在对应服务商的后台确认。

### 配置顺序

1. 在服务商自己的后台创建 API Key，并确认可用模型、余额或计费方式。
2. 打开 **Settings → AI settings**，选择 **OpenAI** 或 **Custom**。其他实验性预设
   需要 Turbo8 的 Developer Mode；使用 OpenAI / Custom 不需要开启它。
3. **先填 ENDPOINT，再填 API KEY**。修改地址会清空密钥输入框，避免误发给另一个主机。
4. 点 **FETCH MODELS** 获取模型；不支持列模型的服务可用 **MANUAL INPUT** 填写准确
   模型 ID。列出来不等于账号一定有调用权限。
5. 协议优先选 **Auto (recommended)**。官方 OpenAI 地址走 Responses，Anthropic
   走 Messages，普通兼容服务默认走 Chat Completions。Auto 不会轮流试接口。
6. 保存后点 **TEST CONNECTION / PROTOCOL**。这是真实的小请求，可能消耗额度；
   文本测试成功不代表所有工具调用和游戏编辑功能都兼容。

Endpoint 填服务商的**基础地址**，不要再附加 `/responses` 或 `/chat/completions`。
上方表格列出了 Turbo8 内置默认值。远程地址必须使用 HTTPS；`localhost` 指运行
Turbo8 的本机，在手机上填写它并不会连接电脑上的模型服务。

不支持推理参数时，把 **REASONING EFFORT** 改为 **Provider default**。不支持联网
搜索时关闭 **PROVIDER WEB SEARCH**；搜索测试也会真实调用服务并可能收费。

401/403 优先查密钥和权限；404 查基础地址、模型名和协议；429 查额度及限流；
网络或证书报错不要靠关闭安全校验解决。若返回模型与请求不同，应检查网关路由，
不要在不知情的情况下换用另一模型。

密钥只填进可信服务商对应的设置，不要放进游戏脚本、聊天截图或 GitHub。请求内容
和相关编辑器上下文会发送给你配置的 Endpoint；泄露密钥后应立即在服务商后台撤销。

官方参考：[OpenAI 入门](https://developers.openai.com/api/docs/quickstart)、
[密钥后台](https://platform.openai.com/api-keys)、
[API 定价](https://developers.openai.com/api/docs/pricing)。

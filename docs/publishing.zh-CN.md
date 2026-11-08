# 发布 Turbo8 卡带

## 提交到官方源

1. 打开作品，选择 PUBLISH → ONLINE (SUBMIT FOR REVIEW) → CONTINUE TO ONLINE。也可以从卡带库里的作品菜单（…）进入 PUBLISH。继续时会保存当前修改；内置作品会另存为 Player 副本。

2. 用自己的 GitHub 账号登录，填写标题和版本（例如 1.0.0）。如果缺少封面，回到 PLAYER，在作品菜单里选择 EDIT COVER。确认自己有权公开分享代码、画面和声音后，勾选分享许可，点击 SUBMIT FOR REVIEW。

3. 到 ONLINE，切换到 Official，再打开 MY SUBMISSIONS 查看进度。需要修改时打开审查链接。管理员合并后仍需等待目录发布；看到 Published 后刷新官方源即可下载。

4. 更新时从原 Player 作品再次进入 PUBLISH，提高版本号并提交。新建副本会得到新的投稿身份。

## 发布到自己的 GitHub 源

1. 在本指南点击 SAVE SOURCE TEMPLATE，解压模板。用自己的账号创建一个空的公开 GitHub 仓库，将解压内容放入仓库根目录。确认默认分支上有 .github/workflows/publish.yml；复制隐藏目录 .github 时不要遗漏。

2. 每张游戏分别选择 PUBLISH → CARTRIDGE ZIP，勾选 INCLUDE COVER IMAGE，再点击 EXPORT CARTRIDGE。将 ZIP 原样放进模板的 cartridges/ 目录，给每张卡带取不同的文件名。每个 ZIP 最大 32 MiB，封面为 256 × 144 PNG，最大 128 KiB。

3. 将模板和卡带提交并推送到仓库的默认分支。在 GitHub 打开 Actions → Publish Turbo8 cartridges → Run workflow，在默认分支运行。成功后，到 Releases 打开标为 Latest 的版本，确认附件中有 catalog-v2.json。只提交文件不会自动发布。

4. 分享仓库主页链接，例如 https://github.com/作者/仓库。玩家在 ONLINE → SOURCE 中粘贴链接，点击 ADD AND OPEN 即可浏览。下载时点封面上的下载按钮，下载完成后再点封面游玩。玩家无需登录 GitHub。

5. 更新时替换同名 ZIP 并重新运行工作流。内容变化的卡带会自动提升补丁版本，未改的卡带沿用原版本。要下架一张，删除其 ZIP 后重新发布。请保留旧 Release，其他卡带可能仍从那里下载。

如果添加源失败，先检查仓库是否公开、工作流是否成功，以及 Latest Release 是否带有目录。作者源由作者直接发布，想让作品出现在默认官方源时，可另行提交官方审核。

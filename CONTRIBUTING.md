# Submit a Turbo8 cartridge

Step-by-step publishing guides: [English](docs/publishing.en.md) · [简体中文](docs/publishing.zh-CN.md).

Open your cartridge and choose **PUBLISH → ONLINE (SUBMIT FOR REVIEW) → CONTINUE TO ONLINE**. After completing the form, choose **SUBMIT FOR REVIEW**. The **Cartridge publishing guide** in PUBLISH also explains how to distribute games from your own GitHub repository. GitHub authentication uses your own account. Every submission is public and reviewed before publication.

One pull request changes one `carts/u<GitHub numeric user ID>-<32 lowercase hex>/` directory. The directory contains `submission.json` and `cartridge/` with the expanded Turbo8 ZIP. Authors must own or have permission to distribute all submitted code, artwork and audio. No separate code or asset permission fields are collected. Keep any required attribution in the cartridge.

Updates keep the cartridge ID and author ID and increase the semantic version. The verified PR author must match the author ID. Only the maintainer merges. A merge means approved; the cartridge becomes available after publication and public download verification.

The review workflow reads PR files as data using trusted base-branch tooling. It never executes submitted JavaScript. A syntax check and candidate ZIP are provided for maintainer review. Run gameplay only in an appropriate isolated player.

Maintainer tooling changes are separate from cartridge submissions. The cartridge validator intentionally rejects changes outside the selected cartridge directory. Administrators retain maintenance access.

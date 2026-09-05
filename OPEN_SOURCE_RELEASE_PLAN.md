# FrameAnimeDesk 开源发布计划

## 项目定位

FrameAnimeDesk 是一个本机运行的 AI 漫画分镜与生图工作台：把项目、角色参考图、World Bible、镜头构图、画风参考和后期对白组织在同一套工作流中，并通过 Playwright 复用用户自己的镜像站登录会话，或调用 OpenAI 兼容的生图 API。仓库同时公开配套的 `Anime AI Art Director` skill，适合想把“写脚本—做分镜—生成画面—导出成品”串成闭环的创作者和开发者。

## 首次发布建议

1. 先做一次凭据与个人数据检查：确认 `.env`、`.browser-profile/`、`data/`、生成图片、参考图和日志都没有进入 Git；检查历史版本也没有泄露。
2. 仓库已选择 MIT License，覆盖软件、配套 skill 和作者 AI 生成的画风/气泡素材。第三方依赖仍适用各自的上游许可证。
   当前内置画风与气泡素材已确认是作者 AI 生成；字体不随仓库分发，网页字体和 Lucide 图标的依赖见 `THIRD_PARTY_NOTICES.md`。
3. 只提交源码、网页、必要的示例素材、测试、构建脚本和文档。不要提交 `build-*`、`dist-*`、`.venv-build` 或 Chromium 缓存。
   skill 文件位于 `skills/anime-ai-art-director/SKILL.md`，与软件代码分开维护，便于单独复用。
   “星落纪元”应以脱敏项目导出文件和可再分发的镜头图片作为示例；当前截图只能作为宣传图，不能替代项目数据。
4. 首次提交后启用 GitHub Actions，推送 `v0.1.0` 标签生成 Windows Release。`.exe` 作为 Release 附件，不作为源码树文件；同时发布 SHA-256 校验值。
5. 发布说明写清楚：当前支持 Windows 桌面版和 Python 启动方式、镜像站页面结构并不统一、需要用户自行登录和配置 API、项目仍处于个人学习版阶段。

## 推荐上传命令

```powershell
git init
git branch -M main
git add LICENSE .gitignore README.md ASSETS.md SECURITY.md CONTRIBUTING.md OPEN_SOURCE_RELEASE_PLAN.md THIRD_PARTY_NOTICES.md app assets scripts skills tests web data/README.md requirements.txt requirements-build.txt desktop_launcher.py FrameAnimeDesk.spec .github
git status
git commit -m "Initial open source release"
git remote add origin https://github.com/<你的用户名>/<仓库名>.git
git push -u origin main
git tag v0.1.0
git push origin v0.1.0
```

执行 `git add` 后务必检查 `git status`，确认没有个人数据或密钥。仓库创建后建议补充 Topics：`ai-art`、`storyboard`、`comic-creation`、`python`、`fastapi`、`playwright`、`windows`。

## GitHub 页面文案

仓库简介可用：

> 本机运行的 AI 漫画分镜与生图工作台，配套 Anime AI Art Director skill，支持角色/世界观/画风参考、镜像站浏览器会话、OpenAI 兼容 API，以及 PNG/PDF/MP4 导出。

英文一句话简介可用：

> A local-first AI storyboard and image-generation desk for comic creators, with mirror-session and OpenAI-compatible API backends.

## 发布后维护

- 用 Issue 模板区分 Bug、镜像站适配、功能建议和安全问题；
- 每个版本记录兼容性、已知问题和数据库/配置迁移说明；
- 收集不同镜像站的能力差异，但不要在公开仓库保存账号数据或私有接口抓包；
- 当稳定用户和贡献者增加后，再拆分“核心代码许可证”和“示例/素材许可证”。

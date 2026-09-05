# FrameAnimeDesk：Anime AI Art Director 生图工作台

FrameAnimeDesk 是一个本机运行的开源 AI 漫画分镜与生图工作台。它通过 Playwright 打开用户自己的镜像站页面、复用本地浏览器登录状态，也可以连接用户自己的 OpenAI 兼容生图 API，并把生成结果保存到本机目录。前端按 `Anime AI Art Director` Skill 组织为导演台、角色库、世界观、艺术指导、分镜板和导出。

配套 skill 已单独公开在 [`skills/anime-ai-art-director/SKILL.md`](skills/anime-ai-art-director/SKILL.md)，可用于把故事整理成结构化角色、世界观和分镜数据；软件本体负责编辑、生成和导出。

## 已实现功能

- 中文制作选项：制作模式、景别、摄影机角度和镜头运动保留稳定英文值，界面显示中文。
- 项目切换：项目名称、角色、World Bible、分镜、参考图、生成记录和状态彼此隔离。
- 项目对话绑定：镜像站模式下，每个本地项目绑定独立的镜像站对话 URL。首次生成自动新建并记录对话，后续生成会精确返回该对话；导演台也可绑定当前对话、新建、打开或解除绑定。
- 角色参考图：支持多张上传、预览、主参考、类型、说明、启用/停用、排序、替换和删除。
- 多角色镜头：每个镜头可独立锁定最多 6 个入镜角色，并分别填写位置、动作和互动关系。发送时角色 ID、参考图序号和独立描述会一一映射，旧项目中的单角色选择会自动迁移。
- 镜头输出设定：每个镜头可独立选择自动、1:1、9:16、16:9、3:4、4:3、3:2 或 2:3 画面比例，以及自动、1K、2K 或 4K 原生输出分辨率。分辨率会按比例换算像素目标写入生成要求，不对结果做插值放大。
- 世界观 Bible：支持地点、科技、魔法、历史、阵营、规则、天气、时间、色彩和材质等字段，并可上传世界主视觉和环境参考图。
- 项目艺术指导：内置三套可选择画风，项目保存可编辑的画风分析、正面提示词和排除提示词。生成时按主参考、线稿、光影、背景顺序附带最多 4 张画风参考图。
- 自定义画风：必须上传 1 张主参考图，可选 0～3 张辅助图；支持 PNG、JPG、JPEG 和 WebP，并可更新分析、提示词和参考图。
- 后期气泡：项目选择气泡包，Agent 可为对白块指定语义类型，用户可逐条覆盖具体气泡样式。气泡与文字只用于后期排版，不发送给生图模型。
- 导演台参考板：支持角色位置、废稿修改、动作姿势、背景颜色、构图等镜头级参考图。
- 参考图继承：世界观、当前角色和当前镜头参考图按层级组合，单次最多发送 6 张。
- 分镜排序：支持拖动、键盘上下箭头和按钮排序，镜头 ID 保持稳定，刷新后顺序仍然保留。
- 设置页：支持镜像站网址、聊天页网址、图片目录、参考图目录、浏览器显示模式和超时时间。
- 生成通道：可在“镜像站浏览器”和“用户自己的 API 节点”之间切换。API 模式支持 OpenAI 兼容的 Images `/images/generations` 和 Responses `/responses` 协议。
- API 密钥：只保存在本机 `data/settings.json` 或 `.env`，后端接口只返回“是否已配置”，不向网页返回密钥正文。
- 设置页还可以验证两个保存目录，并查看当前浏览器会话是否已启动及页面地址。
- 原图保存：优先触发镜像站生成图附近的“下载原图”操作，直接保存浏览器下载的原始字节；无下载控件时才读取原图 URL、`srcset` 或 `blob:`。不截图、不压缩、不重新编码，原图不可读时直接报错。
- 成品导出：独立“导出”模块支持逐格 PNG 压缩包、竖版长 PNG、逐格分页 PDF 和无音轨 MP4。可在导出时合成后期文字与气泡；有镜头缺少成图时会明确阻止导出，不会静默跳过。

## 安装

PowerShell：

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m playwright install chromium
Copy-Item .env.example .env
```

默认 `HEADLESS=false`，首次运行会显示浏览器窗口。请在浏览器窗口中手动登录自己的镜像站账号；登录状态只保存在项目内的 `.browser-profile/`，不会把 Cookie 或 Token 写进代码。

## 启动

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

打开 [http://127.0.0.1:8000/](http://127.0.0.1:8000/)。首次打开时，旧版 `frame-anime-desk-v1` 本地数据会迁移到默认项目；项目状态随后写入 `data/workspace.json`，参考图和生成图片按项目目录保存。

首次登录可以点击工作台左下角的“打开镜像站登录”，完成登录后在导演台生成当前镜头。设置页中的目录使用本机绝对路径文本；浏览器不能安全地把操作系统文件夹路径自动传给后端。

## Windows 桌面版

仓库提供单文件 Windows 桌面版构建。最终用户不需要安装 Python、依赖或浏览器，双击 `FrameAnimeDesk.exe` 即可打开工作台；关闭桌面窗口时，本地服务和自动化浏览器会一起退出。

在 PowerShell 中构建：

```powershell
.\scripts\build_windows.ps1 -Clean
```

首次构建会创建独立的 `.venv-build`、安装 Chromium 并生成：

```text
dist\FrameAnimeDesk.exe
```

Chromium 会被打进单文件程序，因此成品体积较大，首次打开也需要等待 PyInstaller 解压运行资源。桌面版使用 Edge WebView2 显示工作台；Windows 10/11 通常已经随系统安装该运行时。

桌面版用户数据保存在 `%LOCALAPPDATA%\FrameAnimeDesk`：

```text
data\               项目状态与设置
browser-profile\    镜像站本地登录状态
generated\          生成原图
references\         参考图
```

设置环境变量 `FRAME_ANIME_DESK_HOME` 可以覆盖这个根目录。程序不会把用户数据、API 密钥或登录状态打进 `.exe`。

图标方案见 `ICON_BRIEF.md`。将生成的透明背景 1024px PNG 放到 `assets\app-icon.png`，构建脚本会自动生成多尺寸 ICO 并写入程序；没有图标文件时也可以构建，只会使用 Windows 默认程序图标。

仓库中的 `.github/workflows/build-windows.yml` 支持手动构建，也会在推送 `v*` 标签时自动创建 GitHub Release：

```powershell
git tag v0.1.0
git push origin v0.1.0
```

未使用代码签名证书的开源 `.exe` 可能触发 Windows SmartScreen 的“未知发布者”提示。这不影响程序运行，但正式面向公众发布时建议购买代码签名证书，或至少在 Release 页面同时提供 SHA-256 校验值和源代码构建说明。

## 接口

主要接口：

```text
GET    /api/projects
POST   /api/projects
GET    /api/projects/{project_id}
PATCH  /api/projects/{project_id}
DELETE /api/projects/{project_id}
POST   /api/projects/{project_id}/exports

GET    /api/projects/{project_id}/conversation
POST   /api/projects/{project_id}/conversation/bind-current
POST   /api/projects/{project_id}/conversation/new
POST   /api/projects/{project_id}/conversation/open
DELETE /api/projects/{project_id}/conversation

GET    /api/projects/{project_id}/references
POST   /api/projects/{project_id}/references
PATCH  /api/references/{reference_id}
POST   /api/references/{reference_id}/replace
DELETE /api/references/{reference_id}

GET    /api/style-packs
GET    /api/style-packs/{style_pack_id}
POST   /api/style-packs/custom
PATCH  /api/style-packs/{style_pack_id}/custom
PUT    /api/style-packs/{style_pack_id}/custom/assets
DELETE /api/style-packs/{style_pack_id}/custom

GET    /api/bubble-packs

GET    /api/settings
PATCH  /api/settings
POST   /api/settings/test-connection
POST   /api/settings/test-image-api
POST   /api/settings/validate-directories
GET    /api/session/status
POST   /api/generate
```

`/api/generate` 接受 `project_id`、`shot_id` 和最多 6 个项目参考图 ID。项目选择画风后，后端还会在这些图片之前附加最多 4 张画风参考图，因此单次最多发送 10 张。气泡素材不会进入该接口。如果镜像站页面没有可检测到的图片上传控件，接口仍会生成图片，但会返回参考图只保存在本地、没有发送到镜像站的提示。

`/api/projects/{project_id}/exports` 只读取项目中已经保存的 `lastImage`，不会调用生图接口或修改项目修订号。请求格式可选 `png_bundle`、`vertical_comic`、`pdf`、`video`，并可配置文字合成、输出宽度、长图格间距与视频每格停留时间。导出结果保存在项目图片目录的 `exports` 子目录，同时作为附件返回给桌面界面。

## 开源边界

技术上可以开源，但发布前必须确认镜像站的服务条款和自动化访问规则。不要提交以下内容：

- `.env`、`.browser-profile/`、Cookie、Bearer Token 或风控 Token；
- `data/workspace.json`、`data/settings.json`、个人参考图和生成图片；
- 任何镜像站的私有抓包接口或账号信息。

镜像站页面结构、登录方式和上传控件并不统一。默认的 `app/mirror_adapter.py` 只检测通用 `input[type=file]`；需要适配特定镜像站时，应在这个适配器中增加页面选择器和能力检测，而不是把站点私有逻辑写进项目存储层。

## 许可证

软件、配套 skill 以及仓库内由作者 AI 生成的画风和气泡素材统一采用 [MIT License](LICENSE)。第三方运行时依赖和网页资源仍适用各自的上游许可证，详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

## 测试

```powershell
python -m unittest discover -s tests -v
python -m compileall -q app tests
node --check web/app.js
```

测试覆盖项目和参考图隔离、参考图排序/替换/删除、目录可写性、浏览器会话状态、上传能力检测，以及浏览器会话错误的 JSON 响应契约。

# 第三方依赖与来源

## 运行时依赖

Python 依赖的版本范围见 `requirements.txt` 和 `requirements-build.txt`，各自的许可证以对应上游项目为准。

## 网页资源

- 网页通过 Google Fonts 加载 `DM Mono`、`Manrope`、`Noto Sans SC` 和 `Space Grotesk`。仓库不包含这些字体文件；使用者也可以移除 CDN 引用并改用本机字体。
- 网页通过 unpkg 加载 Lucide 图标库。Lucide 使用 ISC License，具体版本由 CDN 的 `latest` 标签决定。

发布稳定版本时，建议将 CDN 依赖固定到明确版本，并在 Release 说明中记录版本号，减少供应链变动。

## 项目素材

`assets/` 下的画风参考图和气泡图由项目作者使用 AI 生成，来源声明记录在各素材包的 `配置.json` 中。它们不代表任何第三方作品或现有角色。

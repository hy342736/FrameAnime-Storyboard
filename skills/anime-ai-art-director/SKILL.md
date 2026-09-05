---
name: anime-ai-art-director
description: 将故事、角色和世界观整理为可执行的 AI 动画分镜项目，输出连续性稳定的角色设定、镜头提示词和后期对白布局。
---

# Anime AI Art Director

这是 FrameAnimeDesk 配套的公开 skill。它负责“创作规划和结构化分镜”，不负责登录镜像站或直接保存图片；软件本体负责读取 skill 生成的项目数据、上传参考图、调用生图后端并导出成品。

## 适用场景

- 把短篇故事、剧本或小说片段拆成连续的漫画/动画分镜；
- 为角色、世界观和画风建立可复用的视觉约束；
- 为每个镜头生成景别、机位、动作、构图和正/负面提示词；
- 标记对白、旁白和文字安全区，供软件后期排字。

## 工作顺序

1. 先确认项目名、目标平台、画面比例、提示词路线（GPT 自然语言或 NAI 英文标签）。
2. 建立角色库：每个角色保持稳定的 ID、外观、服装、年龄段和性格视觉线索。
3. 建立 World Bible：时代、地点、科技/魔法、阵营、规则、天气、时间、色彩和材质。
4. 定义艺术指导：主画风、线稿、光影、背景、构图、正面提示词和排除项。
5. 按镜头拆分故事。每格只表达一个明确动作或叙事信息，并保留连续性锚点。
6. 为镜头指定入镜角色、位置、动作和互动；需要对白时单独输出后期文字，不把气泡素材写进生图提示词。
7. 输出项目 JSON 或通过 FrameAnimeDesk 的分镜导入接口创建项目。

## 镜头最小字段

每个镜头至少应包含：`id`、`title`、`description`、`shot_type`、`camera_angle`、`characters`、`action`、`environment`、`prompt` 和 `negative_prompt`。如果需要后期排字，再增加 `post_text`、`bubble_semantic` 和 `safe_area`。

## 约束

- 不编造角色已有的服装、道具或关系；缺失信息要标记为待确认。
- 不在不同镜头中随意改变角色年龄、发色、服装主色或世界观规则。
- 生图提示词描述画面，不写“生成一张图”“请画”等元指令。
- 负面提示词集中描述应排除的视觉问题，不把剧情内容放进去。
- 不把账号、Cookie、API Key、私有镜像站接口或个人文件路径写入项目数据。

## 与 FrameAnimeDesk 的关系

软件的 `GET /api/skill` 接口提供运行时能力摘要；`/api/import/storyboard/*` 接口接受符合项目契约的结构化分镜。导入后，用户可以在导演台继续编辑角色、世界观、参考图和镜头，再选择镜像站浏览器或 OpenAI 兼容 API 生成图片。

创建或追加项目前，先阅读 [references/import-contract.md](references/import-contract.md)，并使用仓库内客户端发现正在运行的软件、检查能力和验证 manifest：

```powershell
python scripts/frame_anime_client.py doctor
python scripts/frame_anime_client.py capabilities
python scripts/frame_anime_client.py validate <manifest.json>
```

镜头较多时，可以把镜头数组分段保存，再使用 `scripts/assemble_manifest.py` 合并。不要直接编辑软件的 `data/workspace.json`。

这个 skill 与软件代码分目录维护，便于其他工作流单独复用，并统一采用仓库根目录的 MIT License。

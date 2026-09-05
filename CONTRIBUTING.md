# 参与贡献

欢迎提交问题反馈、适配器改进和文档修正。

## 提交前检查

```powershell
python -m unittest discover -s tests -v
python -m compileall -q app tests
node --check web/app.js
```

提交 Issue 时请说明操作系统、Python 版本、生成通道（镜像站或 API）、复现步骤和完整错误信息。请先删除 URL 中的账号标识、Cookie、Token、API Key 以及个人图片。

涉及具体镜像站页面的改动应集中在 `app/mirror_adapter.py`，不要把站点私有选择器或接口细节散落到存储层和通用 API 中。

## Pull Request 建议

- 每个 PR 只解决一个主题，并说明行为变化和测试方式；
- 新增行为应补充对应测试；
- 不要提交 `.env`、`.browser-profile/`、`data/`、`build*/` 或 `dist*/`；
- 新增图片、字体和第三方代码时，请在 PR 中注明来源与许可证。

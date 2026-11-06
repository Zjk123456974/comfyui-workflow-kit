# workflows/ 放什么

把你收集到的 ComfyUI 工作流 `.json` 放在这个目录，然后运行：

```bash
python check.py --workflows workflows --models D:/ComfyUI-下载/models
```

`check.py` 会递归读取这里所有 `.json`，提取其中写死的模型文件名，
并核对本地模型是否齐备、是否放对了子目录。

## 收录规则

- **只收录你有使用或再分发权限的工作流**。第三方工作流请确认原作者的 LICENSE，
  在 `WORKFLOWS.md` 登记表里补齐「来源」与「许可证」两列，并保留原作者署名。
- 没有 LICENSE 的第三方 JSON，请只登记名称和链接，不要把文件本体放进本仓库。
- 建议把文件名改成中文（ComfyUI 的工作流侧栏直接显示文件名），
  但**不要修改 JSON 内部的模型文件名**，否则加载节点会报 `Model not found`。
- 想放私有的、不打算公开的工作流，放进 `workflows/private/`，该目录已被 `.gitignore` 排除。

## 模型文件不要放进这里

`.safetensors` / `.gguf` 动辄几 GB，GitHub 单文件上限 100 MiB。
所有权重文件已被 `.gitignore` 挡在仓库外，详见根目录 `MODELS.md`。

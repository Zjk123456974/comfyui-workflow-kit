#!/usr/bin/env python3
"""ComfyUI 工作流模型核对器（零依赖，Python 3.9+）。

扫描 workflows/ 下的 .json，提取其中写死的模型文件名，
与本地 ComfyUI models 目录比对，报告缺失与放错目录的文件。

用法：
    python check.py
    python check.py --workflows workflows --models D:/ComfyUI-下载/models
    python check.py --json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

VERSION = "1.0.0"
MODEL_EXT = (".safetensors", ".gguf", ".ckpt", ".pt", ".pth", ".bin")
MODEL_RE = re.compile(
    r"[^\s\"'\\/]+\.(?:safetensors|gguf|ckpt|pt|pth|bin)",
    re.IGNORECASE,
)


def iter_strings(obj):
    """递归产出 JSON 中的每一个字符串（兼容 UI 格式与 API 格式）。"""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for value in obj.values():
            yield from iter_strings(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from iter_strings(value)


def extract_models(data):
    """返回工作流引用的模型文件名（去重、排序）。"""
    names = set()
    for text in iter_strings(data):
        names.update(MODEL_RE.findall(text))
    return sorted(names)


def suggest_dir(name):
    """按文件名关键词给出推荐子目录，仅为提示，不是强制规则。"""
    n = name.lower()
    if "vae" in n:
        return "vae"
    if "controlnet" in n:
        return "controlnet"
    if "lora" in n or "lightning" in n:
        return "loras"
    if "clip" in n or "text_encoder" in n or "qwen_2.5_vl" in n or "t5" in n:
        return "text_encoders"
    return "diffusion_models"


def index_models(models_dir):
    """建立 {文件名: [相对子目录, ...]} 索引。目录不存在时返回空索引。"""
    idx = {}
    if not models_dir:
        return idx
    root = Path(models_dir)
    if not root.is_dir():
        return idx
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in MODEL_EXT:
            rel = str(path.parent.relative_to(root)).replace("\\", "/")
            idx.setdefault(path.name, []).append(rel)
    return idx


def load_workflows(wf_dir):
    """读取目录下全部 .json；坏文件不中断，记录错误信息。"""
    root = Path(wf_dir)
    files = sorted(root.rglob("*.json")) if root.is_dir() else []
    result = []
    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            result.append({"file": str(path), "data": data, "error": None})
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            result.append({"file": str(path), "data": None, "error": str(exc)})
    return result


def build_report(wf_dir, models_dir=None):
    checked = bool(models_dir)
    idx = index_models(models_dir)
    workflows = []
    total = {"ok": 0, "missing": 0, "wrong_dir": 0, "unchecked": 0}

    for entry in load_workflows(wf_dir):
        names = extract_models(entry["data"]) if entry["data"] is not None else []
        items = []
        for name in names:
            found = idx.get(name, [])
            expect = suggest_dir(name)
            if not checked:
                status = "unchecked"
            elif not found:
                status = "missing"
            elif any(loc.split("/")[0] == expect for loc in found):
                status = "ok"
            else:
                status = "wrong_dir"
            total[status] += 1
            items.append({
                "name": name,
                "status": status,
                "expect_dir": expect,
                "found_in": found,
            })
        workflows.append({
            "file": entry["file"],
            "error": entry["error"],
            "models": items,
        })

    broken = sum(1 for w in workflows if w["error"])
    failed = total["missing"] + total["wrong_dir"] + broken
    return {
        "version": VERSION,
        "workflow_dir": str(wf_dir),
        "models_dir": str(models_dir) if models_dir else None,
        "checked": checked,
        "indexed_files": len(idx),
        "workflows": workflows,
        "total": total,
        "broken_json": broken,
        "exit_code": 1 if failed else 0,
    }


def render_report(report):
    lines = [
        "comfyui-workflow-kit %s - ComfyUI 工作流模型核对" % report["version"],
        "工作流目录 : %s" % report["workflow_dir"],
        "模型目录   : %s" % (report["models_dir"] or "(未指定，仅列出引用清单)"),
    ]
    if report["checked"]:
        lines.append("已索引权重 : %d 个" % report["indexed_files"])
    lines.append("")

    if not report["workflows"]:
        lines.append("没有找到 .json 工作流。把文件放进 workflows/ 再试。")
    for i, wf in enumerate(report["workflows"], 1):
        lines.append("[%d] %s" % (i, Path(wf["file"]).name))
        if wf["error"]:
            lines.append("    [BAD ] JSON 无法解析: %s" % wf["error"])
        if not wf["models"]:
            lines.append("    (未引用任何模型文件)")
        for item in wf["models"]:
            tag = {
                "ok": "[OK  ]",
                "missing": "[MISS]",
                "wrong_dir": "[DIR ]",
                "unchecked": "[--  ]",
            }[item["status"]]
            extra = ""
            if item["status"] == "missing":
                extra = "  -> 放到 models/%s/" % item["expect_dir"]
            elif item["status"] == "wrong_dir":
                extra = "  -> 现在在 %s，建议 models/%s/" % (
                    ", ".join(item["found_in"]), item["expect_dir"])
            elif item["status"] == "ok":
                extra = "  %s" % ", ".join(item["found_in"])
            else:
                extra = "  (建议 models/%s/)" % item["expect_dir"]
            lines.append("    %s %-50s%s" % (tag, item["name"], extra))
        lines.append("")

    t = report["total"]
    lines.append("汇总: %d 个工作流 / %d 项引用 / OK %d / 缺失 %d / 目录不对 %d / 未核对 %d"
                 % (len(report["workflows"]),
                    sum(t.values()), t["ok"], t["missing"],
                    t["wrong_dir"], t["unchecked"]))
    if report["broken_json"]:
        lines.append("警告: %d 个 .json 解析失败" % report["broken_json"])
    lines.append("自检: %s" % ("FAILED（有缺件，退出码 1）" if report["exit_code"]
                                else "OK（全部就位，退出码 0）"))
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="check.py",
        description="核对 ComfyUI 工作流引用的模型文件是否已就位",
    )
    ap.add_argument("--workflows", default="workflows",
                    help="工作流目录，默认 workflows/")
    ap.add_argument("--models", default=None,
                    help="ComfyUI 的 models 目录；不填则只列引用清单")
    ap.add_argument("--json", action="store_true", dest="as_json",
                    help="输出机器可读的 JSON 报告")
    ap.add_argument("--version", action="version",
                    version="comfyui-workflow-kit " + VERSION)
    args = ap.parse_args(argv)

    report = build_report(args.workflows, args.models)
    if args.as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_report(report))
    return report["exit_code"]


if __name__ == "__main__":
    sys.exit(main())

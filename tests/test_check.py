"""check.py 的单元测试：python -m unittest discover -s tests -v"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check  # noqa: E402


class ExtractTests(unittest.TestCase):
    def test_ui_format(self):
        data = {"nodes": [{"type": "VAELoader",
                           "widgets_values": ["qwen_image_vae.safetensors"]}]}
        self.assertEqual(check.extract_models(data), ["qwen_image_vae.safetensors"])

    def test_api_format(self):
        data = {"1": {"class_type": "UnetLoaderGGUF",
                      "inputs": {"unet_name": "qwen-image-Q3_K_S.gguf"}}}
        self.assertEqual(check.extract_models(data), ["qwen-image-Q3_K_S.gguf"])

    def test_nested_and_dedup(self):
        data = {"a": [{"b": ["x.safetensors", "x.safetensors", "y.gguf"]}]}
        self.assertEqual(check.extract_models(data), ["x.safetensors", "y.gguf"])

    def test_ignores_plain_text(self):
        self.assertEqual(check.extract_models({"note": "hello world"}), [])

    def test_strips_windows_path(self):
        data = {"v": "models\\diffusion_models\\demo.ckpt"}
        self.assertEqual(check.extract_models(data), ["demo.ckpt"])


class SuggestTests(unittest.TestCase):
    def test_vae(self):
        self.assertEqual(check.suggest_dir("qwen_image_vae.safetensors"), "vae")

    def test_text_encoder(self):
        self.assertEqual(
            check.suggest_dir("qwen_2.5_vl_7b_fp8_scaled.safetensors"),
            "text_encoders")

    def test_lora(self):
        self.assertEqual(
            check.suggest_dir("Qwen-Image-Lightning-8steps-V1.0.safetensors"),
            "loras")

    def test_diffusion_model(self):
        self.assertEqual(check.suggest_dir("qwen-image-Q3_K_S.gguf"),
                         "diffusion_models")


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.wf = self.root / "workflows"
        self.models = self.root / "models"
        self.wf.mkdir()
        (self.models / "vae").mkdir(parents=True)
        (self.models / "diffusion_models").mkdir()
        self.addCleanup(self.tmp.cleanup)

    def write_wf(self, name, obj):
        (self.wf / name).write_text(json.dumps(obj), encoding="utf-8")

    def test_all_present_exit_zero(self):
        self.write_wf("a.json", {"nodes": [
            {"widgets_values": ["qwen_image_vae.safetensors"]}]})
        (self.models / "vae" / "qwen_image_vae.safetensors").write_bytes(b"x")
        report = check.build_report(self.wf, self.models)
        self.assertEqual(report["exit_code"], 0)
        self.assertEqual(report["total"]["ok"], 1)

    def test_missing_exit_one(self):
        self.write_wf("a.json", {"v": ["demo.gguf"]})
        report = check.build_report(self.wf, self.models)
        self.assertEqual(report["exit_code"], 1)
        self.assertEqual(report["total"]["missing"], 1)

    def test_wrong_dir_detected(self):
        self.write_wf("a.json", {"v": ["qwen_image_vae.safetensors"]})
        (self.models / "diffusion_models" / "qwen_image_vae.safetensors").write_bytes(b"x")
        report = check.build_report(self.wf, self.models)
        self.assertEqual(report["total"]["wrong_dir"], 1)
        self.assertEqual(report["exit_code"], 1)

    def test_no_models_dir_only_lists(self):
        self.write_wf("a.json", {"v": ["demo.gguf"]})
        report = check.build_report(self.wf, None)
        self.assertEqual(report["exit_code"], 0)
        self.assertEqual(report["total"]["unchecked"], 1)
        self.assertFalse(report["checked"])

    def test_broken_json_is_reported(self):
        (self.wf / "bad.json").write_text("{not json", encoding="utf-8")
        report = check.build_report(self.wf, self.models)
        self.assertEqual(report["broken_json"], 1)
        self.assertEqual(report["exit_code"], 1)

    def test_empty_dir(self):
        report = check.build_report(self.wf, self.models)
        self.assertEqual(len(report["workflows"]), 0)
        self.assertEqual(report["exit_code"], 0)

    def test_render_contains_summary(self):
        self.write_wf("a.json", {"v": ["demo.gguf"]})
        text = check.render_report(check.build_report(self.wf, self.models))
        self.assertIn("汇总", text)
        self.assertIn("[MISS]", text)


if __name__ == "__main__":
    unittest.main()

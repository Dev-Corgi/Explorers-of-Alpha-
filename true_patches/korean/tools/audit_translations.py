"""Write rejected translation details without changing or building a ROM."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import yaml
from ndspy.rom import NintendoDSRom
from patch_engine.apply_korean import load_source, plan_translation, plan_stats


def main():
    module = ROOT / "true_patches/korean"
    manifest = yaml.safe_load((module / "manifest.yaml").read_text(encoding="utf-8"))
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        module / "audit/translation_issues.json"
    )
    rom = NintendoDSRom.fromFile(ROOT / "PatchTesting/Export Rom/Explorers of Alpha+.nds")
    plan = plan_translation(rom, load_source(module, manifest))
    result = {"source": "current English full_stack + korean source data",
              "index_convention": "text_e is zero based; LogMessageById adds one",
              "stats": plan_stats(plan), "rejected_count": len(plan.rejected),
              "rejected": plan.rejected}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(plan.rejected)} rejected translations: {path}")


if __name__ == "__main__":
    main()

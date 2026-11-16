"""Generate all dataset profiles. Usage: python scripts/make_data.py --config configs/data.yaml"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from healgap.env.datagen import DataConfig, build

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--root", type=Path, default=Path("data"))
    args = ap.parse_args()
    cfg = DataConfig.load(args.config)
    for profile in cfg.profiles:
        print(json.dumps(build(cfg, profile, args.root)))

"""
从 pairs/pilot.json 中选取实验样本：
- 6 个不含等待程序（holding_required=false）
- 4 个含等待程序（holding_required=true）
将选中的图片复制到 E:/experiment/data/pilot_10/，并生成 sample_manifest.json
"""

import json
import shutil
from pathlib import Path

PAIRS_FILE  = Path("e:/hangtu3/data/pairs/pilot.json")
CIFP_SRC    = Path("e:/hangtu3/data/cifp/FAACIFP18")
BASE_DIR    = Path("e:/hangtu3/data")
OUT_DIR     = Path("e:/experiment/data/pilot_10")
CHARTS_DIR  = OUT_DIR / "charts"
CIFP_DIR    = OUT_DIR / "cifp"

HOLDING_LEG_TYPES = {"HM", "HF", "HA"}
# holding_required=true 要求图面上有明确等待程序框（HF/HA 腿）
# 仅含 HM（手动终止等待）的程序在图面上通常无 racetrack 框，视为 holding_required=false
EXPLICIT_HOLDING_TYPES = {"HF", "HA"}

# ── 1. 加载 pairs ─────────────────────────────────────────────────────────────
with open(PAIRS_FILE, encoding="utf-8") as f:
    pairs = json.load(f)
print(f"加载 pairs: {len(pairs)} 条")

# ── 2. 判断每个 pair 是否含等待程序 ──────────────────────────────────────────
with_holding    = []
without_holding = []

for pair in pairs:
    legs = pair["cifp"]["legs"]
    has_holding = any(leg["rt_type"].strip() in EXPLICIT_HOLDING_TYPES for leg in legs)
    pair["holding_required"] = has_holding
    if has_holding:
        with_holding.append(pair)
    else:
        without_holding.append(pair)

print(f"含等待程序: {len(with_holding)}, 不含等待程序: {len(without_holding)}")

# ── 3. 选取 10 个样本 ─────────────────────────────────────────────────────────
selected = without_holding[:6] + with_holding[:4]
assert len(selected) == 10, f"样本数量不足: {len(selected)}"

# ── 4. 建立目录 ───────────────────────────────────────────────────────────────
CHARTS_DIR.mkdir(parents=True, exist_ok=True)
CIFP_DIR.mkdir(parents=True, exist_ok=True)

# 复制 CIFP 原始文件
shutil.copy2(CIFP_SRC, CIFP_DIR / "FAACIFP18")
print(f"已复制 CIFP -> {CIFP_DIR / 'FAACIFP18'}")

# ── 5. 复制图片并生成 manifest ──────────────────────────────────────────────���─
manifest = []
print("\n选取样本列表:")
print(f"{'序号':>3}  {'含等待':>6}  {'ID':<20}  {'图片文件'}")
print("-" * 60)

for i, pair in enumerate(selected, 1):
    # 图片路径：相对路径转绝对
    img_src = BASE_DIR / pair["image_path"].replace("data\\", "").replace("data/", "")
    img_dst = CHARTS_DIR / img_src.name
    shutil.copy2(img_src, img_dst)

    flag = "YES" if pair["holding_required"] else "NO"
    print(f"{i:>3}  {flag:>6}  {pair['id']:<20}  {img_src.name}")

    # 提取 missed approach 腿（trans_ident 包含 M 开头，或腿型为 HM/HF/HA）
    ma_legs = [
        leg for leg in pair["cifp"]["legs"]
        if leg["rt_type"].strip() in HOLDING_LEG_TYPES
        or leg["trans_ident"].strip().startswith("M")
    ]

    manifest.append({
        "id": pair["id"],
        "image": img_src.name,
        "airport": pair["cifp"]["airport"],
        "proc_ident": pair["cifp"]["proc_ident"],
        "holding_required": pair["holding_required"],
        "total_legs": len(pair["cifp"]["legs"]),
        "ma_holding_legs": [
            {"rt_type": l["rt_type"].strip(), "wpt_ident": l["wpt_ident"].strip()}
            for l in ma_legs
        ],
    })

# 保存 manifest
manifest_path = OUT_DIR / "sample_manifest.json"
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

print(f"\n完成: {len(manifest)} 个样本")
print(f"  - 不含等待: {sum(1 for m in manifest if not m['holding_required'])} 个")
print(f"  - 含等待:   {sum(1 for m in manifest if m['holding_required'])} 个")
print(f"manifest -> {manifest_path}")

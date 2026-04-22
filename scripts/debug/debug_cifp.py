"""Check actual CIFP record layout for KAAT airport."""
from pathlib import Path

CIFP_FILE = Path("e:/experiment/data/cifp/FAACIFP18")

count = 0
with open(CIFP_FILE, "r", encoding="latin-1") as f:
    for line in f:
        if "KAAT" in line[:20]:
            print(repr(line[:80]))
            count += 1
            if count >= 20:
                break

print(f"\nTotal shown: {count}")

# Also check what format airport codes take
print("\nFirst 5 SUSAP lines (raw):")
count2 = 0
with open(CIFP_FILE, "r", encoding="latin-1") as f:
    for line in f:
        if line.startswith("SUSAP"):
            print(repr(line[:80]))
            count2 += 1
            if count2 >= 5:
                break

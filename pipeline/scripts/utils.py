import os
from pathlib import Path

RAW_ROOT = Path(r"C:\Users\ashraf deen\Downloads\Cognitives- Member Risk Stratification and Care Management\Cognitives---Member-Risk-Stratification-and-Care-Management\pipeline\raw")

for root, dirs, files in os.walk(RAW_ROOT):
    for f in files:
        print(os.path.relpath(os.path.join(root, f), RAW_ROOT))

project_file_path = "/media/jeyanth-s/DevDrive/AI_Workspace/projects/Cognitives---Member-Risk-Stratification-and-Care-Management/pipeline"
import polars as pl
from pathlib import Path
import yaml
import duckdb
project_file_path = Path(project_file_path)
# -------------------------
# Load config paths
# -------------------------
with open(project_file_path / "config/paths.yaml") as f:
    paths = yaml.safe_load(f)

RAW_ROOT = Path(paths["data_root"]) / "raw"
PARQUET_ROOT = Path(paths["data_root"]) / "parquet"
DB_ROOT = Path(paths["data_root"]) / "db"

NULL_VALUES = ["", "NA", "NULL", "V0481"]

# -------------------------
# Helper: ingest CSV → Parquet (Polars)
# -------------------------
def ingest_one(in_path, out_path):
    print(f"Ingesting {in_path} → {out_path}")
    df = pl.scan_csv(in_path, null_values=NULL_VALUES, ignore_errors=True)
    df.collect().write_parquet(out_path)

# -------------------------
# 1️⃣ Beneficiary (yearly)
# -------------------------
for year in [2008, 2009, 2010]:
    in_path = RAW_ROOT / "beneficiary" / f"{year}_beneficiary.csv"
    out_path = PARQUET_ROOT / "beneficiary" / f"{year}_beneficiary.parquet"
    ingest_one(in_path, out_path)

# -------------------------
# 2️⃣ Inpatient (single)
# -------------------------
in_path = RAW_ROOT / "inpatient" / "inpatient_2008_2010.csv"
out_path = PARQUET_ROOT / "inpatient" / "inpatient_2008_2010.parquet"
ingest_one(in_path, out_path)

# -------------------------
# 3️⃣ Outpatient (single)
# -------------------------
in_path = RAW_ROOT / "outpatient" / "outpatient_2008_2010.csv"
out_path = PARQUET_ROOT / "outpatient" / "outpatient_2008_2010.parquet"
ingest_one(in_path, out_path)

# -------------------------
# 4️⃣ Carrier (two parts) → DuckDB ingestion for memory efficiency
# -------------------------
# -------------------------
# Carrier (two parts) → DuckDB ingestion
# -------------------------
carrier_parts = sorted((RAW_ROOT / "carrier").glob("carrier_2008_2010_part*.csv"))
carrier_parquet_out = PARQUET_ROOT / "carrier" / "carrier_2008_2010.parquet"

if carrier_parquet_out.exists():
    carrier_parquet_out.unlink()

con = duckdb.connect()

for i, f in enumerate(carrier_parts):
    print(f"Ingesting {f} into DuckDB...")
    if i == 0:
        con.execute(f"""
            CREATE TABLE carrier AS
            SELECT * FROM read_csv_auto('{f}', nullstr='V0481')
        """)
    else:
        con.execute(f"""
            INSERT INTO carrier
            SELECT * FROM read_csv_auto('{f}', nullstr='V0481')
        """)

print(f"Exporting Carrier to Parquet → {carrier_parquet_out}")
con.execute(f"COPY carrier TO '{carrier_parquet_out}' (FORMAT PARQUET)")
con.close()
print("✅ Carrier ingestion completed!")


# -------------------------
# 5️⃣ PDE (single)
# -------------------------
in_path = RAW_ROOT / "pde" / "pde_2008_2010.csv"
out_path = PARQUET_ROOT / "pde" / "pde_2008_2010.parquet"
ingest_one(in_path, out_path)

print("✅ Full ETL to Parquet completed successfully!")

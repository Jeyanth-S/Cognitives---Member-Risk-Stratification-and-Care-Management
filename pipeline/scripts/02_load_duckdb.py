import duckdb
from pathlib import Path
import yaml
project_file_path = "/media/jeyanth-s/DevDrive/AI_Workspace/projects/Cognitives---Member-Risk-Stratification-and-Care-Management/pipeline"
project_file_path = Path(project_file_path)
# -------------------------
# Load config paths
# -------------------------
with open(project_file_path / "config/paths.yaml") as f:
    paths = yaml.safe_load(f)

PARQUET_ROOT = Path(paths["data_root"]) / "parquet"
DB_ROOT = Path(paths["data_root"]) / "db"
DB_ROOT.mkdir(exist_ok=True, parents=True)
DB_FILE = DB_ROOT / "synpuf.duckdb"

# -------------------------
# Connect DuckDB
# -------------------------
con = duckdb.connect(database=str(DB_FILE))

# -------------------------
# 1️⃣ Beneficiary (yearly)
# -------------------------
beneficiary_dir = PARQUET_ROOT / "beneficiary"
for year_file in sorted(beneficiary_dir.glob("*.parquet")):
    table_name = f"beneficiary_{year_file.stem.split('_')[0]}"
    print(f"Loading {year_file} → DuckDB table {table_name}")
    con.execute(f"""
        CREATE OR REPLACE TABLE {table_name} AS
        SELECT * FROM read_parquet('{year_file}')
    """)

# Optionally, merge all years into a single table
print("Merging all Beneficiary years into table 'beneficiary_all'")
con.execute(f"""
    CREATE OR REPLACE TABLE beneficiary_all AS
    SELECT * FROM read_parquet('{beneficiary_dir}/2008_beneficiary.parquet')
    UNION ALL
    SELECT * FROM read_parquet('{beneficiary_dir}/2009_beneficiary.parquet')
    UNION ALL
    SELECT * FROM read_parquet('{beneficiary_dir}/2010_beneficiary.parquet')
""")

# -------------------------
# 2️⃣ Inpatient
# -------------------------
inpatient_file = PARQUET_ROOT / "inpatient" / "inpatient_2008_2010.parquet"
print(f"Loading {inpatient_file} → DuckDB table inpatient")
con.execute(f"""
    CREATE OR REPLACE TABLE inpatient AS
    SELECT * FROM read_parquet('{inpatient_file}')
""")

# -------------------------
# 3️⃣ Outpatient
# -------------------------
outpatient_file = PARQUET_ROOT / "outpatient" / "outpatient_2008_2010.parquet"
print(f"Loading {outpatient_file} → DuckDB table outpatient")
con.execute(f"""
    CREATE OR REPLACE TABLE outpatient AS
    SELECT * FROM read_parquet('{outpatient_file}')
""")

# -------------------------
# 4️⃣ Carrier
# -------------------------
carrier_file = PARQUET_ROOT / "carrier" / "carrier_2008_2010.parquet"
print(f"Loading {carrier_file} → DuckDB table carrier")
con.execute(f"""
    CREATE OR REPLACE TABLE carrier AS
    SELECT * FROM read_parquet('{carrier_file}')
""")

# -------------------------
# 5️⃣ PDE
# -------------------------
pde_file = PARQUET_ROOT / "pde" / "pde_2008_2010.parquet"
print(f"Loading {pde_file} → DuckDB table pde")
con.execute(f"""
    CREATE OR REPLACE TABLE pde AS
    SELECT * FROM read_parquet('{pde_file}')
""")

# -------------------------
# Optional: check row counts
# -------------------------
tables = ["beneficiary_all", "inpatient", "outpatient", "carrier", "pde"]
for t in tables:
    count = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"Table {t} has {count} rows")

con.close()
print(f"✅ All Parquet files loaded into DuckDB: {DB_FILE}")

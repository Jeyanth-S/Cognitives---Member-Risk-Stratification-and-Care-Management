import duckdb
from pathlib import Path
import yaml
project_file_path = "/media/jeyanth-s/DevDrive/AI_Workspace/projects/Cognitives---Member-Risk-Stratification-and-Care-Management/pipeline"
project_file_path = Path(project_file_path)
with open(project_file_path / "config/paths.yaml") as f:
    paths = yaml.safe_load(f)

DB_PATH = Path(paths["data_root"]) / "db" / "synpuf.duckdb"
conn = duckdb.connect(DB_PATH)

# Example: aggregate Carrier claims by Part A / Part B
conn.execute("""
CREATE OR REPLACE TABLE carrier_part_a AS
SELECT 
    DESYNPUF_ID,
    COUNT(DISTINCT CLM_ID) AS part_a_claims,
    SUM(
        COALESCE(LINE_NCH_PMT_AMT_1,0) + COALESCE(LINE_NCH_PMT_AMT_2,0)
        -- add all LINE_NCH_PMT_AMT_3..13 similarly
    ) AS part_a_spend
FROM carrier
GROUP BY DESYNPUF_ID
""")

conn.execute("""
CREATE OR REPLACE TABLE carrier_part_b AS
SELECT 
    DESYNPUF_ID,
    COUNT(DISTINCT CLM_ID) AS part_b_claims,
    SUM(
        COALESCE(LINE_BENE_PTB_DDCTBL_AMT_1,0) + COALESCE(LINE_BENE_PTB_DDCTBL_AMT_2,0)
        -- add all LINE_BENE_PTB_DDCTBL_AMT_3..13 similarly
    ) AS part_b_spend
FROM carrier
GROUP BY DESYNPUF_ID
""")

# Join with Beneficiary and other tables for ML features
conn.execute("""
CREATE OR REPLACE TABLE ml_features AS
SELECT b.DESYNPUF_ID,
       b.BENE_BIRTH_DT, b.BENE_SEX_IDENT_CD, b.BENE_RACE_CD,
       ca.part_a_claims, ca.part_a_spend,
       cb.part_b_claims, cb.part_b_spend
FROM beneficiary_all b
LEFT JOIN carrier_part_a ca USING(DESYNPUF_ID)
LEFT JOIN carrier_part_b cb USING(DESYNPUF_ID)
""")

# Export ML-ready Parquet
conn.execute("COPY ml_features TO '/media/jeyanth-s/DevDrive/AI_Workspace/projects/Cognitives---Member-Risk-Stratification-and-Care-Management/pipeline/features/ml_features.parquet' (FORMAT PARQUET)")
conn.close()

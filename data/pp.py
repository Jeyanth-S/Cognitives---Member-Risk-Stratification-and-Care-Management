# Feature Engineering Pipeline for CMS DE-SynPUF Project (VS Code - Python)

import pandas as pd
from datetime import datetime

# ------------------------------
# STEP 1: Load Beneficiary Summary Files
# ------------------------------
ben_08 = pd.read_csv("beneficiary_summary_2008_10k.csv")
ben_08['YEAR'] = 2008

ben_09 = pd.read_csv("beneficiary_summary_2009_10k.csv")
ben_09['YEAR'] = 2009

ben_10 = pd.read_csv("beneficiary_summary_2010_10k.csv")
ben_10['YEAR'] = 2010

beneficiary_df = pd.concat([ben_08, ben_09, ben_10], ignore_index=True)

# Deduplicate: Keep only the latest year for each patient
# beneficiary_df.sort_values(by='YEAR', ascending=False, inplace=True)
 # beneficiary_df = beneficiary_df.drop_duplicates(subset='DESYNPUF_ID', keep='first')


# ------------------------------
# STEP 2: Process Beneficiary Features
# ------------------------------
beneficiary_df['BENE_BIRTH_DT'] = pd.to_datetime(beneficiary_df['BENE_BIRTH_DT'], format='%Y%m%d', errors='coerce')
beneficiary_df['age'] = beneficiary_df['YEAR'] - beneficiary_df['BENE_BIRTH_DT'].dt.year

chronic_cols = [col for col in beneficiary_df.columns if col.startswith("SP_")]
beneficiary_df['chronic_conditions_count'] = beneficiary_df[chronic_cols].sum(axis=1)

# ------------------------------
# STEP 3: Load and Combine Claims
# ------------------------------
inpatient = pd.read_csv("inpatient_10K.csv")
outpatient = pd.read_csv("outpatient_10k.csv")
pde = pd.read_csv("prescription_drug_10k.csv")

# ------------------------------
# STEP 4: Aggregate Inpatient Claims
# ------------------------------
inpatient['CLM_FROM_DT'] = pd.to_datetime(inpatient['CLM_FROM_DT'], format='%Y%m%d', errors='coerce')
inpatient['CLM_THRU_DT'] = pd.to_datetime(inpatient['CLM_THRU_DT'], format='%Y%m%d', errors='coerce')

inpatient_agg = inpatient.groupby('DESYNPUF_ID').agg({
    'CLM_ID': 'count',
    'CLM_PMT_AMT': 'sum',
    'CLM_THRU_DT': 'max'
}).rename(columns={
    'CLM_ID': 'inpatient_count',
    'CLM_PMT_AMT': 'inpatient_cost',
    'CLM_THRU_DT': 'recent_inpatient_date'
}).reset_index()

# ------------------------------
# STEP 5: Aggregate Outpatient Claims
# ------------------------------
outpatient_agg = outpatient.groupby('DESYNPUF_ID').agg({
    'CLM_ID': 'count',
    'CLM_PMT_AMT': 'sum'
}).rename(columns={
    'CLM_ID': 'outpatient_count',
    'CLM_PMT_AMT': 'outpatient_cost'
}).reset_index()

# ------------------------------
# STEP 6: Aggregate Prescription Drug Claims
# ------------------------------
pde_agg = pde.groupby('DESYNPUF_ID').agg({
    'PDE_ID': 'count',
    'DAYS_SUPLY_NUM': 'mean',
    'TOT_RX_CST_AMT': 'sum'
}).rename(columns={
    'PDE_ID': 'drug_refills',
    'DAYS_SUPLY_NUM': 'days_supply_avg',
    'TOT_RX_CST_AMT': 'total_drug_cost'
}).reset_index()

# ------------------------------
# STEP 7: Merge All Aggregated Feature Sets
# ------------------------------
features_df = beneficiary_df.merge(inpatient_agg, on='DESYNPUF_ID', how='left')\
                               .merge(outpatient_agg, on='DESYNPUF_ID', how='left')\
                               .merge(pde_agg, on='DESYNPUF_ID', how='left')

# ------------------------------
# STEP 8: Handle Missing Values
# ------------------------------
features_df.fillna({
    'inpatient_count': 0,
    'inpatient_cost': 0,
    'outpatient_count': 0,
    'outpatient_cost': 0,
    'drug_refills': 0,
    'days_supply_avg': 0,
    'total_drug_cost': 0
}, inplace=True)

# ------------------------------
# STEP 9: Optional Label Creation (e.g. high risk if admitted inpatient)
# ------------------------------
features_df['high_risk_label'] = features_df['inpatient_count'].apply(lambda x: 1 if x > 0 else 0)

# ------------------------------
# STEP 10: Save Final Dataset
# ------------------------------
features_df.to_csv("final_features_dataset.csv", index=False)

print("✅ Feature engineering completed. Final dataset saved as 'final_features_dataset.csv'")

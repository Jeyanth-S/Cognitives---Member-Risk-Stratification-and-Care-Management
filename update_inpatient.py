import pandas as pd

# Load existing updated inpatient file with correct path
df = pd.read_csv(r"data\inpatient_10K_UPDATED.csv")

# Correct diagnosis columns prefix (matches your data variable names)
diag_cols = [f'ICD9_DGNS_CD_{i}' for i in range(1, 9)]

def has_icd(row, codes):
    for col in diag_cols:
        code = str(row.get(col, '')).strip()
        if code and code != 'nan':
            if any(code.startswith(c) for c in codes):
                return 1
    return 0

# Define ICD codes for each condition (examples; expand as needed)
alz_codes = ['331', '290']
chf_codes = ['428', '398', '402']
kidney_codes = ['585']
cancer_codes = ['140', '141', '142']
copd_codes = ['490', '491', '492']
diabetes_codes = ['250']
ihd_codes = ['410', '411', '412', '413', '414']
osteo_codes = ['733']
rao_codes = ['714', '715']
stroke_codes = ['430', '431', '432']

# Add flags for each chronic condition
df['HAS_ALZ'] = df.apply(lambda row: has_icd(row, alz_codes), axis=1)
df['HAS_CHF'] = df.apply(lambda row: has_icd(row, chf_codes), axis=1)
df['HAS_KIDNEY'] = df.apply(lambda row: has_icd(row, kidney_codes), axis=1)
df['HAS_CANCER'] = df.apply(lambda row: has_icd(row, cancer_codes), axis=1)
df['HAS_COPD'] = df.apply(lambda row: has_icd(row, copd_codes), axis=1)
df['HAS_DIABETES'] = df.apply(lambda row: has_icd(row, diabetes_codes), axis=1)
df['HAS_IHD'] = df.apply(lambda row: has_icd(row, ihd_codes), axis=1)
df['HAS_OSTEO'] = df.apply(lambda row: has_icd(row, osteo_codes), axis=1)
df['HAS_RAO'] = df.apply(lambda row: has_icd(row, rao_codes), axis=1)
df['HAS_STROKE'] = df.apply(lambda row: has_icd(row, stroke_codes), axis=1)

# Save back to original file with a full valid path (replace with your actual path)
df.to_csv(r'D:\Member-Risk-Stratification-and-Care-Management\Cognitives---Member-Risk-Stratification-and-Care-Management\data\inpatient_10K_UPDATED.csv', index=False)

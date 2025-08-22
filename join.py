import pandas as pd

# --- 1. LOAD ALL DATASETS ---

# Replace with your actual file paths
beneficiary_file = r'C:\Users\ashraf deen\OneDrive\Desktop\Cognitives - Patient Risk Startification and Care Management\Cognitives---Member-Risk-Stratification-and-Care-Management\data\beneficiary_summary_2008_10k.csv'
inpatient_file = r'C:\Users\ashraf deen\OneDrive\Desktop\Cognitives - Patient Risk Startification and Care Management\Cognitives---Member-Risk-Stratification-and-Care-Management\data\inpatient_10K.csv'
labeled_snapshots_file = r'C:\Users\ashraf deen\OneDrive\Desktop\Cognitives - Patient Risk Startification and Care Management\Cognitives---Member-Risk-Stratification-and-Care-Management\data\member_snapshots_labeled.csv'

# Load beneficiaries
beneficiaries = pd.read_csv(beneficiary_file)

# Load inpatient claims, parse admission date
inpatient_claims = pd.read_csv(inpatient_file, parse_dates=['CLM_ADMSN_DT'])
inpatient_claims.rename(columns={'CLM_ADMSN_DT': 'admission_date'}, inplace=True)

# Load labeled snapshots (created earlier)
member_snapshots = pd.read_csv(labeled_snapshots_file, parse_dates=['index_date'])

# --- OPTIONAL: If member_snapshots not created yet, uncomment and use the label creation code ---
# def approx_enrollment_dates(row, year=2008):
#     enroll_start = pd.Timestamp(f'{year}-01-01')
#     months_covered = row.get('BENE_HI_CVRAGE_TOT_MONS', 0)
#     enroll_end = enroll_start + pd.Timedelta(days=months_covered * 30)
#     return pd.Series([enroll_start, enroll_end])
#
# beneficiaries[['coverage_start_date', 'coverage_end_date']] = beneficiaries.apply(approx_enrollment_dates, axis=1)
# beneficiaries = beneficiaries[beneficiaries['coverage_end_date'] > beneficiaries['coverage_start_date']]
#
# def generate_quarterly_index_dates(row):
#     start_date = row['coverage_start_date'] + pd.Timedelta(days=180)
#     end_date = row['coverage_end_date']
#     if end_date < start_date:
#         return []
#     dates = []
#     current = start_date
#     while current <= end_date:
#         dates.append(current)
#         current += pd.Timedelta(days=90)
#     return dates
#
# index_date_rows = []
# for _, row in beneficiaries.iterrows():
#     for d in generate_quarterly_index_dates(row):
#         index_date_rows.append({'DESYNPUF_ID': row['DESYNPUF_ID'], 'index_date': d})
# member_snapshots = pd.DataFrame(index_date_rows)
#
# def label_hospitalization(row):
#     member = row['DESYNPUF_ID']
#     idx_date = row['index_date']
#     window_end = idx_date + pd.Timedelta(days=90)
#     admissions = inpatient_claims[
#         (inpatient_claims['DESYNPUF_ID'] == member) &
#         (inpatient_claims['admission_date'] > idx_date) &
#         (inpatient_claims['admission_date'] <= window_end)
#     ]
#     return 1 if not admissions.empty else 0
#
# member_snapshots['label'] = member_snapshots.apply(label_hospitalization, axis=1)

# --- 2. JOIN labeled snapshots with beneficiary data on DESYNPUF_ID ---

df = member_snapshots.merge(beneficiaries, on='DESYNPUF_ID', how='left')

# --- 3. EXTRACT INPATIENT ADMISSION COUNT IN PAST 6 MONTHS FOR EACH SNAPSHOT ---

def count_inpatient_admissions(row):
    member_id = row['DESYNPUF_ID']
    idx_date = row['index_date']
    lookback_start = idx_date - pd.Timedelta(days=180)  # 6 months lookback

    past_admissions = inpatient_claims[
        (inpatient_claims['DESYNPUF_ID'] == member_id) &
        (inpatient_claims['admission_date'] >= lookback_start) &
        (inpatient_claims['admission_date'] < idx_date)
    ]
    return past_admissions.shape[0]

df['past_6mo_inpatient_adm_count'] = df.apply(count_inpatient_admissions, axis=1)

# --- 4. INSPECT RESULT ---

print(df.head())

# Optionally, save the extended dataframe
df.to_csv(r'C:\Users\ashraf deen\OneDrive\Desktop\Cognitives - Patient Risk Startification and Care Management\Cognitives---Member-Risk-Stratification-and-Care-Management\data\member_snapshots_features.csv', index=False)

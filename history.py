import pandas as pd

# --- 1. LOAD DATA ---

beneficiary_file = r'C:\Users\ashraf deen\OneDrive\Desktop\Cognitives - Patient Risk Startification and Care Management\Cognitives---Member-Risk-Stratification-and-Care-Management\data\beneficiary_summary_2008_10k.csv'
inpatient_file = r'C:\Users\ashraf deen\OneDrive\Desktop\Cognitives - Patient Risk Startification and Care Management\Cognitives---Member-Risk-Stratification-and-Care-Management\data\inpatient_10K.csv'

beneficiaries = pd.read_csv(beneficiary_file)
inpatient_claims = pd.read_csv(inpatient_file, parse_dates=['CLM_ADMSN_DT'])
inpatient_claims.rename(columns={'CLM_ADMSN_DT': 'admission_date'}, inplace=True)

# --- 2. APPROXIMATE ENROLLMENT DATES FROM COVERAGE MONTHS ---

def approx_enrollment_dates(row, year=2008):
    enroll_start = pd.Timestamp(f'{year}-01-01')
    months_covered = row.get('BENE_HI_CVRAGE_TOT_MONS', 0)  # use your actual column
    enroll_end = enroll_start + pd.Timedelta(days=months_covered * 30)
    return pd.Series([enroll_start, enroll_end])

beneficiaries[['coverage_start_date', 'coverage_end_date']] = beneficiaries.apply(approx_enrollment_dates, axis=1)

# Filter to only beneficiaries with valid coverage (end after start)
beneficiaries = beneficiaries[beneficiaries['coverage_end_date'] > beneficiaries['coverage_start_date']]

print(f'Valid beneficiaries after filtering coverage: {len(beneficiaries)}')

# --- 3. GENERATE QUARTERLY INDEX DATES ---

def generate_quarterly_index_dates(row):
    start_date = row['coverage_start_date'] + pd.Timedelta(days=180)  # start 6 months after enrollment start
    end_date = row['coverage_end_date']
    if end_date < start_date:
        return []
    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current)
        current += pd.Timedelta(days=90)
    return dates

index_date_rows = []
for _, row in beneficiaries.iterrows():
    q_dates = generate_quarterly_index_dates(row)
    for d in q_dates:
        index_date_rows.append({'DESYNPUF_ID': row['DESYNPUF_ID'], 'index_date': d})

member_snapshots = pd.DataFrame(index_date_rows)

print(f'Number of member index dates generated: {len(member_snapshots)}')
print(member_snapshots.head())

# --- 4. LABEL CREATION ---

def label_hospitalization(row):
    member = row['DESYNPUF_ID']
    idx_date = row['index_date']
    window_end = idx_date + pd.Timedelta(days=90)
    admissions = inpatient_claims[
        (inpatient_claims['DESYNPUF_ID'] == member) &
        (inpatient_claims['admission_date'] > idx_date) &
        (inpatient_claims['admission_date'] <= window_end)
    ]
    return 1 if not admissions.empty else 0

# Safety check for empty member_snapshots before applying
if not member_snapshots.empty:
    member_snapshots['label'] = member_snapshots.apply(label_hospitalization, axis=1)
    print(member_snapshots.head())

    # Save output labeled data
    member_snapshots.to_csv(r'C:\Users\ashraf deen\OneDrive\Desktop\member_snapshots_labeled.csv', index=False)

else:
    print("No index dates generated, member_snapshots is empty.")

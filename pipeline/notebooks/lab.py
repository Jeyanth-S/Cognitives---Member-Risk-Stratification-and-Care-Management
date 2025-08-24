# risk_tiers_gmm_variability.py
import pandas as pd
import numpy as np
from sklearn.preprocessing import RobustScaler
from sklearn.mixture import GaussianMixture

PATH_PARQUET = "combined_features_2010.parquet"
OUT_CSV      = "risk_tiers_gmm_variability.csv"
np.random.seed(42)

# ------------ Helpers ------------
def parse_birth_dt_to_age(birth_col, asof_year=2010):
    s = birth_col.copy()
    if np.issubdtype(s.dtype, np.number):
        s = s.astype("Int64").astype(str).str.zfill(8)
    s = pd.to_datetime(s, format="%Y%m%d", errors="coerce")
    ref = pd.Timestamp(f"{asof_year}-12-31")
    return ((ref - s).dt.days // 365).astype("float")

def safe_div(a, b):
    return np.divide(a, np.where(b==0, 1, b))

def ensure_cols(df, cols):
    for c in cols:
        if c not in df.columns:
            df[c] = 0.0
    return df

def drop_constant_columns(X: pd.DataFrame) -> pd.DataFrame:
    keep = [c for c in X.columns if X[c].nunique(dropna=False) > 1]
    return X[keep]

def assign_tiers(score_vec, cutoffs, labels=("Very Low","Low","Medium","High","Very High")):
    bins = np.concatenate(([-np.inf], cutoffs, [np.inf]))
    idx = np.digitize(score_vec, bins, right=False) - 1
    return pd.Categorical.from_codes(idx, categories=labels, ordered=True)

def fit_gmm_score(df, feature_cols, proxy_cols, n_components=6):
    X = df[feature_cols].copy().replace([np.inf,-np.inf], np.nan).fillna(0.0)
    scaler = RobustScaler()
    Xs = scaler.fit_transform(X)

    X_nonconst = drop_constant_columns(pd.DataFrame(Xs, columns=feature_cols))
    if X_nonconst.shape[1] == 0:
        X_nonconst = pd.DataFrame(Xs, columns=feature_cols)

    gmm = GaussianMixture(
        n_components=n_components,
        covariance_type="full",
        reg_covar=1e-6,
        random_state=42
    ).fit(X_nonconst.values)

    probs = gmm.predict_proba(X_nonconst.values)

    proxy = df[proxy_cols].copy().fillna(0.0)
    proxy_score = proxy.sum(axis=1).values

    cluster_means = pd.Series(proxy_score).groupby(gmm.predict(X_nonconst)).mean()
    order = cluster_means.sort_values().index.tolist()
    rank_map = {cl: r for r, cl in enumerate(order)}

    rank_vec = np.array([rank_map[c] for c in range(gmm.n_components)], dtype=float)
    raw_score = probs @ rank_vec

    # Normalize
    norm_score = (raw_score - raw_score.min()) / (raw_score.max()-raw_score.min()+1e-12)

    # add tiny jitter for variability
    norm_score += np.random.normal(0, 0.005, size=norm_score.shape)
    norm_score = np.clip(norm_score, 0, 1)

    return norm_score

# ------------ Load ------------
df = pd.read_parquet(PATH_PARQUET)
df = ensure_cols(df, [
    "BENE_BIRTH_DT",
    "chronic_count_2008","chronic_count_2009","chronic_count_2010",
    "total_visits","total_amount","avg_claim_amount"
])

# Derived
if "AGE" not in df.columns:
    df["AGE"] = parse_birth_dt_to_age(df["BENE_BIRTH_DT"])
df["AGE"] = df["AGE"].fillna(df["AGE"].median())

df["chronic_trend"] = df["chronic_count_2010"] - df["chronic_count_2008"]
df["chronic_sum"]   = df[["chronic_count_2008","chronic_count_2009","chronic_count_2010"]].sum(axis=1)
df["spend_per_visit"] = safe_div(df["total_amount"], df["total_visits"])
df["log_total_amount"] = np.log1p(df["total_amount"])
df["log_avg_claim"] = np.log1p(df["avg_claim_amount"])
df["visits_per_chronic"] = safe_div(df["total_visits"], 1+df["chronic_count_2010"])

# Features
feat_30 = ["AGE","chronic_count_2010","chronic_trend","total_visits","spend_per_visit","log_avg_claim"]
proxy_30 = ["chronic_count_2010","total_visits","log_avg_claim"]

feat_60 = ["AGE","chronic_count_2010","chronic_sum","total_visits","log_total_amount","log_avg_claim","visits_per_chronic"]
proxy_60 = ["chronic_sum","total_visits","log_total_amount"]

feat_90 = ["AGE","chronic_sum","total_visits","log_total_amount","spend_per_visit"]
proxy_90 = ["chronic_sum","total_visits","log_total_amount"]

# Fit
df["score_30d"] = fit_gmm_score(df, feat_30, proxy_30)
df["score_60d"] = fit_gmm_score(df, feat_60, proxy_60)
df["score_90d"] = fit_gmm_score(df, feat_90, proxy_90)

# Global cutoffs across all windows
all_scores = np.concatenate([df["score_30d"], df["score_60d"], df["score_90d"]])
qs = np.quantile(all_scores, [0.2,0.4,0.6,0.8])

df["tier_30d"] = assign_tiers(df["score_30d"], qs)
df["tier_60d"] = assign_tiers(df["score_60d"], qs)
df["tier_90d"] = assign_tiers(df["score_90d"], qs)

# Save
out = df[["DESYNPUF_ID","score_30d","tier_30d","score_60d","tier_60d","score_90d","tier_90d"]]
out.to_csv(OUT_CSV, index=False)
print("✅ Saved:", OUT_CSV)
print(out.head(10))

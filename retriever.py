# retriever.py
import pandas as pd
import pinecone
import config

# --- Init Pinecone ---
pc = pinecone.Pinecone(api_key=config.PINECONE_API_KEY)
index = pc.Index(config.PINECONE_INDEX_NAME)

# --- Load Patient Dataset ---
patients_df = pd.read_csv(
    r"C:\Users\ashraf deen\Downloads\Cognitives- Member Risk Stratification and Care Management\Cognitives---Member-Risk-Stratification-and-Care-Management\pipeline\notebooks\combined_features_2010.csv"
)


def check_condition(patient_value, condition, threshold=None, min_value=None, max_value=None, value=None):
    """Evaluate if patient_value satisfies the rule from knowledge base."""
    try:
        # Convert to numeric if possible
        if isinstance(patient_value, str) and patient_value.isdigit():
            patient_value = int(patient_value)
        elif isinstance(patient_value, str):
            try:
                patient_value = float(patient_value)
            except:
                pass

        if condition == ">=" and threshold is not None:
            return patient_value >= threshold
        elif condition == "<=" and threshold is not None:
            return patient_value <= threshold
        elif condition == "==" and value is not None:
            return patient_value == value
        elif condition == "between" and min_value is not None and max_value is not None:
            return min_value <= patient_value <= max_value
        elif condition in ["exists", "present"]:  # for binary flags like SP_CHF
            return str(patient_value) == "1"
        elif condition == "high" and threshold is not None:
            return patient_value >= threshold
        elif condition == "low" and max_value is not None:
            return patient_value <= max_value
        elif condition == "frequent" and threshold is not None:
            return patient_value >= threshold
        elif condition == "senior" and min_value is not None:
            return patient_value >= min_value
        elif condition == "increasing" and threshold is not None:
            return patient_value >= threshold
    except Exception as e:
        print(f"⚠️ Condition check failed for value={patient_value}, condition={condition}: {e}")
    return False


def get_patient_info(patient_id: str):
    """Retrieve patient diseases & suggestions from Pinecone knowledge base."""

    # filter patient row by DESYNPUF_ID
    patient_row = patients_df[patients_df["DESYNPUF_ID"] == patient_id]
    if patient_row.empty:
        return {"patient_id": patient_id, "diseases": [], "suggestions": []}

    patient_row = patient_row.iloc[0]  # single row
    diseases, suggestions = [], []

    for col in patient_row.index:
        if col == "DESYNPUF_ID":
            continue

        patient_value = patient_row[col]

        # Fetch KB entry for this feature directly from Pinecone
        try:
            result = index.fetch(ids=[col])   # returns FetchResponse
            vectors = result.vectors          # dict of {id: Vector}
        except Exception as e:
            print(f"⚠️ Pinecone fetch failed for {col}: {e}")
            continue

        if not vectors or col not in vectors:
            continue

        kb = vectors[col].metadata  # metadata is stored here

        # Check condition from KB
        if check_condition(
            patient_value,
            kb.get("condition"),
            kb.get("threshold"),
            kb.get("min_value"),
            kb.get("max_value"),
            kb.get("value")
        ):
            diseases.append(col)
            suggestions.append(kb.get("suggestion", ""))

    return {
        "patient_id": patient_id,
        "diseases": diseases,
        "suggestions": suggestions
    }

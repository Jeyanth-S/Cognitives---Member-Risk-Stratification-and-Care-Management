from typing import List, Dict
import config
import re

USE_LOCAL = config.USE_LOCAL_GENERATOR and config.GENERATIVE_MODEL

# Lazy import to avoid heavy startup if not used
generator_pipeline = None
tokenizer_for_trunc = None
if USE_LOCAL:
    try:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
        print("Loading generator model:", config.GENERATIVE_MODEL)
        tokenizer_for_trunc = AutoTokenizer.from_pretrained(config.GENERATIVE_MODEL)
        model = AutoModelForSeq2SeqLM.from_pretrained(config.GENERATIVE_MODEL)
        generator_pipeline = pipeline("text2text-generation", model=model, tokenizer=tokenizer_for_trunc, device=-1)
    except Exception as e:
        print("⚠️ Could not initialize local generator model:", e)
        generator_pipeline = None
        tokenizer_for_trunc = None

def clean_suggestions(text: str) -> str:
    """Remove duplicate lines and excessive repetition (preserve order)."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    seen = set()
    out = []
    for ln in lines:
        lower = ln.lower()
        if lower not in seen:
            seen.add(lower)
            out.append(ln)
    return "\n".join(out)

def extractive_fallback(retrieved_texts: List[str], max_items=5) -> str:
    """
    If the model fails or output looks generic, return short extractive bullets
    from the retrieved_texts (original sentences).
    """
    keywords = ["treat", "treatment", "manage", "management", "diagnos", "symptom",
                "prevent", "screen", "therapy", "surgery", "medic", "vaccine", "recommend"]
    bullets = []
    seen = set()
    for t in retrieved_texts:
        s = t.strip()
        low = s.lower()
        if any(k in low for k in keywords) or len(bullets) < 2:
            # take sentence if it contains a keyword, otherwise allow a couple of general sentences
            if low not in seen:
                seen.add(low)
                bullets.append("- " + s)
        if len(bullets) >= max_items:
            break
    if not bullets:
        return "No clear suggestion in provided context."
    return "\n".join(bullets)

def _shorten_context_by_chars(text: str, max_chars=1500) -> str:
    if len(text) <= max_chars:
        return text
    # try to cut on sentence boundary near max_chars
    cut = text.rfind('.', 0, max_chars)
    if cut == -1:
        return text[:max_chars]
    return text[:cut+1]

def summarize_context(disease: str, retrieved_texts: List[str], max_new_tokens=128) -> Dict:
    """
    Produces a structured summary dict:
      { "disease": disease, "suggestion": "<string>", "source_chunks": retrieved_texts }
    - Prefer model-based structured output (Diagnosis/Treatment/Prevention) on a SHORT context.
    - If model missing or output is generic/garbled, fallback to extractive_fallback (original sentences).
    """
    concatenated = "\n\n".join(retrieved_texts).strip()
    if not concatenated:
        return {"disease": disease, "suggestion": "", "source_chunks": retrieved_texts}

    # Keep context short so model input tokens remain within model limits
    truncated_context = _shorten_context_by_chars(concatenated, max_chars=1500)

    prompt = (
        f"Using only the text in Context, extract concise bullets under three headers for '{disease}'.\n\n"
        f"Context:\n{truncated_context}\n\n"
        f"Output exactly like:\nDiagnosis:\n- point\nTreatment:\n- point\nPrevention:\n- point\n\n"
        f"Do NOT add information not present in the context. If a section lacks info, put 'Not available.'\n"
    )

    suggestion = ""
    if generator_pipeline:
        try:
            out = generator_pipeline(
                prompt,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                num_return_sequences=1
            )[0].get("generated_text", "")
            suggestion = clean_suggestions(out.strip())
            # quick sanity checks: if output is too short or contains placeholder 'Point', fallback
            if (len(suggestion) < 20) or ("point 1" in suggestion.lower()) or ("- point" in suggestion.lower()):
                suggestion = extractive_fallback(retrieved_texts)
        except Exception as e:
            # model error -> fallback extractive
            suggestion = f"(generator error) {e}\n\n" + extractive_fallback(retrieved_texts)
    else:
        # no model available — do extractive fallback
        suggestion = extractive_fallback(retrieved_texts)

    # final clean-up: avoid extremely long repetition
    if len(suggestion) > 1200:
        suggestion = suggestion[:1200] + "..."

    return {"disease": disease, "suggestion": suggestion, "source_chunks": retrieved_texts}

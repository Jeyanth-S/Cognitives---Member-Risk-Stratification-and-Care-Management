# """
# Generate a concise suggestion from retrieved context.
# By default this tries a small local HF model (flan-t5-small).
# If USE_LOCAL_GENERATOR is false or the model isn't installed, it falls back to returning
# the concatenated retrieved text (safe fallback).
# """

# from typing import List, Dict
# import config

# USE_LOCAL = config.USE_LOCAL_GENERATOR and config.GENERATIVE_MODEL

# # Lazy import to avoid heavy startup if not used
# generator_pipeline = None
# if USE_LOCAL:
#     try:
#         from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
#         print("Loading generator model:", config.GENERATIVE_MODEL)
#         tokenizer = AutoTokenizer.from_pretrained(config.GENERATIVE_MODEL)
#         model = AutoModelForSeq2SeqLM.from_pretrained(config.GENERATIVE_MODEL)
#         generator_pipeline = pipeline("text2text-generation", model=model, tokenizer=tokenizer, device=-1)
#     except Exception as e:
#         print("⚠️ Could not initialize local generator model:", e)
#         generator_pipeline = None

# def clean_suggestions(text: str) -> str:
#     lines = [line.strip() for line in text.splitlines() if line.strip()]
#     seen = set()
#     unique_lines = []
#     for line in lines:
#         if line not in seen:
#             seen.add(line)
#             unique_lines.append(line)
#     return "\n".join(unique_lines)



# # def summarize_context(disease: str, retrieved_texts: List[str], max_length=128) -> Dict:
# #     """
# #     Returns a dict: { "disease": disease, "suggestion": "<text>", "source_chunks": [...] }
# #     """
# #     concatenated = "\n\n".join(retrieved_texts).strip()
# #     if not concatenated:
# #         return {"disease": disease, "suggestion": "", "source_chunks": []}

# #     suggestion = ""
# #     if generator_pipeline:
# #         # Compose an instruction-like prompt that asks the LLM to extract/tidy suggestions
# #         # prompt = (
# #         #     f"Extract a concise clinical suggestion (1-3 short bullet points) for the condition "
# #         #     f"'{disease}' based only on the context below. Do NOT hallucinate. If the context doesn't "
# #         #     f"contain explicit treatment suggestions, say 'No clear suggestion in provided context.'\n\n"
# #         #     f"Context:\n{concatenated}\n\nSuggestion:"
# #         # )
# #         # prompt = (
# #         #     f"How is '{disease}' diagnosed? What are the treatment and prevention options? Provide your answer "
# #         #     # f"in 2-3 bullet points. Do not repeat sentences. "
# #         #     f"Only use information explicitly present in the context. "
# #         #     f"If no treatment or prevention advice is present, respond with: 'No clear suggestion in provided context.'\n\n"
# #         #     f"Context:\n{concatenated}\n\n"
# #         #     f"Suggestions:"
# #         # )

# #         prompt = (
# #             f"Given the following medical context about '{disease}',\n"
# #             f"extract and provide three sections clearly labeled:\n"
# #             f"Diagnosis:\nTreatment:\nPrevention:\n\n"
# #             f"Only include information explicitly present in the context.\n"
# #             f"If any section lacks information, leave it blank or say 'Not available.'\n\n"
# #             f"Context:\n{concatenated}\n\n"
# #             f"Please format your answer exactly like this:\n"
# #             f"Diagnosis:\n- Point 1\n- Point 2\nTreatment:\n- Point 1\n- Point 2\nPrevention:\n- Point 1\n- Point 2\n"
# #         )



# #         try:
# #             out = generator_pipeline(prompt, max_length=max_length, do_sample=False)[0]["generated_text"]
# #             suggestion = clean_suggestions(out.strip())
# #             if len(suggestion) > 800:
# #                 suggestion = suggestion[:800] + "..."
# #         except Exception as e:
# #             suggestion = f"(generator error) {e}"
# #     else:
# #         # Fallback: return the retrieved chunks concatenated
# #         suggestion = concatenated[:1000] + ("..." if len(concatenated) > 1000 else "")

# #     return {
# #         "disease": disease,
# #         "suggestion": suggestion,     # ✅ now it's a plain string
# #         "source_chunks": retrieved_texts
# #     }



# def summarize_context(disease: str, retrieved_texts: List[str], max_new_tokens=256) -> Dict:
#     """
#     Summarize disease context into Diagnosis, Treatment, Prevention sections.
#     """
#     # Join retrieved chunks
#     concatenated = "\n\n".join(retrieved_texts).strip()

#     if not concatenated:
#         return {"disease": disease, "suggestion": "", "source_chunks": []}

#     # 🔹 Limit context length to avoid exceeding model's max (512 tokens)
#     from transformers import AutoTokenizer
#     tokenizer = AutoTokenizer.from_pretrained("distilgpt2")  # or your model name

#     max_input_tokens = 400  # keep under 512
#     tokens = tokenizer.encode(concatenated, truncation=True, max_length=max_input_tokens)
#     truncated_context = tokenizer.decode(tokens)

#     # Build structured prompt
#     prompt = (
#         f"Given the following medical context about '{disease}',\n"
#         f"extract and provide three sections clearly labeled:\n"
#         f"Diagnosis:\nTreatment:\nPrevention:\n\n"
#         f"Only include information explicitly present in the context.\n"
#         f"If any section lacks information, leave it blank or say 'Not available.'\n\n"
#         f"Context:\n{truncated_context}\n\n"
#         f"Please format your answer exactly like this:\n"
#         f"Diagnosis:\n- Point 1\n- Point 2\nTreatment:\n- Point 1\n- Point 2\nPrevention:\n- Point 1\n- Point 2\n"
#     )

#     suggestion = ""
#     if generator_pipeline:
#         try:
#             out = generator_pipeline(
#                 prompt,
#                 max_new_tokens=max_new_tokens,   # ✅ use only this
#                 do_sample=False
#             )[0]["generated_text"]
#             suggestion = out.strip()
#             if len(suggestion) > 800:
#                 suggestion = suggestion[:800] + "..."
#         except Exception as e:
#             suggestion = f"(generator error) {e}"
#     else:
#         suggestion = truncated_context[:1000] + ("..." if len(truncated_context) > 1000 else "")

#     return {
#         "disease": disease,
#         "suggestion": suggestion,
#         "source_chunks": retrieved_texts
#     }




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

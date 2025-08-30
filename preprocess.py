import fitz  # PyMuPDF
import re
import unicodedata 

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    return full_text



def clean_text(text):
    # Remove page numbers and excessive newlines
    lines = text.split('\n')
    cleaned_lines = [line.strip() for line in lines if line.strip() and not line.strip().isdigit()]
    cleaned_text = " ".join(cleaned_lines)

    # 🔹 Remove bullet/box characters like ▪, , ■, �, etc.
    cleaned_text = re.sub(r"[■▪�●\uf0b7\u2022\u2023\u25A0]+", " ", cleaned_text)

    # Replace multiple spaces with one
    cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()

    return cleaned_text


def chunk_text(text, max_chunk_size=1000):
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_chunk_size):
        chunk = " ".join(words[i:i+max_chunk_size])
        chunks.append(chunk)
    return chunks

def save_cleaned_text(cleaned_text, output_file_path):
    """Save cleaned text to a text file."""
    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write(cleaned_text)
    print(f"Cleaned text saved to: {output_file_path}")


# ---- Example usage ----
pdf_text = extract_text_from_pdf(
    r"C:\Users\ashraf deen\Downloads\Cognitives- Member Risk Stratification and Care Management\Cognitives---Member-Risk-Stratification-and-Care-Management\11_diseases[1].pdf"
)

cleaned_text = clean_text(pdf_text)
text_chunks = chunk_text(cleaned_text)
print(f"Total chunks created: {len(text_chunks)}")
print(f"Sample chunk:\n{text_chunks[0]}")

output_path = r"C:\Users\ashraf deen\Downloads\Cognitives- Member Risk Stratification and Care Management\cleaned_medical_book.txt"
save_cleaned_text(cleaned_text, output_path)

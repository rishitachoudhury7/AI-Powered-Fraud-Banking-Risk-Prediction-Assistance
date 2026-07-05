import os
import re
from sentence_transformers import SentenceTransformer
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
model = SentenceTransformer("all-MiniLM-L6-v2")

def chunk_markdown(filepath: str) -> list[dict]:
    """Split the case studies doc into chunks by section headers (##)."""
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    sections = re.split(r"\n(?=## )", text)
    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        title_match = re.match(r"## (.+)", section)
        title = title_match.group(1) if title_match else "Untitled"
        chunks.append({"section": title, "content": section})
    return chunks

def ingest():
    chunks = chunk_markdown("api/knowledge_base/fraud_case_studies.md")
    print(f"Found {len(chunks)} chunks. Embedding and uploading...")

    for chunk in chunks:
        embedding = model.encode(chunk["content"]).tolist()
        supabase.table("policy_chunks").insert({
            "content": chunk["content"],
            "section": chunk["section"],
            "embedding": embedding
        }).execute()
        print(f"Uploaded: {chunk['section']}")

    print("Done.")

if __name__ == "__main__":
    ingest()

import os
import re
import requests
from supabase import create_client
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=env_path, override=True)

supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])

HF_API_URL = "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction"
HF_HEADERS = {"Authorization": f"Bearer {os.environ['HF_API_TOKEN']}"}

def get_embedding(text: str) -> list[float]:
    response = requests.post(
        HF_API_URL,
        headers=HF_HEADERS,
        json={"inputs": text, "options": {"wait_for_model": True}}
    )
    response.raise_for_status()
    return response.json()

def chunk_markdown(filepath: str) -> list[dict]:
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    text = text.replace("\r\n", "\n")
    sections = re.split(r"\n(?=##\s)", text)
    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        title_match = re.match(r"##\s+(.+)", section)
        title = title_match.group(1) if title_match else "Document Header"
        chunks.append({"section": title, "content": section})

    print(f"Debug: split into {len(chunks)} sections")
    for c in chunks:
        print(f"  - {c['section']} ({len(c['content'])} chars)")

    return chunks

def ingest():
    chunks = chunk_markdown("api/knowledge_base/fraud_case_studies.md")
    print(f"\nFound {len(chunks)} chunks. Clearing old entries and re-uploading...")

    # Clear existing chunks first so re-running this script after editing
    # fraud_case_studies.md doesn't leave stale/duplicate rows behind.
    supabase.table("policy_chunks").delete().neq("section", "").execute()

    for chunk in chunks:
        embedding = get_embedding(chunk["content"])
        supabase.table("policy_chunks").insert({
            "content": chunk["content"],
            "section": chunk["section"],
            "embedding": embedding
        }).execute()
        print(f"Uploaded: {chunk['section']}")

    print("Done.")

if __name__ == "__main__":
    ingest()

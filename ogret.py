import os
import json
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings # Güncel paket
from langchain_community.vectorstores import SupabaseVectorStore
from supabase import create_client, Client
import torch # PyTorch cihaz kontrolü için

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def verileri_supabase_yukle(json_dosya="owasp_docs_rag_final.json"):
    if not os.path.exists(json_dosya):
        print(f"Hata: {json_dosya} dosyası bulunamadı!")
        return

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Cihazı kesin olarak CPU seçiyoruz (CUDA hatasını keser)
    device = "cpu"
    print(f"Embedding modeli BGE-M3, '{device}' üzerinde çalıştırılıyor...")

    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        model_kwargs={"device": device},
        encode_kwargs={"normalize_embeddings": True}
    )

    with open(json_dosya, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    texts = []
    metadatas = []

    for item in dataset:
        texts.append(item["content"])
        metadatas.append({
            "id": item["id"],
            "title": item["title"]
        })

    print(f"Toplam {len(texts)} kayıt BGE-M3 ile vektörleştirilip Supabase'e aktarılıyor...")

    vector_store = SupabaseVectorStore.from_texts(
        texts=texts,
        embedding=embeddings,
        client=supabase,
        table_name="owasp_docs",
        metadatas=metadatas,
        query_name="match_owasp_docs"
    )

    print("İşlem tamamlandı! Bütün veriler BGE-M3 ile işlenip Supabase'e yüklendi.")

if __name__ == "__main__":
    verileri_supabase_yukle()
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import SupabaseVectorStore
from supabase import create_client

from prompts import get_rag_prompt

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# BGE-M3 Embedding modeli
embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)

# 1. TR7 VectorStore
tr7_vectorstore = SupabaseVectorStore(
    client=supabase,
    embedding=embeddings,
    table_name="tr7_docs",
    query_name="match_documents"
)
tr7_retriever = tr7_vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 12}
)

# 2. OWASP / Altyapı VectorStore (owasp_docs tablosu)
owasp_vectorstore = SupabaseVectorStore(
    client=supabase,
    embedding=embeddings,
    table_name="owasp_docs",
    query_name="match_owasp_docs"
)
owasp_retriever = owasp_vectorstore.as_retriever(search_kwargs={"k": 5})

# Personaların yaratıcı çalışabilmesi için temperature 0.2 yapıldı
llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama-3.3-70b-versatile",
    temperature=0.2,
    max_tokens=512
)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def generate_rag_response(history, question, tavir="resmi", source_type="tr7"):
    try:
        # source_type owasp gelirse direkt owasp_retriever kullan
        if source_type == "owasp":
            retrieved_docs = owasp_retriever.invoke(question)
        else:
            retrieved_docs = tr7_retriever.invoke(question)

        # Doküman boş gelse bile hata dönmek yerine LLM'e haber verilir.
        # Böylece persona kendi karakterine uygun ret mesajını kendisi yazar.
        context_text_docs = format_docs(retrieved_docs) if retrieved_docs else "BİLGİ BULUNAMADI."

        rag_prompt = get_rag_prompt(tavir)

        final_prompt = rag_prompt.format(
            context=context_text_docs,
            history=history,
            question=question
        )

        response = llm.invoke(final_prompt)
        content = response.content

        for prefix in ["Cevap:", "Kullanıcı,", "Bu soruya"]:
            if prefix in content:
                content = content.split(prefix)[-1].strip()

        return content.strip()
    except Exception as e:
        print(f"RAG Üretim Hatası: {e}")
        return f"Sorgu işlenirken teknik bir hata oluştu: {str(e)}"
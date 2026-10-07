import os
import json
import re
import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from supabase.client import create_client, Client
from langchain_core.documents import Document
import uvicorn
from dotenv import load_dotenv

from router import detect_intent, check_security_threats
from rana_handler import handle_rana_message
from rag import generate_rag_response

logging.basicConfig(level=logging.INFO)
load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

dosya_yolu = "tr7_docs_kurtarilan.json"
documents = []
doc_index = {} 

if os.path.exists(dosya_yolu):
    with open(dosya_yolu, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    
    for chunk in chunks:
        content = chunk.get("content", chunk.get("page_content", ""))
        metadata = chunk.get("metadata", {})
        if not metadata:
            cat = "rana" if str(chunk.get("id", "")).startswith("rana") else "general"
            metadata = {"id": chunk.get("id"), "title": chunk.get("title", ""), "url": chunk.get("url", ""), "category": cat}
        else:
            if "category" not in metadata:
                metadata["category"] = "rana" if str(metadata.get("id", "")).startswith("rana") else "general"
        
        doc = Document(page_content=content, metadata=metadata)
        documents.append(doc)
        
        doc_id = str(metadata.get("id", "")).lower().strip()
        if doc_id:
            doc_index[doc_id] = doc

def find_doc(doc_id):
    if not doc_id:
        return None
    clean_id = doc_id.lower().strip()
    
    doc = doc_index.get(clean_id)
    if doc:
        return doc.page_content
    
    if clean_id == "rana_hata_kodu_bulma":
        return (
            "Hata kodunu bulmak için şu adımları izleyin:\n\n"
            "1. Sistem arayüzüne giriş yapın.\n"
            "2. Sağ üst köşedeki Ayarlar ikonuna tıklayın.\n"
            "3. 'Sistem Logları' bölümüne girin.\n"
            "4. Listelenen son hatanın yanındaki RANA- ile başlayan kodu okuyun."
        )
    return None

def get_history(session_id, chat_type, limit=3):
    try:
        db_response = supabase.table("chat_history") \
            .select("user_message, bot_message") \
            .eq("session_id", session_id) \
            .eq("state", chat_type) \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()
        
        history_rows = db_response.data if db_response.data else []
        history_rows.reverse()

        formatted_history = ""
        for row in history_rows:
            safe_bot_msg = row['bot_message']
            if len(safe_bot_msg) > 300:
                safe_bot_msg = safe_bot_msg[:300] + "... [Kısaltıldı]"
            formatted_history += f"Kullanıcı: {row['user_message']}\nAsistan: {safe_bot_msg}\n"
        
        return formatted_history
    except Exception:
        return ""

def save_to_history(session_id, user_msg, bot_msg, chat_type):
    try:
        supabase.table("chat_history").insert({
            "session_id": session_id,
            "user_message": user_msg,
            "bot_message": bot_msg,
            "state": chat_type
        }).execute()
    except Exception as e:
        logging.error(f"History kayıt hatası: {e}")

class QueryModel(BaseModel):
    question: str
    session_id: str
    tavir: str = "resmi"  # Varsayılan değer 'resmi'

class ClearModel(BaseModel):
    session_id: str

class NewSessionModel(BaseModel):
    session_id: str
    title: str = "Yeni Sohbet"

@app.get("/sessions")
def get_sessions():
    try:
        response = supabase.table("chat_sessions") \
            .select("session_id, title, created_at, updated_at") \
            .order("updated_at", desc=True) \
            .execute()
        return {"sessions": response.data if response.data else []}
    except Exception as e:
        logging.exception(e)
        return {"sessions": []}

@app.post("/sessions")
def create_session(payload: NewSessionModel):
    try:
        supabase.table("chat_sessions").upsert({
            "session_id": payload.session_id,
            "title": payload.title
        }, on_conflict="session_id").execute()
        return {"status": "success"}
    except Exception as e:
        logging.exception(e)
        return {"status": "error"}

@app.get("/history/{session_id}")
def get_session_history(session_id: str):
    try:
        response = supabase.table("chat_history") \
            .select("id, session_id, state, user_message, bot_message, created_at") \
            .eq("session_id", session_id) \
            .order("created_at", desc=True) \
            .execute()
        
        history_data = response.data if response.data else []
        history_data.reverse()
        return {"history": history_data}
    except Exception as e:
        logging.exception(e)
        return {"history": []}

@app.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    try:
        supabase.table("chat_history").delete().eq("session_id", session_id).execute()
        supabase.table("chat_sessions").delete().eq("session_id", session_id).execute()
        return {"status": "success"}
    except Exception as e:
        logging.exception(e)
        return {"status": "error"}

@app.post("/chat")
def chat_endpoint(payload: QueryModel):
    try:
        session_id = payload.session_id
        user_message = payload.question.strip()
        tavir = payload.tavir  
        lower_user_msg = re.sub(r"\s+", " ", user_message.lower())

        # --- YENİ EKLENEN KISIM: WAF / Güvenlik Kontrolü ---
        threat_status, warning_message = check_security_threats(user_message)
        
        if threat_status == "HARD_BLOCK":
            # Gerçek saldırı: Veritabanına BLOCKED kaydet ve arayüzü kilitle
            save_to_history(session_id, user_message, warning_message, "BLOCKED")
            return {"response": warning_message, "is_blocked": True}
            
        elif threat_status == "SOFT_BLOCK":
            # Şifre/Kuralları sorma: Veritabanına normal (RAG) olarak kaydet, arayüzü KİLİTLEME
            save_to_history(session_id, user_message, warning_message, "RAG")
            return {"response": warning_message, "is_blocked": False}
        # ----------------------------------------------------

        intent = detect_intent(session_id, user_message, lower_user_msg)    

        if intent == "GREETING":
            cevap = "Merhaba! TR7 teknik destek asistanı olarak buradayım. Size nasıl yardımcı olabilirim?"
            save_to_history(session_id, user_message, cevap, "RAG")
            return {"response": cevap}

        if intent == "RANA":
            cevap = handle_rana_message(session_id, user_message, lower_user_msg, find_doc)
            save_to_history(session_id, user_message, cevap, "RANA")
            return {"response": cevap}

        formatted_history = get_history(session_id, "RAG", limit=3)
        
        # Router'dan gelen intent "OWASP" ise kaynak türünü owasp yapıyoruz
        source_type = "owasp" if intent == "OWASP" else "tr7"

        cevap = generate_rag_response(formatted_history, user_message, tavir, source_type=source_type)
        
        save_to_history(session_id, user_message, cevap, "RAG")
        return {"response": cevap}
        
    except Exception as e:
        logging.exception(e)
        return {"response": "Beklenmeyen bir hata oluştu. Lütfen daha sonra tekrar deneyin."}
    try:
        session_id = payload.session_id
        user_message = payload.question.strip()
        tavir = payload.tavir  
        lower_user_msg = re.sub(r"\s+", " ", user_message.lower())

        # --- YENİ EKLENEN KISIM: WAF / Güvenlik Kontrolü ---
        is_threat, warning_message = check_security_threats(user_message)
        if is_threat:
            save_to_history(session_id, user_message, warning_message, "BLOCKED")
            return {"response": warning_message, "is_blocked": True}
        # ----------------------------------------------------

        intent = detect_intent(session_id, user_message, lower_user_msg)    

        if intent == "GREETING":
            cevap = "Merhaba! TR7 teknik destek asistanı olarak buradayım. Size nasıl yardımcı olabilirim?"
            save_to_history(session_id, user_message, cevap, "RAG")
            return {"response": cevap}

        if intent == "RANA":
            cevap = handle_rana_message(session_id, user_message, lower_user_msg, find_doc)
            save_to_history(session_id, user_message, cevap, "RANA")
            return {"response": cevap}

        formatted_history = get_history(session_id, "RAG", limit=3)
        
        # Router'dan gelen intent "OWASP" ise kaynak türünü owasp yapıyoruz
        source_type = "owasp" if intent == "OWASP" else "tr7"

        cevap = generate_rag_response(formatted_history, user_message, tavir, source_type=source_type)
        
        save_to_history(session_id, user_message, cevap, "RAG")
        return {"response": cevap}
        
    except Exception as e:
        logging.exception(e)
        return {"response": "Beklenmeyen bir hata oluştu. Lütfen daha sonra tekrar deneyin."}


@app.post("/clear")
def clear_history(payload: ClearModel):
    try:
        supabase.table("chat_history").delete().eq("session_id", payload.session_id).execute()
        return {"status": "success"}
    except Exception as e:
        logging.exception(e)
        return {"status": "error"}

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "index.html")

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
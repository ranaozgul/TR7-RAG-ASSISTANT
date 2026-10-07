import json
import os
import time
import uuid
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

# .env dosyasındaki GROQ_API_KEY'i yükler
load_dotenv()

class QAItem(BaseModel):
    title: str = Field(description="Sorunun kısa ve özeti niteliğinde başlığı (Örn: Docker Ağ İzolasyonu Çözümü)")
    content: str = Field(description="Doğrudan kullanıcıya hitap eden, 'Senaryo', 'Çözüm' gibi kelimeler KULLANMAYAN, teknik komutlar ve log yolları içeren detaylı çözüm metni.")

class QADataset(BaseModel):
    data: list[QAItem]

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.8,
    max_retries=3
)
structured_llm = llm.with_structured_output(QADataset)

system_prompt = """
Sen uzman bir siber güvenlik ve Linux sistem yöneticisisin. Bir yapay zeka asistanının veritabanı (RAG) için teknik destek yanıtları üretiyorsun.

KONULAR: Sadece ModSecurity (WAF), HAProxy, Docker Compose ağları ve Linux Debian sunucu logları.

KESİN KURALLAR:
1. Çıktı metninde ASLA "Senaryo:", "Çözüm Adımları:", "Şu durum verilmiş" gibi meta-açıklamalar kullanma.
2. Doğrudan kullanıcıya çözüm anlatan, profesyonel ama doğal bir dil kullan.
3. Örnek başlangıç: "HAProxy üzerinden 503 hatası alıyorsanız ilk olarak..." veya "ModSecurity loglarında XSS engellemesi görüyorsanız..."
4. Komut satırı işlemlerini (docker ps, iptables -L), log dosyası yollarını (/var/log/auth.log) ve spesifik teknik terimleri mutlaka kullan.
5. Bana her seferinde birbirinden tamamen farklı {num_scenarios} adet yepyeni problem/çözüm verisi üret.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "Lütfen tamamen yeni ve özgün konularda, doğal dilde yazılmış teknik destek verileri üret.")
])

chain = prompt | structured_llm

def generate_dataset(total_target=5000, batch_size=5, output_file="owasp_docs_rag.json", start_fresh=True):
    all_data = []
    
    # Eski JSON dosyasını silme işlemi
    if start_fresh and os.path.exists(output_file):
        os.remove(output_file)
        print(f"Eski {output_file} dosyası silindi. Yepyeni, tertemiz bir veri seti oluşturuluyor...\n")
    
    # Kaldığı yerden devam etme işlemi (start_fresh=False ise çalışır)
    if not start_fresh and os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            try:
                all_data = json.load(f)
                print(f"Mevcut dosyadan {len(all_data)} kayıt yüklendi. Üretime devam ediliyor...\n")
            except json.JSONDecodeError:
                pass

    remaining_target = total_target - len(all_data)
    if remaining_target <= 0:
        print("Hedeflenen veriye zaten ulaşıldı!")
        return

    iterations = remaining_target // batch_size
    print(f"Kalan {remaining_target} veri için işlem başlıyor...\n")

    for i in range(iterations):
        try:
            response = chain.invoke({"num_scenarios": batch_size})
            for item in response.data:
                all_data.append({
                    "id": uuid.uuid4().int >> 64, # Supabase için benzersiz ID
                    "title": item.title,
                    "content": item.content
                })
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(all_data, f, ensure_ascii=False, indent=4)
            
            print(f"Başarılı! Toplam ulaşılan veri: {len(all_data)}")
            time.sleep(3) 
            
        except Exception as e:
            print(f"API hatası (Limit aşımı vb.), 10 saniye bekleniyor... Hata: {e}")
            time.sleep(10)
            continue

if __name__ == "__main__":
    # Sıfırdan başlamak için start_fresh=True olarak bırak. 
    # Yarıda kesip kaldığın yerden devam etmek istersen False yap.
    generate_dataset(total_target=5000, batch_size=5, start_fresh=False)
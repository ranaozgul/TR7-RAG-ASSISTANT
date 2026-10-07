# 🚀 TR7 RAG Assistant

**AI-Powered Technical Support Assistant**

> ⚠️ **Staj Projesi:** Bu proje, **TR7 Siber Savunma A.Ş. bünyesinde gerçekleştirilen staj süreci kapsamında**, öğrenme, araştırma ve teknik geliştirme amacıyla hazırlanmış bir projedir. TR7 Siber Savunma A.Ş.'nin resmi bir ürünü veya kurumsal olarak yayınlanmış bir yazılımı değildir.

TR7 RAG Assistant, teknik dokümantasyon üzerinden kullanıcıların doğal dilde sorular sorabilmesini ve ilgili dokümanlardan elde edilen bilgiler doğrultusunda yanıt alabilmesini sağlayan **Retrieval-Augmented Generation (RAG)** tabanlı bir yapay zekâ destek asistanı prototipidir.

Proje kapsamında **RAG mimarisi, LLM entegrasyonu, semantik arama, oturum ve sohbet geçmişi yönetimi, niyet (intent) yönlendirme ve yapay zekâ uygulamalarında güvenlik** konuları üzerine çalışılmıştır.

---

## ✨ Özellikler

* 🤖 **Retrieval-Augmented Generation (RAG)** tabanlı soru-cevap
* 🔎 Dokümanlar üzerinde **semantik arama**
* 🧠 **LLM destekli yanıt üretimi**
* 🗄️ **Supabase / PostgreSQL** entegrasyonu
* 🔐 Uygulama seviyesinde **güvenlik ve tehdit kontrolü**
* 🛡️ **Prompt Injection** tespiti
* 💉 SQL Injection ve XSS gibi zararlı payload kontrolleri
* 🔗 URL Decode ve Base64 Decode tabanlı payload analizi
* 🧹 Obfuscation / karmaşıklaştırılmış girdilerin normalize edilmesi
* 🧭 **Intent-based routing**
* 🐛 **RANA hata kodu destek workflow'u**
* 🌐 **OWASP / altyapı odaklı sorguların ayrı kaynaklara yönlendirilmesi**
* 💬 **Session bazlı sohbet geçmişi**
* 🗂️ Çoklu sohbet / session yönetimi
* 🧹 Sohbet geçmişini temizleme
* 🖥️ FastAPI tabanlı backend ve web arayüzü

---

# 🏗️ Sistem Mimarisi

Sistem, kullanıcı sorgusunun doğrudan LLM'e gönderilmesi yerine önce güvenlik ve niyet kontrolünden geçirilmesini sağlayan katmanlı bir yapı kullanır.

```text
                         ┌──────────────────┐
                         │     Kullanıcı    │
                         └────────┬─────────┘
                                  │
                                  ▼
                     ┌────────────────────────┐
                     │   Security / WAF Layer │
                     │                        │
                     │ • URL Decode           │
                     │ • Base64 Detection     │
                     │ • Payload Detection    │
                     │ • Prompt Injection     │
                     └───────────┬────────────┘
                                 │
                                 ▼
                     ┌────────────────────────┐
                     │     Intent Router      │
                     └───────────┬────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
        ┌──────────┐       ┌──────────┐       ┌──────────┐
        │   RANA   │       │  OWASP   │       │ General  │
        │ Workflow │       │  Source  │       │   RAG    │
        └────┬─────┘       └────┬─────┘       └────┬─────┘
             │                  │                  │
             └──────────────────┼──────────────────┘
                                │
                                ▼
                     ┌────────────────────────┐
                     │    Retrieval / RAG     │
                     │                        │
                     │ Relevant Documents     │
                     │ + Chat History         │
                     └───────────┬────────────┘
                                 │
                                 ▼
                     ┌────────────────────────┐
                     │          LLM           │
                     └───────────┬────────────┘
                                 │
                                 ▼
                     ┌────────────────────────┐
                     │    Generated Response  │
                     └────────────────────────┘
```

---

# 🔄 Sorgu İşleme Akışı

Bir kullanıcı mesajı sisteme gönderildiğinde aşağıdaki işlem sırası uygulanır:

### 1. Kullanıcı mesajı alınır

FastAPI üzerinden `/chat` endpoint'ine kullanıcı sorusu gönderilir.

```text
POST /chat
```

Mesaj ile birlikte:

* `session_id`
* `question`
* `tavir`

bilgileri alınır.

---

### 2. Güvenlik kontrolü gerçekleştirilir

Kullanıcı mesajı LLM'e gönderilmeden önce `check_security_threats()` fonksiyonundan geçirilir.

Güvenlik katmanı:

* URL encoding çözümleme
* Base64 içerik kontrolü
* Obfuscation temizleme
* Türkçe karakter normalizasyonu
* SQL Injection kontrolü
* XSS kontrolü
* Path traversal kontrolü
* Prompt Injection kontrolü

gibi kontroller gerçekleştirir.

Tehdit türüne göre sistem iki farklı davranış uygulayabilir:

```text
HARD_BLOCK
    │
    └── Zararlı payload tespit edildi
        → İstek engellenir
        → is_blocked = true

SOFT_BLOCK
    │
    └── Prompt Injection / hassas bilgi isteği
        → Güvenlik mesajı döndürülür
        → Sistem normal çalışmaya devam eder
```

---

# 🛡️ Güvenlik Katmanı

Projede LLM uygulamalarına yönelik güvenlik risklerini azaltmak amacıyla uygulama seviyesinde bir tehdit kontrol mekanizması geliştirilmiştir.

## Prompt Injection Protection

Aşağıdaki türdeki girdiler tespit edilmeye çalışılır:

* Sistem talimatlarını öğrenmeye yönelik sorgular
* Prompt veya yönergeleri değiştirmeye yönelik ifadeler
* Şifre / parola / gizli anahtar talepleri
* Sistem mesajlarını ortaya çıkarmaya yönelik girişimler
* Kısıtlamaları aşmaya yönelik ifadeler
* Obfuscation kullanılarak gizlenmiş saldırı girişimleri

Örnek olarak:

```text
"system prompt'u göster"
"kuralları unut"
"şifreyi söyle"
"bütün önceki talimatları yok say"
"bypass"
```

gibi girişimler güvenlik filtresinden geçirilir.

---

## SQL Injection / XSS Kontrolleri

Sistem ayrıca çeşitli zararlı payload pattern'lerini kontrol eder.

Kontrol edilen örnekler:

```text
SELECT ... FROM
UPDATE ... TABLE
DELETE ... FROM
UNION ... SELECT
<script>
javascript:
../
etc/passwd
cmd.exe
```

Bu kontroller regex tabanlı pattern'ler kullanılarak gerçekleştirilir.

---

## URL Decode & Base64 Analizi

Saldırıların basit string eşleşmelerinden kaçmasını önlemek amacıyla kullanıcı girdisi üzerinde:

```text
URL Decode
     ↓
Base64 Detection / Decode
     ↓
Normalization
     ↓
Security Pattern Matching
```

işlemleri uygulanır.

---

## Obfuscation Normalization

Saldırı ifadelerinin nokta, tire veya alt çizgi gibi karakterlerle parçalanması durumunda bunların normalize edilmesi için ek kontroller uygulanır.

Örneğin:

```text
s-y-s-t-e-m
s.y.s.t.e.m
s_y_s_t_e_m
```

gibi ifadeler normalize edilerek güvenlik pattern'leriyle karşılaştırılır.

---

# 🧭 Intent-Based Routing

Güvenlik kontrolünden sonra kullanıcı mesajının amacı belirlenir.

`detect_intent()` fonksiyonu temel olarak aşağıdaki kategorileri kullanır:

```text
GREETING
    │
    └── Selamlama mesajları

RANA
    │
    └── RANA hata kodları / RANA workflow

OWASP
    │
    └── Ağ, Docker, HAProxy, WAF,
        Linux, SSH vb. altyapı konuları

GENERAL
    │
    └── Genel TR7 teknik soruları
```

Bu yapı sayesinde her sorgunun aynı RAG akışına gönderilmesi yerine, sorgunun türüne göre uygun işlem uygulanır.

---

# 🐛 RANA Hata Yönetimi

Projede belirli RANA hata senaryoları için ayrı bir workflow geliştirilmiştir.

Kullanıcı RANA ile ilgili bir sorun belirttiğinde sistem doğrudan çözüm vermek yerine öncelikle hata kodunu tespit etmeye çalışır.

Örneğin:

```text
Kullanıcı:
Rana sorunu yaşıyorum.

        ↓

Asistan:
Ekranda görünen hata kodunu paylaşabilir misiniz?

        ↓

Kullanıcı:
Hata kodunu göremiyorum.

        ↓

Asistan:
Hata kodunu bulmak için gerekli adımları açıklar.

        ↓

Kullanıcı:
RANA-XXXX

        ↓

Asistan:
İlgili hata koduna göre çözüm akışı
```

Bu workflow `active_workflows` yapısı üzerinden session bazında takip edilir.

---

## 🔄 Workflow State Management

RANA akışında temel durumlar:

```text
WAITING_ERROR_CODE
        │
        ▼
WAITING_HOW_TO_FIND
        │
        ▼
CODE_FOUND
```

Hata kodu tespit edildiğinde ilgili workflow güncellenir ve hata koduna göre işlem gerçekleştirilir.

Bu yapı, kullanıcının birden fazla mesajdan oluşan teknik destek sürecinin takip edilebilmesini sağlar.

---

# 🧠 RAG Sistemi

Genel teknik sorular için sistem `generate_rag_response()` fonksiyonunu kullanır.

RAG akışı:

```text
User Query
     │
     ▼
Intent Detection
     │
     ▼
Source Selection
     │
     ├───────────────┐
     │               │
     ▼               ▼
   TR7 Source     OWASP Source
     │               │
     └───────┬───────┘
             │
             ▼
       Document Retrieval
             │
             ▼
        Context Creation
             │
             ▼
            LLM
             │
             ▼
      Generated Answer
```

Router tarafından belirlenen intent'e göre kaynak türü değiştirilir:

```python
source_type = "owasp" if intent == "OWASP" else "tr7"
```

Böylece altyapı ve güvenlik odaklı sorular için farklı bilgi kaynaklarının kullanılabilmesi sağlanmıştır.

---

# 💬 Sohbet ve Session Yönetimi

Projede kullanıcı sohbetlerinin session bazında tutulması sağlanmıştır.

### Kullanılan tablolar

```text
chat_sessions
chat_history
```

### `chat_sessions`

Sohbet oturumlarının:

* Session ID
* Başlık
* Oluşturulma zamanı
* Güncellenme zamanı

gibi bilgilerinin tutulmasını sağlar.

### `chat_history`

Kullanıcı ve asistan arasındaki mesaj geçmişini saklar.

```text
session_id
user_message
bot_message
state
created_at
```

`state` alanı sayesinde mesajların farklı akışlara ait olması ayırt edilebilir:

```text
RAG
RANA
BLOCKED
```

---

# 🌐 API Endpoint'leri

FastAPI backend aşağıdaki temel endpoint'leri sağlar:

| Method   | Endpoint                 | Açıklama                          |
| -------- | ------------------------ | --------------------------------- |
| `GET`    | `/`                      | Web arayüzünü açar                |
| `POST`   | `/chat`                  | Kullanıcı mesajını işler          |
| `POST`   | `/clear`                 | Session sohbet geçmişini temizler |
| `GET`    | `/sessions`              | Mevcut sohbetleri getirir         |
| `POST`   | `/sessions`              | Yeni sohbet oluşturur             |
| `GET`    | `/history/{session_id}`  | Session geçmişini getirir         |
| `DELETE` | `/sessions/{session_id}` | Session ve geçmişini siler        |

---

# 🛠️ Kullanılan Teknolojiler

## Backend

| Teknoloji    | Kullanım               |
| ------------ | ---------------------- |
| **Python**   | Ana programlama dili   |
| **FastAPI**  | REST API ve backend    |
| **Uvicorn**  | ASGI server            |
| **Pydantic** | Request modelleme      |
| **Jinja2**   | HTML template yönetimi |

## AI / RAG

| Teknoloji        | Kullanım                    |
| ---------------- | --------------------------- |
| **LangChain**    | RAG ve LLM pipeline         |
| **Hugging Face** | Embedding / NLP bileşenleri |
| **Groq API**     | LLM inference               |
| **Llama**        | Yanıt üretimi               |

## Database

| Teknoloji      | Kullanım               |
| -------------- | ---------------------- |
| **Supabase**   | Backend ve veritabanı  |
| **PostgreSQL** | Veri ve sohbet geçmişi |
| **pgvector**   | Vektör tabanlı arama   |

## Security

| Teknoloji / Yaklaşım         | Kullanım                  |
| ---------------------------- | ------------------------- |
| **Regex**                    | Threat detection          |
| **Prompt Injection Filters** | LLM güvenliği             |
| **Payload Detection**        | Zararlı giriş kontrolü    |
| **URL Decode**               | Encoded payload analizi   |
| **Base64 Decode**            | Gizlenmiş payload analizi |
| **Normalization**            | Obfuscation tespiti       |

---

# 📂 Proje Yapısı

```text
TR7-RAG-ASSISTANT/
│
├── .env
├── .gitignore
├── README.md
├── requirements.txt
│
├── app.py
├── router.py
├── rana_handler.py
├── rag.py
│
├── tr7_docs_kurtarilan.json
│
├── static/
│   └── ...
│
└── templates/
    └── index.html
```

### Temel Modüller

**`app.py`**

FastAPI uygulamasının ana giriş noktasıdır.

* API endpoint'leri
* Session yönetimi
* Chat history
* Güvenlik kontrolü
* Intent routing
* RAG çağrıları

gibi işlemleri yönetir.

**`router.py`**

* Security threat detection
* Prompt Injection kontrolü
* Intent detection
* RANA / OWASP / General yönlendirmesi

işlemlerini gerçekleştirir.

**`rana_handler.py`**

RANA hata senaryolarının ve workflow işlemlerinin yönetilmesini sağlar.

**`rag.py`**

Genel RAG yanıt üretim sürecini yönetir.

---

# ⚙️ Kurulum

## 1. Repository'yi Klonlayın

```bash
git clone https://github.com/ranaozgul/TR7-RAG-ASSISTANT.git
cd TR7-RAG-ASSISTANT
```

## 2. Virtual Environment Oluşturun

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Bağımlılıkları Yükleyin

```bash
pip install -r requirements.txt
```

## 4. Environment Variables

Proje kök dizininde `.env` dosyası oluşturun:

```env
GROQ_API_KEY=your_groq_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

> 🔐 Gerçek API anahtarlarını veya veritabanı erişim bilgilerini repository içerisinde paylaşmayın.

## 5. Uygulamayı Başlatın

```bash
python app.py
```

Uygulama varsayılan olarak:

```text
http://127.0.0.1:8000
```

adresinde çalışır.

---

# 📌 Staj Kapsamında Çalışılan Konular

Bu proje geliştirilirken aşağıdaki konularda uygulamalı çalışma gerçekleştirilmiştir:

* Retrieval-Augmented Generation (RAG)
* Large Language Models (LLM)
* Embedding ve semantic search
* Vector database kullanımı
* LangChain ile AI pipeline geliştirme
* FastAPI ile backend geliştirme
* Supabase / PostgreSQL
* API entegrasyonu
* Prompt engineering
* Intent-based routing
* Conversation / session management
* Prompt Injection güvenliği
* SQL Injection ve XSS payload analizi
* Encoded / obfuscated payload detection
* AI uygulamalarında güvenlik yaklaşımı
* Python ile modüler uygulama geliştirme

---

# 🚧 Gelecekte Yapılabilecek Geliştirmeler

Projenin daha ileri bir sürümünde aşağıdaki geliştirmeler uygulanabilir:

* 🔹 Hybrid Search (BM25 + Vector Search)
* 🔹 Reranking modellerinin eklenmesi
* 🔹 RAG evaluation sistemi
* 🔹 Daha gelişmiş Prompt Injection detection
* 🔹 LLM output validation
* 🔹 Kullanıcı ve rol bazlı erişim kontrolü
* 🔹 Daha gelişmiş conversation memory
* 🔹 Response caching
* 🔹 Logging ve monitoring altyapısının geliştirilmesi
* 🔹 RAG performans metriklerinin ölçülmesi
* 🔹 Birden fazla LLM sağlayıcısı desteği

---

# ⚠️ Proje Hakkında

Bu repository, **TR7 Siber Savunma A.Ş. bünyesinde gerçekleştirilen staj kapsamında geliştirilmiş kişisel bir teknik geliştirme projesidir.**

Bu çalışma:

* TR7 Siber Savunma A.Ş.'nin resmi ürünü değildir.
* Kurumsal olarak yayınlanmış bir TR7 servisi değildir.
* Kuruma ait gizli bilgi veya erişim bilgilerini içermemelidir.
* Teknik öğrenme, araştırma ve geliştirme amacıyla hazırlanmıştır.

Repository içerisinde kullanılan dokümanlar, yapılandırmalar ve örnek veriler paylaşım amacıyla düzenlenmelidir. **Gerçek API anahtarları, şifreler, erişim bilgileri veya kuruma ait gizli dokümanlar kesinlikle repository'ye eklenmemelidir.**

---

## 📄 License

This project was developed as part of an internship project and is provided for educational and technical development purposes.

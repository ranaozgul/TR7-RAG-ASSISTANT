import re
import urllib.parse
import base64
from rana_handler import active_workflows

def check_security_threats(text: str) -> tuple[str, str]:
    # 1. URL Decode ve Base64 Çözümleme İşlemleri
    decoded_text = urllib.parse.unquote(text)
    
    base64_matches = re.findall(r'[a-zA-Z0-9+/]{10,}={0,2}', decoded_text)
    for match in base64_matches:
        try:
            b64_decoded = base64.b64decode(match).decode('utf-8')
            decoded_text += f" {b64_decoded}" 
        except Exception:
            pass

    # 2. Obfuscation (Karmaşıklaştırma) Temizliği
    # Araya konulan nokta, tire, alt çizgi gibi ayırıcıları siliyoruz
    clean_text = re.sub(r'[\.\-\_]', '', decoded_text.lower()) 
    
    # Tüm boşlukları siliyoruz
    normalized_text = clean_text.replace(" ", "")
    
    # Türkçe karakterleri İngilizce karakterlere dönüştürüyoruz
    tr_to_eng = str.maketrans("çğıöşü", "cgiosu")
    normalized_text = normalized_text.translate(tr_to_eng)

    # 3. KULLANICININ GÖNDERDİĞİ ORİJİNAL (HAM) METNİ DE NORMALIZE EDELİM
    raw_clean_text = re.sub(r'[\.\-\_]', '', text.lower())
    raw_normalized_text = raw_clean_text.replace(" ", "")
    raw_normalized_text = raw_normalized_text.translate(tr_to_eng)
    
    whitelist = ["dropdown", "tableyapisi", "selectbox", "formsubmit"]
    is_whitelisted = any(safe_word in normalized_text for safe_word in whitelist)
    
    # Çıktının anında terminale düşmesi için flush=True
    print(f"[WAF DEBUG] Gelen Metin: {normalized_text}", flush=True)

    # Listeleri tanımlıyoruz
    malicious_payload_patterns = [
        r"%[^%\s]+%",                  
        r"(select|update|delete|insert|drop|union).*?(from|into|table)", 
        r"(--|#|\/\*)",                
        r"('or'1'='1|'or1=1)",         
        r"(<script.*?>.*?<\/script>)", 
        r"(javascript:)",              
        r"(\.\.\/|\.\.\\)",            
        r"(etc\/passwd|cmd\.exe)"      
    ]

    prompt_injection_patterns = [
        r"(kural|talimat|yonerge|prompt).*?(unut|yoksay|soyle|acikla|nedir|ver|goster|listele|ozetle)",
        r"(s[i1]fr[e3]|p[@a]r[o0]l[@a]|g[i1]zl[i1]anahtar|p[@a]ssw[o0]rd|s[e3]cr[e3]t)",
        r"(butun|tum|onceki).*?(unut|yoksay|iptal)",
        r"(s[i1]st[e3]m|syst[e3]m)(prompt|m[e3]saj)",
        r"(bypass|k[i1]s[i1]tlamalar|[i1]gn[o0]r[e3])",
        r"(s[e3]nart[i1]k|s[e3]nb[i1]r).*(as[i1]stan|adm[i1]n|yon[e3]t[i1]c[i1])"
    ]

    # --- 1. DÖNGÜ: ÖNCE SERT ENGEL (SQLi vb.) KONTROL EDİLMELİ ---
    for pattern in malicious_payload_patterns:
        # DÜZELTME: Hem normalized_text hem de raw_normalized_text regex'ten geçiriliyor
        if re.search(pattern, normalized_text) or re.search(pattern, raw_normalized_text):
            if is_whitelisted and pattern == r"(select|update|delete|insert|drop|union).*?(from|into|table)":
                continue
            return "HARD_BLOCK", "⚠️ Güvenlik İhlali: Zararlı payload (SQLi/XSS vb.) tespit edildi. İstek engellendi."

    # --- 2. DÖNGÜ: SONRA YUMUŞAK ENGEL (Prompt Injection) KONTROL EDİLMELİ ---
    for pattern in prompt_injection_patterns:
        # DÜZELTME: Hem normalized_text hem de raw_normalized_text regex'ten geçiriliyor
        if re.search(pattern, normalized_text) or re.search(pattern, raw_normalized_text):
            return "SOFT_BLOCK", "Güvenlik politikalarım gereği sistem yönergeleri, şifreler veya hassas veriler hakkında bilgi paylaşamam. Size TR7 ile ilgili teknik bir konuda yardımcı olabilir miyim?"

    # Her şey temizse SAFE dönüyoruz
    return "SAFE", ""

# --- 2. NİYET (INTENT) YÖNLENDİRİCİSİ ---
def detect_intent(session_id: str, user_message: str, lower_msg: str) -> str:
    # 1. Selamlama Kontrolü
    greetings = ["merhaba", "selam", "günaydın", "iyi günler", "hello", "hi", "selamlar"]
    if lower_msg in greetings or (len(lower_msg.split()) <= 3 and any(g in lower_msg for g in greetings)):
        return "GREETING"

    # 2. RANA Akış ve Kelime Kontrolleri (Öncelikli)
    has_rana_word = "rana" in lower_msg
    has_error_code = bool(re.search(r"RANA[-\s]?\d{4}", user_message.upper()) or re.search(r"\b\d{4}\b", user_message))
    
    help_keywords = ['nerde', 'nerede', 'nerden', 'nereden', 'bulamıyorum', 'bulamadım', 'nasıl', 'göremiyorum', 'kod', 'bul']
    is_asking_for_location = any(w in lower_msg for w in help_keywords)
    is_in_rana_workflow = session_id in active_workflows

    if is_in_rana_workflow:
        if has_error_code or is_asking_for_location or has_rana_word:
            return "RANA"
        else:
            active_workflows.pop(session_id, None)
            return "GENERAL"

    if has_rana_word or has_error_code:
        return "RANA"

    # 3. TR7 Kontrolü 
    if "tr7" in lower_msg:
        return "GENERAL"

    # 4. OWASP (Altyapı) Kontrolü
    infra_keywords = [
        "docker", "compose", "container", "konteyner", "network", "ağ", "izolasyon", 
        "bridge", "overlay", "port", "ipam", "subnet", "gateway", "dns",
        "haproxy", "503", "502", "gateway", "time-out", "timeout", "maxconn", 
        "load balancing", "backend", "frontend", "stats", "ssl", "tls", "sertifika", 
        "certificate", "cipher", "stickiness", "proxy",
        "modsecurity", "waf", "secrule", "secruleengine", "xss", "csrf", 
        "sql injection", "sqli", "ipdeny", "kural", "rule", "audit", "block", 
        "engelleme", "firewall",
        "debian", "linux", "iptables", "ssh", "sshd", "auth.log", "syslog", 
        "log", "logrotate", "brute-force", "fail2ban", "root", "apt-get", 
        "systemctl", "netstat", "service"
    ]
    
    if any(keyword in lower_msg for keyword in infra_keywords):
        return "OWASP"

    # 5. Hiçbirine uymuyorsa normal TR7 cihaz sorusudur
    return "GENERAL"
import re

# Bu sözlüğü router.py da okuyabilsin diye burada global tutuyoruz
active_workflows = {}

def handle_rana_message(session_id: str, user_message: str, lower_msg: str, find_doc_func) -> str:
    # 1. Kullanıcı 4 Haneli Bir Hata Kodu mu Yazdı?
    match = re.search(r"RANA[-\s]?(\d{4})", user_message.upper())
    if not match:
        match = re.search(r"\b(\d{4})\b", user_message)

    if match:
        code = match.group(1)
        cevap = find_doc_func(f"rana_{code}")
        
        # Kod bulundu, işlem bitti, workflow'u temizle
        active_workflows.pop(session_id, None)
        
        return cevap if cevap else f"RANA-{code} hata kodu dokümantasyonda bulunamadı."

    # 2. Kullanıcı Kodu Nerede Bulacağını mı Soruyor?
    help_keywords = ['nerde', 'nerede', 'nerden', 'nereden', 'bulamıyorum', 'bulamadım', 'nasıl', 'göremiyorum', 'kod', 'bul']
    if any(w in lower_msg for w in help_keywords):
        active_workflows[session_id] = {"state": "WAITING_CODE"}
        
        return (
            "Hata kodunu bulmak için şu adımları izleyin:\n\n"
            "1. TR7 sistem arayüzüne (Web GUI) yönetici yetkileriyle giriş yapın.\n"
            "2. Sağ üst köşede bulunan 'Ayarlar' (Dişli) ikonuna tıklayın.\n"
            "3. Açılan menüden 'Sistem Logları' bölümüne girin.\n"
            "4. Karşılaştığınız hatanın saatine denk gelen log kaydını bulun.\n"
            "5. Log detayındaki 'RANA-' ile başlayan 4 haneli kodu (Örn: RANA-1001) okuyun."
        )

    # 3. Genel RANA Sorunu (İlk Bildirim)
    active_workflows[session_id] = {"state": "WAITING_CODE"}
    return (
        "Size yardımcı olabilmem için lütfen ekranda gördüğünüz "
        "RANA hata kodunu paylaşır mısınız?\n\n"
        "Örneğin: RANA-1001 veya doğrudan 1001 yazabilirsiniz.\n\n"
        "Eğer hata kodunu bulamıyorsanız "
        "'kodu bulamıyorum' yazabilirsiniz."
    )
import json
import re

def final_clean_dataset(input_file="owasp_docs_rag_temiz.json", output_file="owasp_docs_rag_final.json"):
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    cleaned_data = []

    for item in data:
        content = item.get("content", "")
        
        # Art arda tekrarlanan uzun komut yığınlarını ve kelime öbeklerini temizle
        content = re.sub(r'(\b[a-zA-Z0-9\-/._\s]+?\b)(?:\s*,\s*\1)+', r'\1', content)
        
        # Ard arda gelen aynı cümle tekrarlarını regex ile ayıkla
        sentences = content.split(". ")
        unique_sentences = []
        seen = set()
        for sentence in sentences:
            clean_s = sentence.strip()
            if clean_s not in seen:
                seen.add(clean_s)
                unique_sentences.append(clean_s)
        
        final_content = ". ".join(unique_sentences)
        if not final_content.endswith("."):
            final_content += "."

        cleaned_data.append({
            "id": item.get("id"),
            "title": item.get("title"),
            "content": final_content
        })

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=4)

    print(f"Temizlik tamamlandı. Toplam {len(cleaned_data)} kayıt kaydedildi.")

if __name__ == "__main__":
    final_clean_dataset()
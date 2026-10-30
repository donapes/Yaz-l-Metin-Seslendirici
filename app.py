import streamlit as st
import asyncio
import os
import pypdf
import docx
import edge_tts
import tempfile
import re

# Sayfa Yapılandırması
st.set_page_config(page_title="Hukuki Mevzuat Seslendirici - Profesyonel Akış", page_icon="🎧", layout="wide")

st.title("🎧 Profesyonel Mevzuat Seslendirici (Doğal Es ve Vurgulu)")
st.markdown("Noktalama işaretlerine göre **gerçek duraklamalar (esler) yapan ve nefes alan** akıcı spiker modu.")

# Yan Menü - Ses ve Hız Ayarları
st.sidebar.header("⚙️ Ses ve Akış Ayarları")
voice_choice = st.sidebar.selectbox(
    "Ses Karakteri (Spiker Diksiyonu):",
    ("Seda (Sempatik / Yumuşak - Kadın)", "Emel (Duru / Doğal - Kadın)", "Ahmet (Tok / Erkek)")
)

voice_map = {
    "Seda (Sempatik / Yumuşak - Kadın)": "tr-TR-SedaNeural",
    "Emel (Duru / Doğal - Kadın)": "tr-TR-EmelNeural",
    "Ahmet (Tok / Erkek)": "tr-TR-AhmetNeural"
}
selected_voice = voice_map[voice_choice]

hiz_secimi = st.sidebar.selectbox("Okuma Hızı:", ("Normal / Rahat Dinleme (1.0x)", "Biraz Yavaş / Sindirerek (0.9x)", "Akıcı (1.1x)"))
rate_map = {
    "Normal / Rahat Dinleme (1.0x)": "+0%",
    "Biraz Yavaş / Sindirerek (0.9x)": "-8%",
    "Akıcı (1.1x)": "+10%"
}
selected_rate = rate_map[hiz_secimi]

# Dosya Yükleme Alanı
uploaded_file = st.file_uploader("Mevzuat Dosyanızı Yükleyin (PDF veya Word)", type=["pdf", "docx"])

def pdf_oku(file):
    reader = pypdf.PdfReader(file)
    return "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])

def word_oku(file):
    doc = docx.Document(file)
    return "\n".join([p.text for p in doc.paragraphs if p.text])

def metni_ssml_donustur(metin):
    """
    Noktalama işaretlerini ve duraklama yerlerini algılayarak 
    yapay zekaya gerçek insan esleri (nefes araları) verir.
    """
    # Fazla boşlukları temizle
    metin = re.sub(r'\s+', ' ', metin)
    
    # Hukuki kısaltmaları düzgün okutalım
    metin = re.sub(r'\bmd\.\s*', 'madde ', metin, flags=re.IGNORECASE)
    metin = re.sub(r'\bfık\.\s*', 'fıkrası, ', metin, flags=re.IGNORECASE)
    metin = re.sub(r'\bbknz\.\s*', 'bakınız, ', metin, flags=re.IGNORECASE)
    
    # Noktalama işaretlerine özel SSML duraklama etiketleri ekleyelim (Robotikliği bitiren kısım)
    # Virgüllerde kısa es (350ms)
    metin = metin.replace(', ', ', <break time="350ms"/> ')
    # Noktalı virgüllerde orta es (500ms)
    metin = metin.replace('; ', '; <break time="500ms"/> ')
    # Noktalarda uzun es ve nefes (750ms)
    metin = metin.replace('. ', '. <break time="750ms"/> ')
    # İki noktalarda hafif es (400ms)
    metin = metin.replace(': ', ': <break time="400ms"/> ')
    
    # Madde başlıklarına özel uzun duraklama ve vurgu
    metin = re.sub(r'(MADDE\s+\d+)', r'<break time="800ms"/> \1 <break time="600ms"/>', metin, flags=re.IGNORECASE)
    metin = re.sub(r'(Madde\s+\d+)', r'<break time="800ms"/> \1 <break time="600ms"/>', metin, flags=re.IGNORECASE)

    # Edge-TTS için SSML format sarmalayıcısı
    ssml_metin = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="tr-TR">
        <voice name="{selected_voice}">
            <prosody rate="{selected_rate}">
                {metin}
            </prosody>
        </voice>
    </speak>"""
    
    return ssml_metin

def maddelere_ayir(metin):
    pattern = r'(?=(?:MADDE|Madde)\s+\d+)'
    parcalar = re.split(pattern, metin)
    
    maddeler = []
    for i, p in enumerate(parcalar):
        if p.strip():
            satirlar = [s.strip() for s in p.strip().split('\n') if s.strip()]
            madde_adi = satirlar[0] if satirlar else f"Bölüm {i+1}"
            
            if len(satirlar) > 1 and len(madde_adi) < 25:
                madde_adi = f"{satirlar[0]} - {satirlar[1][:50]}"
            else:
                madde_adi = madde_adi[:75]
                
            maddeler.append({
                "id": i,
                "baslik": madde_adi,
                "metin": p.strip()
            })
    return maddeler

async def sese_cevir(metin, cikis_dosyasi):
    ssml_icerik = metni_ssml_donustur(metin)
    communicate = edge_tts.Communicate(ssml_icerik, selected_voice)
    await communicate.save(cikis_dosyasi)

if uploaded_file is not None:
    ext = uploaded_file.name.split(".")[-1].lower()
    with st.spinner("📄 Mevzuat metni taranıyor ve profesyonel akış için esler ekleniyor..."):
        ham_metin = pdf_oku(uploaded_file) if ext == "pdf" else word_oku(uploaded_file)

    if ham_metin.strip():
        maddeler_listesi = maddelere_ayir(ham_metin)
        st.success(f"✅ Dosya başarıyla okundu! Toplam {len(maddeler_listesi)} adet madde analiz edildi.")

        tab1, tab2 = st.tabs(["🎧 Tüm Kanunu Dinle / İndir", "📑 Madde Arama ve Seçmeli Dinleme"])

        # TAB 1: Tüm Kanun
        with tab1:
            st.subheader("Tüm Mevzuat Metni (Nefes Alan Akış)")
            if st.button("🎙️ Tüm Kanunu Akıcı Seslendir (MP3 Üret)", type="primary", key="btn_tum"):
                with st.spinner("Spiker seslendiriyor, duraklamalar işleniyor..."):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                        tmp_path = tmp.name
                    
                    try:
                        asyncio.run(sese_cevir(ham_metin, tmp_path))
                        st.success("🎉 Seslendirme başarıyla tamamlandı!")
                        
                        with open(tmp_path, "rb") as f:
                            audio_bytes = f.read()
                        
                        st.audio(audio_bytes, format="audio/mp3")
                        cikis_adi = uploaded_file.name.rsplit(".", 1)[0] + "_dogal_sesli.mp3"
                        st.download_button("📥 MP3 Dosyasını İndir", data=audio_bytes, file_name=cikis_adi, mime="audio/mp3")
                    except Exception as e:
                        st.error(f"Hata oluştu: {e}")

        # TAB 2: Madde Arama ve Dinleme
        with tab2:
            st.subheader("Madde İçinde Arama ve Seçmeli Dinleme")
            
            arama_sorgusu = st.text_input("🔍 Anahtar Kelime ile Madde Ara (Örn: av, ceza, izin, yasak):", "")
            
            if arama_sorgusu.strip():
                filtrelenmis_maddeler = [m for m in maddeler_listesi if arama_sorgusu.lower() in m["metin"].lower()]
                st.info(f"'{arama_sorgusu}' kelimesi için {len(filtrelenmis_maddeler)} madde bulundu.")
            else:
                filtrelenmis_maddeler = maddeler_listesi

            if filtrelenmis_maddeler:
                secilen_baslik = st.selectbox(
                    "İncelemek/Dinlemek istediğiniz maddeyi seçin:",
                    [m["baslik"] for m in filtrelenmis_maddeler]
                )
                
                secilen_madde = next((m for m in filtrelenmis_maddeler if m["baslik"] == secilen_baslik), None)
                
                if secilen_madde:
                    st.markdown(f"**Seçilen Madde İçeriği:**")
                    st.text_area("Metin Önizlemesi", secilen_madde['metin'], height=150)
                    
                    if st.button("🎧 Bu Maddeyi Akıcı Seslendir", type="primary", key="btn_tek_ssml"):
                        with st.spinner("Seçilen madde doğal eslerle seslendiriliyor..."):
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_tek:
                                tmp_tek_path = tmp_tek.name
                            
                            try:
                                asyncio.run(sese_cevir(secilen_madde["metin"], tmp_tek_path))
                                st.success("🎉 Madde başarıyla seslendirildi!")
                                
                                with open(tmp_tek_path, "rb") as f:
                                    tek_audio_bytes = f.read()
                                
                                st.audio(tek_audio_bytes, format="audio/mp3")
                                st.download_button(
                                    "📥 Bu Maddeyi MP3 Olarak İndir", 
                                    data=tek_audio_bytes, 
                                    file_name=f"madde_{secilen_baslik[:15]}.mp3".replace(" ", "_"), 
                                    mime="audio/mp3"
                                )
                            except Exception as e:
                                st.error(f"Hata oluştu: {e}")
            else:
                st.warning("Aradığınız kritere uygun madde bulunamadı.")
    else:
        st.warning("⚠️ Dosya içeriğinde okunabilir metin bulunamadı.")

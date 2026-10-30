import streamlit as st
import asyncio
import os
import pypdf
import docx
import edge_tts
import tempfile
import re

# Sayfa Yapılandırması
st.set_page_config(page_title="Profesyonel Mevzuat Seslendirici", page_icon="🎙️", layout="wide")

st.title("🎙️ Profesyonel Mevzuat Seslendirici (Madde Madde Bölümlü)")
st.markdown("Kanun ve yönetmeliklerinizi doğal spiker sesiyle dinleyin; **maddelere göre kolayca gezinin**.")

# Yan Menü - Ses ve Hız Ayarları
st.sidebar.header("⚙️ Ses Ayarları")
voice_choice = st.sidebar.selectbox(
    "Ses Karakteri (Spiker Diksiyonu):",
    ("Ahmet (Tok / Erkek - Doğal)", "Emel (Duru / Kadın - Doğal)")
)

voice_map = {
    "Ahmet (Tok / Erkek - Doğal)": "tr-TR-AhmetNeural",
    "Emel (Duru / Kadın - Doğal)": "tr-TR-EmelNeural"
}
selected_voice = voice_map[voice_choice]

hiz_secimi = st.sidebar.selectbox("Okuma Hızı:", ("Normal (1.0x)", "Biraz Hızlı (1.1x)", "Biraz Yavaş (0.9x)"))
rate_map = {
    "Normal (1.0x)": "+0%",
    "Biraz Hızlı (1.1x)": "+10%",
    "Biraz Yavaş (0.9x)": "-10%"
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

def maddelere_ayir(metin):
    """Metni 'MADDE X' veya 'Madde X' kalıplarına göre parçalara böler."""
    pattern = r'(?=(?:MADDE|Madde)\s+\d+)'
    parcalar = re.split(pattern, metin)
    
    maddeler = []
    for i, p in enumerate(parcalar):
        if p.strip():
            satirlar = p.strip().split('\n')
            baslik = satirlar[0][:60] if satirlar else f"Bölüm {i+1}"
            if not ("madde" in baslik.lower() or "bölüm" in baslik.lower() or "kısım" in baslik.lower()):
                baslik = f"Giriş / Genel Metin {i}"
            maddeler.append({
                "id": i,
                "baslik": baslik,
                "metin": p.strip()
            })
    return maddeler

async def sese_cevir(metin, cikis_dosyasi, ses, hiz):
    communicate = edge_tts.Communicate(metin, ses, rate=hiz)
    await communicate.save(cikis_dosyasi)

if uploaded_file is not None:
    ext = uploaded_file.name.split(".")[-1].lower()
    with st.spinner("📄 Mevzuat metni taranıyor ve maddelere ayrılıyor..."):
        ham_metin = pdf_oku(uploaded_file) if ext == "pdf" else word_oku(uploaded_file)

    if ham_metin.strip():
        maddeler_listesi = maddelere_ayir(ham_metin)
        st.success(f"✅ Dosya başarıyla okundu! Toplam {len(maddeler_listesi)} adet madde/bölüm tespit edildi.")

        # Sekmeler oluştur: 1. Tüm Kanun, 2. Madde Madde İnceleme
        tab1, tab2 = st.tabs(["🎧 Tüm Kanunu Dinle / İndir", "📑 Madde Madde Gezin ve Dinle"])

        # TAB 1: Tüm Kanun
        with tab1:
            st.subheader("Tüm Mevzuat Metni Seslendirmesi")
            if st.button("🎙️ Tüm Kanunu Seslendir (MP3 Üret)", type="primary", key="btn_tum"):
                with st.spinner("Yapay zeka spiker tüm metni seslendiriyor, lütfen bekleyin..."):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                        tmp_path = tmp.name
                    
                    try:
                        asyncio.run(sese_cevir(ham_metin, tmp_path, selected_voice, selected_rate))
                        st.success("🎉 Tüm kanun seslendirmesi tamamlandı!")
                        
                        with open(tmp_path, "rb") as f:
                            audio_bytes = f.read()
                        
                        st.audio(audio_bytes, format="audio/mp3")
                        cikis_adi = uploaded_file.name.rsplit(".", 1)[0] + "_tam_sesli.mp3"
                        st.download_button("📥 Tüm MP3 Dosyasını İndir", data=audio_bytes, file_name=cikis_adi, mime="audio/mp3")
                    except Exception as e:
                        st.error(f"Hata oluştu: {e}")

        # TAB 2: Madde Madde Gezinme
        with tab2:
            st.subheader("Kanun Maddeleri İçindekiler")
            st.markdown("Aşağıdan tekrar dinlemek istediğiniz maddeyi seçebilir ve sadece o maddeyi seslendirebilirsiniz:")
            
            # Seçim kutusu için madde başlıkları
            secilen_madde_baslik = st.selectbox(
                "Dinlemek istediğiniz maddeyi seçin:",
                [m["baslik"] for m in maddeler_listesi]
            )
            
            # Seçilen maddeyi bul
            secilen_madde = next((m for m in maddeler_listesi if m["baslik"] == secilen_madde_baslik), None)
            
            if secilen_madde:
                st.info(f"**Seçilen Madde Önizlemesi:**\n\n{secilen_madde['metin'][:400]}...")
                
                if st.button("🎧 Seçilen Maddeyi Seslendir", type="primary", key="btn_tek"):
                    with st.spinner("Seçilen madde seslendiriliyor..."):
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_tek:
                            tmp_tek_path = tmp_tek.name
                        
                        try:
                            asyncio.run(sese_cevir(secilen_madde["metin"], tmp_tek_path, selected_voice, selected_rate))
                            st.success("🎉 Madde seslendirildi!")
                            
                            with open(tmp_tek_path, "rb") as f:
                                tek_audio_bytes = f.read()
                            
                            st.audio(tek_audio_bytes, format="audio/mp3")
                            st.download_button(
                                "📥 Bu Maddeyi MP3 Olarak İndir", 
                                data=tek_audio_bytes, 
                                file_name=f"madde_{secilen_madde_baslik[:20]}.mp3".replace(" ", "_"), 
                                mime="audio/mp3"
                            )
                        except Exception as e:
                            st.error(f"Hata oluştu: {e}")
    else:
        st.warning("⚠️ Dosya içeriğinde okunabilir metin bulunamadı.")

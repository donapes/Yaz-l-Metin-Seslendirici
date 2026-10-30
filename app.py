import streamlit as st
import asyncio
import os
import pypdf
import docx
import edge_tts
import tempfile

# Sayfa Yapılandırması
st.set_page_config(page_title="Profesyonel Mevzuat Seslendirici", page_icon="🎙️", layout="wide")

st.title("🎙️ Profesyonel Mevzuat Seslendirici (Yüksek Kaliteli İnsan Sesi)")
st.markdown("Kanun, yönetmelik ve tebliğlerinizi robotik sesler olmadan, **doğal insan vurgularıyla ve spiker diksiyonuyla** dinleyin.")

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

async def sese_cevir(metin, cikis_dosyasi, ses, hiz):
    communicate = edge_tts.Communicate(metin, ses, rate=hiz)
    await communicate.save(cikis_dosyasi)

if uploaded_file is not None:
    ext = uploaded_file.name.split(".")[-1].lower()
    with st.spinner("📄 Mevzuat metni taranıyor ve temizleniyor..."):
        metin = pdf_oku(uploaded_file) if ext == "pdf" else word_oku(uploaded_file)

    if metin.strip():
        st.success(f"✅ Dosya başarıyla okundu! (Karakter Sayısı: {len(metin):,})")

        if st.button("🎧 Profesyonel Seslendiriciyi Başlat (MP3 Üret)", type="primary"):
            with st.spinner("🎙️ Yapay zeka spiker metni seslendiriyor, lütfen bekleyin..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                    tmp_path = tmp.name
                
                try:
                    # Asenkron seslendirmeyi çalıştır
                    asyncio.run(sese_cevir(metin, tmp_path, selected_voice, selected_rate))
                    st.success("🎉 Seslendirme tamamlandı!")
                    
                    with open(tmp_path, "rb") as f:
                        audio_bytes = f.read()
                    
                    # Web üzerinden doğrudan dinleme paneli
                    st.audio(audio_bytes, format="audio/mp3")
                    
                    # İndirme Butonu
                    cikis_adi = uploaded_file.name.rsplit(".", 1)[0] + "_prof_sesli.mp3"
                    st.download_button(
                        label="📥 Ses Dosyasını İndir (.mp3)",
                        data=audio_bytes,
                        file_name=cikis_adi,
                        mime="audio/mp3"
                    )
                except Exception as e:
                    st.error(f"Bir hata oluştu: {e}")
    else:
        st.warning("⚠️ Dosya içeriğinde okunabilir metin bulunamadı.")

import streamlit as st
import asyncio
import os
import pypdf
import docx
import edge_tts
import tempfile
import re

# Sayfa Yapılandırması
st.set_page_config(page_title="Profesyonel Hukuki Mevzuat Seslendirici", page_icon="🎙️", layout="wide")

st.title("🎙️ Profesyonel Mevzuat Seslendirici & Hukuki Asistan (İnsan Vurgulu)")
st.markdown("Kanun ve yönetmeliklerinizi **robotik tonlardan arındırılmış, profesyonel spiker diksiyonuyla** dinleyin.")

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

hiz_secimi = st.sidebar.selectbox("Okuma Hızı:", ("Normal / Akıcı (1.0x)", "Biraz Yavaş / Sindirerek (0.9x)", "Hızlı (1.1x)"))
rate_map = {
    "Normal / Akıcı (1.0x)": "+0%",
    "Biraz Yavaş / Sindirerek (0.9x)": "-8%",
    "Hızlı (1.1x)": "+10%"
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

def metni_insansilestir_ve_duzenle(metin):
    """
    Yapay zekanın robotik okumasını engellemek, hece yutmasını önlemek 
    ve insansı vurgular kazandırmak için metni hukuki diksiyona uyarlar.
    """
    # Gereksiz fazla boşlukları ve satır sonu bölünmelerini temizle
    metin = re.sub(r'\s+', ' ', metin)
    
    # Hukuki kısaltmaları açık ve akıcı okunacak şekilde düzenle
    metin = re.sub(r'\bmd\.\s*', 'madde ', metin, flags=re.IGNORECASE)
    metin = re.sub(r'\bfık\.\s*', 'fıkrası, ', metin, flags=re.IGNORECASE)
    metin = re.sub(r'\bbknz\.\s*', 'bakınız, ', metin, flags=re.IGNORECASE)
    
    # Madde başlıklarının robotik okunmasını engellemek için araya duraklama hissi katacak ekleme
    metin = re.sub(r'(MADDE\s+\d+[\s\-]*)', r'\n\n \1. \n ', metin, flags=re.IGNORECASE)
    metin = re.sub(r'(Madde\s+\d+[\s\-]*)', r'\n\n \1. \n ', metin, flags=re.IGNORECASE)
    
    # Noktalama işaretlerinden sonra yapay zekanın nefes alması için boşlukları düzenle
    metin = metin.replace(';', '; ')
    metin = metin.replace(':', ': ')
    
    return metin

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

async def sese_cevir(metin, cikis_dosyasi, ses, hiz):
    islenmis_metin = metni_insansilestir_ve_duzenle(metin)
    communicate = edge_tts.Communicate(islenmis_metin, ses, rate=hiz)
    await communicate.save(cikis_dosyasi)

if uploaded_file is not None:
    ext = uploaded_file.name.split(".")[-1].lower()
    with st.spinner("📄 Mevzuat metni taranıyor ve insan sesine uygun formata dönüştürülüyor..."):
        ham_metin = pdf_oku(uploaded_file) if ext == "pdf" else word_oku(uploaded_file)

    if ham_metin.strip():
        maddeler_listesi = maddelere_ayir(ham_metin)
        st.success(f"✅ Dosya başarıyla okundu! Toplam {len(maddeler_listesi)} adet madde analiz edildi.")

        tab1, tab2 = st.tabs(["🎧 Tüm Kanunu Dinle / İndir", "📑 Madde Arama ve Seçmeli Dinleme"])

        # TAB 1: Tüm Kanun
        with tab1:
            st.subheader("Tüm Mevzuat Metni (Spiker Diksiyonu)")
            if st.button("🎙️ Tüm Kanunu Akıcı Seslendir (MP3 Üret)", type="primary", key="btn_tum"):
                with st.spinner("Yapay zeka spiker metni doğal vurgularla seslendiriyor, lütfen bekleyin..."):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                        tmp_path = tmp.name
                    
                    try:
                        asyncio.run(sese_cevir(ham_metin, tmp_path, selected_voice, selected_rate))
                        st.success("🎉 Seslendirme başarıyla tamamlandı!")
                        
                        with open(tmp_path, "rb") as f:
                            audio_bytes = f.read()
                        
                        st.audio(audio_bytes, format="audio/mp3")
                        cikis_adi = uploaded_file.name.rsplit(".", 1)[0] + "_insansi_sesli.mp3"
                        st.download_button("📥 MP3 Dosyasını İndir", data=audio_bytes, file_name=cikis_adi, mime="audio/mp3")
                    except Exception as e:
                        st.error(f"Hata oluştu: {e}")

        # TAB 2: Madde Arama ve Dinleme
        with tab2:
            st.subheader("Madde İçinde Arama ve Nokta Atışı Dinleme")
            
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
                    
                    if st.button("🎧 Bu Maddeyi Akıcı Seslendir", type="primary", key="btn_tek_gelismis"):
                        with st.spinner("Seçilen madde insani tonlamalarla seslendiriliyor..."):
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_tek:
                                tmp_tek_path = tmp_tek.name
                            
                            try:
                                asyncio.run(sese_cevir(secilen_madde["metin"], tmp_tek_path, selected_voice, selected_rate))
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

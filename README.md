# 🎙️ Profesyonel Mevzuat Seslendirici

Kurum veya iş yerinizdeki yoğun mevzuat, kanun, yönetmelik, tebliğ ve genelgeleri okumaktan gözleriniz yoruluyorsa; bu araç belgelerinizi **doğal insan sesine ve spiker diksiyonuna** dönüştürerek kulaklıkla dinlemenizi sağlar.

## 🚀 Özellikler
- **PDF ve Word Desteği:** Yüklediğiniz `.pdf` veya `.docx` formatındaki mevzuatları otomatik olarak okur ve metne dönüştürür.
- **Yapay Zeka Nöral Sesler:** Robotik sesler yerine Microsoft Edge-TTS altyapısını kullanarak son derece akıcı, vurgulu ve anlaşılır Türkçe spiker sesleri sunar (`Ahmet` veya `Emel`).
- **Hız Ayarı:** Okuma hızını ihtiyacınıza göre ayarlayabilirsiniz.
- **İndirilebilir MP3:** Oluşturulan ses dosyalarını telefonunuza veya bilgisayarınıza indirerek yolda, yürüyüşte veya masanızda rahatça dinleyebilirsiniz.

## 🛠️ Kurulum ve Çalıştırma (GitHub Codespaces ile)

Bu aracı çalıştırmak için bilgisayarınızda yerel bir Python kurulumuna ihtiyacınız yoktur. Tamamen tarayıcınız üzerinden (Codespaces ile) çalıştırabilirsiniz:

1. Deponuzu GitHub'da açın.
2. Klavyenizden **`.` (nokta)** tuşuna basarak Codespaces ortamını başlatın.
3. Alttaki Terminal penceresine sırasıyla şu komutları yazın:
   ```bash
   pip install streamlit edge-tts pypdf python-docx
   streamlit run app.py

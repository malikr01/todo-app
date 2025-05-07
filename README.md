# 📝 To-Do App (FastAPI + JWT Authentication)

Bu proje, FastAPI kullanılarak geliştirilmiş, JWT tabanlı kimlik doğrulama sistemi içeren basit bir To-Do (Yapılacaklar) uygulamasıdır.

## 🚀 Özellikler

- JWT ile kimlik doğrulama (Login sistemi)
- Yetkiye göre erişim kontrolü (Admin/user ayrımı)
- Kullanıcıya özel TO-DO Listesi ve TO-DO Adımı oluşturma
- Soft-delete desteği (silme tarihi ile veri gizleme)
- Tamamlanma yüzdesi hesaplama
- Swagger UI üzerinden test edilebilir API

## 🧰 Kullanılan Teknolojiler

- Python 3.9+
- FastAPI
- Pydantic
- JWT (via `python-jose`)
- OAuth2PasswordBearer (FastAPI default auth flow)

## 🛠️ Kurulum

```bash
# Sanal ortam oluştur
python3 -m venv venv
source venv/bin/activate

# Gereksinimleri yükle
pip install -r requirements.txt

# Uygulamayı çalıştır
uvicorn app:app --reload

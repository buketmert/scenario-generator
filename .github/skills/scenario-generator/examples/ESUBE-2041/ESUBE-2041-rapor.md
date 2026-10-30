# Kart Yeterlilik Raporu — ESUBE-2041

**Kart:** E-Şube'den EFT ile para gönderme  
**Durum:** kısmi — Kart büyük ölçüde test edilebilir. IBAN uzunluğu çelişkisi Q-01 yanıtıyla çözüldü; yetersiz bakiye davranışı tanımsız ve akış videosu işlenemedi.  
**Test ortamı:** TEST ortamı, E-Şube web, Chrome, sürüm 4.12, bireysel müşteri  
**Üretilen senaryo:** 6 (6 hazır, 0 taslak)

## Açık sorular

| ID | Soru | Bloklayıcı | Muhatap | İlgili |
|---|---|---|---|---|
| Q-02 | Tutar, gönderici hesabın kullanılabilir bakiyesinden büyükse sistem nasıl davranmalı ve hangi mesaj gösterilmeli? | hayır | ürün sahibi | R5 |
| Q-03 | mevcut-akis-kaydi.mp4 içeriği işlenemedi. Videoda kabul kriterlerinde olmayan bir kural veya akış adımı var mı? Varsa karta metin olarak eklenebilir mi? | hayır | ürün sahibi | R10 |

## Yanıtlanan sorular

Yanıtlar kullanıcı tarafından seçildi; kart sahibiyle teyit edilmesi önerilir.

| ID | Soru | Yanıt |
|---|---|---|
| Q-01 | AC-02'ye göre 26 karakterden uzun IBAN'da "Geçersiz IBAN" mesajı gösterilmeli; geliştirici yorumuna (C-01) göre alan 26 karakterden fazlasını kabul etmiyor. Beklenen davranış hangisi: 27. karakterin girilememesi mi, mesaj gösterilmesi mi? | a) 27. karakter girilemez; alan 26 karakterle sınırlıdır ve mesaj gösterilmez (C-01) |

## Yeterlilik kontrolleri

| ID | Kontrol | Sonuç | Bulgu |
|---|---|---|---|
| R1 | Amaç: ne, kimin için, neden | geçti | Kullanıcı hikâyesi: bireysel müşteri E-Şube'den başka bankadaki hesaba para göndermek istiyor. |
| R2 | Test edilecek gereksinim var | geçti | 4 kabul kriteri, ekteki limit tablosu ve ürün sahibi yorumundan 2 iş kuralı. |
| R3 | Gereksinimler test edilebilir | geçti | Tüm gereksinimler gözlemlenebilir sonuç tanımlıyor; tutar limitleri ekteki tablodan alındı. |
| R4 | Veri kuralları | geçti | IBAN formatı, tutar limitleri (eft-limitleri.xlsx) ve zorunlu alanlar (AC-01, C-02) tanımlı. |
| R5 | Hata ve olumsuz durumlardaki davranış | kısmi | Zorunlu alan, IBAN ve limit hatalarının mesajları var. Tutar bakiyeden büyükse ne olacağı yazılmamış. |
| R6 | Roller, yetkiler, ön koşullar | geçti | Bireysel müşteri; kurumsal müşteri C-03 ile kapsam dışı bırakıldı. |
| R7 | Alanlar arası tutarlılık | geçti | CF-01 Q-01 yanıtıyla (BR-03) çözüldü; CF-02 C-02 ile çözüldü. |
| R8 | Kapsam sınırı | geçti | E-Şube web, ana sayfa → Para Transferleri → EFT ekranı. |
| R9 | Test ortamı | geçti | Environment alanı: TEST, E-Şube web, Chrome. Sürüm fix version alanından: 4.12. |
| R10 | Ekler ve bağlantılar işlendi | kısmi | Ekran tasarımı ve limit tablosu dosya olarak paylaşıldı ve işlendi; mevcut-akis-kaydi.mp4 okunamadı; ESUBE-2039 ve EFT akışı sayfası açılmadı (XML'de yalnızca anahtar / adres). |

## Çelişkiler

| ID | Açıklama | Öğeler | Durum | Çözüm / soru |
|---|---|---|---|---|
| CF-01 | AC-02, 26 karakterden uzun IBAN'da "Geçersiz IBAN" mesajı bekliyor; C-01'e göre alan 26 karakterden fazlasını kabul etmiyor, mesaj hiç oluşmayabilir. | AC-02, CN-01 | sonraki kararla çözüldü | BR-03 |
| CF-02 | AC-01 yalnızca IBAN ve tutarı zorunlu sayıyor; ekran tasarımında Alıcı Adı Soyadı da zorunlu işaretli. | AC-01, UI-01 | sonraki kararla çözüldü | BR-02 |

## Kart envanteri

### Alanlar

| Alan | Durum | Not |
|---|---|---|
| summary | kullanıldı |  |
| issue_type | kullanıldı | Story |
| description | kullanıldı |  |
| acceptance_criteria | kullanıldı | Özel alan: Acceptance Criteria |
| environment | kullanıldı |  |
| priority | kullanıldı |  |
| labels | kullanıldı |  |
| components | kullanıldı |  |
| affects_versions | ilgisiz | Story kartı |
| fix_versions | kullanıldı |  |
| reporter | kullanıldı |  |
| assignee | kullanıldı |  |
| subtasks | boş |  |
| custom_fields | boş |  |

### Ekler

| Ek | Tür | Durum | Çıkarılan bilgi | Öğeler |
|---|---|---|---|---|
| eft-ekran-tasarimi.png | image | işlendi | EFT formu: alan adları ve zorunluluk işaretleri, tutar hata durumu metni. | UI-01, UI-02 |
| eft-limitleri.xlsx | spreadsheet | işlendi | Müşteri tipine göre tek işlem limitleri. Bireysel satırı kullanıldı; kurumsal satırı kapsam dışı (C-03). | BR-01 |
| mevcut-akis-kaydi.mp4 | video | okunamadı | Video içeriği işlenemedi; içerdiği akış veya kurallar senaryolara yansımadı. |  |

### Yorumlar

| ID | Yazar | Tarih | Rol | Durum | Özet | Öğeler |
|---|---|---|---|---|---|---|
| C-01 | mkaya | 2026-10-20 | geliştirici | kullanıldı | IBAN alanında 26 karakter sınırı (maxlength) tanımlı. | CN-01 |
| C-02 | ayilmaz | 2026-10-21 | ürün sahibi | kullanıldı | Alıcı Adı Soyadı da zorunlu; AC-01 buna göre güncellendi. | BR-02 |
| C-03 | ayilmaz | 2026-10-22 | ürün sahibi | kullanıldı | Kurumsal müşteriler bu kartın kapsamında değil. |  |

### Bağlı kartlar ve dış bağlantılar

| Kaynak | Tür | Durum | Not |
|---|---|---|---|
| ESUBE-1980 | epic | kullanıldı | Para transferleri yenileme epic'i; bağlam için okundu, ek kural gelmedi. |
| ESUBE-2039 | relates to | erişilemedi | relates to; XML'de yalnızca anahtar var |
| https://wiki.example.test/display/ESUBE/EFT+Akisi | dış bağlantı | erişilemedi | XML modunda bağlantı açılmaz |

## Uçtan uca akışlar

| Akış | Tür | Başlangıçtan sonuca | Senaryo |
|---|---|---|---|
| UC-ANA | ana akış | E-Şube'ye bireysel müşteri girişi → Para Transferleri > EFT → Gönderici Hesap seçimi → Alıcı IBAN, Alıcı Adı Soyadı ve Tutar girişi → Gönder → başarı mesajı ve dekont numarası | TS-ESUBE-2041-001 |
| UC-ALT-CIFTGONDER | alternatif akış | Ana akış; Gönder butonuna art arda iki kez basılır → tek başarı mesajı ve tek dekont numarası | TS-ESUBE-2041-002 |
| UC-HATA-LIMIT | hata akışı | Ana akış; Tutar limit dışında → "Tutar 1,00 TL ile 50.000,00 TL arasında olmalıdır" mesajı, EFT başlatılmaz | TS-ESUBE-2041-003 |
| UC-HATA-ZORUNLU | hata akışı | Ana akış; zorunlu alanlardan biri boş → "Lütfen zorunlu alanları doldurunuz" mesajı, EFT başlatılmaz | TS-ESUBE-2041-004 |
| UC-HATA-IBAN | hata akışı | Ana akış; Alıcı IBAN TR ile başlamıyor veya 26 karakterden kısa → "Geçersiz IBAN" mesajı, EFT başlatılmaz | TS-ESUBE-2041-005 |
| UC-HATA-IBANUZUN | hata akışı | Ana akış; Alıcı IBAN alanına 26 karakterden uzun değer yazılır → 27. karakter girilemez, mesaj gösterilmez (Q-01 yanıtı) | TS-ESUBE-2041-006 |

## Kapsam

| Öğe | Senaryolar | Durum | Not |
|---|---|---|---|
| AC-01 | TS-ESUBE-2041-001, TS-ESUBE-2041-004 | kapsandı |  |
| AC-02 | TS-ESUBE-2041-001, TS-ESUBE-2041-005, TS-ESUBE-2041-006 | kapsandı |  |
| AC-03 | TS-ESUBE-2041-001, TS-ESUBE-2041-003 | kapsandı |  |
| AC-04 | TS-ESUBE-2041-001, TS-ESUBE-2041-002 | kapsandı |  |
| BR-01 | TS-ESUBE-2041-001, TS-ESUBE-2041-003 | kapsandı |  |
| BR-02 | TS-ESUBE-2041-001, TS-ESUBE-2041-004 | kapsandı |  |
| BR-03 | TS-ESUBE-2041-006 | kapsandı |  |

## Kapsam dışı

- Kurumsal müşteri EFT'si: Ürün sahibi kurumsal müşterileri bu kartın kapsamı dışında bıraktı.
- Yetersiz bakiye davranışı: Kartta tanımlı değil; Q-02 yanıtlanınca senaryo eklenecek.
- Fonksiyonel olmayan testler (performans, güvenlik): Kartta ölçülebilir fonksiyonel olmayan gereksinim yok.

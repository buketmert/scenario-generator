# Kart Yeterlilik Raporu — ESUBE-2041

**Kart:** E-Şube'den EFT ile para gönderme  
**Durum:** kısmi — Kart büyük ölçüde test edilebilir. 26 karakterden uzun IBAN'daki davranış çelişkili (CF-01), yetersiz bakiye davranışı tanımsız ve akış videosu işlenemedi.  
**Test ortamı:** TEST ortamı, E-Şube web, Chrome, sürüm 4.12, bireysel müşteri  
**Üretilen senaryo:** 7 (6 hazır, 1 taslak)

## Açık sorular

| ID | Soru | Bloklayıcı | Muhatap | İlgili |
|---|---|---|---|---|
| Q-01 | AC-02'ye göre 26 karakterden uzun IBAN'da "Geçersiz IBAN" mesajı gösterilmeli; geliştirici yorumuna (C-01) göre alan 26 karakterden fazlasını kabul etmiyor. Beklenen davranış hangisi: 27. karakterin girilememesi mi, mesaj gösterilmesi mi? | evet | ürün sahibi | AC-02, CN-01, CF-01, R7 |
| Q-02 | Tutar, gönderici hesabın kullanılabilir bakiyesinden büyükse sistem nasıl davranmalı ve hangi mesaj gösterilmeli? | hayır | ürün sahibi | R5 |
| Q-03 | mevcut-akis-kaydi.mp4 içeriği işlenemedi. Videoda kabul kriterlerinde olmayan bir kural veya akış adımı var mı? Varsa karta metin olarak eklenebilir mi? | hayır | ürün sahibi | R10 |

## Yeterlilik kontrolleri

| ID | Kontrol | Sonuç | Bulgu |
|---|---|---|---|
| R1 | Amaç: ne, kimin için, neden | geçti | Kullanıcı hikâyesi: bireysel müşteri E-Şube'den başka bankadaki hesaba para göndermek istiyor. |
| R2 | Test edilecek gereksinim var | geçti | 4 kabul kriteri, ekteki limit tablosu ve ürün sahibi yorumundan 2 iş kuralı. |
| R3 | Gereksinimler test edilebilir | geçti | Tüm gereksinimler gözlemlenebilir sonuç tanımlıyor; tutar limitleri ekteki tablodan alındı. |
| R4 | Veri kuralları | geçti | IBAN formatı, tutar limitleri (eft-limitleri.xlsx) ve zorunlu alanlar (AC-01, C-02) tanımlı. |
| R5 | Hata ve olumsuz durumlardaki davranış | kısmi | Zorunlu alan, IBAN ve limit hatalarının mesajları var. Tutar bakiyeden büyükse ne olacağı yazılmamış. |
| R6 | Roller, yetkiler, ön koşullar | geçti | Bireysel müşteri; kurumsal müşteri C-03 ile kapsam dışı bırakıldı. |
| R7 | Alanlar arası tutarlılık | kısmi | CF-01 (AC-02 ile geliştirici yorumu C-01) çözülmedi. CF-02 (AC-01 ile ekran tasarımı) C-02 ile çözüldü. |
| R8 | Kapsam sınırı | geçti | E-Şube web, ana sayfa → Para Transferleri → EFT ekranı. |
| R9 | Test ortamı | geçti | Environment alanı: TEST, E-Şube web, Chrome. Sürüm fix version alanından: 4.12. |
| R10 | Ekler ve bağlantılar işlendi | kısmi | 3 ekten 2'si işlendi; mevcut-akis-kaydi.mp4 okunamadı. |

## Çelişkiler

| ID | Açıklama | Öğeler | Durum | Çözüm / soru |
|---|---|---|---|---|
| CF-01 | AC-02, 26 karakterden uzun IBAN'da "Geçersiz IBAN" mesajı bekliyor; C-01'e göre alan 26 karakterden fazlasını kabul etmiyor, mesaj hiç oluşmayabilir. | AC-02, CN-01 | çözülmedi | Q-01 |
| CF-02 | AC-01 yalnızca IBAN ve tutarı zorunlu sayıyor; ekran tasarımında Alıcı Adı Soyadı da zorunlu işaretli. | AC-01, UI-01 | sonraki kararla çözüldü | BR-02 |

## Kart envanteri

### Alanlar

| Alan | Durum | Not |
|---|---|---|
| summary | kullanıldı |  |
| issue_type | kullanıldı | Story |
| description | kullanıldı | Kullanıcı hikâyesi, ekran yolu, gönderici hesap seçimi, eklere atıf |
| acceptance_criteria | kullanıldı | 4 kabul kriteri |
| environment | kullanıldı | TEST ortamı, E-Şube web, Chrome |
| priority | kullanıldı | High → risk etki puanına girdi |
| labels | kullanıldı | eft |
| components | kullanıldı | Para Transferleri |
| affects_versions | ilgisiz | Story kartı |
| fix_versions | kullanıldı | E-Şube 4.12 |
| reporter | kullanıldı | A. Yılmaz; yorum yazarlarının rolünü belirlemede kullanıldı |
| subtasks | boş |  |
| custom_fields | boş | Test Notları alanı boş |

### Ekler

| Ek | Tür | Durum | Çıkarılan bilgi | Öğeler |
|---|---|---|---|---|
| eft-ekran-tasarimi.png | image | işlendi | EFT formu: alan adları ve zorunluluk işaretleri, tutar hata durumu metni. | UI-01, UI-02 |
| eft-limitleri.xlsx | spreadsheet | işlendi | Müşteri tipine göre tek işlem limitleri. Bireysel satırı kullanıldı; kurumsal satırı kapsam dışı (C-03). | BR-01 |
| mevcut-akis-kaydi.mp4 | video | okunamadı | Video içeriği işlenemedi; içerdiği akış veya kurallar senaryolara yansımadı. |  |

### Yorumlar

| ID | Yazar | Tarih | Rol | Durum | Özet | Öğeler |
|---|---|---|---|---|---|---|
| C-01 | M. Kaya | 2026-10-20 | geliştirici | kullanıldı | IBAN alanında 26 karakter sınırı (maxlength) tanımlı. | CN-01 |
| C-02 | A. Yılmaz | 2026-10-21 | ürün sahibi | kullanıldı | Alıcı Adı Soyadı da zorunlu; AC-01 buna göre güncellendi. | BR-02 |
| C-03 | A. Yılmaz | 2026-10-22 | ürün sahibi | kullanıldı | Kurumsal müşteriler bu kartın kapsamında değil. |  |

### Bağlı kartlar ve dış bağlantılar

| Kaynak | Tür | Durum | Not |
|---|---|---|---|
| ESUBE-1980 | epic | kullanıldı | Para transferleri yenileme epic'i; bağlam için okundu, ek kural gelmedi. |

## Kapsam

| Öğe | Senaryolar | Durum | Not |
|---|---|---|---|
| AC-01 | TS-ESUBE-2041-001, TS-ESUBE-2041-004 | kapsandı |  |
| AC-02 | TS-ESUBE-2041-001, TS-ESUBE-2041-005, TS-ESUBE-2041-006 | kısmen | 26 karakterden uzun IBAN senaryosu (TS-ESUBE-2041-006) Q-01 yanıtını bekliyor. |
| AC-03 | TS-ESUBE-2041-001, TS-ESUBE-2041-002, TS-ESUBE-2041-003 | kapsandı |  |
| AC-04 | TS-ESUBE-2041-001, TS-ESUBE-2041-002, TS-ESUBE-2041-007 | kapsandı |  |
| BR-01 | TS-ESUBE-2041-001, TS-ESUBE-2041-002, TS-ESUBE-2041-003 | kapsandı |  |
| BR-02 | TS-ESUBE-2041-001, TS-ESUBE-2041-004 | kapsandı |  |

**Taslak senaryolar** (yanıt bekleyen):

- TS-ESUBE-2041-006: IBAN 26 karakterden uzun girildiğinde Geçersiz IBAN mesajı gösterilir — Q-01

## Varsayımlar

- A-01 (Q-01): 26 karakterden uzun IBAN girilebiliyorsa AC-02'deki "Geçersiz IBAN" mesajı gösterilir.

## Kapsam dışı

- Kurumsal müşteri EFT'si: Ürün sahibi kurumsal müşterileri bu kartın kapsamı dışında bıraktı.
- Yetersiz bakiye davranışı: Kartta tanımlı değil; Q-02 yanıtlanınca senaryo eklenecek.
- Fonksiyonel olmayan testler (performans, güvenlik): Kartta ölçülebilir fonksiyonel olmayan gereksinim yok.

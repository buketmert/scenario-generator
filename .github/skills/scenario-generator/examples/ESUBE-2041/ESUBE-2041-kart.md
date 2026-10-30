# ESUBE-2041 — E-Şube'den EFT ile para gönderme

> scripts/parse_jira_xml.py ile XML'den üretildi. Kaynak bilgileri, envanter, yorum kimlikleri ve
> kabul kriterleri `ESUBE-2041-kart.json` içinde hazır; JSON'a `source` ve `card_inventory` yazma,
> kabul kriterlerini yeniden yazma (AC kimlikleriyle an). Yalnızca yorumların rolünü, özetini ve
> bağladığı öğeleri yaz.

- **Tür:** Story · **Öncelik:** High · **Durum:** In Progress
- **Bileşenler:** Para Transferleri · **Etiketler:** eft
- **Etkilenen sürüm:** — · **Düzeltme sürümü:** E-Şube 4.12
- **Raporlayan:** A. Yılmaz · **Atanan:** M. Kaya
- **Ortam (environment):** TEST ortamı, E-Şube web, Chrome

## Açıklama

Bireysel müşteri olarak E-Şube'den başka bankadaki bir hesaba EFT ile para gönderebilmeliyim.
Ekran yolu: Ana sayfa → Para Transferleri → EFT
Gönderici hesap, müşterinin vadesiz TL hesapları arasından seçilir. Limitler ekteki tabloda (eft-limitleri.xlsx), ekran tasarımı ekte (eft-ekran-tasarimi.png).
Mevcut akışın kaydı için bkz. EFT akışı sayfası.

## Kabul kriterleri (özel alan: Acceptance Criteria)

- **AC-01:** Alıcı IBAN ve tutar alanları zorunludur. Biri boş bırakılıp Gönder butonuna basılırsa işlem başlatılmaz ve "Lütfen zorunlu alanları doldurunuz" mesajı gösterilir.
- **AC-02:** Alıcı IBAN "TR" ile başlamalı ve 26 karakter olmalıdır. Aksi halde "Geçersiz IBAN" mesajı gösterilir.
- **AC-03:** Tutar, ekteki limit tablosundaki (eft-limitleri.xlsx) bireysel müşteri limitleri içinde olmalıdır. Limit dışındaki tutarda uyarı gösterilir ve işlem başlatılmaz.
- **AC-04:** Başarılı işlemde "İşleminiz başarıyla gerçekleştirilmiştir" mesajı ve dekont numarası gösterilir.

## Diğer özel alanlar

- **Test Notları:** (boş)

## Yorumlar (eskiden yeniye)

### C-01 · mkaya · 2026-10-20

IBAN alanında maxlength=26 tanımlı; 26 karakterden fazlası girilemiyor.

### C-02 · ayilmaz · 2026-10-21

Tasarımdaki gibi Alıcı Adı Soyadı da zorunlu olacak; AC-01 bu şekilde güncellenmiş kabul edilsin.

### C-03 · ayilmaz · 2026-10-22

Kurumsal müşteriler bu kartın kapsamında değil, ayrı kartta ele alınacak.

## Ekler (içerik XML'de yok; envanterde not_provided)

- eft-ekran-tasarimi.png (image, 240 KB)
- eft-limitleri.xlsx (spreadsheet, 18 KB)
- mevcut-akis-kaydi.mp4 (video, 10240 KB)

## Bağlı kartlar (yalnızca anahtar; envanterde not_accessible)

- ESUBE-1980 (epic)
- ESUBE-2039 (relates to)

## Dış bağlantılar (açılmaz; envanterde not_accessible)

- https://wiki.example.test/display/ESUBE/EFT+Akisi

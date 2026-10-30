# KBTYTKM3-1832 — Düzenli Ödeme Talimatı

> scripts/parse_jira_xml.py ile XML'den üretildi. Kaynak bilgileri, envanter, yorum kimlikleri ve
> kabul kriterleri `KBTYTKM3-1832-kart.json` içinde hazır; JSON'a `source` ve `card_inventory` yazma,
> kabul kriterlerini yeniden yazma (AC kimlikleriyle an). Yalnızca yorumların rolünü, özetini ve
> bağladığı öğeleri yaz.

- **Tür:** Cross-functional · **Öncelik:** Low · **Durum:** Open
- **Bileşenler:** — · **Etiketler:** —
- **Etkilenen sürüm:** — · **Düzeltme sürümü:** —
- **Raporlayan:** Buket MERT (Test Mimarisi ve Otomasyonu) · **Atanan:** Buket MERT (Test Mimarisi ve Otomasyonu)
- **Ortam (environment):** boş

## Açıklama

Düzenli Ödeme Talimat Giriş Ekranı (DMTOE)
Düzenli ödemeler talimat giriş ekranı müşteri hesaplarına otomatik eft, havale işlemleri tanımlamak amaçlı kullanılır.
Müşteri numarası girilip listelemeye basıldığında müşteriye ait aktif talimatlar listelenecektir. İptal/pasif talimatlar da listelensin istendiğinde İptal/pasif talimatlar tiki işaretlenerek listelendiğinde müşteriye ait tüm talimatlar listelenecektir.
1.2 Amaç
Düzenli ödeme talimatlarının yapılabilmesi, güncellenmesi ve iptal edilmesi işleminin yapılabilmesi amaçlanmaktadır. Mevcuttaki DMTOE ekranı kullanım açısından ve talimatların yönetimi açısından kullanıcıya zorluk çıkartmaktadır. Bu sebeple yeni ekrana ihtiyaç duyulmuştur.
1.3 Kapsama Alınan Maddeler
Mevcuttaki ekranda tanımlanmış olan ve aktif olan talimatlar yeni tasarlanan ekranda listelenebilecektir. Ek olarak yeni talimat tanımları yeni ekrandan verilmeye başlanacaktır.
Müşteri kendi hesapları arasında talimat tanımlayabilecektir.
1.4 Kapsam Dışı Bırakılan Maddeler
DMTOE ekranındaki Düzenli Ödeme Tipi “Kurum” olan talimatlar DMTOE2 ekranında olmayacaktır. Kurum tahsilatları ekibinin mevuttaki projesi ile o kısım ayrıca Kurum Tahsilatları ekibi tarafından gerçekleştirilecektir.
Kredi kartına EFT işlemi Şube kanalı aracılığıyla yapılamayacaktır. İnternet ve mobil şube ile kredi kartına EFT işlemi yapılabilmektedir. Kredi Kartına EFT talimatı sadece internet ve mobil şubeden verilmeye devam edecektir.

## Kabul kriterleri (özel alan: Kabul Kriterleri)

- **AC-01:** FONKSİYONEL GEREKSİNİMLER
- **AC-02:** Ödeme Tipleri ile ilgili gereksinimler aşağıda madde madde açıklanmıştır:
- **AC-03:** 1) IBAN
- **AC-04:** Ziraat Katılım IBAN’ı haricindeki IBANlar girilebilir. Ziraat Katılım IBAN’I girildiğinde şu şekilde uyarı verilecektir:
- **AC-05:** IBAN Ziraat Katılım Bankasına ait olduğundan işlem "BANKAMIZ HESABINA" sekmesi ile yapılmalıdır.
- **AC-06:** IBAN bilgisi girildiğinde aşağıdaki şekilde Ad/Soyad Banka ve TCKN/VKN bilgileri otomatik getirilir, pasif alandır. Alıcı Ad\Soyad maskelenmiş olarak gelecektir.
- **AC-07:** Alıcı Ad, Soyad bilgisi zorunlu alandır. Bilgi girişi yapılmadığında aşağıdaki gibi uyarı verilcektir. IBAN sekmesinden yapılan işlemlerde IBAN ve Alıcı Ad/Soyad alanları zorunludur.
- **AC-08:** Ad soyad alanına hatalı giriş yapıldığında ekranda uyarı verilmeyecektir. Ancak EFT işlemi de gerçekleşmeyecektir.
- **AC-09:** 2) Başka Banka Hesabına
- **AC-10:** Düzenli ödeme Tipi: Başka Banka Hesabına seçilince İşlem türü Hesaba EFT ve İsme EFT seçenekleri çıkacaktır. Burada tüm alanları doldurmak zorunludur.
- **AC-11:** BAŞKA BANKA HESABINA sekmesinden yapılan işlemlerde Alıcı Ad/Soyad, Alıcı Banka, Alıcı Şube alanları zorunludur.
- **AC-12:** BAŞKA BANKA HESABINA sekmesinden yapılan Hesaba EFT işlemlerinde Alıcı Hesap No alanı zorunludur.
- **AC-13:** İşlem Tipi: Hesaba EFT
- **AC-14:** Alıcı Banka Kodu Alıcı hesabın banka kodu girilir. Zorunlu alandır.
- **AC-15:** Alıcı Şube Kodu Alıcı hesabın şube kodu girilir. Zorunlu alandır.
- **AC-16:** Alıcının Hesabı Alıcının Hesabı girilir. Zorunlu alandır.
- **AC-17:** Ad – Soyad / Unvan Alacaklı hesap sahibinin ad-soyad bilgileri girilir. Zorunlu alandır.
- **AC-18:** İşlem Tipi: İsme EFT
- **AC-19:** Alıcı Banka Kodu Alıcı hesabın banka kodu girilir
- **AC-20:** Alıcı Şube Kodu Alıcı hesabın şube kodu girilir
- **AC-21:** Alıcı Adı – Soyadı / Unvanı Alacaklı hesap sahibinin ad-soyad bilgileri girilir. Zorunlu alandır.
- **AC-22:** Anne Adı Alıcının anne adı girilir.
- **AC-23:** Baba Adı Alacaklının baba adı girilir, zorunlu alandır.
- **AC-24:** Doğum Tarihi Alacaklının doğum tarihi girilir.
- **AC-25:** Alıcının Adresi Alacaklının adres bilgisi girilir. Alıcının adresi veya telefon numaralarından en az bir tanesi girilmelidir.
- **AC-26:** Ev Tel. Alacaklının ev telefonu bilgisi girilir. Alıcının adresi veya telefon numaralarından en az bir tanesi girilmelidir.
- **AC-27:** Cep Tel. Alacaklının cep telefonu bilgisi girilir. Alıcının adresi veya telefon numaralarından en az bir tanesi girilmelidir.

## Diğer özel alanlar

- **Authentication Mehtod:** Client Secret(Basic)
- **BGR - Etkilenen iş doldur:** 1
- **Client Environment:** Test
- **Client Status:** ENABLED
- **Client Type:** Confidential
- **Create User:** False
- **Development:** (boş)
- **Dönem:** 2017
- **Erişim Noktası:** İnternet
- **Güvenlik Testine ihtiyaç var mı?:** Hayır
- **Interval Time:** Limitless
- **Kanal Testi:** Hayır
- **Kullanıcı Profili:** Anonim
- **Ldap Client Environment:** Test
- **Ldap Target Apigateway:** Internet Api Gateway
- **Master Key:** false
- **Meeting Type:** Meeting
- **PCF Space Name:** fed
- **Performans/Yük Testine ihtiyaç var mı?:** Hayır
- **Pilot Testine ihtiyaç var mı?:** Hayır
- **QA Test Required:** Yes
- **S1-Soru-1:** Evet
- **Servis Yöneticiliği:** VERİPARK
- **Skip Code Review:** No
- **Skip Code Review:** No
- **Source ApiGateway:** Internet Api Gateway
- **Target ApiGateway:** Internet Api Gateway
- **Test Senaryosu Tipi:** Manuel
- **UX Testine ihtiyaç var mı?:** Hayır
- **gitBranch:** (boş)

## Yorumlar (eskiden yeniye)

Yorum yok.

## Ekler (içerik XML'de yok; envanterde not_provided)

Ek yok.

## Bağlı kartlar (yalnızca anahtar; envanterde not_accessible)

Bağlı kart yok.

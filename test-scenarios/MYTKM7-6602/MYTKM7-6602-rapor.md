# Kart Yeterlilik Raporu — MYTKM7-6602

**Kart:** Onay Şemasına İş Havuzu İşlemleri İçin Atama Geçmişi Eklenmesi  
**Durum:** kısmi — Kart test edilebilir: dört kabul kriteri sekme görünürlüğünü, sekme sıralamasını, log tablosu gösterimini ve boş veri mesajını tanımlıyor; QA yorumu davranışları test ortamında doğrulamış. Bilgilendirme mesajının birebir metni ('benzeri' diye geçiyor), Small Version tablo formatının kolonları (okunamayan eklerde) ve kullanıcı profili çelişkisi netleştirilmemiş.  
**Test ortamı:** ZB TEST ortamı, İnternet kanalı, şube personeli/Genel Müdürlük kullanıcısı; sürüm 06.11.2026 Kasım Aylık Yaygınlaştırma  
**Üretilen senaryo:** 3 (3 hazır, 0 taslak)

## Açık sorular

| ID | Soru | Bloklayıcı | Muhatap | İlgili |
|---|---|---|---|---|
| Q-01 | Atama geçmişi bulunmayan işlemde gösterilecek bilgilendirme mesajının birebir metni nedir? Kart '"Görüntülenecek atama geçmişi bulunmamaktadır" benzeri bir uyarı mesajı' diyerek metni örnekle açık bırakıyor. | hayır | ürün sahibi | AC-04, R5 |
| Q-02 | Onay işlemini yapan kullanıcının profili nedir? Kullanıcı Hikâyesi 'Şube Personeli/Genel Müdürlük Kullanıcısı' derken 'Kullanıcı Profili' özel alanı 'Anonim' olarak dolu; ikisi çelişiyor. | hayır | iş analisti | BR-01, BR-02, CF-01, R6, R7 |
| Q-03 | 'Small Version' tablo formatının kolonları nelerdir? Kart 'tarih, kullanıcı, işlem tipi vb.' diyor; format detayı paylaşılmayan ekran görüntüsü eklerinde duruyor olabilir. Kolon listesi metin olarak paylaşılabilir mi? | hayır | tasarımcı | AC-03, R4, R10 |

## Yeterlilik kontrolleri

| ID | Kontrol | Sonuç | Bulgu |
|---|---|---|---|
| R1 | Amaç: ne, kimin için, neden | geçti | Şube Personeli/Genel Müdürlük Kullanıcısı, İş Havuzu onaylarında atama süreçlerini ve geçmiş hareketlerini şema üzerinden hızlıca takip etmek için 'Atama Geçmişi' sekmesini istiyor (Kullanıcı Hikayesi). |
| R2 | Test edilecek gereksinim var | geçti | 'Kabul Kriterleri' özel alanında 4 madde: koşullu sekme görünürlüğü, sekme konumlandırması, FLA_WORKITEMACTION loglarının Small Version tabloda listelenmesi, boş veri senaryosu. |
| R3 | Gereksinimler test edilebilir | geçti | Her kriter gözlemlenebilir sonuç tanımlıyor: sekme görüntülenir/görüntülenmez, sıralama, tablo formatında log listesi, bilgilendirme mesajı. |
| R4 | Veri kuralları: zorunlu alan, format, min/max | kısmi | Girdi alanı yok; ancak 'Small Version' tablo formatının kolonları 'tarih, kullanıcı, işlem tipi vb.' diye açık bırakılmış ve format detayı paylaşılmayan tasarım eklerinde (Q-03). |
| R5 | Hata ve olumsuz durumlardaki davranış | kısmi | Sekmenin standart onaylarda görüntülenmemesi ve boş veri mesajı tanımlı; ancak mesaj metni '"Görüntülenecek atama geçmişi bulunmamaktadır" benzeri' diye birebir verilmemiş (Q-01). |
| R6 | Roller, yetkiler, ön koşullar | kısmi | Kullanıcı Hikâyesi 'Şube Personeli/Genel Müdürlük Kullanıcısı' derken 'Kullanıcı Profili' özel alanı 'Anonim' diyor (CF-01, Q-02). |
| R7 | Tutarlılık: alanlar arası çelişki | kısmi | Kullanıcı Hikâyesi ile Kullanıcı Profili özel alanı arasında çözülmemiş profil çelişkisi var (CF-01); ana akışın sonucunu değiştirmez, yalnızca ön koşul profilini etkiler. |
| R8 | Kapsam sınırı: ekran, kanal, bağımlılık | geçti | Kapsam net: Onay Şema Bileşeni içinde yalnızca İş Havuzu tabındaki onay işlemleri; kanal İnternet. Standart onaylarda sekme çıkmaması kapsam sınırını netleştiriyor. |
| R9 | Test ortamı | geçti | Client Environment: Test; QA yorumunda ZB TEST; Erişim Noktası: İnternet; sürüm 06.11.2026 Kasım Aylık Yaygınlaştırma (fixVersion). Geliştirme test ortamına taşınmış (C-03). |
| R10 | Ekler ve bağlantılar işlendi | kısmi | İki ekran görüntüsü eki yalnızca adıyla var (içerik paylaşılmadı), 3 bağlı kart (KDTKM1-3056, MYTKM7-6748, MYTKM7-6650) ve ZTKD-1701 dış bağlantısı erişilemedi. Kurallar kabul kriterleri alanında olduğu için senaryo üretimini bloke etmez; Small Version format detayı eklerdeyse Q-03 ile netleşmelidir. |

## Çelişkiler

| ID | Açıklama | Öğeler | Durum | Çözüm / soru |
|---|---|---|---|---|
| CF-01 | 'Kullanıcı Profili' özel alanı 'Anonim' değerini taşırken Kullanıcı Hikâyesi aktörü 'Şube Personeli/Genel Müdürlük Kullanıcısı' olarak tanımlıyor. Onay işlemleri oturumlu kullanıcı gerektirdiği için 'Anonim' değerinin kart şablonundan kalan varsayılan olduğu düşünülmektedir; ancak bu yorum kartta açık bir karar olarak yer almıyor. | BR-01, BR-02 | çözülmedi | Q-02 |

## Kart envanteri

### Alanlar

| Alan | Durum | Not |
|---|---|---|
| summary | kullanıldı | Özellik adı olarak kullanıldı |
| issue_type | kullanıldı | Story → story |
| description | boş | XML'de <description/> boş; kullanıcı hikâyesi 'Kullanıcı Hikayesi' özel alanında |
| acceptance_criteria | kullanıldı | 'Kabul Kriterleri' özel alanında 4 kriter (sekme görünürlüğü, konumlandırma, tablo yapısı, boş veri) |
| environment | boş | XML'de boş; ortam bilgisi özel alanlardan ve QA yorumundan alındı |
| priority | kullanıldı | Low → risk etki puanına girdi |
| labels | boş | XML'de boş |
| components | sağlanmadı | XML'de yok |
| affects_versions | ilgisiz | Story kartı |
| fix_versions | kullanıldı | 06.11.2026 Kasım Aylık Yaygınlaştırma → test ortamı sürümü |
| reporter | kullanıldı | Asiye Nur ARSLAN (Yazılım Araçları) |
| assignee | kullanıldı | Asiye Nur ARSLAN (Yazılım Araçları); geliştirici |
| subtasks | boş | XML'de boş |
| custom_fields | kullanıldı | Kullanıcı Hikayesi, Kabul Kriterleri, Erişim Noktası, Kullanıcı Profili, Client Environment, Epic Link, Test Senaryosu Tipi |

### Ekler

| Ek | Tür | Durum | Çıkarılan bilgi | Öğeler |
|---|---|---|---|---|
| image-2026-10-22-16-07-07-246.png | image | sağlanmadı | XML'de yalnızca ek adı var; içerik paylaşılmadı. QA yorumunda (C-04) kullanıcıya atanmış işlemin Atama Geçmişi sekmesi ekran görüntüsü olarak gömülü atfı var. |  |
| image-2026-10-22-16-24-57-789.png | image | sağlanmadı | XML'de yalnızca ek adı var; içerik paylaşılmadı. QA yorumunda (C-04) havuzda hiç aksiyon alınmamış işlemin ekran görüntüsü olarak gömülü atfı var. |  |

### Yorumlar

| ID | Yazar | Tarih | Rol | Durum | Özet | Öğeler |
|---|---|---|---|---|---|---|
| C-01 | JIRAUSER24340 | 2026-10-08 | test uzmanı | kullanıldı | Konuyla ilgili UX'e ZTKD-1701 biletinin açıldığı bildiriliyor; dış bağlantı olarak kaydedildi, açılmadı. |  |
| C-02 | JIRAUSER24340 | 2026-10-19 | test uzmanı | kullanıldı | Sekme içeriğinin UX dönüşüne göre tablo olarak ekleneceği belirtiliyor; AC-03'teki tablo gösterimini destekler (CN-01). | CN-01 |
| C-03 | skarakas | 2026-10-21 | geliştirici | kullanıldı | Geliştirmenin test ortamına taşındığı, taşınacak nesnenin APRTINBX[FED] olduğu ve testlerden sonra Dinamik ortam taşıması yapılacağı bildiriliyor (CN-02). | CN-02 |
| C-04 | JIRAUSER24340 | 2026-10-22 | test uzmanı | kullanıldı | QA doğrulaması (Kullanıcı:SOZMEN, Ortam:ZB TEST): İş Havuzu onaylarında sekmenin 'Onay Akışı' ve 'Mesajlaşma' arasında geldiği, standart onaylarda gelmediği teyit edildi. Kullanıcıya atanmış işlem için FLA_WORKITEMACTION sorgusu ve iki ekran görüntüsü; havuzda hiç aksiyon alınmamış işlem örneği (Kullanıcı: DOGOZKAN) var. Bu bulgular AC-01 ve AC-04 davranışlarını doğrulayan test kanıtıdır; yeni kural içermez. |  |

### Bağlı kartlar ve dış bağlantılar

| Kaynak | Tür | Durum | Not |
|---|---|---|---|
| KDTKM1-3056 | relates to | erişilemedi | XML'de yalnızca anahtar var; açıklama yok. |
| MYTKM7-6748 | tested by | erişilemedi | XML'de yalnızca anahtar var; kart bir test kartı tarafından test ediliyor (Tests bağlantısı) |
| MYTKM7-6650 | epic | erişilemedi | Epic Link özel alanı; XML'de yalnızca anahtar var |
| ZTKD-1701 | dış bağlantı | erişilemedi | C-01 yorumunda UX tasarım biletinin Jira adresi anılıyor; açılmadı. |

## Uçtan uca akışlar

| Akış | Tür | Başlangıçtan sonuca | Senaryo |
|---|---|---|---|
| UC-ANA | ana akış | Onay sistemine şube personeli girişi → İş Havuzu sekmesinden atama aksiyonu alınmış onay bekleyen işlemi açma → Onay Akışı ile Mesajlaşma arasında Atama Geçmişi sekmesi görüntülenir → sekmede işleme ait atama logları Small Version tablo formatında listelenir | TS-MYTKM7-6602-001 |
| UC-HATA-SEKMEYOK | hata akışı | Ana akış; İş Havuzu dışındaki standart onay işlemi açılır → Atama Geçmişi sekmesi görüntülenmez | TS-MYTKM7-6602-002 |
| UC-HATA-BOSS | hata akışı | Ana akış; İş Havuzu sekmesinden hiç aksiyon alınmamış onay bekleyen işlemi açma → Atama Geçmişi sekmesi görüntülenir → sekmede bilgilendirme mesajı gelir, log tablosu yok | TS-MYTKM7-6602-003 |

## Kapsam

| Öğe | Senaryolar | Durum | Not |
|---|---|---|---|
| AC-01 | TS-MYTKM7-6602-001, TS-MYTKM7-6602-002 | kapsandı | Hem görünürlük (İş Havuzu) hem görünmezlik (standart onay) tarafı test ediliyor. |
| AC-02 | TS-MYTKM7-6602-001 | kapsandı |  |
| AC-03 | TS-MYTKM7-6602-001 | kısmen | Tablo gösterimi test ediliyor; Small Version kolon seti Q-03 yanıtıyla netleşmeli. |
| AC-04 | TS-MYTKM7-6602-003 | kısmen | Boş veri davranışı test ediliyor; mesajın birebir metni Q-01 yanıtı bekliyor. |
| BR-01 | TS-MYTKM7-6602-001 | kapsandı | Kullanıcı Hikâyesi aktörü ve sekme ihtiyacı ana akışta karşılanıyor. |
| BR-02 | — | kapsanmadı | 'Kullanıcı Profili: Anonim' değeri Kullanıcı Hikâyesi ile çelişiyor (CF-01, Q-02); profil davranışı çelişki çözülene kadar test edilemez. |

## Kapsam dışı

- Geliştirmenin Dinamik ortamına taşınması ve taşınacak nesneler (APRTINBX[FED]): Geliştirici yorumundaki (C-03) teslim/dağıtım işlemi; manuel fonksiyonel senaryo kapsamı dışında, ortam hazır bilgisidir.
- UX tasarım çalışması (ZTKD-1701 biletinin kapsamı): UX tasarımı ayrı bilette yönetiliyor; bu kart yalnızca tasarlanan sekmenin davranışını test eder.

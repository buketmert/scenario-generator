# Kart Analizi Kuralları

Senaryoların kalitesi, kartın içerdiği bilginin kalitesiyle sınırlıdır. Bu
dosya, Jira kartının **tüm alanlarının ve eklerinin** nasıl okunacağını, her
bilginin nasıl kaynağıyla kaydedileceğini, alanlar çeliştiğinde ne yapılacağını
ve kartın senaryo üretmeye yeterli olup olmadığına nasıl karar verileceğini
tanımlar. `SKILL.md` iş akışının 1. ve 2. adımlarında kullanılır.

## 1. Temel ilke

- Kartın her alanı **test esasıdır** (test basis). Yalnızca açıklama ve kabul
  kriterleri değil; ekler, ortam, yorumlar, bağlı kartlar ve özel alanlar da
  okunur.
- Okunan her alan ve ek `card_inventory` içine kaydedilir; boş, sağlanmamış
  veya okunamayan alanlar da kaydedilir. Böylece "neye bakıldı, neye
  bakılamadı" her çıktıda görünür.
- Senaryoda kullanılan her kural, değer, alan adı ve mesaj metni bir kaynağa
  dayanır (`source`). Kaynağı olmayan bilgi senaryoya girmez.

## 2. Alanlar ve senaryoya katkıları

| Alan | Ne aranır | Senaryoya katkısı |
|---|---|---|
| Summary | Kapsamın kısa adı | `feature.name` (Özellik adı) |
| Issue type | story, task, bug, sub-task | Akış seçimi: bug → doğrulama + regresyon |
| Description | Kullanıcı hikâyesi, iş kuralları, akış adımları, tablolar, ekran yolu, kapsam dışı notları, eklere ve dış dokümanlara yapılan atıflar | İş kuralları (`BR`), ön koşullar, navigasyon |
| Acceptance criteria | Ayrı alan veya açıklama içindeki kriter listesi | Kabul kriterleri (`AC`) |
| Environment | Ortam (TEST, PREPROD), kanal (web, mobil, şube), sürüm/build, cihaz, işletim sistemi, tarayıcı, test kullanıcı tipi | `test_environment`; ortama özgü ön koşullar |
| Comments | Netleştirmeler, kararlar, kapsam değişiklikleri, teknik kısıtlar, test notları | Yeni veya güncellenmiş kurallar (`BR`), kısıtlar (`CN`), kapsam dışı, sorular |
| Attachments | Ekran tasarımı, doküman, tablo, log, video (bkz. §4) | Alan adları ve mesajlar (`UI`), kurallar ve değer tabloları (`BR`) |
| Linked issues | Epic, blocks / is blocked by, relates, duplicates, cloned | Bağlam, bağımlılıklar (ön koşul veya kapsam dışı), regresyon alanı |
| Sub-tasks | İşin parçaları | Kapsamın tamamlığı |
| Labels, Components | Modül ve alan bilgisi | `feature.tags`, regresyon alanı |
| Priority | İş önceliği | Risk değerlendirmesinde etki puanına girdi |
| Affects / Fix version | Hatanın görüldüğü ve düzeltildiği sürüm | `test_environment` (sürüm) |
| Reporter, Assignee | Kartı kimin açtığı, kimin geliştirdiği | Yorum yazarlarının rolünü belirleme |
| Custom fields | Kurumda tanımlı alanlar ("Test Notları", "Etkilenen Kanallar" gibi) | İçeriğine göre `BR`, `CN` veya `test_environment` |

## 3. İşleme sırası

1. **Metin alanları:** summary, açıklama, kabul kriterleri, ortam, sürümler,
   özel alanlar.
2. **Ekler:** her ek tek tek açılır (§4).
3. **Yorumlar:** eskiden yeniye okunur. Her yoruma `C-01`, `C-02`… kimliği
   verilir; yazar, tarih ve rol kaydedilir.
4. **Bağlı kartlar ve alt görevler:** erişilebiliyorsa özet ve kabul
   kriterleri okunur.
5. **Çapraz kontrol:** aynı konu için farklı alanlardaki bilgiler
   karşılaştırılır; çelişkiler `conflicts` içine yazılır (§6).

## 4. Ekler

| Ek türü | Ne çıkarılır |
|---|---|
| Ekran görüntüsü / tasarım (png, jpg, tasarım çıktısı) | Alan adları ve sırası, buton metinleri, zorunlu alan işaretleri, varsayılan değerler, hata ve bilgi mesajlarının birebir metni |
| Doküman (pdf, docx) | İş kuralları, akışlar, değer tabloları, istisnalar |
| Tablo (xlsx, csv) | Limitler, değer listeleri, kural kombinasyonları. Doğrudan denklik sınıfı veya karar tablosu girdisidir |
| Log, HAR, hata çıktısı | Hata mesajı, hata kodu, hatanın oluştuğu adım, ortam (bug kartları) |
| Video | Akış ve yeniden üretme adımları. İşlenemiyorsa `not_readable` |

Kurallar:

1. Her ek `card_inventory.attachments` içine yazılır: ad, tür, durum
   (`processed`, `not_readable`, `not_relevant`, `not_provided`), çıkarılan
   bilginin özeti ve üretilen test esası öğeleri (`basis_ids`).
2. Görsellerden metin **birebir** alınır. Okunması belirsiz metin tahmin
   edilmez; soru yazılır.
3. Okunamayan veya sağlanmayan ek R10'u `pass` olmaktan çıkarır. Kurallar
   yalnızca o ekte duruyorsa (açıklama "ekteki dokümana bakınız" diyorsa) R10
   `fail` olur.
4. Açıklamadaki dış bağlantılar (Confluence, tasarım aracı) da
   `card_inventory.external_links` içine yazılır. Erişilemeyen bağlantı ekle
   aynı şekilde değerlendirilir.
5. Eklerdeki örnek veriler gerçek müşteri verisi içerebilir; test verisine
   kopyalanmaz, sentetik karşılığı üretilir.

## 5. Kaynak gösterme

Her test esası öğesi (`test_basis.items`) bir `source` taşır:

| `source.field` | `source.ref` |
|---|---|
| `acceptance_criteria`, `description`, `environment`, `summary`, `priority`, `labels`, `components`, `fix_versions`, `affects_versions`, `reporter` | Gerekmez |
| `attachment` | Ek adı (`eft-limitleri.xlsx`). Gerekirse sayfa veya bölge eklenir |
| `comment` | Yorum kimliği (`C-02`) |
| `linked_issue`, `subtask` | Kart anahtarı (`ESUBE-1980`) |
| `custom_field` | Alan adı (`Test Notları`) |

Test esası öğe türleri:

| Tür | ID | Ne içerir | Kapsanması zorunlu mu |
|---|---|---|---|
| `acceptance_criterion` | `AC-NN` | Kabul kriteri | Evet |
| `business_rule` | `BR-NN` | Açıklama, yorum veya ekten gelen iş kuralı | Evet |
| `ui_detail` | `UI-NN` | Tasarımdan gelen alan adı, mesaj metni, varsayılan değer | Hayır, senaryolarda başvuru kaynağıdır |
| `constraint` | `CN-NN` | Teknik kısıt (geliştirici yorumu, alan uzunluğu) | Hayır, beklenen sonucu etkiliyorsa çelişki kontrolüne girer |

Metin, kaynaktaki haliyle ve değiştirilmeden yazılır.

## 6. Öncelik ve çelişki kuralları

Aynı konuda alanlar farklı şey söylüyorsa şu sırayla karar verilir:

1. **Ürün sahibi veya analistin açık kararı en güçlüdür.** Daha yeni tarihli
   bir yorumda açıkça verilmiş karar, açıklamayı ve kabul kriterlerini
   günceller. Yeni kural `business_rule` olarak yazılır, `updates` alanında
   güncellediği öğeyi gösterir ve çelişki `resolved_by_later_decision` olarak
   kapatılır.
2. **Kabul kriterleri alanı, açıklamadaki genel ifadeden önce gelir.**
3. **Geliştirici yorumu teknik bilgi verir ama iş kuralını tek başına
   değiştirmez.** Gözlenecek davranışı değiştiriyorsa (örneğin alanın fazla
   karakter kabul etmemesi, kriterdeki hata mesajını imkânsız kılıyorsa)
   çelişki `unresolved` kalır ve soru yazılır.
4. **Ek ile metin çelişirse agent seçim yapmaz.** Daha yeni bir karar yoksa
   çelişki `unresolved` kalır ve soru yazılır.
5. **Rolü belirlenemeyen yazar:** yorum kural değiştiriyorsa onay sorusu
   yazılır; kural, onaylanana kadar varsayım olarak kalır.

Her çelişki `conflicts` içine yazılır: ilgili öğeler, açıklama, çözüm durumu,
çözüldüyse çözen öğe, çözülmediyse soru. **Çelişki hiçbir zaman sessizce
çözülmez.** Çözülmemiş bir çelişki yalnızca etkilediği kapsam öğelerini bloke
eder; diğer senaryolar üretilmeye devam eder.

## 7. Yeterlilik kontrolleri (R1–R10)

| ID | Kontrol | Bakılan alanlar | `partial` | `fail` |
|---|---|---|---|---|
| R1 | Amaç: ne, kimin için, neden | Summary, açıklama | Amaç var, fayda veya kullanıcı belirsiz | Yalnızca başlık var |
| R2 | Test edilecek gereksinim var | Kabul kriterleri, açıklama, yorumlar, ekler | Gereksinimler var ama dağınık veya eksik | Hiçbir alanda test edilecek kural yok |
| R3 | Gereksinimler test edilebilir | Tüm gereksinim öğeleri | Bir kısmı ölçülemez ("hızlı", "uygun") | Hiçbiri ölçülemez |
| R4 | Veri kuralları: zorunlu alan, format, min/max | Kabul kriterleri, ekler (tablo, tasarım) | Bazı alanların kuralı yok | Girdi alanları var, hiçbirinin kuralı yok |
| R5 | Hata ve olumsuz durumlardaki davranış | Kabul kriterleri, tasarımdaki hata durumları | Bazı hata durumları tanımsız | Hiçbir hata davranışı tanımlı değil |
| R6 | Roller, yetkiler, ön koşullar | Açıklama, yorumlar, ortam | Kısmen belli | İşlemi kimin yapacağı belli değil |
| R7 | Tutarlılık: alanlar arası çelişki | Tüm alanlar | Çözülmemiş çelişki ayrıntıyla sınırlı | Ana akışın sonucunu değiştiren çözülmemiş çelişki |
| R8 | Kapsam sınırı: ekran, kanal, bağımlılık | Açıklama, bileşenler, bağlı kartlar | Kısmen belli | Hangi ekran veya kanal olduğu anlaşılmıyor |
| R9 | Test ortamı | Environment, sürümler, özel alanlar | Ortam veya sürümden biri eksik (story) | Bug kartında ortam ve sürüm yok |
| R10 | Ekler ve bağlantılar işlendi | Ekler, dış bağlantılar, bağlı kartlar | Bazı ekler okunamadı veya sağlanmadı | Kurallar yalnızca okunamayan ekte veya erişilemeyen dokümanda |

Tutarlılık kuralları (script denetler):

- `conflicts` içinde `unresolved` bir çelişki varsa R7 `pass` olamaz.
- `not_readable`, `not_provided` veya `not_accessible` durumunda bir ek,
  bağlantı veya bağlı kart varsa R10 `pass` olamaz.
- `test_environment.details` boşsa R9 `pass` olamaz.

## 8. Bug kartları

Bug kartlarında şu bilgiler ayrıca aranır; eksikse ilgili kontrol düşer:

- Yeniden üretme adımları (açıklama, video, log) → yoksa R2 `fail`
- Gerçekleşen ve beklenen davranış → yoksa R3 `fail`
- Ortam ve etkilenen sürüm → yoksa R9 `fail`
- Hata mesajı veya kodu (ekran görüntüsü, log) → doğrulama testinin beklenen
  sonucunda kullanılır

## 9. Pipeline'dan beklenen girdi

Agent, kartın tüm alanlarını, yorumlarını, eklerinin içeriğini ve bağlı
kartların özetini almalıdır. Pipeline yalnızca metin alanlarını iletiyorsa
eksik kalan alanlar `card_inventory` içinde `not_provided` olarak işaretlenir ve
R10 `partial` olur. Bu durum yeterlilik raporunda görünür; agent eksik bilgiyi
tahminle doldurmaz.

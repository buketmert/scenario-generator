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
2. **Ekler:** her ek tek tek kaydedilir (§4). XML yalnızca ek adını taşır;
   içerik yalnızca kullanıcı dosyayı açıkça eklediyse okunur (§9).
3. **Yorumlar:** eskiden yeniye okunur. Her yoruma `C-01`, `C-02`… kimliği
   verilir; yazar, tarih ve rol kaydedilir.
4. **Bağlı kartlar ve alt görevler:** XML'de yalnızca anahtarları vardır;
   `not_accessible` olarak kaydedilir. Kullanıcı bağlı kartın XML'ini de
   paylaştıysa özeti ve kabul kriterleri okunur ve `used` olur.
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
   `card_inventory.external_links` içine yazılır. Bağlantılar açılmaz;
   `not_accessible` olarak kaydedilir ve okunamayan ekle aynı şekilde
   değerlendirilir.
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

## 9. Girdi: Jira XML dışa aktarımı

Kart, kullanıcının Jira'dan aldığı XML dışa aktarımıyla (kart → Dışa aktar →
XML) gelir. Jira'ya bağlanılmaz, oturum açılmaz, ek indirilmez; XML'deki
`<link>` ve diğer adresler açılmaz. Kart verisinin tek kaynağı XML ve
kullanıcının isteğe açıkça eklediği dosyalardır.

### 9.1 Öğe eşlemesi

Her kart, `<rss><channel>` altındaki bir `<item>` öğesidir. Birden fazla
`<item>` varsa her biri ayrı karttır.

| XML öğesi | Alan | Not |
|---|---|---|
| `<key>` | `source.jira_key` | |
| `<summary>` | `summary` | `<title>` içindeki `[KEY]` ön eki kullanılmaz |
| `<link>` | `source.url` | Yalnızca kaydedilir, açılmaz |
| `<type>` | `issue_type` | Story / Hikâye → `story`, Task / Görev → `task`, Bug / Hata → `bug`, Sub-task / Alt Görev → `sub_task`, Epic → `epic`, diğerleri → `other` |
| `<description>` | `description` | HTML olarak kaçışlıdır; bkz. §9.2 |
| `<environment>` | `environment` | Boşsa `empty` |
| `<priority>` | `priority`, `source.jira_priority` | |
| `<labels><label>` | `labels` | |
| `<component>` (tekrarlanabilir) | `components` | |
| `<version>` | `affects_versions` | Etkilenen sürüm |
| `<fixVersion>` | `fix_versions` | |
| `<reporter>`, `<assignee>` | `reporter`, `assignee` | Öğe metni görünen addır |
| `<customfields><customfield>` | `custom_fields` | Adı `<customfieldname>`, değeri `<customfieldvalues><customfieldvalue>`. "Acceptance Criteria" / "Kabul Kriterleri" adlı özel alan `acceptance_criteria` alanıdır |
| `<comments><comment>` | Yorumlar | `author` özniteliği yazar, `created` özniteliği tarih; metin HTML olarak kaçışlıdır |
| `<attachments><attachment>` | Ekler | Yalnızca `name`, `size`, `author`, `created` öznitelikleri vardır; içerik yoktur |
| `<issuelinks>` | `linked_issues` | `<issuelinktype><name>` ve `<outwardlinks>` / `<inwardlinks>` `description` özniteliği bağlantı türüdür; `<issuekey>` anahtardır |
| `<parent>`, "Epic Link" özel alanı | `linked_issues` | Bağlantı türü `parent` veya `epic` |
| `<subtasks><subtask>` | `subtasks`, `linked_issues` | Yalnızca anahtar vardır. `subtasks` alanı `used` olur ve `note` anahtarları listeler; her alt görev ayrıca bağlantı türü `subtask` ile `linked_issues` içine yazılır |
| `<status>`, `<resolution>`, `<created>`, `<updated>`, `<votes>`, `<watches>` | — | Test esası değildir; kullanılmaz |

Kabul kriterleri ayrı bir özel alanda değilse açıklamanın içinde aranır
("Kabul Kriterleri", "Acceptance Criteria" başlığı veya listesi). İkisinde de
yoksa `acceptance_criteria` alanı `not_provided` olur.

### 9.2 İçeriğin okunması

- `<description>`, yorum ve metin özel alanlarının içeriği HTML'dir ve XML
  içinde kaçışlıdır (`&lt;p&gt;`) ya da `<![CDATA[...]]>` içindedir. Önce
  varlıkları çöz (`&lt;` → `<`, `&quot;` → `"`, `&#39;` → `'`), sonra HTML'i
  yapısıyla oku: `<li>` liste maddesi, `<table>` tablo, `<b>` / `<strong>`
  başlık veya vurgu.
- Test esası öğesine metin yazarken HTML etiketlerini kaldır; metnin kendisini
  değiştirme. Mesaj metinleri ve alan adları birebir kalır.
- Açıklamadaki `<img>` veya `!dosya.png!` gibi gömülü görseller bir eke işaret
  eder; o ek görsel içerik olmadan okunamaz.
- Yorum tarihleri `Tue, 21 Oct 2026 09:12:00 +0300` biçimindedir; envantere
  `2026-10-21` olarak yazılır.
- Yorumun `author` özniteliği kullanıcı adı veya hesap kimliği olabilir; rolü
  yorumun içeriğinden ya da raporlayan / atanan eşleşmesinden belirlenemiyorsa
  `unknown` olur.

### 9.3 XML'de olmayan bilgi

| Kaynak | Envanterdeki durum | `summary` / `note` |
|---|---|---|
| Ek (kullanıcı dosyayı eklemediyse) | `not_provided` | XML'de yalnızca ek adı var; içerik paylaşılmadı |
| Ek (kullanıcı ekledi, okunamadı) | `not_readable` | Okunamama nedeni |
| Bağlı kart, alt görev (`linked_issues`) | `not_accessible` | Bağlantı türü; XML'de yalnızca anahtar var. Kullanıcı o kartın XML'ini de paylaştıysa `used` |
| Açıklamadaki dış bağlantı | `not_accessible` | Bağlantı açılmadı |
| XML'de hiç bulunmayan alan | `not_provided` | |

Bu kayıtların her biri R10'u `pass` olmaktan çıkarır (§7). Kurallar
yalnızca içeriği paylaşılmamış bir ekte veya bağlı kartta duruyorsa R10
`fail` olur ve kart `not_ready` olur. Bu durumda yazılan soru, ekin veya
bağlı kartın içeriğinin metin ya da dosya olarak paylaşılmasını ister. Eksik
bilgi tahminle doldurulmaz.

---
name: scenario-generator
description: Jira kartının (story, task, cross-functional, bug) kullanıcının paylaştığı XML dışa aktarımından uçtan uca manuel test senaryoları üretir ve Türkçe Gherkin ile yazar. Önce karttaki iş akışlarını (ana, alternatif, hata) çıkarır, her akış için girişten sonuca bir senaryo yazar; sınır değer, denklik sınıfı gibi ISTQB teknikleri akışların veri satırlarını üretir. Jira'ya bağlanmaz, ek indirmez. Kartın yeterliliğini değerlendirir, eksik ve çelişkili bilgiler için soru üretir. Çıktı references/output-schema.json formatında tek bir JSON'dur; .feature dosyası, kart yeterlilik raporu ve seçim listesi scripts/render_gherkin.py ile oluşturulur; kullanıcının işaretlediği senaryolar scripts/jira_export.py ile karta bağlanacak Test Senaryosu kartlarına (Jira CSV) dönüştürülür. Jira XML'i, kart içeriği veya kullanıcı hikâyesi verilip test senaryosu, test case, test durumu ya da Gherkin/feature istendiğinde kullan.
---

# Scenario Generator

Jira kartını **test esası** (test basis) kabul eder ve ISTQB test sürecinin
analiz → tasarım → uygulama adımlarını izleyerek **uçtan uca manuel test
senaryoları** üretir. Senaryonun nasıl kurulduğu
`references/scenario-construction.md`'dedir.

## Uçtan uca süreç

Kullanıcı "test senaryosu oluştur" deyip kartın XML'ini verdiğinde Adım 1–8
arada onay istenmeden uygulanır; Adım 9'da kullanıcıya hangi senaryoların
Test Senaryosu kartına dönüştürüleceği sorulur ve seçilenlerden Jira dosyası
üretilir.

```text
XML → kart envanteri ve yeterlilik → test esası ve koşullar → akışlar (UC)
    → teknikler (veri satırları) → her akış için uçtan uca senaryo → JSON
    → .feature + rapor + seçim listesi → kullanıcı seçer → Test Senaryosu kartları (CSV)
```

Süreç yalnızca üç yerde durur: XML verilmediyse (XML istenir), kart
`not_ready` ise (rapor ve sorular verilir, senaryo yazılmaz) ve Adım 9'daki
seçim sorusunda.

- **Girdi:** kullanıcının paylaştığı Jira XML dışa aktarımı (kart → Dışa
  aktar → XML). Alanlar, yorumlar, ek listesi ve bağlı kart anahtarları
  buradan okunur. Jira'ya bağlanılmaz, ekler indirilmez; XML'de olmayan bilgi
  `not_provided` olarak kaydedilir (`card-analysis-rules.md` §9).
- **Agent'ın çıktısı:** tek bir JSON belgesi. Kart envanteri, yeterlilik,
  test esası, çelişkiler, akışlar, senaryolar ve kapsam burada tutulur.
  Senaryo adımları Türkçe Gherkin cümleleridir.
- **Script'in çıktıları:** `.feature` dosyası (test uzmanı için), kart
  yeterlilik raporu (ürün sahibi / analist için) ve seçim listesi.
  Kullanıcının işaretlediği senaryolar `jira_export.py` ile Jira CSV'sine
  yazılır; her biri kaynak karta bağlantıyla bağlanacak bir **Test Senaryosu**
  kartıdır.

Adım kalıpları için şu an kurumsal bir standart yoktur; Gherkin cümleleri
serbesttir ve `gherkin-format-rules.md`'deki okunabilirlik kurallarına uyar.

## Dosyalar

| Dosya | Ne zaman okunur |
|---|---|
| `references/card-analysis-rules.md` | Adım 1–2'de: hangi alanın nasıl okunacağı, XML eşlemesi (§9), ekler, kaynak gösterme, çelişki kuralları, R1–R10 |
| `references/scenario-construction.md` | Adım 4–5'te: **test senaryosu nasıl oluşturulur** — akışları çıkarma, teknikleri akışlara bağlama, uçtan uca senaryoyu yazma |
| `references/test-design-rules.md` | Adım 3–5'te: risk, test derinliği, teknik seçimi, teknikler, senaryo yazım kuralları |
| `references/gherkin-format-rules.md` | Adım 5'te: Gherkin anahtar kelimeleri, cümle yazımı, Örnekler, Geçmiş |
| `references/output-schema.json` | Adım 6–8'de: çıktının tek geçerli formatı |
| `scripts/render_gherkin.py` | Adım 8'de: JSON'u doğrular, `.feature`, yeterlilik raporu ve seçim listesi üretir |
| `scripts/jira_export.py` | Adım 9'da: seçim listesinde işaretli senaryolardan Jira CSV'si üretir |
| `examples/sample-output.json` | Biçim ve ayrıntı düzeyi örneği. İçeriği kopyalanmaz. Örnekte üç ek kullanıcı tarafından dosya olarak (video okunamamıştır), epic de ayrı bir XML olarak paylaşılmıştır; paylaşılmayan ek ve bağlı kart `not_provided` / `not_accessible` olur |
| `examples/sample-output.feature`, `examples/sample-report.md`, `examples/sample-secim.md`, `examples/sample-jira.csv` | Örnek JSON'dan script'lerle üretilmiş çıktılar (seçim listesi varsayılan işaretlerle) |

## İş akışı

### Adım 1: Kart verilerini topla

`card-analysis-rules.md` §2–§5'e göre kartın tüm alanlarını oku ve
`card_inventory` alanını doldur. XML öğelerinin hangi alana karşılık geldiği
§9'dadır.

1. Metin alanları: summary, issue type, açıklama, kabul kriterleri,
   environment, öncelik, etiketler, bileşenler, sürümler, raporlayan, özel
   alanlar. Boş veya XML'de bulunmayan alanları da kaydet.
2. Ekler: XML'deki her eki `not_provided` olarak kaydet. Yalnızca kullanıcının
   isteğe açıkça eklediği ek dosyalarını oku; okuduğunu `processed`,
   okuyamadığını `not_readable` yap. Ek indirmeye çalışma.
3. Yorumlar: eskiden yeniye oku; her yoruma `C-NN` kimliği, yazar, tarih ve
   rol ver.
4. Bağlı kartlar ve alt görevler: XML'de yalnızca anahtarları vardır;
   `not_accessible` olarak kaydet. Açıklamadaki dış bağlantıları açma;
   `not_accessible` olarak kaydet.
5. `test_environment`: ortam, kanal, sürüm, cihaz/tarayıcı ve kullanıcı tipini
   kaynağıyla yaz.

### Adım 2: Yeterlilik ve çelişki kontrolü (statik test)

1. Aynı konudaki bilgileri alanlar arasında karşılaştır. Her çelişkiyi
   `conflicts` içine yaz ve `card-analysis-rules.md` §6'daki öncelik
   kurallarıyla değerlendir. Çözülemeyen çelişki için soru yaz.
2. On kontrolün her birini `pass`, `partial` veya `fail` olarak değerlendir
   (`card-analysis-rules.md` §7) ve bulguyu `readiness.checks` içine yaz.

| ID | Kontrol |
|---|---|
| R1 | Amaç: ne, kimin için, neden |
| R2 | Test edilecek gereksinim var |
| R3 | Gereksinimler test edilebilir |
| R4 | Veri kuralları |
| R5 | Hata ve olumsuz durumlardaki davranış |
| R6 | Roller, yetkiler, ön koşullar |
| R7 | Alanlar arası tutarlılık |
| R8 | Kapsam sınırı |
| R9 | Test ortamı |
| R10 | Ekler ve bağlantılar işlendi |

**Karar kuralı**

| Durum | Koşul | Davranış |
|---|---|---|
| `not_ready` | R2, R3, R7 veya R10 `fail` | Senaryo üretme. `test_scenarios` boş, `clarification_questions` dolu döner. Akış Adım 7'ye atlar. |
| `partial` | `not_ready` değil, en az bir kontrol `partial` veya `fail` | Test edilebilir kısımlar için senaryo üret, eksikler için soru yaz. |
| `ready` | On kontrolün tamamı `pass` | Tam akış. |

Her eksik için, ürün sahibi veya analistin doğrudan yanıtlayabileceği
somutlukta bir soru yaz. Yanıt gelmeden bir kapsam öğesi test edilemiyorsa
soru `blocking: true` olur.

### Adım 3: Test analizi

1. Tüm alanlardan test esası öğelerini çıkar ve `test_basis.items` içine
   kaynağıyla yaz: kabul kriterleri (`AC`), iş kuralları (`BR`), tasarım
   ayrıntıları (`UI`), teknik kısıtlar (`CN`). Metin değiştirilmez.
2. `AC` ve `BR` öğelerini test edilebilirlik açısından işaretle: `testable`,
   `partially_testable`, `not_testable`. İlk değer dışındakiler `issue` ister.
3. Test koşullarını çıkar (`COND-01`…): neyin test edileceği. Bir koşul birden
   fazla öğeye dayanabilir.
4. Her koşul için risk: olasılık (1–3) × etki (1–3). Jira önceliği etki
   puanına girdidir. Seviye eşlemesi `test-design-rules.md` §3'te.

### Adım 4: Test tasarımı — akışlar ve kapsam öğeleri

1. **Akışları çıkar** (`scenario-construction.md` §2): kartın ana akışı,
   kartta tanımlı alternatif akışlar ve kartta tanımlı her red veya uyarı
   davranışı için bir hata akışı. Her akış bir `UC` kapsam öğesidir
   (`technique: use_case_based`, `flow_type`: `main`, `alternative` veya
   `exception`); `description` akışı "Giriş → … → Sonuç" biçiminde özetler.
   Sonucu kartta tanımlı olmayan akış için soru yazılır.
2. Her koşula `test-design-rules.md` §2'ye göre teknik ata. Her koşulda en az
   bir teknik; her kartta hata tahmini.
3. Risk seviyesine göre derinliği `test-design-rules.md` §3'teki tablodan al.
4. Kapsam öğelerini çıkar: denklik sınıfları, sınır değerler, karar tablosu
   kuralları, durum geçişleri, hata tahminleri.
5. **Kapsam öğelerini akışlara yerleştir** (`scenario-construction.md` §3):
   geçerli değerler ana veya alternatif akışın, geçersiz değerler
   tetikledikleri hata akışının veri satırı olur. Hedef: her kapsam öğesi bir
   senaryoda; kapsanamayan öğe gerekçesiyle `uncovered_items` içine yazılır.

**Senaryo sayısı akış sayısıdır.** Kategori kotası veya dağılım hedefi
uygulanmaz; koşum sayısı veri satırlarından ve risk derinliğinden çıkar.

### Adım 5: Her akış için uçtan uca senaryo yaz

`scenario-construction.md` §4, `gherkin-format-rules.md` ve
`test-design-rules.md` §5'e göre:

- `feature` alanına Özellik adını, etiketleri ve tüm senaryolarda ortak ön
  koşulları (`background`: giriş, ekrana gitme) yaz.
- Her akış için bir senaryo yaz. Geçmiş ve senaryo adımları birlikte
  kullanıcının giriş noktasından başlar ve akışın sonucunda biter. Senaryo,
  `coverage_item_ids` içinde tam bir `UC` öğesine bağlıdır.
- Adımları test uzmanının tek başına uygulayabileceği somutlukta yaz: ön
  koşullar (`Diyelim ki`), sıradaki her kullanıcı eylemi (`Eğer ki` / `Ve`),
  kartta tanımlı ara ve son doğrulamalar (`O zaman`).
- Başarı akışında sonucu ve kartta tanımlı sonraki etkileri, hata akışında
  hata mesajını ve işlemin gerçekleşmediğini doğrula.
- Ekran ve alan adlarını kartta geçtiği gibi, beklenen mesajları tırnak
  içinde ve kaynaktaki haliyle yaz.
- Akışın değişen değerlerini `<parametre>` ile yaz ve veri satırlarına koy.
- Akış kalıcı bir değişiklik bırakıyorsa (para hareketi, kayıt, durum
  değişikliği) `postconditions` alanına bıraktığı durumu ve temizliği yaz
  (`test-design-rules.md` §5 madde 13).
- Duman testini `test-design-rules.md` §3'teki sorularla seç ve `@smoke`
  etiketiyle işaretle; çoğunlukla ana akıştır.

### Adım 6: Kapsam özeti

`coverage_summary` alanını doldur: her `AC` ve `BR` öğesinin hangi
senaryolarla kapsandığı, teknik bazında kapsam yüzdesi (akışlar
`use_case_based` satırındadır), kapsanamayan öğeler ve senaryo sayıları.

### Adım 7: Öz denetim

Çıktıyı vermeden önce her maddeyi kontrol et:

- [ ] Kartın tüm alanları, ekleri, yorumları ve bağlantıları `card_inventory` içinde
- [ ] Her test esası öğesinin kaynağı var; ek ve yorum kaynakları envanterde tanımlı
- [ ] Her çelişki kayıtlı; çözülmemiş olanların sorusu var
- [ ] R7, R9, R10 sonuçları envanter ve çelişkilerle tutarlı
- [ ] JSON, `output-schema.json` ile geçerli
- [ ] Kartın bir ana akışı ve kartta tanımlı her red/uyarı davranışı için bir hata akışı (`UC`) var
- [ ] Her senaryo tam bir `UC` akışına bağlı; aynı akış iki senaryoda değil
- [ ] Her senaryo (Geçmiş dâhil) giriş noktasından başlıyor ve akışın sonucunda bitiyor
- [ ] Her senaryo en az bir test esası öğesine ve bir test koşuluna bağlı
- [ ] Her kapsam öğesi bir senaryoda veya `uncovered_items` içinde
- [ ] Her `AC` ve `BR` öğesi `coverage_summary.basis` içinde
- [ ] Her koşul, risk seviyesinin gerektirdiği derinlikte test edilmiş
- [ ] Her senaryo beklenen sonuçla (`O zaman`) bitiyor
- [ ] Kalıcı değişiklik bırakan her senaryoda `postconditions` var ve ürün davranışı iddia etmiyor
- [ ] Tırnak içindeki her beklenen metin kartta birebir geçiyor
- [ ] Her `<parametre>` senaryonun tüm veri setlerinde tanımlı
- [ ] Bir veri setinde en fazla bir geçersiz değer
- [ ] Senaryo önceliği, bağlı koşulların en yüksek risk seviyesine eşit
- [ ] Sayımlar ve kapsam yüzdeleri senaryolarla tutarlı
- [ ] Kartta olmayan değer, mesaj, alan, ekran veya kural uydurulmamış

### Adım 8: Çıktı

1. JSON belgesini oluştur.
2. Kod çalıştırabiliyorsan JSON'u kaydet ve script'i çalıştır. Yol, skill
   klasörüne göredir (VS Code'da `.github/skills/scenario-generator/`):

   ```bash
   python <skill-klasörü>/scripts/render_gherkin.py cikti.json cikti.feature --report rapor.md --selection cikti-secim.md
   ```

   Script hata verirse JSON'u düzelt ve tekrar çalıştır; hata kalmayana kadar
   sürdür. Uyarılar bilgi amaçlıdır.
3. Kod çalıştıramıyorsan yalnızca JSON'u döndür; dönüşümü pipeline yapar.

Kullanıcıyla konuşmadan (pipeline'da) çalışıyorsan yanıt olarak yalnızca JSON
belgesini (ve üretildiyse `.feature`, rapor ve seçim listesini) döndür; önünde
veya arkasında açıklama metni olmaz ve Adım 9 uygulanmaz. Kullanıcıyla
konuşuyorsan Adım 9'a geç.

### Adım 9: Seçim ve Test Senaryosu kartlarına dönüştürme

Hangi senaryonun Jira'da **Test Senaryosu kartına** dönüştürüleceğine
**kullanıcı karar verir.** Seçim listesi (`cikti-secim.md`) bu kararın tek
kaydıdır:

```text
- [x] 1. TS-ESUBE-2041-001 · ana akış · yüksek · pozitif · hazır · @smoke — Geçerli bilgilerle …
- [ ] 5. TS-ESUBE-2041-006 · hata akışı · yüksek · negatif · taslak (Q-01) — IBAN 26 karakterden uzun …
```

1. Script listeyi koşum sırasıyla üretir: önce `@smoke`, sonra risk seviyesi.
   Hazır senaryolar işaretli, taslak senaryolar işaretsiz gelir. Bu yalnızca
   başlangıç önerisidir.
2. Listeyi kullanıcıya numaralarıyla göster ve hangilerinin Test Senaryosu
   kartına dönüştürüleceğini sor. Kullanıcı dosyadaki kutuları kendisi de
   işaretleyebilir. Kullanıcı seçimini isteğinde zaten söylediyse ("hepsini
   aktar", "taslak olmayanları aktar") sormadan uygula.
3. Kullanıcının yanıtını ("3 ve 7'yi ekleme", "yalnızca smoke olanlar")
   listedeki `[x]` / `[ ]` işaretlerine uygula. Başka hiçbir satırı değiştirme;
   kullanıcının söylemediği bir senaryonun işaretini değiştirme. Yanıt
   belirsizse uygulamadan önce sor.
4. Taslak bir senaryo seçilirse bloklayıcı sorusunun açık olduğunu söyle; yine
   de seçilmesini isterse işaretle.
5. Aktarım dosyasını üret:

   ```bash
   python <skill-klasörü>/scripts/jira_export.py cikti.json cikti-secim.md cikti-jira.csv
   ```

   Kart türü varsayılan olarak `Test Senaryosu`dur; kurumda adı farklıysa
   `--issue-type "<ad>"` ekle. Script, liste JSON'la uyuşmuyorsa (başka karta
   ait satır, değişmiş başlık, tekrar eden satır) veya hiç işaret yoksa dosya
   üretmez; listeyi yeniden üret ya da kullanıcıya sor.

Kart güncellenip JSON yeniden üretildiğinde aynı `--selection` yolu verilir:
kullanıcının işaretleri korunur. Yalnızca yeni senaryolar ve başlığı değişen
senaryolar varsayılana döner; script bunları uyarı olarak yazar.

**CSV'deki her satır bir Test Senaryosu kartıdır:**

| Sütun | İçerik |
|---|---|
| `Summary` | `[TS-…] <başlık>` |
| `Issue Type` | `Test Senaryosu` |
| `Priority` | Risk seviyesinden: kritik → Highest, yüksek → High, orta → Medium, düşük → Low |
| `Kaynak Kart` | Senaryonun üretildiği kartın anahtarı (bağlantı için) |
| `Akış` | ana akış / alternatif akış / hata akışı |
| `Ön Koşullar` | Geçmiş ve `Diyelim ki` adımları, numaralı |
| `Test Adımları` | Eylem ve doğrulama adımları sırasıyla, numaralı (uçtan uca) |
| `Beklenen Sonuç` | `O zaman` adımları, numaralı |
| `Test Verisi` | Veri satırları tablosu (birden fazla satırda) veya tek satırın değerleri |
| `Description` | Amaç, akış, öncelik, teknik, izlenebilirlik, test ortamı, Geçmiş dâhil tam Gherkin, son koşullar, notlar, açık sorular |
| `Labels` | Özellik ve senaryo etiketleri, akış türü (`ana-akis`, `alternatif-akis`, `hata-akisi`), `pozitif`/`negatif`, `taslak`, kaynak kart anahtarı |

**CSV'nin Jira'ya yüklenmesi** (kullanıcı yapar; agent Jira'ya bağlanmaz):

1. Jira'nın CSV içe aktarımını açın (Issues → Import issues from CSV), kodlama
   olarak UTF-8 seçin, kartların açılacağı projeyi seçin.
2. `Summary`, `Issue Type`, `Priority`, `Description` ve `Labels` sütunlarını
   aynı adlı alanlara eşleyin.
3. Test Senaryosu kartınızda Ön Koşullar, Test Adımları, Beklenen Sonuç veya
   Test Verisi alanları varsa ilgili sütunları onlara eşleyin; yoksa eşlemeden
   bırakın — aynı içerik Description'da da vardır.
4. `Kaynak Kart` sütununu, Test Senaryosu kartının kaynak karta bağlandığı
   bağlantı türüne eşleyin (Link "…"). Sihirbaz bağlantı eşlemesi sunmazsa
   sütunu boş bırakın; kartlar kaynak kart anahtarı etiketiyle bulunup
   bağlanabilir.
5. Öncelik adları Jira'nın varsayılanlarıdır (Highest, High, Medium, Low);
   kurumda farklıysa sihirbazın değer eşlemesinde düzeltin.

## Zorunlu kurallar

1. **Tüm alanlar okunur.** Açıklama ve kabul kriterleriyle yetinilmez; ekler,
   ortam, yorumlar ve bağlı kartlar da test esasıdır. Okunamayan her şey
   kaydedilir, atlanmaz.
2. **Kaynak gösterilir.** Her kural, değer, alan adı ve mesaj metni kartın
   bir alanına dayanır.
3. **Uydurma yok.** Kartta yer almayan iş kuralı, sınır değer, mesaj metni,
   alan veya ekran adı üretilmez. Varsayıma dayanan senaryo `assumptions`
   ile ilişkilendirilir ve `needs_clarification` olur.
4. **Çelişki sessizce çözülmez.** Daha yeni ve yetkili bir karar yoksa soru
   yazılır; çelişki yalnızca etkilediği kapsam öğelerini bloke eder.
5. **Beklenen sonuç test esasından türetilir** (test oracle); sistemin mevcut
   davranışından veya tahminden değil.
6. **İzlenebilirlik.** Her senaryo test esası öğelerine, test koşullarına ve
   (kabul kriterine dayalı teknik dışında) kapsam öğelerine bağlıdır.
7. **İki taraflı kapsam.** Her `AC` ve `BR` için hem kuralın sağlandığı hem
   ihlal edildiği durum test edilir.
8. **Geçersiz değerler tek tek test edilir.** Bir veri setinde birden fazla
   geçersiz değer birleştirilmez.
9. **Bir senaryo, bir uçtan uca akış.** Senaryo giriş noktasından başlar,
   akışın sonucunda ve kartta tanımlı sonraki etkilerde biter. Farklı sonuçla
   biten akışlar (ana, alternatif, hata) ayrı senaryolardır; aynı akışı aynı
   tür sonuçla izleyen farklı veriler veri satırı olur.
10. **Sabit sayı yok.** Senaryo sayısı veya kategori dağılımı hedeflenmez.
11. **Kapsam sınırları.** Fonksiyonel olmayan senaryo yalnızca kart ölçülebilir
    bir gereksinim içeriyorsa üretilir; yoksa `out_of_scope` içine yazılır.
12. **Gerçek kişisel veri yok.** Eklerdeki gerçek veriler test verisine
    kopyalanmaz; TCKN, IBAN, kart numarası, telefon ve e-posta sentetiktir.
13. **Dil.** Senaryo metinleri kartın dilinde yazılır. JSON anahtarları ve
    enum değerleri şemadaki gibi İngilizce kalır.
14. **Örnek kopyalanmaz.** `examples/` altındaki dosyalar yalnızca biçim ve
    ayrıntı düzeyini gösterir.
15. **Ağ erişimi yok.** Jira'ya veya başka bir adrese bağlanılmaz, oturum
    açılmaz, kimlik bilgisi istenmez, ek indirilmez. Kart verisinin tek
    kaynağı paylaşılan XML ve kullanıcının açıkça eklediği dosyalardır.
16. **Jira seçimi kullanıcınındır.** Agent seçim listesindeki işaretleri
    yalnızca kullanıcının söylediği gibi değiştirir. Jira kayıtlarını agent
    oluşturmaz; CSV'yi kullanıcı yükler.

## Bug kartları (değişiklikle ilgili test)

- **Doğrulama testi** (confirmation test): yeniden üretme adımları (açıklama,
  video, log) uçtan uca akış olarak izlenir; bu akış kartın ana akışıdır ve
  beklenen sonuç düzeltilmiş davranıştır. Etiket: `@confirmation`.
- **Regresyon testleri**: hatanın dokunduğu komşu akışlar (bağlı kartlar,
  bileşenler) için, değişikliğin mevcut davranışı bozmadığını doğrulayan
  uçtan uca senaryolar; her biri bir alternatif akıştır. Etiket:
  `@regression`.
- Ortam ve etkilenen sürüm, `test_environment` içine ve gerekiyorsa
  `Diyelim ki` adımına yazılır.

## ID biçimleri

| Öğe | Biçim | Örnek |
|---|---|---|
| Kabul kriteri / iş kuralı | `AC-NN` / `BR-NN` | `AC-03`, `BR-01` |
| Tasarım ayrıntısı / teknik kısıt | `UI-NN` / `CN-NN` | `UI-02`, `CN-01` |
| Yorum | `C-NN` | `C-02` |
| Çelişki | `CF-NN` | `CF-01` |
| Test koşulu | `COND-NN` | `COND-02` |
| Akış (kapsam öğesi) | `UC-ANA`, `UC-ALT-<AD>`, `UC-HATA-<AD>` | `UC-HATA-LIMIT` |
| Kapsam öğesi | `<TEKNİK>-<ALAN>-<DEĞER>` | `EP-IBAN-I1`, `BVA-AMT-0.99` |
| Senaryo | `TS-<JIRA_KEY>-NNN` | `TS-ESUBE-2041-003` |
| Veri seti | `DS-NN` | `DS-01` |
| Soru / varsayım | `Q-NN` / `A-NN` | `Q-02`, `A-01` |

Teknik ön ekleri: `UC` uçtan uca akış, `EP` denklik sınıfı, `BVA` sınır
değer, `DT` karar tablosu, `ST` durum geçişi, `EG` hata tahmini, `CL` kontrol
listesi. ID'lerde yalnızca büyük ASCII harf, rakam, `.`, `_` ve `-` kullanılır
(`UC-HATA-IBANUZUN`; Türkçe karakter yok).

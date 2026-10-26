---
name: scenario-generator
description: Jira kartının (story, task, bug) kullanıcının paylaştığı XML dışa aktarımından ISTQB tabanlı manuel test senaryoları üretir ve Türkçe Gherkin ile yazar. Jira'ya bağlanmaz, ek indirmez. XML'deki tüm alanları (açıklama, kabul kriterleri, ortam, yorumlar, ek listesi, bağlı kartlar, özel alanlar) okur, kartın senaryo üretmeye yeterli olup olmadığını değerlendirir, eksik ve çelişkili bilgiler için soru üretir. Çıktı references/output-schema.json formatında tek bir JSON'dur; .feature dosyası ve kart yeterlilik raporu scripts/render_gherkin.py ile oluşturulur. Jira XML'i, kart içeriği veya kullanıcı hikâyesi verilip test senaryosu, test case, test durumu ya da Gherkin/feature istendiğinde kullan.
---

# Scenario Generator

Jira kartını **test esası** (test basis) kabul eder ve ISTQB test sürecinin
analiz → tasarım → uygulama adımlarını izleyerek **manuel test senaryoları**
üretir.

- **Girdi:** kullanıcının paylaştığı Jira XML dışa aktarımı (kart → Dışa
  aktar → XML). Alanlar, yorumlar, ek listesi ve bağlı kart anahtarları
  buradan okunur. Jira'ya bağlanılmaz, ekler indirilmez; XML'de olmayan bilgi
  `not_provided` olarak kaydedilir (`card-analysis-rules.md` §9).
- **Agent'ın çıktısı:** tek bir JSON belgesi. Kart envanteri, yeterlilik,
  test esası, çelişkiler, senaryolar ve kapsam burada tutulur. Senaryo
  adımları Türkçe Gherkin cümleleridir.
- **Script'in çıktıları:** `.feature` dosyası (test uzmanı için) ve kart
  yeterlilik raporu (ürün sahibi / analist için).

Adım kalıpları için şu an kurumsal bir standart yoktur; Gherkin cümleleri
serbesttir ve `gherkin-format-rules.md`'deki okunabilirlik kurallarına uyar.

## Dosyalar

| Dosya | Ne zaman okunur |
|---|---|
| `references/card-analysis-rules.md` | Adım 1–2'de: hangi alanın nasıl okunacağı, XML eşlemesi (§9), ekler, kaynak gösterme, çelişki kuralları, R1–R10 |
| `references/test-design-rules.md` | Adım 3–5'te: risk, test derinliği, teknik seçimi, teknikler, senaryo yazım kuralları |
| `references/gherkin-format-rules.md` | Adım 5'te: Gherkin anahtar kelimeleri, cümle yazımı, Örnekler, Geçmiş |
| `references/output-schema.json` | Adım 6–8'de: çıktının tek geçerli formatı |
| `scripts/render_gherkin.py` | Adım 8'de: JSON'u doğrular, `.feature` ve yeterlilik raporu üretir |
| `examples/sample-output.json` | Biçim ve ayrıntı düzeyi örneği. İçeriği kopyalanmaz. Örnekte üç ek kullanıcı tarafından dosya olarak (video okunamamıştır), epic de ayrı bir XML olarak paylaşılmıştır; paylaşılmayan ek ve bağlı kart `not_provided` / `not_accessible` olur |
| `examples/sample-output.feature`, `examples/sample-report.md` | Örnek JSON'dan script ile üretilmiş çıktılar |

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

### Adım 4: Test tasarımı

1. Her koşula `test-design-rules.md` §2'ye göre teknik ata. Her koşulda en az
   bir teknik; her kartta hata tahmini.
2. Risk seviyesine göre derinliği `test-design-rules.md` §3'teki tablodan al.
3. Kapsam öğelerini çıkar: denklik sınıfları, sınır değerler, karar tablosu
   kuralları, durum geçişleri, hata tahminleri.
4. Kapsam öğelerini senaryolara dönüştür. Hedef: her kapsam öğesi en az bir
   senaryoda. Kapsanamayan öğe gerekçesiyle `uncovered_items` içine yazılır.

**Senaryo sayısı sabit değildir.** Kategori kotası veya dağılım hedefi
uygulanmaz; sayı kapsam öğelerinden ve risk derinliğinden çıkar.

### Adım 5: Senaryoları Gherkin ile yaz

`gherkin-format-rules.md` ve `test-design-rules.md` §5'e göre:

- `feature` alanına Özellik adını, etiketleri ve tüm senaryolarda ortak ön
  koşulları (`background`) yaz.
- Her senaryonun adımlarını `Diyelim ki` → `Eğer ki` → `O zaman` sırasıyla,
  test uzmanının tek başına uygulayabileceği somutlukta yaz.
- Ekran ve alan adlarını kartta veya ekteki tasarımda geçtiği gibi kullan.
- Beklenen mesajları tırnak içinde, kaynaktaki haliyle yaz.
- Farklı verilerle tekrarlanan senaryoda değerleri `<parametre>` ile yaz ve
  veri setlerine koy.

### Adım 6: Kapsam özeti

`coverage_summary` alanını doldur: her `AC` ve `BR` öğesinin hangi
senaryolarla kapsandığı, teknik bazında kapsam yüzdesi, kapsanamayan öğeler ve
senaryo sayıları.

### Adım 7: Öz denetim

Çıktıyı vermeden önce her maddeyi kontrol et:

- [ ] Kartın tüm alanları, ekleri, yorumları ve bağlantıları `card_inventory` içinde
- [ ] Her test esası öğesinin kaynağı var; ek ve yorum kaynakları envanterde tanımlı
- [ ] Her çelişki kayıtlı; çözülmemiş olanların sorusu var
- [ ] R7, R9, R10 sonuçları envanter ve çelişkilerle tutarlı
- [ ] JSON, `output-schema.json` ile geçerli
- [ ] Her senaryo en az bir test esası öğesine ve bir test koşuluna bağlı
- [ ] Her kapsam öğesi bir senaryoda veya `uncovered_items` içinde
- [ ] Her `AC` ve `BR` öğesi `coverage_summary.basis` içinde
- [ ] Her koşul, risk seviyesinin gerektirdiği derinlikte test edilmiş
- [ ] Her senaryo beklenen sonuçla (`O zaman`) bitiyor
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
   python <skill-klasörü>/scripts/render_gherkin.py cikti.json cikti.feature --report rapor.md
   ```

   Script hata verirse JSON'u düzelt ve tekrar çalıştır; hata kalmayana kadar
   sürdür. Uyarılar bilgi amaçlıdır.
3. Kod çalıştıramıyorsan yalnızca JSON'u döndür; dönüşümü pipeline yapar.

Yanıt olarak JSON belgesini (ve üretildiyse `.feature` ile raporu) döndür.
Önünde veya arkasında açıklama metni olmaz.

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
9. **Bir senaryo, tek davranış.** Farklı beklenen sonuçlar ayrı senaryolardır;
   aynı adımlar ve aynı türde sonuç için farklı veriler veri seti olur.
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

## Bug kartları (değişiklikle ilgili test)

- **Doğrulama testi** (confirmation test): yeniden üretme adımları (açıklama,
  video, log) izlenir; beklenen sonuç düzeltilmiş davranıştır. Etiket:
  `@confirmation`.
- **Regresyon testleri**: hatanın dokunduğu komşu akışlar (bağlı kartlar,
  bileşenler) için, değişikliğin mevcut davranışı bozmadığını doğrulayan
  senaryolar. Etiket: `@regression`.
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
| Kapsam öğesi | `<TEKNİK>-<ALAN>-<DEĞER>` | `EP-IBAN-I1`, `BVA-AMT-0.99` |
| Senaryo | `TS-<JIRA_KEY>-NNN` | `TS-ESUBE-2041-003` |
| Veri seti | `DS-NN` | `DS-01` |
| Soru / varsayım | `Q-NN` / `A-NN` | `Q-02`, `A-01` |

Teknik ön ekleri: `EP` denklik sınıfı, `BVA` sınır değer, `DT` karar tablosu,
`ST` durum geçişi, `EG` hata tahmini, `CL` kontrol listesi.

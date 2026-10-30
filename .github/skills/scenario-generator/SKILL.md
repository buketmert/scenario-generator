---
name: scenario-generator
description: Jira kartının (story, task, cross-functional, bug) kullanıcının paylaştığı XML dışa aktarımından uçtan uca manuel test senaryoları üretir ve Türkçe Gherkin ile yazar. Önce karttaki iş akışlarını (ana, alternatif, hata) çıkarır, her akış için girişten sonuca bir senaryo yazar; sınır değer, denklik sınıfı gibi ISTQB teknikleri akışların veri satırlarını üretir. Jira'ya bağlanmaz, ek indirmez. Kartın yeterliliğini değerlendirir, eksik ve çelişkili bilgiler için soru üretir. XML'i scripts/parse_jira_xml.py ayrıştırır; belirsizlikler çoktan seçmeli sorulur ve yanıtla devam edilir. LLM yalın bir JSON yazar; scripts/render_gherkin.py onu tamamlar, doğrular, .feature dosyası, yeterlilik raporu, seçim listesi ve senaryoların incelenip işaretlendiği seçim ekranını (HTML) üretir. Jira XML'i, kart içeriği veya kullanıcı hikâyesi verilip test senaryosu, test case, test durumu ya da Gherkin/feature istendiğinde kullan.
---

# Scenario Generator

Jira kartını **test esası** (test basis) kabul eder ve ISTQB test sürecinin
analiz → tasarım → uygulama adımlarını izleyerek **uçtan uca manuel test
senaryoları** üretir. Senaryonun nasıl kurulduğu
`references/scenario-construction.md`'dedir.

## Uçtan uca süreç

Kullanıcı "test senaryosu oluştur" deyip kartın XML'ini verdiğinde adımlar
arada onay istenmeden uygulanır. Mekanik işi script'ler yapar; LLM yalnızca
muhakeme gerektiren kısmı (yeterlilik, akışlar, senaryolar) yazar.

```text
XML ──parse_jira_xml.py──> <KEY>-kart.md + <KEY>-kart.json          (LLM'siz, saniyeler)
     → LLM: yeterlilik, test esası, akışlar → çoktan seçmeli sorular (tek tur)
     → LLM: yalın <KEY>.json (bir kerede)
     ──render_gherkin.py --all --open──> tamamlar + doğrular → .feature, rapor,
        seçim listesi, seçim ekranı (HTML, tarayıcıda açılır)
     → kullanıcı Test Senaryosu kartı olacak senaryoları seçer
```

Süreç yalnızca üç yerde durur: XML verilmediyse (XML istenir), Adım 4b'deki
sorularda (yanıt beklenir) ve kart `not_ready` ise (rapor ve sorular verilir).

- **Girdi:** kullanıcının paylaştığı Jira XML dışa aktarımı (kart → Dışa
  aktar → XML). `parse_jira_xml.py` onu `<KEY>-kart.md` (LLM'in okuduğu sade
  metin) ve `<KEY>-kart.json` (script'in kullandığı hazır veri) dosyalarına
  çevirir. Jira'ya bağlanılmaz, ekler indirilmez.
- **LLM'in çıktısı:** yalın bir JSON (`references/output-template.md`):
  yeterlilik, test esası, çelişkiler, sorular ve yanıtları, akışlar, senaryolar.
  Kart bilgileri, envanter ve hesaplanabilen alanlar yazılmaz.
- **Script'in çıktıları:** `.feature` dosyası (test uzmanı için), kart
  yeterlilik raporu (ürün sahibi / analist için), seçim listesi ve seçim ekranı
  (`<KEY>-secim.html`). Seçilen her senaryo, kaynak karta bağlantıyla
  bağlanacak bir **Test Senaryosu** kartı adayıdır.

**Okuma bütçesi:** `output-schema.json` ve `examples/` altındaki JSON okunmaz
(birlikte ~23 bin token); yerlerine `output-template.md` okunur. Script şemaya
göre doğrular ve hatayı yerini göstererek söyler. Ham XML de okunmaz;
`<KEY>-kart.md` okunur.

Adım kalıpları için şu an kurumsal bir standart yoktur; Gherkin cümleleri
serbesttir ve `gherkin-format-rules.md`'deki okunabilirlik kurallarına uyar.

## Dosyalar

| Dosya | Ne zaman |
|---|---|
| `scripts/parse_jira_xml.py` | Adım 1'de çalıştırılır: XML → `<KEY>-kart.md` + `<KEY>-kart.json` |
| `references/output-template.md` | Adım 1'de okunur: **ne yazılır, ne yazılmaz** — yalın JSON iskeleti, soru ve yanıt biçimi |
| `references/card-analysis-rules.md` | Adım 1–2'de: kaynak gösterme, çelişki kuralları (§6), R1–R10 (§7) |
| `references/scenario-construction.md` | Adım 4–5'te: **test senaryosu nasıl oluşturulur** — akışları çıkarma, teknikleri akışlara bağlama, uçtan uca senaryoyu yazma |
| `references/test-design-rules.md` | Adım 3–5'te: risk, test derinliği, teknik seçimi, teknikler, senaryo yazım kuralları |
| `references/gherkin-format-rules.md` | Adım 5'te: Gherkin anahtar kelimeleri, cümle yazımı, Örnekler, Geçmiş |
| `references/output-schema.json` | Okunmaz; script doğrulamada kullanır |
| `scripts/render_gherkin.py` | Adım 8'de çalıştırılır: JSON'u tamamlar ve doğrular; `.feature`, rapor, seçim listesi ve seçim ekranı (`scripts/selection_page.py`) üretir |
| `examples/ESUBE-2041.xml` → `examples/ESUBE-2041/` | Uçtan uca örnek: girdi XML ve agent'ın ürettiği her dosya (yalın JSON, kart dosyaları, `.feature`, rapor, seçim listesi ve ekranı). Q-01 çoktan seçmeli yanıtlanmıştır. İçeriği kopyalanmaz |

## İş akışı

### Adım 1: XML'i ayrıştır ve kartı oku

```bash
python <skill-klasörü>/scripts/parse_jira_xml.py <kart.xml> --out-dir test-scenarios
```

XML sohbete yapıştırıldıysa önce bir dosyaya (`test-scenarios/_girdi.xml`)
yazılır. Script her kart için `test-scenarios/<KEY>/` altına iki dosya yazar:

- `<KEY>-kart.md` — okunacak olan. HTML çözülmüş açıklama, `AC-NN`
  numaralı kabul kriterleri, `C-NN` numaralı yorumlar (eskiden yeniye), ek
  listesi, bağlı kartlar, dış bağlantılar.
- `<KEY>-kart.json` — script'in JSON'u tamamladığı hazır veri: `source`,
  `card_inventory` (alan durumları, ekler `not_provided`, bağlı kartlar ve dış
  bağlantılar `not_accessible`, yorumların yazar ve tarihi) ve kabul kriteri
  alanındaki `AC` öğeleri.

LLM'in bu adımda yazacakları yalnızca:

1. Her yorum için `role`, `status`, `summary`, `basis_ids` (`card-analysis-rules.md` §3, §6).
2. Kart dosyasından farklı olan envanter kayıtları, aynı kimlikle: kullanıcı
   bir eki dosya olarak verdiyse `processed`, bağlı kartın XML'i de
   paylaşıldıysa `used`, alan ilgisizse `not_relevant`.
3. `test_environment`: ortam, kanal, sürüm, cihaz/tarayıcı ve kullanıcı tipi,
   kaynağıyla.

Python yoksa script çalışmaz; o durumda XML okunur ve JSON tam şemayla yazılır
(`card-analysis-rules.md` §9).

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
   ayrıntıları (`UI`), teknik kısıtlar (`CN`). Metin değiştirilmez. Kabul
   kriteri alanındaki `AC` öğeleri `<KEY>-kart.json`'dan gelir: metinlerini
   yeniden yazma, yalnızca değiştirdiğin alanı (ör. `testability`, `issue`)
   aynı kimlikle yaz.
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

### Adım 4b: Çoktan seçmeli sorular — senaryoları yazmadan önce, tek tur

Adım 2–4'te çıkan sorulardan senaryoyu etkileyenler (bloklayıcılar ve sonucu
tanımsız akışlar) senaryo yazılmadan **önce**, hepsi **bir kerede** sorulur.
Böylece senaryolar yanıtla bir kez yazılır; taslak yazıp yeniden üretmek
gerekmez.

1. Her soruya kartta geçen olası yorumlardan 2–4 seçenek yaz (`options`,
   `a`–`f`). Çelişkide her taraf bir seçenektir ve kaynağını taşır
   ("… (C-01)", "… (AC-02)"). Kartta hiç ipucu yoksa seçenekler olası
   davranışlardır ve öyle olduğu belli olur.
2. Sorarken her soruya iki seçenek daha eklenir: **Bilinmiyor — senaryo
   taslak kalsın** ve **Diğer (yazın)**.
3. VS Code'da `vscode/askQuestions` aracı varsa sorular onunla, yoksa
   sohbette harfli liste olarak sorulur ("Q-01: a, Q-02: c" biçiminde
   yanıtlanır). Yanıt gelene kadar beklenir.
4. Yanıt `answer` alanına yazılır: `{"choice": "a"}`,
   `{"choice": "other", "text": "…"}` veya `{"choice": "unknown"}`
   (`output-template.md`).
5. Yanıt davranışı belirliyorsa kaynağı `{"field": "clarification", "ref":
   "Q-NN"}` olan bir `BR` eklenir; metni yanıtın metnidir. Çözdüğü çelişki
   `resolved_by_later_decision` olur. Yanıtlanan soruya bağlı senaryo hazır
   sayılır; "Bilinmiyor" seçilen bloklayıcı sorunun senaryosu taslak kalır.
6. Raporun "Yanıtlanan sorular" tablosu yanıtları gösterir; yanıtı kullanıcı
   verdiği için kart sahibiyle teyit edilmesi önerilir.

Senaryoyu etkilemeyen sorular (ör. okunamayan bir ekin içeriği) sorulmadan
rapora yazılır. Kullanıcı yanıt vermek istemezse süreç sorular açık kalarak
devam eder.

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

### Adım 6: Kapsam özeti — script hesaplar

`coverage_summary` yazılmaz; script senaryolardan hesaplar (her `AC` ve `BR`
için senaryolar ve durum, teknik bazında kapsam, senaryo sayıları). LLM yalnızca
hiçbir senaryoya bağlanamayan kapsam öğesinin gerekçesini
`coverage_summary.uncovered_items` içine yazar; yoksa script hata verir. Bir
kuralın bir tarafı eksik kaldıysa ilgili `basis` kaydına `partially_covered`
ve `note` yazılabilir; script ihtiyatlı olanı korur.

### Adım 7: Öz denetim

Çıktıyı vermeden önce her maddeyi kontrol et:

Script'in hesapladığı alanlar (envanter, risk seviyesi, öncelik, durum,
kapsam ve sayımlar) bu listede yoktur.

- [ ] Her yorumun rolü ve özeti yazılı; kullanıcının dosya olarak verdiği ekler `processed`
- [ ] Her test esası öğesinin kaynağı var; ek ve yorum kaynakları envanterde tanımlı
- [ ] Her çelişki kayıtlı; çözülmemiş olanların sorusu var
- [ ] Senaryoyu etkileyen her soru seçenekleriyle soruldu; yanıtlar `answer` içinde, davranış belirleyen yanıtlar `clarification` kaynaklı BR olarak eklendi
- [ ] R7, R9, R10 sonuçları envanter ve çelişkilerle tutarlı
- [ ] Kartın bir ana akışı ve kartta tanımlı her red/uyarı davranışı için bir hata akışı (`UC`) var
- [ ] Her senaryo tam bir `UC` akışına bağlı; aynı akış iki senaryoda değil
- [ ] Her senaryo (Geçmiş dâhil) giriş noktasından başlıyor ve akışın sonucunda bitiyor
- [ ] Her senaryo en az bir test esası öğesine ve bir test koşuluna bağlı
- [ ] Her kapsam öğesi bir senaryoda veya gerekçesiyle `uncovered_items` içinde
- [ ] Her koşul, risk seviyesinin gerektirdiği derinlikte test edilmiş
- [ ] Her senaryo beklenen sonuçla (`O zaman`) bitiyor
- [ ] Kalıcı değişiklik bırakan her senaryoda `postconditions` var ve ürün davranışı iddia etmiyor
- [ ] Tırnak içindeki her beklenen metin kartta birebir geçiyor
- [ ] Her `<parametre>` senaryonun tüm veri setlerinde tanımlı
- [ ] Bir veri setinde en fazla bir geçersiz değer
- [ ] Kartta veya kullanıcının yanıtında olmayan değer, mesaj, alan, ekran veya kural uydurulmamış

### Adım 8: Çıktı — tek komut

JSON'u `test-scenarios/<KEY>/<KEY>.json` olarak **bir kerede** yaz ve çalıştır
(yol skill klasörüne göredir; VS Code'da `.github/skills/scenario-generator/`):

```bash
python <skill-klasörü>/scripts/render_gherkin.py test-scenarios/<KEY>/<KEY>.json --all --open
```

Script `<KEY>-kart.json`'u bulur, JSON'u tamamlar ve doğrular, yanına
`<KEY>.feature`, `<KEY>-rapor.md`, `<KEY>-secim.md` ve `<KEY>-secim.html`
yazar ve seçim ekranını tarayıcıda açar. `[HATA]` varsa yalnızca gösterilen
yeri düzelt ve komutu yeniden çalıştır; hesaplanan alanlardaki farklar uyarıdır
ve JSON'un yeniden yazılmasını gerektirmez. Kod çalıştıramıyorsan yalnızca
JSON'u döndür.

Kullanıcıyla konuşmadan (pipeline'da) çalışıyorsan `--open` kullanılmaz;
yanıt olarak yalnızca dosya yolları döner ve Adım 9 uygulanmaz.

### Adım 9: Ekrandan seçim

Hangi senaryonun Jira'da **Test Senaryosu kartına** dönüştürüleceğine
**kullanıcı karar verir**:

- `<KEY>-secim.html` tek dosyalık bir sayfadır, internet gerektirmez. Senaryolar
  koşum sırasıyla (önce `@smoke`, sonra risk) listelenir; her satırda akış
  türü, öncelik, pozitif/negatif ve taslak işareti, "Ayrıntı" altında amaç,
  Geçmiş dâhil Gherkin ve son koşullar vardır.
- Hazır senaryolar işaretli, taslaklar işaretsiz gelir; **Tümü**, **Hazırlar**,
  **Hiçbiri** düğmeleri vardır. Taslak seçilirse sayfa uyarır.
- Seçim sohbetten de yapılabilir: kullanıcı "3 ve 7'yi ekleme" derse
  `<KEY>-secim.md` dosyasında yalnızca söylediği satırların `[x]` / `[ ]`
  işareti değiştirilir (yanıt belirsizse önce sorulur).

Kart güncellenip JSON yeniden üretildiğinde aynı komut çalıştırılır:
`<KEY>-secim.md` içindeki işaretler korunur ve ekran da onlarla açılır.
Yalnızca yeni senaryolar ve başlığı değişen senaryolar varsayılana döner;
script bunları uyarı olarak yazar.

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
16. **Jira seçimi kullanıcınındır.** Seçim ekranda kullanıcı tarafından
    yapılır; agent seçim listesindeki işaretleri yalnızca kullanıcının
    söylediği gibi değiştirir.
17. **Yanıt, kaynaktır ama karar değildir.** Kullanıcının seçtiği yanıt test
    esası olur (`clarification`) ve süreç onunla ilerler; rapor bu yanıtların
    kart sahibiyle teyit edilmesini önerir. Yanıt yoksa veya "Bilinmiyor"
    seçildiyse soru açık kalır, ilgili senaryo taslak olur.

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

# Test Tasarım Kuralları

ISTQB CTFL v4.0 test tasarım tekniklerinin Jira kartına uygulanış biçimi.
Bu dosya `SKILL.md` iş akışının 3–5. adımlarında kullanılır.

## 1. Temel kavramlar

| Kavram | Anlamı | Çıktıdaki karşılığı |
|---|---|---|
| Test esası (test basis) | Testin dayandığı kaynak: Jira kartının tüm alanları, yorumları ve ekleri (`card-analysis-rules.md`) | `test_basis.items` |
| Test koşulu (test condition) | Test edilecek şey | `test_conditions` |
| Kapsam öğesi (coverage item) | Teknikle türetilen, test edilmesi gereken somut öğe: bir sınıf, bir sınır, bir kural | `coverage_items` |
| Test senaryosu (test case) | Ön koşul, veri, adım ve beklenen sonuçtan oluşan, manuel uygulanabilir test | `test_scenarios` |
| Test oracle | Beklenen sonucun kaynağı. Her zaman test esasıdır | `O zaman` adımları |

Akış: **Test esası öğesi (AC, BR) → test koşulu → kapsam öğesi → senaryo.**

**Pozitif ve negatif senaryo**

- `positive`: geçerli girdi veya izinli akış; sistem işlemi başarıyla tamamlar.
- `negative`: geçersiz girdi, izinsiz akış veya beklenmeyen kullanım; sistem
  işlemi doğru şekilde reddeder ve veri bozulmaz.

Sınır değer bir senaryo türü değil, tekniktir. 18 değerinin kabulü pozitif,
17 değerinin reddi negatif bir sınır değer senaryosudur.

## 2. Teknik seçimi

Kartta gördüğün sinyale göre tekniği seç. Bir koşula birden fazla teknik
uygulanabilir.

| Kartta gördüğün | Teknik | Kapsam öğesi ön eki |
|---|---|---|
| Her kabul kriteri ve iş kuralı (`AC`, `BR`) | Kabul kriterine dayalı test | (öğenin kendisi) |
| Ekteki tablo: limit, değer listesi, kural kombinasyonu | Tablonun yapısına göre denklik sınıfı, sınır değer veya karar tablosu | `EP`, `BVA`, `DT` |
| Girdi alanı ve izinli değer kümesi veya format ("yalnızca rakam", "A, B veya C") | Denklik paylarına ayırma | `EP` |
| Sayısal, tarih veya uzunluk aralığı ("en az", "en fazla", "18–65", "200 TL ve üzeri") | Denklik paylarına ayırma + sınır değer analizi | `EP`, `BVA` |
| Sonucu birden fazla koşulun birleşimi belirliyor ("eğer … ve … ise") | Karar tablosu | `DT` |
| Statü alanı, iş akışı, adım sırası (taslak → onay → yayın) | Durum geçişi | `ST` |
| Her kart | Hata tahmini | `EG` |
| Kartta ölçülebilir fonksiyonel olmayan gereksinim var | Kontrol listesine dayalı test | `CL` |

## 3. Risk ve öncelik

Her test koşulu için ürün riski: **seviye = olasılık × etki**. Jira önceliği,
bileşen ve yorumlardaki teknik notlar (karmaşık entegrasyon, geçmiş hatalar)
puanlamaya girdidir; puanın gerekçesi `rationale` alanına yazılır.

| Puan | Olasılık (hatanın bulunma ihtimali) | Etki (hata canlıya çıkarsa) |
|---|---|---|
| 1 | Basit kural, değişmeyen veya olgun alan | Kozmetik, kolay geçici çözüm |
| 2 | Orta karmaşıklık, yeni geliştirme | Bir kullanıcı grubunu etkiler, geçici çözüm var |
| 3 | Karmaşık mantık, çok entegrasyon, geçmişte hata çıkmış alan | Para kaybı, veri kaybı/bozulması, güvenlik, KVKK veya yasal yükümlülük |

| Olasılık × etki | Seviye (`risk.level`) |
|---|---|
| 9 | `critical` |
| 6 | `high` |
| 3–4 | `medium` |
| 1–2 | `low` |

Senaryonun `priority` değeri, bağlı olduğu test koşullarının en yüksek risk
seviyesidir.

**`@smoke` (duman testi).** Kart başına 1–2 mutlu yol senaryosu alır. Seçerken
şu sorulara bakılır; "evet" yanıtı çok olan yol önce gelir:

1. Kullanıcı bu akış olmadan işini yapamaz mı?
2. Akış para hareketi, ücret veya gelir üretiyor mu?
3. Akış kişisel veya hassas veri işliyor mu?
4. Akış kartın en sık kullanılacak yolu mu?

`@smoke` senaryoları koşum sırasında ve Jira seçim listesinde ilk sırada yer
alır; ardından senaryolar risk seviyesine göre (kritikten düşüğe) sıralanır.
Sıralamayı script yapar.

### Senaryo sayısı ve test derinliği

**Sabit senaryo sayısı, kategori kotası veya dağılım hedefi yoktur.** Senaryo
sayısı, kapsam öğelerinin ve her koşula risk seviyesine göre uygulanan
derinliğin sonucudur. Kart büyüdükçe veya risk arttıkça sayı artar; küçük ve
düşük riskli bir kart birkaç senaryoyla tamamlanabilir.

Her test koşulu, risk seviyesine karşılık gelen satırdaki tüm teknikleri alır.
Satırlar birikimlidir: üst satır alttakileri de içerir.

| Risk | Uygulanacak derinlik |
|---|---|
| `low` | Kabul kriterine dayalı test: kuralın sağlandığı ve ihlal edildiği taraf. Her geçersiz denklik sınıfı için bir temsilci |
| `medium` | + Tüm denklik sınıfları, 2 değerli sınır değer analizi, karar tablosunun ilgili sütunları, geçerli durum geçişleri |
| `high` | + 3 değerli sınır değer analizi, karar tablosunun tüm uygulanabilir sütunları, geçersiz durum geçişleri |
| `critical` | + Tüm geçişler (geçerli ve geçersiz) |

Hata tahmini kart başına seçilir ve kartın en yüksek risk seviyesine bağlıdır:
`low` 0–1, `medium` 1, `high` 1–3, `critical` 3–5 kapsam öğesi. `critical`
kartta sonucu para, veri veya güvenliği etkileyen her hata tahmini eklenir.

Sayıyı belirleyen kurallar:

1. Yeni bir kapsam öğesi eklemeyen senaryo yazılmaz; sayıyı artırmak gerekçe
   değildir.
2. Sayıyı azaltmak için kapsam öğesi atlanmaz. Kapsanamayan öğe gerekçesiyle
   `uncovered_items` içine yazılır.
3. Aynı adımlar ve aynı türde beklenen sonuç için farklı veriler tek
   senaryoda veri seti olarak toplanır. Böylece senaryo sayısı değil koşum
   sayısı artar.
4. Pozitif/negatif oranı hedeflenmez; kartın kurallarından çıkar.

## 4. Teknikler

### 4.1 Kabul kriterine dayalı test (ATDD)

**Ne zaman:** her kartta, her kabul kriteri için.

**Nasıl:**
1. Kriterin tanımladığı davranışı en az bir senaryoya dönüştür.
2. Given/When/Then formatındaki kriterlerde Given → `Diyelim ki`, When →
   `Eğer ki`, Then → `O zaman` adımları.
3. Kural formatındaki kriterlerde kuralın sağlandığı ve ihlal edildiği iki
   tarafı belirle.

**Kapsam ölçütü:** her kabul kriteri en az bir senaryoda.

### 4.2 Denklik paylarına ayırma (Equivalence Partitioning)

**Ne zaman:** bir girdinin veya çıktının değerleri, sistemin aynı şekilde
davrandığı gruplara ayrılabiliyorsa.

**Nasıl:**
1. Her girdi için geçerli ve geçersiz sınıfları çıkar. Kartta tanımlı her
   kural en az bir geçersiz sınıf doğurur.
2. Her sınıftan bir temsilci değer seç.
3. Geçerli sınıflar bir senaryoda birleştirilebilir.
4. **Geçersiz sınıflar tek tek test edilir.** Bir veri setinde yalnızca bir
   geçersiz değer olur; diğer tüm girdiler geçerli tutulur.

**Kapsam ölçütü:** test edilen sınıf / tanımlanan sınıf × 100. Hedef %100.
Birden fazla girdi varsa her girdinin her sınıfı en az bir kez test edilir
(each choice).

**Örnek:** Kupon kodu 6–12 karakter, yalnızca harf ve rakam.

| ID | Sınıf | Tür | Temsilci |
|---|---|---|---|
| EP-LEN-V | 6–12 karakter | geçerli | `YAZ2026` (7) |
| EP-LEN-I1 | 6 karakterden kısa | geçersiz | `KUP12` (5) |
| EP-LEN-I2 | 12 karakterden uzun | geçersiz | `KUPON2026ABCD` (13) |
| EP-CHR-V | Yalnızca harf ve rakam | geçerli | `YAZ2026` |
| EP-CHR-I1 | Harf/rakam dışı karakter | geçersiz | `YAZ-2026` (uzunluk geçerli tutuldu) |

### 4.3 Sınır değer analizi (Boundary Value Analysis)

**Ne zaman:** yalnızca sıralı sınıflarda: sayı, tutar, tarih, uzunluk, adet.

**Nasıl:**
1. Denklik sınıflarının sınırlarını belirle.
2. Adım büyüklüğünü belirle: tam sayı 1, tutar 0,01, tarih 1 gün, metin
   uzunluğu 1 karakter, saat 1 dakika veya 1 saniye (karttaki hassasiyete göre).
3. Değerleri seç:
   - **2 değerli BVA (varsayılan):** her sınırda sınır değerin kendisi ve
     komşu sınıftaki en yakın değer.
   - **3 değerli BVA (`high` ve `critical` riskte):** sınır değer ve her iki
     yanındaki komşular.

**Kapsam ölçütü:** test edilen sınır değer / tanımlanan sınır değer × 100.
Hedef %100.

**Örnek:** Yaş 18–65 kabul edilir.
- 2 değerli: 17, 18, 65, 66
- 3 değerli: 17, 18, 19, 64, 65, 66

**Kural:** sınırın dahil mi hariç mi olduğu kartta belirsizse ("200 TL'ye
kadar", "son kullanma tarihine kadar") sınır değer senaryosu üretilmez,
soru yazılır.

### 4.4 Karar tablosu (Decision Table)

**Ne zaman:** sonucu birden fazla koşulun birleşimi belirliyorsa.

**Nasıl:**
1. Koşulları (girdiler) ve eylemleri (çıktılar) listele.
2. Her sütun bir kuraldır. İkili koşullarda tam tablo 2ⁿ sütundur.
3. Olanaksız birleşimleri çıkar.
4. Sonucu bir koşula bağlı olmayan sütunları "–" (fark etmez) ile birleştir.
5. **Kartta sonucu tanımlanmayan sütun bir boşluktur:** senaryo üretilmez,
   `blocking` soru yazılır ve öğe `uncovered_items` içine girer. Karar
   tablosunun en büyük değeri bu boşlukları ortaya çıkarmasıdır.

**Kapsam ölçütü:** test edilen uygulanabilir sütun / tüm uygulanabilir sütun
× 100.

**Örnek:**

| Koşul / Eylem | DT-R1 | DT-R2 | DT-R3 | DT-R4 |
|---|---|---|---|---|
| Kupon süresi geçerli | E | E | H | H |
| Sepet ≥ 200 TL | E | H | E | H |
| Kupon uygulanır | ✓ | | | ? |
| Minimum tutar uyarısı | | ✓ | | ? |
| Süre doldu mesajı | | | ✓ | ? |

DT-R4 kartta tanımsız: soru yazılır.

### 4.5 Durum geçişi (State Transition)

**Ne zaman:** kaydın bir statüsü varsa veya sistemin davranışı önceki
adımlara bağlıysa.

**Nasıl:**
1. Durumları, olayları, koşulları (guard) ve eylemleri çıkar.
2. Geçerli geçişleri listele; her biri bir kapsam öğesi (`ST-T01`…).
3. `high` ve `critical` riskte geçersiz geçişleri de listele (taslak
   durumundaki siparişi "teslim edildi" yapmak gibi). Her geçersiz geçiş ayrı
   senaryoda test edilir.

**Kapsam ölçütleri:**
- Tüm durumlar: her durum en az bir kez ziyaret edilir.
- Geçerli geçişler (0-switch): her geçerli geçiş en az bir kez. **Varsayılan.**
- Tüm geçişler: geçerli ve geçersiz tüm geçişler. `high` ve `critical` riskte.

### 4.6 Hata tahmini (Error Guessing)

**Ne zaman:** her kartta, en yüksek riskli koşullar için.

**Nasıl:** aşağıdaki listeden kartla ilgili olanları seç. Yalnızca beklenen
sonucu test esasından türetilebilen durumlar senaryo olur; türetilemiyorsa
soru yazılır. Kaç tane seçileceği, kartın en yüksek risk seviyesine göre
§3'teki tablodan belirlenir.

| Alan | Olası hatalar |
|---|---|
| Metin girdisi | Boş, yalnızca boşluk, baş/sondaki boşluk, çok uzun metin, özel karakter, HTML/script içeriği, tek tırnak, SQL ifadesi (`' OR '1'='1`), emoji |
| Türkçe | ç ğ ı İ ö ş ü; büyük/küçük harf dönüşümü (i/İ, ı/I); sıralama ve arama |
| Sayı | 0, negatif, ondalık ayırıcı (virgül/nokta), binlik ayırıcı, çok büyük değer, yuvarlama |
| Tarih ve saat | Geçmiş/gelecek, 29 Şubat, ay sonu, yıl dönümü, gece yarısı, saat dilimi |
| Etkileşim | Çift tıklama, tekrar gönderim, geri tuşu, sayfa yenileme, iki sekmede aynı işlem, oturum zaman aşımı, ağ kesintisi |
| Yetki | Yetkisiz rol, oturumsuz erişim, düşük yetkili rolle yetkili işlem (yetki yükseltme), URL'deki ID'yi değiştirerek başka kullanıcının verisine erişim |
| Veri | Mükerrer kayıt, silinmiş veya pasif kayıt, ilişkili kaydın olmaması, eşzamanlı güncelleme |
| Entegrasyon | Harici servisin (EFT/FAST, SMS, ödeme sağlayıcı) zaman aşımına düşmesi veya hata dönmesi, boş ya da beklenmeyen yanıt, aynı isteğin tekrar gönderilmesi |

Entegrasyon satırı yalnızca kart harici bir sisteme bağımlılık içeriyorsa
seçilir. Bu durumlarda kullanıcıya gösterilecek mesaj ve işlemin durumu çoğu
kartta tanımlı değildir; tanımlı değilse senaryo yerine soru yazılır.

### 4.7 Kontrol listesine dayalı test (fonksiyonel olmayan)

**Ne zaman:** yalnızca kart ölçülebilir bir fonksiyonel olmayan gereksinim
içeriyorsa.

ISO/IEC 25010 kalite karakteristikleri (`quality_characteristic`):
`performance_efficiency`, `compatibility`, `usability`, `reliability`,
`security`, `maintainability`, `portability`.

Ölçülebilir değer yoksa ("sayfa hızlı açılmalı") senaryo üretilmez; R3 için
soru yazılır veya `out_of_scope` içine eklenir.

## 5. Senaryo yazım kuralları

Senaryolar manuel test için yazılır: test uzmanı başka bir kaynağa bakmadan
senaryoyu uygulayabilmeli ve sonucu değerlendirebilmelidir. Gherkin biçimi
`gherkin-format-rules.md`'de.

1. **Başlık** sonucu söyler, 120 karakteri geçmez: "Tutar 0,99 TL olduğunda
   EFT başlatılmaz ve limit uyarısı gösterilir".
2. **Bağımsızlık.** Her senaryo tek başına ve herhangi bir sırayla uygulanır.
   Gereken durum ön koşulda tanımlanır; başka senaryonun sonucuna dayanmaz.
3. **Ön koşullar** `Diyelim ki` adımlarıdır: kullanıcı tipi, açık ekran, test
   verisi (bakiye, kayıt durumu). Tüm senaryolarda aynı olanlar
   `feature.background` (Geçmiş) içine yazılır.
4. **Tek eylem, tek adım.** Her adım test uzmanının uygulayabileceği
   somutluktadır: hangi ekranda, hangi alana, hangi değer.
5. **Adlar karttan gelir.** Ekran, alan ve buton adları kartta veya ekteki
   tasarımda geçtiği gibi yazılır. Kartta adı geçmeyen öğe uydurulmaz.
6. **Veri ayrımı.** Değişen değerler `<parametre>` ile yazılır ve veri
   setlerinde tutulur. Parametre adları küçük harf ve alt çizgidir
   (`ad_soyad`).
7. **Doğrulama.** Her senaryo `O zaman` bloğuyla biter. Beklenen sonuç somut ve
   gözlemlenebilirdir. Tırnak içindeki beklenen metin kartta birebir geçer.
8. **Yan etki kontrolü.** Negatif senaryolar işlemin gerçekleşmediğini de
   doğrular (`Fakat işlem başlatılmaz`).
9. **Deterministik veri.** Tarihler göreli yazılır ("bugünün tarihi − 1 gün").
   Rastgele değer kullanılmaz. Benzersiz olması gereken veri ön koşulda
   belirtilir.
10. **Veri setleri.** Aynı adımlar ve aynı türde beklenen sonuç için
    kullanılır. Her veri seti, neyi temsil ettiğini söyleyen bir `label`
    taşır ("Alt sınırın altı: 0,99"). Script bunları `Örnekler` tablosuna
    dönüştürür.
11. **Etiketler.** Agent senaryo `tags` içine `@smoke` (kritik mutlu yol),
    `@regression`, `@confirmation` (bug doğrulama) veya ekibin kullandığı
    diğer etiketleri yazar. Jira key, senaryo ID, `@pozitif` / `@negatif` ve
    `@taslak` script tarafından eklenir.
12. **Notlar.** Test uzmanının bilmesi gereken teknik ayrıntılar veya dikkat
    edilecek noktalar adımlara değil `notes` alanına yazılır.
13. **Son koşullar.** Senaryo sistemde kalıcı bir değişiklik bırakıyorsa
    (para hareketi, kayıt oluşturma veya silme, durum değişikliği, limit
    kullanımı) bu durum ve gerekiyorsa temizlik `postconditions` alanına
    yazılır: "Gönderici test hesabından gerçek bir EFT işlemi oluşur; tekrar
    koşmadan önce bakiye kontrol edilmelidir." Son koşul beklenen sonuç
    değildir. Ürünün ne yapması gerektiği `O zaman` adımında doğrulanır; son
    koşul yalnızca testi yeniden koşabilmek ve ortamı temiz bırakmak içindir.
    Kartta olmayan bir ürün davranışını iddia etmez. Kalıcı değişiklik
    bırakmayan senaryoda alan yazılmaz.

## 6. Test seviyesi ve tipi

| `test_level` | Ne zaman |
|---|---|
| `component` | Tek bir birimin mantığı. Jira kartından nadiren üretilir |
| `component_integration` | Servisler veya modüller arası sözleşme (API isteği/yanıtı) |
| `system` | Uçtan uca kullanıcı akışı, UI veya API üzerinden. **Story için varsayılan** |
| `system_integration` | Harici sistemlerle etkileşim: ödeme sağlayıcı, SMS, e-posta servisi |
| `acceptance` | İş kullanıcısının bakış açısıyla kabul doğrulaması (UAT) |

| `test_type` | Ne zaman |
|---|---|
| `functional` | Sistemin ne yaptığı. Varsayılan |
| `non_functional` | Sistemin nasıl yaptığı. `quality_characteristic` zorunlu |

Değişiklikle ilgili testler (doğrulama ve regresyon) ayrı bir tip değildir;
`@confirmation` ve `@regression` etiketleriyle işaretlenir.

## 7. Kaçınılacak ifadeler

Beklenen sonuçta ve adımlarda kullanılmaz; yerine somut sonuç yazılır.

| Kaçın | Yerine |
|---|---|
| Doğru çalışır, sorunsuz çalışır | Sepet toplamı 450,00 TL olur |
| Beklendiği gibi | Kartta tanımlı sonucu yaz |
| Hata verir | Kupon uygulanmaz, "Kuponun süresi dolmuş" mesajı gösterilir |
| Kontrol edilir | Neyin hangi değere eşit olduğunu yaz |
| Uygun bir değer gir | `"<kupon_kodu>"` ve veri setinde somut değer |
| vb., gibi, ve diğerleri | Her durumu ayrı kapsam öğesi olarak yaz |
| Hızlıca, birkaç kez | "Aralarında bekleme olmadan iki kez" |

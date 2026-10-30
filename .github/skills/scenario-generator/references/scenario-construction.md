# Test Senaryosu Nasıl Oluşturulur

Bu dosya, bir Jira kartından **uçtan uca test senaryosunun** adım adım nasıl
kurulduğunu anlatır. `SKILL.md` iş akışının 4. ve 5. adımlarında kullanılır.
Örnekler `examples/ESUBE-2041/` altındaki EFT kartındandır; kartın XML'i
`examples/ESUBE-2041.xml`.

## 1. Test senaryosu nedir

Test senaryosu, kartın tanımladığı bir iş akışının **baştan sona** manuel
olarak uygulanabilir tarifidir: kim, hangi durumda, hangi veriyle, hangi
adımları izleyerek, hangi sonucu görmelidir.

- **Bir senaryo, bir akış.** Senaryo kullanıcının işe başladığı noktada (giriş,
  menü, ekran) başlar; akışın sonucunda ve kartta tanımlı sonraki etkilerde
  (dekont, kayıt, bildirim) biter. Kartta tanımlı olmayan bir sonraki etki
  eklenmez.
- **Tek başına uygulanır.** Test uzmanı başka bir senaryoya, karta veya kişiye
  bakmadan senaryoyu baştan sona koşabilir ve sonucu değerlendirebilir.
- **Jira'da bir Test Senaryosu kartıdır.** Seçilen her senaryo, kaynak karta
  bağlı ayrı bir kart olur; kartın alanları aşağıdaki bileşenlerden dolar.

| Bileşen | Ne yazılır | JSON alanı | Test Senaryosu kartında |
|---|---|---|---|
| Başlık | Akış ve sonucu, tek cümle | `title` | Summary |
| Amaç | Hangi akışı ve hangi kuralları doğruladığı | `objective` | Description |
| Akış | Başlangıçtan sonuca akışın özeti ve türü | `UC` kapsam öğesi | Akış, Description |
| Ön koşullar | Kullanıcı, kanal, açık ekran, gereken veri durumu | `Diyelim ki` adımları, `feature.background` | Ön Koşullar |
| Adımlar | Giriş noktasından sonuca her kullanıcı eylemi | `Eğer ki` / `Ve` adımları | Test Adımları |
| Doğrulamalar | Ara noktalarda ve sonda gözlenecek sonuç | `O zaman` / `Ve` / `Fakat` adımları | Beklenen Sonuç |
| Test verisi | Değişen değerler ve her satırın ne temsil ettiği | `test_data` | Test Verisi |
| Son koşul | Testin bıraktığı kalıcı durum ve temizlik | `postconditions` | Description |
| İzlenebilirlik | Dayandığı AC/BR, koşul ve kapsam öğeleri | `traceability` | Description |
| Öncelik | Bağlı koşulların en yüksek risk seviyesi | `priority` | Priority |

## 2. Adım 1 — Kartın akışlarını çıkar

Senaryo yazmadan önce kartın iş akışları listelenir. Her akış bir **UC
kapsam öğesidir** (`technique: use_case_based`). Kaynaklar: açıklama
(kullanıcı hikâyesi, akış adımları), kabul kriterleri, tasarım ayrıntıları,
yorumlar.

1. **Aktör ve giriş noktası.** İşi kim yapıyor (müşteri tipi, rol), hangi
   kanalda, nereden başlıyor? Örnek: bireysel müşteri, E-Şube web, giriş →
   Para Transferleri → EFT.
2. **Ana akış (`main`).** Kartın amacını gerçekleştiren başarı yolu. Adımlar
   kartta geçtiği sırayla, sonuç ve kartta tanımlı sonraki etkilerle yazılır.
   Her kartın bir ana akışı vardır.
3. **Alternatif akışlar (`alternative`).** Aynı amaca başka bir yoldan ulaşan
   geçerli akışlar: kartta tanımlı seçenekler (kayıtlı alıcı, ileri tarihli
   işlem, farklı kanal) ve hata tahmininden gelen kullanım varyasyonları (art
   arda iki tıklama, geri tuşu).
4. **Hata akışları (`exception`).** Kartta tanımlı her red, uyarı veya engelleme
   davranışı. Aynı mesajla ve aynı sonuçla biten farklı sebepler **aynı**
   akıştır ("zorunlu alanlardan biri boş"); farklı mesaj veya sonuç **ayrı**
   akıştır.
5. **Sonucu tanımsız akış.** Kart akışın sonucunu söylemiyorsa (yetersiz bakiye
   ne olur?) akış için senaryo uydurulmaz: soru yazılır. Sonuç çelişkiliyse
   akış kaydedilir ve senaryosu taslak (`needs_clarification`) olur.

UC öğesinin `description` alanı akışı başlangıçtan sonuca tek satırda özetler:
`Giriş → … → Sonuç`. Ana akıştan türeyen akışlar "Ana akış; <farkı> → <sonucu>"
biçiminde yazılır.

**Örnek (ESUBE-2041):**

| UC | Tür | Başlangıçtan sonuca |
|---|---|---|
| `UC-ANA` | ana | E-Şube girişi → Para Transferleri > EFT → Gönderici Hesap → Alıcı IBAN, Alıcı Adı Soyadı, Tutar → Gönder → başarı mesajı ve dekont numarası |
| `UC-ALT-CIFTGONDER` | alternatif | Ana akış; Gönder'e art arda iki kez basılır → tek başarı mesajı, tek dekont |
| `UC-HATA-LIMIT` | hata | Ana akış; tutar limit dışında → limit mesajı, EFT başlatılmaz |
| `UC-HATA-ZORUNLU` | hata | Ana akış; zorunlu alanlardan biri boş → zorunlu alan mesajı, EFT başlatılmaz |
| `UC-HATA-IBAN` | hata | Ana akış; IBAN TR ile başlamıyor veya kısa → "Geçersiz IBAN", EFT başlatılmaz |
| `UC-HATA-IBANUZUN` | hata | Ana akış; IBAN 26 karakterden uzun → davranış çelişkili (soru, taslak) |

Yetersiz bakiye kartta tanımlı olmadığı için akış değil, sorudur (Q-02).

## 3. Adım 2 — Teknikleri akışlara bağla

Denklik sınıfları, sınır değerler, karar tablosu kuralları ve hata
tahminleri (`test-design-rules.md` §2–§4) ayrı senaryolar değil, **akışların
verisidir**. Her kapsam öğesi, sonucuna göre bir akışa yerleşir:

| Kapsam öğesi | Nereye gider | Örnek |
|---|---|---|
| Geçerli denklik sınıfı, geçerli sınır değer | Ana (veya ilgili alternatif) akışın veri satırı | `BVA-AMT-1.00` → `UC-ANA` satırı "Alt sınır: 1,00" |
| Geçersiz denklik sınıfı, geçersiz sınır değer | Tetiklediği hata akışının veri satırı; satır başına tek geçersiz değer | `BVA-AMT-0.99` → `UC-HATA-LIMIT` satırı |
| Karar tablosu kuralı | Sonucu aynı olan kurallar aynı akışın satırları; farklı sonuç ayrı akış | — |
| Durum geçişi | Geçiş dizisi bir akıştır; geçersiz geçiş bir hata akışıdır | — |
| Hata tahmini | Adımı değiştiriyorsa alternatif akış, sonucu değiştiriyorsa hata akışı | `EG-01` → `UC-ALT-CIFTGONDER` |

Böylece senaryo sayısı akış sayısına, koşum sayısı veri satırlarına eşit olur.
Her kapsam öğesi bir senaryoda veya gerekçesiyle `uncovered_items` içindedir.

## 4. Adım 3 — Senaryoyu yaz

Her akış için bir senaryo yazılır. Sıra:

1. **Başlık:** akış + gözlenen sonuç, 120 karakteri geçmez. "Geçerli bilgilerle
   gönderilen EFT tamamlanır ve dekont numarası gösterilir".
2. **Amaç:** hangi akışın uçtan uca doğrulandığı ve kapsanan kurallar.
3. **Ön koşullar (`Diyelim ki`):** kullanıcı tipi veya rolü, kanal, açık ekran ve
   akış için gereken veri durumu (bakiye, kayıt durumu). Bütün senaryolarda
   birebir aynı olanlar `feature.background` (Geçmiş) içine yazılır; Geçmiş +
   senaryo adımları birlikte giriş noktasından başlar.
4. **Adımlar (`Eğer ki` / `Ve`):** giriş noktasından sonuca kadar kullanıcının
   yaptığı her şey, sırasıyla. Tek eylem, tek adım. Ekran, alan ve buton
   adları kartta geçtiği gibi. Atlanan bir ara adım (onay ekranı, şifre
   doğrulama) yalnızca kartta tanımlıysa yazılır.
5. **Doğrulamalar (`O zaman`):** akışın kartta tanımlı ara noktalarında (ör.
   onay ekranında gösterilen bilgiler) ve sonunda gözlenecek sonuç. Ara
   doğrulamadan sonra akış `Eğer ki` ile devam edebilir. Senaryo her zaman bir
   doğrulamayla biter.
   - Başarı akışı: sonuç mesajı ve kartta tanımlı sonraki etkiler (dekont
     numarası).
   - Hata akışı: hata mesajı **ve** işlemin gerçekleşmediği (`Fakat işlem
     başlatılmaz`). Kart hatadan sonraki davranışı tanımlıyorsa (alan
     temizlenir, tekrar denenebilir) o da doğrulanır.
6. **Veri:** değişen değerler `<parametre>` ile yazılır; her veri satırı neyi
   temsil ettiğini söyleyen bir etiket taşır ("Üst sınır: 50.000,00"). Tek
   satır varsa değerler adımlara yerleşir.
7. **Son koşul:** akış kalıcı bir değişiklik bırakıyorsa (para hareketi, kayıt,
   durum değişikliği) bıraktığı durum ve tekrar koşmak için gereken temizlik.
8. **İzlenebilirlik ve öncelik:** dayanılan AC/BR/UI öğeleri, test koşulları,
   kapsam öğeleri (UC dâhil); öncelik bağlı koşulların en yüksek risk
   seviyesidir. Ana akışın en kritik senaryosu `@smoke` alır
   (`test-design-rules.md` §3).

**Örnek — ana akış (`UC-ANA`):**

```gherkin
  Geçmiş:
    Diyelim ki E-Şube'ye bireysel müşteri olarak giriş yapmışım
    Ve Para Transferleri menüsünden EFT ekranını açmışım
    Ve Gönderici Hesap listesinden vadesiz TL hesabımı seçmişim

  @TS-ESUBE-2041-001 @pozitif @smoke
  Senaryo Taslağı: Geçerli bilgilerle gönderilen EFT tamamlanır ve dekont numarası gösterilir
    Diyelim ki gönderici hesabımda en az "<tutar>" TL kullanılabilir bakiye var
    Eğer ki Alıcı IBAN alanına "<iban>" yazarsam
    Ve Alıcı Adı Soyadı alanına "<ad_soyad>" yazarsam
    Ve Tutar alanına "<tutar>" yazarsam
    Ve Gönder butonuna basarsam
    O zaman "İşleminiz başarıyla gerçekleştirilmiştir" mesajını görürüm
    Ve ekranda işlemin dekont numarasını görürüm

    Örnekler:
      | durum                             | iban                       | ad_soyad   | tutar     |
      | Tipik tutar: 1.000,00             | TR330006100519786457841326 | Test Alıcı | 1.000,00  |
      | Alt sınır: 1,00                   | TR330006100519786457841326 | Test Alıcı | 1,00      |
      | Üst sınır: 50.000,00              | TR330006100519786457841326 | Test Alıcı | 50.000,00 |
```

**Örnek — hata akışı (`UC-HATA-ZORUNLU`):** aynı giriş noktası ve aynı
adımlar; boş bırakılan alan veri satırıdır, sonuç mesaj ve işlemin
başlatılmamasıdır:

```gherkin
    O zaman "Lütfen zorunlu alanları doldurunuz" mesajını görürüm
    Fakat işlem başlatılmaz

    Örnekler:
      | durum                | iban                       | ad_soyad   | tutar    |
      | Alıcı IBAN boş       |                            | Test Alıcı | 1.000,00 |
      | Alıcı Adı Soyadı boş | TR330006100519786457841326 |            | 1.000,00 |
      | Tutar boş            | TR330006100519786457841326 | Test Alıcı |          |
```

## 5. Ayrı senaryo mu, veri satırı mı?

| Durum | Karar |
|---|---|
| Aynı adımlar, aynı tür sonuç, farklı veri | Aynı senaryonun veri satırı |
| Farklı sonuç (başarı ↔ hata, farklı hata mesajı) | Ayrı akış, ayrı senaryo |
| Farklı adım dizisi (art arda iki tıklama, farklı menü, ek onay adımı) | Alternatif akış, ayrı senaryo |
| Sonucu açık bir soruya bağlı | Ayrı akış, taslak senaryo |
| Aynı akış iki senaryoda | Yanlış; script uyarır, veri satırı olarak birleştirilir |

## 6. Kontrol listesi (her senaryo için)

- [ ] Tam bir UC kapsam öğesine (akışa) bağlı
- [ ] Geçmiş + adımlar giriş noktasından başlıyor; ön koşullar akışın başında
- [ ] Akışın her kullanıcı eylemi ayrı bir adım; adlar karttaki gibi
- [ ] Doğrulamayla bitiyor; başarı akışında kartta tanımlı sonraki etkiler,
      hata akışında işlemin gerçekleşmediği doğrulanıyor
- [ ] Tırnak içindeki her beklenen metin kartta birebir geçiyor
- [ ] Veri satırlarının her biri etiketli; bir satırda en fazla bir geçersiz değer
- [ ] Kalıcı değişiklik bırakıyorsa son koşul yazılı
- [ ] Test uzmanı başka bir kaynağa bakmadan baştan sona uygulayabilir

# Gherkin Yazım Kuralları (manuel test senaryoları)

Senaryolar manuel test için yazılır: okuyan bir test uzmanı, başka bir kaynağa
bakmadan senaryoyu uygulayabilmeli ve sonucu değerlendirebilmelidir.

Adım kalıpları için şu an kurumsal bir standart yoktur; cümleler serbesttir.
Bu dosya yalnızca okunabilirlik ve tutarlılık için temel kuralları içerir.
İleride adım standardı belirlenirse bu dosya genişletilir.

## 1. İş bölümü

| Kim | Ne yapar |
|---|---|
| Agent | Adımları JSON'da Gherkin cümlesi olarak yazar: `{"keyword": "when", "text": "..."}`. Ortak ön koşulları `feature.background`, test verisini `test_data` içine koyar. |
| `scripts/render_gherkin.py` | `.feature` dosyasını oluşturur: anahtar kelimeleri Türkçeye çevirir, Geçmiş ve Örnekler bloklarını, etiketleri ve kaynak yorumlarını ekler; yapıyı ve tırnak içindeki beklenen metinleri denetler. |

## 2. Anahtar kelimeler

Dosya `# language: tr` satırıyla başlar.

| JSON `keyword` | Gherkin | Ne için kullanılır | Örnek |
|---|---|---|---|
| `given` | `Diyelim ki` | Başlangıç durumu, ön koşul, test verisi hazırlığı | `Diyelim ki gönderici hesabımda en az 1.000,00 TL kullanılabilir bakiye var` |
| `when` | `Eğer ki` | Test edilen eylem | `Eğer ki alıcı IBAN alanına "TR33..." yazarsam` |
| `then` | `O zaman` | Beklenen, gözlemlenebilir sonuç | `O zaman "Geçersiz IBAN" mesajını görürüm` |
| `and` | `Ve` | Önceki adımın türünde devam | `Ve Gönder butonuna basarsam` |
| `but` | `Fakat` | Olumsuz devam, çoğunlukla sonuçta | `Fakat işlem başlatılmaz` |

## 3. Senaryo yapısı

1. Sıra `Diyelim ki` → `Eğer ki` → `O zaman`. `Ve` ve `Fakat` önceki adımın
   türünü sürdürür; senaryonun ilk adımı olamaz.
2. **Tek davranış:** bir senaryoda bir eylem bloğu ve bir sonuç bloğu olur.
   Sonuçtan sonra yeni bir eylem geliyorsa senaryo ikiye bölünür (script
   uyarır).
3. **Sonuçla biter:** son adım `O zaman` bloğunda olur (script hata verir).
4. **Geçmiş (`feature.background`):** yalnızca tüm senaryolarda birebir aynı
   olan ön koşullar (giriş, ekrana gitme) buraya yazılır. Yalnızca `given` ve
   `and` içerir. Geçmiş varsa senaryo doğrudan `Eğer ki` ile başlayabilir.
5. **Bağımsızlık:** her senaryo tek başına ve herhangi bir sırayla
   uygulanabilir; başka bir senaryonun sonucuna dayanmaz.

## 4. Cümle yazımı

- **Tutarlı şahıs ve kip:** bir Özellik içinde tek biçim kullanılır. Önerilen
  biçim birinci tekil şahıs:
  - `Diyelim ki` → durum: "giriş yapmışım", "EFT ekranını açmışım", "… var"
  - `Eğer ki` → koşul: "yazarsam", "seçersem", "basarsam"
  - `O zaman` → gözlem: "görürüm", "… görüntülenir", "işlem başlatılmaz"
- **Adlar karttaki gibi:** ekran, alan ve buton adları kartta veya ekteki
  tasarımda nasıl geçiyorsa öyle yazılır (`Alıcı IBAN`, `Gönder butonu`).
  Kartta olmayan ekran veya alan adı uydurulmaz.
- **Tek eylem, tek adım:** "IBAN'ı yazıp tutarı girip gönderirsem" yerine üç
  ayrı adım.
- **Somut değer:** girilen değerler ve beklenen metinler tırnak içinde yazılır.
  "Uygun bir değer gir", "doğru çalıştığını kontrol et" gibi ifadeler
  kullanılmaz (`test-design-rules.md` §7).
- **Beklenen metin kartta geçer:** `O zaman` bloğunda tırnak içindeki her
  metin, test esası öğelerinden birinde (kabul kriteri, iş kuralı, tasarım
  ayrıntısı) birebir bulunur. Script bunu denetler; kartta metin yoksa
  davranış tırnaksız yazılır ("hata mesajı görüntülenir") ve metin için soru
  sorulur.
- **Gözlemlenebilir sonuç:** ekranda görünen metin, alanın durumu, işlemin
  gerçekleşip gerçekleşmediği, oluşan kayıt.
- **Teknik ayrıntı yok:** CSS seçici, XPath, SQL, API yolu adımlara yazılmaz.
  Test uzmanına gereken teknik bilgi `notes` içine yazılır.

## 5. Test verisi ve Örnekler

- Değişen değerler `<parametre>` ile yazılır: `Eğer ki tutar alanına "<tutar>" yazarsam`.
- **Tek veri seti:** değerler adımlara yerleştirilir, `Senaryo:` olarak yazılır.
- **Birden fazla veri seti:** `Senaryo Taslağı:` ve `Örnekler:` tablosu
  oluşur. Tablonun ilk sütunu `durum`dur ve veri setinin `label` değerini
  taşır ("Alt sınırın altı: 0,99").
- Bir satırda yalnızca bir geçersiz değer olur; diğerleri geçerli tutulur.
- Test verisi sentetiktir. Tarihler göreli yazılır ("bugünün tarihi + 1 gün").
- Değer biçimi kartla aynıdır (kartta "1,00 TL" yazıyorsa tutar `1,00` yazılır).

## 6. Test ortamı ve ön koşullar

- `test_environment` dosya başında yorum olarak yazılır; her senaryoda
  tekrarlanmaz.
- Bir senaryo farklı bir ortam veya kanal gerektiriyorsa bu `Diyelim ki`
  adımında söylenir ("Diyelim ki mobil uygulamada Android 14 cihazla giriş
  yapmışım").
- Test verisi hazırlığı (bakiye, müşteri tipi, kayıt durumu) `Diyelim ki`
  adımlarıyla yazılır.

## 7. Etiketler

- Script ekler: Jira key (Özellik), senaryo ID, `@pozitif` / `@negatif`,
  taslak senaryolar için `@taslak`.
- Agent ekler: `feature.tags` (bileşen, modül) ve senaryo `tags`
  (`@smoke`, `@regression`, `@confirmation` veya ekibin kullandığı diğerleri).

## 8. Üretilen dosyanın yapısı

```gherkin
# language: tr
# Kaynak: ESUBE-2041 — E-Şube'den EFT ile para gönderme
# Test ortamı: TEST ortamı, E-Şube web, Chrome, sürüm 4.12, bireysel müşteri
# Kart durumu: partial | Açık sorular: Q-01, Q-02, Q-03
# Bu dosya scenario-generator çıktısından üretilmiştir.

@ESUBE-2041 @para-transferleri @eft
Özellik: EFT Para Transferi
  Bireysel müşteri olarak E-Şube'den başka bankadaki bir hesaba EFT ile para gönderebilmeliyim.

  Geçmiş:
    Diyelim ki E-Şube'ye bireysel müşteri olarak giriş yapmışım
    Ve Para Transferleri menüsünden EFT ekranını açmışım
    Ve Gönderici Hesap listesinden vadesiz TL hesabımı seçmişim

  @TS-ESUBE-2041-003 @negatif
  Senaryo Taslağı: Tutar limit dışında olduğunda EFT başlatılmaz ve limit uyarısı gösterilir
    # Kaynak: AC-03, BR-01, UI-02 | COND-03 | BVA-AMT-0.99, BVA-AMT-50000.01, EP-AMT-I1, EP-AMT-I2
    # Not: Bakiye ön koşulu, yetersiz bakiye kontrolünün limit kontrolünü maskelememesi için tutar kadar olmalıdır.
    Diyelim ki gönderici hesabımda en az "<tutar>" TL kullanılabilir bakiye var
    Eğer ki Alıcı IBAN alanına "<iban>" yazarsam
    Ve Alıcı Adı Soyadı alanına "<ad_soyad>" yazarsam
    Ve Tutar alanına "<tutar>" yazarsam
    Ve Gönder butonuna basarsam
    O zaman "Tutar 1,00 TL ile 50.000,00 TL arasında olmalıdır" mesajını görürüm
    Fakat işlem başlatılmaz

    Örnekler:
      | durum                       | iban                       | ad_soyad   | tutar     |
      | Alt sınırın altı: 0,99      | TR330006100519786457841326 | Test Alıcı | 0,99      |
      | Üst sınırın üstü: 50.000,01 | TR330006100519786457841326 | Test Alıcı | 50.000,01 |
```

Tam örnek: `examples/sample-output.json` → `examples/sample-output.feature`.

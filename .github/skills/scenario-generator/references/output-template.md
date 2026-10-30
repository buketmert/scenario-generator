# JSON Yazım Kılavuzu (yalın)

`test-scenarios/<KEY>/<KEY>.json` dosyasına **yalnızca aşağıdaki alanları**
yaz. Kart bilgisi, senaryo kimlikleri, durum (hazır/taslak), `@smoke` ve Jira
alanları script tarafından doldurulur. İzlenebilirlik (AC/COND/UC kimlikleri,
risk puanı, yeterlilik kontrolleri) yazılmaz.

```json
{
  "ozellik": "EFT Para Transferi",
  "ortam": "TEST, E-Şube web, bireysel müşteri",
  "gecmis": ["Diyelim ki E-Şube'ye bireysel müşteri olarak giriş yapmışım"],
  "sorular": [
    {"id": "Q-01", "soru": "26 karakterden uzun IBAN'da ne olmalı?", "bloklayici": true,
     "secenekler": ["27. karakter girilemez (C-01)", "\"Geçersiz IBAN\" gösterilir (AC-02)"],
     "yanit": "a"}
  ],
  "senaryolar": [
    {"baslik": "Geçerli bilgilerle gönderilen EFT tamamlanır", "akis": "ana", "oncelik": "yüksek",
     "adimlar": ["Eğer ki Para Transferleri > EFT ekranını açarsam",
                 "Ve Alıcı IBAN alanına \"<iban>\" yazarsam",
                 "Ve Tutar alanına \"<tutar>\" yazarsam",
                 "Ve Gönder butonuna basarsam",
                 "O zaman \"İşleminiz başarıyla gerçekleştirilmiştir\" mesajını görürüm",
                 "Ve dekont oluşur"],
     "ornekler": [{"durum": "Alt sınır", "iban": "TR330006100519786457841326", "tutar": "1"},
                  {"durum": "Üst sınır", "iban": "TR330006100519786457841326", "tutar": "50000"}],
     "son_kosul": ["Hesap bakiyesi gönderilen tutar kadar azalır"]},
    {"baslik": "Tutar boşken EFT başlatılmaz", "akis": "hata", "oncelik": "orta",
     "adimlar": ["Eğer ki EFT ekranında Tutar alanını boş bırakıp Gönder butonuna basarsam",
                 "O zaman \"Lütfen zorunlu alanları doldurunuz\" mesajını görürüm",
                 "Fakat işlem başlatılmaz"],
     "sorular": ["Q-01"]}
  ],
  "kapsam_disi": [{"oge": "Kurumsal müşteri", "neden": "Ayrı kartta (C-03)"}]
}
```

## Alanlar

| Alan | Kural |
|---|---|
| `ozellik` | Özellik adı; yazmazsan kart özeti |
| `ortam` | Karttaki ortam; yoksa yazma |
| `gecmis` | Tüm senaryoların ortak ön koşulu (yalnızca `Diyelim ki` / `Ve`) |
| `adimlar` | Her satır `Diyelim ki`, `Eğer ki`, `Ve`, `Fakat` veya `O zaman` ile başlar; tek satır tek eylem; son blok `O zaman` |
| `akis` | `ana` (bir tane), `alternatif`, `hata` |
| `oncelik` | `kritik`, `yüksek`, `orta`, `düşük` — iş etkisi ve hata olasılığına göre |
| `ornekler` | Yalnızca veri değişince: her satır bir veri; `durum` satırın adıdır, diğer anahtarlar adımlarda `<ad>` |
| `sorular` (senaryoda) | Senaryonun bağlı olduğu soru kimlikleri; bloklayıcı soru yanıtsızsa senaryo taslak olur |
| `son_kosul` | Testin sistemde bıraktığı kalıcı durum (isteğe bağlı) |
| `yetersiz` | Kart senaryo üretmeye yetmiyorsa gerekçe; `senaryolar: []` |

## Sorular

- Her soruda kartta geçen yorumlardan türeyen 2–4 seçenek. "Bilinmiyor" ve
  "Diğer" soru sorulurken eklenir, JSON'a yazılmaz.
- `yanit`: seçenek harfi (`"a"`), kullanıcının kendi metni veya `"bilinmiyor"`.
  Yanıtlanmamışsa alanı yazma.

## Kontrol

Script hata verirse yalnızca gösterilen yeri düzelt. Tırnak içindeki mesaj
kartta bulunamazsa uyarı verir; mesajı karttaki gibi yazdığını kontrol et.

# Kullanım Kılavuzu — Senaryo Üretici

Jira kartından (story, task, cross-functional, bug) uçtan uca manuel test
senaryoları üreten VS Code Copilot kurulumu. Bu dosya, projeyi başka biriyle
paylaştığınızda karşı tarafın yapması gerekenleri anlatır.

## Bu proje nedir?

- Jira kartı verilir (XML dışa aktarımı **veya** kart anahtarı), kartın ana,
  alternatif ve hata akışları çıkarılır; her akış için bir uçtan uca senaryo
  Türkçe Gherkin ile yazılır.
- Kart yeterliliği değerlendirilir; eksik/çelişkili bilgiler için kullanıcıya
  netleştirme soruları sorulur.
- Senaryolar VS Code içinde bir seçim ekranında açılır; işaretlenenler tek
  tuşla Jira'da **Test Senaryosu** kartı olarak açılıp kaynak karta bağlanır.

## 1. Gereksinimler

| Gereksinim | Ne için | Kontrol |
|---|---|---|
| VS Code + GitHub Copilot (agent modu) | Agent, skill ve prompt dosyalarını çalıştırmak için | Copilot Chat açılıyor mu |
| Python 3.10+ | Tüm script'ler (`parse_jira_xml.py`, `render_gherkin.py`, `jira_create.py`) saf Python stdlib kullanır; tek isteğe bağlı paket `jsonschema` | `python --version` |
| `jsonschema` pip paketi | Senaryo JSON'u şemaya göre doğrulanır. Kurulu değilse doğrulama **uyarıyla atlanır**, üretim devam eder — zorunlu değil | `python -m pip install jsonschema` |

Not: Script'ler ek Python paketi istemez (`urllib`, `json` gibi yalnızca
stdlib). Windows'ta `python` yoksa `py` komutu denenir.

## 2. Projeyi klonlama / kopyalama

Depoyu olduğu gibi alın; `.github/` klasörü kurulumun kendisidir:

```text
.github/
  copilot-instructions.md                  → workspace talimatı (giriş: /senaryo-uret)
  agents/scenario-generator.agent.md       → "Senaryo Üretici" agent'ı
  agents/scenario-xml-analyst.agent.md     → yardımcı agent (Python yoksa XML analizi)
  prompts/senaryo-uret.prompt.md           → /senaryo-uret komutu
  skills/scenario-generator/
    SKILL.md                               → akışın tanımı (agent okur, siz okumazsınız)
    references/                            → analiz/yazım kuralları
    scripts/                               → Python script'leri
    examples/                              → örnek XML ve çıktılar
test-scenarios/                            → üretilen dosyalar buraya birikir
```

VS Code'da klasörü açtığınızda Copilot `.github/agents`, `.github/prompts` ve
`.github/skills` dosyalarını otomatik görür; **ek kurulum gerekmez**.

## 3. Kullanım

1. Copilot Chat'i **Agent** moduna alın.
2. Sohbete şunu yazın:

   ```text
   /senaryo-uret <KART-ANAHTARI>
   ```

   örn. `/senaryo-uret KBTYTKM3-1832` — kart Jira REST'ten okunur (aşağıdaki
   Jira kurulumu gerekir).

   Jira kurulumu yapmadan çalışmak için kartın XML dışa aktarımını verin:

   ```text
   /senaryo-uret test-scenarios/girdi/ESUBE-2041.xml
   ```

   XML'i Jira'dan almak için: kartı aç → ⋯ (veya sağ üst menü) → **Dışa
   aktar → XML**.

3. Agent kartı okur; senaryoyu etkileyen netleştirme sorularını önerileriyle
   birlikte tek bir liste hâlinde sorar ve **yanıtınızı bekler**.
4. Yanıtlar geldikten sonra senaryolar üretilir ve VS Code içinde seçim
   ekranı açılır.
5. Test Senaryosu kartı olacakları işaretleyin → **Jira'da aç** düğmesine
   basın. Kartlar Jira'da açılır ve kaynak karta bağlanır; soru-yanıt özeti
   kaynak karta yorum olarak eklenir.

Üretilen dosyalar `test-scenarios/<KART-ANAHTARI>/` klasörüne yazılır:
`<KEY>.feature` (Gherkin), `<KEY>-rapor.md` (yeterlilik raporu),
`<KEY>-secim.md` / `<KEY>-secim.html` (seçim listesi/ekranı),
`<KEY>-kart.md` / `<KEY>-kart.json` (ayrıştırılmış kart).

## 4. Jira bağlantısı — bir kerelik kurulum

Kart anahtarıyla çalışmak (`--from-jira`) ve "Jira'da aç" düğmesini
kullanmak için:

### 4.1 Jeton oluşturma

Jira Server / Data Center: Profil → **Kişisel Erişim Jetonları** (Personal
Access Tokens) → jeton oluşturun.

Jira Cloud: id.atlassian.com → Security → **API token**.

Jetonu **hiçbir dosyaya yazmayın, sohbete yapıştırmayın**; ortam
değişkenine koyun:

**Windows (kullanıcı kalıcı):**

```powershell
[Environment]::SetEnvironmentVariable("JIRA_PAT", "<jetonunuz>", "User")
```

Sonra VS Code'u kapatıp açın (ortam değişkenleri yeni süreçlerde okunur).

**macOS / Linux:** `~/.zshrc` veya `~/.bashrc` içine:

```bash
export JIRA_PAT="<jetonunuz>"
```

Jira Cloud için ayrıca:

```bash
export JIRA_EMAIL="<jira e-postanız>"
export JIRA_API_TOKEN="<jetonunuz>"
```

(Kimlik doğrulama sırası: `JIRA_PAT` varsa onu kullanır; yoksa
`JIRA_EMAIL + JIRA_API_TOKEN` ikilisini ister.)

### 4.2 Jira ayar dosyası (keşif)

`test-scenarios/jira-ayar.json` dosyası, script'e Jira adresini, kart türünü
("Test Senaryosu") ve bağlantı türünü söyler. Tek komutla keşfettirin:

```bash
python .github/skills/scenario-generator/scripts/jira_create.py test-scenarios/<KEY>/<KEY>.json --kesfet --url https://jira.kurum.local --kaydet
```

Bu komut Jira'nın sürümünü, bağlantı türlerini ve Test Senaryosu kartının
alanlarını okuyup `test-scenarios/jira-ayar.json` önerisini yazar.
Örneği de inceleyebilirsiniz:
`.github/skills/scenario-generator/examples/jira-ayar.ornek.json`

Ayarlarda dikkat edilecekler:

- `url` — Jira adresiniz.
- `kimlik` — `pat` (Server/DC) veya `cloud`.
- `kart_turu` — Test senaryosu kartının Jira'daki adı.
- `baglanti.tur` / `baglanti.test_karti` — Test Senaryosu kartının kaynak
  karta hangi bağlantı türüyle bağlanacağı; keşif bunu bulur, bulamazsa
  uyarıp `Relates` önerir.
- `alanlar` — Kart türünde özel alanlar varsa (ön koşullar, test adımları,
  beklenen sonuç, test verisi) `customfield_…` kimlikleri.

### 4.3 Deneme

Kart açmadan gönderilecek alanları görmek için:

```bash
python .github/skills/scenario-generator/scripts/jira_create.py test-scenarios/<KEY>/<KEY>.json --deneme
```

### 4.4 Jira kurulumu olmadan kullanım

Jira ayarı/jeton yoksa:

- Kart anahtarıyla üretim yapılamaz → kullanıcının **XML dışa aktarımı** vermesi istenir.
- "Jira'da aç" düğmesi kapalı gelir → senaryolar `.feature` dosyası olarak üretilir, elle Jira'ya taşınır.

Yani aracı tamamen Jira'sız da kullanabilirsiniz; yalnızca kart okuma ve
kart açma adımları manuel olur.

## 5. Sık karşılaşılan sorunlar

| Sorun | Neden / çözüm |
|---|---|
| `python` bulunamadı | `py` komutunu deneyin; Python kurulu değilse python.org'dan kurun. PATH'e ekli olduğundan emin olun. |
| `[HATA] Jira ayarı yok` | `test-scenarios/jira-ayar.json` yok → §4.2'deki keşif komutunu çalıştırın veya XML dışa aktarımı verin. |
| `[HATA] jeton yok` | `JIRA_PAT` (veya Cloud'da `JIRA_EMAIL` + `JIRA_API_TOKEN`) ortam değişkeni kurulu değil → §4.1. VS Code'u yeniden başlatın. |
| jsonschema uyarısı: "şema doğrulaması atlandı" | `python -m pip install jsonschema` |
| Seçim ekranı açılmadı | Adres sohbette yazılır (ör. `http://127.0.0.1:20080/`); VS Code içinde tarayıcı aracıyla açın. Dış tarayıcı gerekmez. |
| "Jira'da aç" düğmesi kapalı | Jira ayarı veya jeton eksik → §4. Keşif ve deneme komutlarını sırayla çalıştırın. |
| Bağlantı yönü uyarısı | `jira-ayar.json` içindeki `baglanti.test_karti` değerini `outward`/`inward` çevirin. |

## 6. Güvenlik notları

- Jeton yalnızca ortam değişkeninden okunur; hiçbir dosyaya yazılmaz, sohbete yapıştırılmaz, log'lara düşmez.
- Script'ler yalnızca `jira-ayar.json`'daki Jira adresine bağlanır.
- Kullanıcı onayı olmadan Jira'da kart açılmaz: kart açma yalnızca seçim ekranındaki **Jira'da aç** düğmesiyle veya açık taleple çalışır.
- Test verileri sentetiktir; gerçek müşteri/hesap verisi kullanılmaz.

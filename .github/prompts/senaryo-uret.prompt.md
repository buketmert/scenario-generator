---
name: senaryo-uret
description: Jira kartının XML'inden veya --from-jira ile REST'ten okunarak uçtan uca test senaryoları üretir; belirsizlikleri çoktan seçmeli sorar, seçilenleri Jira'da Test Senaryosu kartı olarak açtırır.
argument-hint: XML dosyasının yolu (ör. test-scenarios/girdi/ESUBE-2041.xml) ya da kart anahtarı (ör. MYTKM7-6655; jira-ayar.json ve JIRA_PAT kuruluysa)
agent: Senaryo Üretici
---

Verilen Jira kartından uçtan uca test senaryoları üret. Senaryo Üretici
agent'ının akışını uygula: kartı `parse_jira_xml.py --yazdir` ile ayrıştır
(XML dosyası verildiyse; yapıştırıldıysa önce `test-scenarios/girdi/_girdi.xml`
dosyasına yaz), kart anahtarı verildiyse `parse_jira_xml.py --from-jira
<KART-ANAHTARI> --yazdir` ile REST'ten oku; senaryoyu etkileyen soruları
("Bilinmiyor" seçeneği de olacak) sohbette tek seferde sor ve yanıt bekle,
JSON'u bir kerede yaz,
`render_gherkin.py --all --sunucu --open` ile seçim ekranının adresini al ve
o adresi sohbetin tarayıcı aracıyla VS Code içinde aç (dış tarayıcı veya yeni
pencere açma).

Girdi verilmediyse yolunu veya kart anahtarını iste. Kart anahtarıyla
`--from-jira` çalışamazsa ([HATA] Jira ayarı yok / jeton yok) kullanıcıdan XML
dışa aktarımını iste ve SKILL.md'deki bir kerelik Jira kurulumunu kısaca ver.

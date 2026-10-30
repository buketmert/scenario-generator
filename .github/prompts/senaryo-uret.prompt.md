---
name: senaryo-uret
description: Jira kartının XML'inden uçtan uca test senaryoları üretir; belirsizlikleri çoktan seçmeli sorar, seçilenleri Jira'da Test Senaryosu kartı olarak açtırır.
argument-hint: XML dosyasının yolu (ör. test-scenarios/girdi/ESUBE-2041.xml)
agent: Senaryo Üretici
---

Verilen Jira kartı XML'inden uçtan uca test senaryoları üret. Senaryo Üretici
agent'ının akışını uygula: XML'i `parse_jira_xml.py --yazdir` ile ayrıştır,
senaryoyu etkileyen soruları tek seferde sor, JSON'u bir kerede yaz,
`render_gherkin.py --all --sunucu --open` ile seçim ekranını aç.

XML dosyası verilmediyse yolunu iste.

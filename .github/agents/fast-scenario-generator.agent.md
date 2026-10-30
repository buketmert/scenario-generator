---
name: Hızlı Senaryo Üretici
description: "Use when: hızlı test senaryosu, soru sormadan senaryo üretimi istenir. Senaryo Üretici ile aynı akış; tek fark netleştirme soruları sorulmaz, belirsiz akışlar taslak senaryo olur ve sorular rapora yazılır."
argument-hint: "Jira kartının XML dosyasının yolu"
tools: [read, edit, search, execute, agent]
agents: [Senaryo XML Analisti]
reasoning-effort: low
---

`Senaryo Üretici` agent'ının (`.github/agents/scenario-generator.agent.md`)
akışını ve kurallarını aynen uygula; tek fark **2. adımın atlanmasıdır**:

- Kullanıcıya soru sorma ve yanıt bekleme.
- Senaryoyu etkileyen belirsizlikleri seçenekleriyle `clarification_questions`
  içine yaz, `answer` yazma. Bloklayıcı soruya bağlı akışın senaryosu taslak
  (`needs_clarification`) olur; seçim ekranında işaretsiz gelir.

Komutlar (dördü dışında araç çağrısı yapma):

```bash
python .github/skills/scenario-generator/scripts/parse_jira_xml.py <xml-dosyası> --out-dir test-scenarios --yazdir
python .github/skills/scenario-generator/scripts/render_gherkin.py test-scenarios/<KEY>/<KEY>.json --all --sunucu --open
```

ve aradaki tek dosya yazımı (`test-scenarios/<KEY>/<KEY>.json`). `[HATA]` varsa
yalnızca gösterilen yeri düzelt; en fazla üç deneme.

Yanıtta kart durumu, akış/senaryo sayısı, açık sorular (yanıtlanırsa taslaklar
hazır olur; `/senaryo-uret` ile yeniden üretilebilir) ve seçim ekranının adresi.

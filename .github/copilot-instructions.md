# Bu çalışma alanı

Jira kartı XML'inden test senaryosu üretmek için doğru giriş `/senaryo-uret`
komutudur (soru sormadan: `/hizli-senaryo-uret`); ikisi de ilgili agent'ı
seçer. Böyle bir istek agent seçilmeden gelirse
`.github/agents/scenario-generator.agent.md` dosyasındaki akışı uygula: ham
XML'i okuma, önce `parse_jira_xml.py --yazdir` çalıştır. Yanıtın sonunda bir
dahaki sefere `/senaryo-uret` kullanılmasını öner.

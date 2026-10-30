# Bu çalışma alanı

Jira kartı XML'inden test senaryosu üretmek için tek ve önerilen giriş
`/senaryo-uret` komutudur. Bu çalışma alanında ayrı bir "hızlı senaryo"
sekmesi yoktur; aynı agent içinde akış tek ve nettir. Böyle bir istek agent
seçilmeden gelirse `.github/agents/scenario-generator.agent.md` dosyasındaki
akışı uygula: ham XML'i okuma, önce `parse_jira_xml.py --yazdir`
çalıştır. Yanıtın sonunda bir dahaki sefere `/senaryo-uret`
kullanılmasını öner.

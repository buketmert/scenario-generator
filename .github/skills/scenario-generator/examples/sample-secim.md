# Jira'ya aktarılacak senaryolar — ESUBE-2041

**Kart:** E-Şube'den EFT ile para gönderme

Jira'ya Test kaydı olarak eklenecek senaryoların kutusunu işaretleyin (`[x]`),
eklenmeyecekleri boş bırakın (`[ ]`). Taslak senaryolar bloklayıcı soru
yanıtlanana kadar işaretsiz gelir. Sıra koşum sırasıdır: önce `@smoke`, sonra
risk seviyesi.

- [x] 1. TS-ESUBE-2041-001 · yüksek · pozitif · hazır · @smoke — Geçerli bilgilerle gönderilen EFT başarıyla tamamlanır ve dekont numarası gösterilir
- [x] 2. TS-ESUBE-2041-002 · yüksek · pozitif · hazır — Tutar limitlerde veya limitlerin hemen içinde olduğunda EFT başarıyla tamamlanır
- [x] 3. TS-ESUBE-2041-003 · yüksek · negatif · hazır — Tutar limit dışında olduğunda EFT başlatılmaz ve limit uyarısı gösterilir
- [x] 4. TS-ESUBE-2041-005 · yüksek · negatif · hazır — IBAN TR ile başlamadığında veya 26 karakterden kısa olduğunda EFT başlatılmaz
- [ ] 5. TS-ESUBE-2041-006 · yüksek · negatif · taslak (Q-01) — IBAN 26 karakterden uzun girildiğinde Geçersiz IBAN mesajı gösterilir
- [x] 6. TS-ESUBE-2041-007 · yüksek · negatif · hazır — Gönder butonuna art arda iki kez basıldığında tek EFT işlemi oluşur
- [x] 7. TS-ESUBE-2041-004 · orta · negatif · hazır — Zorunlu alanlardan biri boş bırakıldığında EFT başlatılmaz ve zorunlu alan mesajı gösterilir

Aktarım: `python <skill-klasörü>/scripts/jira_export.py <KEY>.json <KEY>-secim.md <KEY>-jira.csv`

# Jira'ya aktarılacak senaryolar — ESUBE-2041

**Kart:** E-Şube'den EFT ile para gönderme

Test Senaryosu kartına dönüştürülecek senaryoların kutusunu işaretleyin (`[x]`),
dönüştürülmeyecekleri boş bırakın (`[ ]`). Taslak senaryolar bloklayıcı soru
yanıtlanana kadar işaretsiz gelir. Sıra koşum sırasıdır: önce `@smoke`, sonra
risk seviyesi.

- [x] 1. TS-ESUBE-2041-001 · ana akış · yüksek · pozitif · hazır · @smoke — Geçerli bilgilerle gönderilen EFT tamamlanır ve dekont numarası gösterilir
- [x] 2. TS-ESUBE-2041-002 · alternatif akış · yüksek · negatif · hazır — Gönder butonuna art arda iki kez basıldığında tek EFT işlemi oluşur
- [x] 3. TS-ESUBE-2041-003 · hata akışı · yüksek · negatif · hazır — Tutar limit dışında olduğunda EFT başlatılmaz ve limit uyarısı gösterilir
- [x] 4. TS-ESUBE-2041-005 · hata akışı · yüksek · negatif · hazır — IBAN TR ile başlamadığında veya 26 karakterden kısa olduğunda EFT başlatılmaz
- [x] 5. TS-ESUBE-2041-006 · hata akışı · yüksek · negatif · hazır — IBAN alanına 26 karakterden fazlası girilemez
- [x] 6. TS-ESUBE-2041-004 · hata akışı · orta · negatif · hazır — Zorunlu alanlardan biri boş bırakıldığında EFT başlatılmaz ve zorunlu alan mesajı gösterilir

Ekrandan seçim: `<KEY>-secim.html`.

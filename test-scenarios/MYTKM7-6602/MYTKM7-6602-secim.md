# Jira'ya aktarılacak senaryolar — MYTKM7-6602

**Kart:** Onay Şemasına İş Havuzu İşlemleri İçin Atama Geçmişi Eklenmesi

Test Senaryosu kartına dönüştürülecek senaryoların kutusunu işaretleyin (`[x]`),
dönüştürülmeyecekleri boş bırakın (`[ ]`). Taslak senaryolar bloklayıcı soru
yanıtlanana kadar işaretsiz gelir. Sıra koşum sırasıdır: önce `@smoke`, sonra
risk seviyesi.

- [x] 1. TS-MYTKM7-6602-001 · ana akış · orta · pozitif · hazır · @smoke — İş Havuzu onayında Atama Geçmişi sekmesi doğru sırayla görüntülenir ve atama logları Small Version tabloda listelenir
- [x] 2. TS-MYTKM7-6602-002 · hata akışı · orta · negatif · hazır — İş Havuzu dışındaki standart onay işleminde Atama Geçmişi sekmesi görüntülenmez
- [x] 3. TS-MYTKM7-6602-003 · hata akışı · düşük · negatif · hazır — Atama geçmişi olmayan İş Havuzu işleminde bilgilendirme mesajı gösterilir

Aktarım: `python <skill-klasörü>/scripts/jira_export.py <KEY>.json <KEY>-secim.md <KEY>-jira.csv`

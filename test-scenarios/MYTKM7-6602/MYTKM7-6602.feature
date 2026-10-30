# language: tr
# Kaynak: MYTKM7-6602 — Onay Şemasına İş Havuzu İşlemleri İçin Atama Geçmişi Eklenmesi
# Test ortamı: ZB TEST ortamı, İnternet kanalı, şube personeli/Genel Müdürlük kullanıcısı; sürüm 06.11.2026 Kasım Aylık Yaygınlaştırma
# Kart durumu: partial | Açık sorular: Q-01, Q-02, Q-03
# Bu dosya scenario-generator çıktısından üretilmiştir.

@MYTKM7-6602 @onay-semasi @is-havuzu @dys
Özellik: Onay Şemasına İş Havuzu İşlemleri İçin Atama Geçmişi Eklenmesi
  Şube Personeli/Genel Müdürlük Kullanıcısı, İş Havuzu onay işlemlerinde Onay Şema Bileşeni içinde Atama Geçmişi sekmesini görür; işlemin atama logları Small Version tablo formatında listelenir.

  Geçmiş:
    Diyelim ki Şube Personeli/Genel Müdürlük Kullanıcısı olarak onay sistemine giriş yapmışım

  @TS-MYTKM7-6602-001 @pozitif @smoke
  Senaryo: İş Havuzu onayında Atama Geçmişi sekmesi doğru sırayla görüntülenir ve atama logları Small Version tabloda listelenir
    # Akış (ana akış): Onay sistemine şube personeli girişi → İş Havuzu sekmesinden atama aksiyonu alınmış onay bekleyen işlemi açma → Onay Akışı ile Mesajlaşma arasında Atama Geçmişi sekmesi görüntülenir → sekmede işleme ait atama logları Small Version tablo formatında listelenir
    # Kaynak: AC-01, AC-02, AC-03, BR-01 | COND-01, COND-02, COND-03 | UC-ANA
    # Not: Kullanıcı Hikâyesi rolleri ile 'Kullanıcı Profili: Anonim' değeri çelişiyor (CF-01, Q-02); senaryo Kullanıcı Hikâyesi rollerini esas alır.
    # Not: QA kanıtı (C-04): aynı davranış ZB TEST ortamında Kullanıcı:SOZMEN işlemiyle gözlemlenmiştir.
    Eğer ki Eğer ki Onay Şema Bileşeni'nde İş Havuzu sekmesinden atama aksiyonu alınmış onay bekleyen bir işlemi açarsam
    O zaman "Onay Akışı" ve "Mesajlaşma" sekmeleri arasında "Atama Geçmişi" sekmesini görürüm
    Ve sekmelerin "Onay Akışı" → "Atama Geçmişi" → "Mesajlaşma" sırasıyla dizildiğini görürüm
    Eğer ki Eğer ki "Atama Geçmişi" sekmesine tıklarsam
    O zaman işleme ait atama loglarının tarih, kullanıcı ve işlem tipi bilgileriyle "Small Version" tablo formatında listelendiğini görürüm

  @TS-MYTKM7-6602-002 @negatif
  Senaryo: İş Havuzu dışındaki standart onay işleminde Atama Geçmişi sekmesi görüntülenmez
    # Akış (hata akışı): Ana akış; İş Havuzu dışındaki standart onay işlemi açılır → Atama Geçmişi sekmesi görüntülenmez
    # Kaynak: AC-01 | COND-01 | UC-HATA-SEKMEYOK
    # Not: QA kanıtı (C-04): standart onay işlemlerinde sekmenin gelmediği teyit edilmiştir.
    Eğer ki Eğer ki İş Havuzu dışındaki standart bir onay işlemini açarsam
    O zaman işlem detayında "Atama Geçmişi" sekmesi görüntülenmez

  @TS-MYTKM7-6602-003 @negatif
  Senaryo: Atama geçmişi olmayan İş Havuzu işleminde bilgilendirme mesajı gösterilir
    # Akış (hata akışı): Ana akış; İş Havuzu sekmesinden hiç aksiyon alınmamış onay bekleyen işlemi açma → Atama Geçmişi sekmesi görüntülenir → sekmede bilgilendirme mesajı gelir, log tablosu yok
    # Kaynak: AC-04 | COND-04 | UC-HATA-BOSS
    # Not: Kartta mesaj metni '"Görüntülemecek atama geçmişi bulunmamaktadır" benzeri' diye açık bırakıldığı için beklenen metin tırnaksız yazılmıştır; birebir metin Q-01 yanıtıyla senaryoya işlenecektir.
    # Not: QA kanıtı (C-04): havuzda hiç aksiyon alınmamış işlem (Kullanıcı:DOGOZKAN) örneğiyle doğrulanmıştır.
    Eğer ki Eğer ki İş Havuzu sekmesinden hiç atama aksiyonu alınmamış onay bekleyen bir işlemi açarsam
    O zaman "Atama Geçmişi" sekmesini görürüm
    Eğer ki Eğer ki "Atama Geçmişi" sekmesine tıklarsam
    O zaman işleme ait atama geçmişi bulunmadığına dair bir bilgilendirme mesajı görüntülenir

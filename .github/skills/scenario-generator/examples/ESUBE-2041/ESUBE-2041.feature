# language: tr
# Kaynak: ESUBE-2041 — E-Şube'den EFT ile para gönderme
# Test ortamı: TEST ortamı, E-Şube web, Chrome, sürüm 4.12, bireysel müşteri
# Kart durumu: partial | Açık sorular: Q-02, Q-03
# Bu dosya scenario-generator çıktısından üretilmiştir.

@ESUBE-2041 @para-transferleri @eft
Özellik: EFT Para Transferi
  Bireysel müşteri olarak E-Şube'den başka bankadaki bir hesaba EFT ile para gönderebilmeliyim.

  Geçmiş:
    Diyelim ki E-Şube'ye bireysel müşteri olarak giriş yapmışım
    Ve Para Transferleri menüsünden EFT ekranını açmışım
    Ve Gönderici Hesap listesinden vadesiz TL hesabımı seçmişim

  @TS-ESUBE-2041-001 @pozitif @smoke
  Senaryo Taslağı: Geçerli bilgilerle gönderilen EFT tamamlanır ve dekont numarası gösterilir
    # Akış (ana akış): E-Şube'ye bireysel müşteri girişi → Para Transferleri > EFT → Gönderici Hesap seçimi → Alıcı IBAN, Alıcı Adı Soyadı ve Tutar girişi → Gönder → başarı mesajı ve dekont numarası
    # Kaynak: AC-01, BR-02, AC-02, AC-03, BR-01, AC-04, UI-01 | COND-01, COND-02, COND-03, COND-04 | UC-ANA, EP-REQ-V, EP-IBAN-V, BVA-IBAN-26, EP-AMT-V, BVA-AMT-1.00, BVA-AMT-1.01, BVA-AMT-49999.99, BVA-AMT-50000.00
    # Son koşul: Her veri satırı gönderici test hesabından ayrı bir EFT işlemi oluşturur; satırlar art arda koşulacaksa toplam tutar kadar bakiye hazırlanmalıdır.
    Diyelim ki gönderici hesabımda en az "<tutar>" TL kullanılabilir bakiye var
    Eğer ki Alıcı IBAN alanına "<iban>" yazarsam
    Ve Alıcı Adı Soyadı alanına "<ad_soyad>" yazarsam
    Ve Tutar alanına "<tutar>" yazarsam
    Ve Gönder butonuna basarsam
    O zaman "İşleminiz başarıyla gerçekleştirilmiştir" mesajını görürüm
    Ve ekranda işlemin dekont numarasını görürüm

    Örnekler:
      | durum                             | iban                       | ad_soyad   | tutar     |
      | Tipik tutar: 1.000,00             | TR330006100519786457841326 | Test Alıcı | 1.000,00  |
      | Alt sınır: 1,00                   | TR330006100519786457841326 | Test Alıcı | 1,00      |
      | Alt sınırın hemen üstü: 1,01      | TR330006100519786457841326 | Test Alıcı | 1,01      |
      | Üst sınırın hemen altı: 49.999,99 | TR330006100519786457841326 | Test Alıcı | 49.999,99 |
      | Üst sınır: 50.000,00              | TR330006100519786457841326 | Test Alıcı | 50.000,00 |

  @TS-ESUBE-2041-002 @negatif
  Senaryo: Gönder butonuna art arda iki kez basıldığında tek EFT işlemi oluşur
    # Akış (alternatif akış): Ana akış; Gönder butonuna art arda iki kez basılır → tek başarı mesajı ve tek dekont numarası
    # Kaynak: AC-04 | COND-04 | UC-ALT-CIFTGONDER, EG-01
    # Not: Beklenen sonuç AC-04'e dayanır: tek gönderim için tek başarı mesajı ve tek dekont numarası.
    # Son koşul: Gönderici test hesabından EFT işlemi oluşur. Senaryo tekrar koşulmadan önce bakiyenin ön koşuldaki tutarı karşıladığı kontrol edilmelidir.
    # Veri: Geçerli bilgiler, tutar 1.000,00
    Diyelim ki gönderici hesabımda en az "1.000,00" TL kullanılabilir bakiye var
    Eğer ki Alıcı IBAN alanına "TR330006100519786457841326" yazarsam
    Ve Alıcı Adı Soyadı alanına "Test Alıcı" yazarsam
    Ve Tutar alanına "1.000,00" yazarsam
    Ve Gönder butonuna aralarında bekleme olmadan iki kez basarsam
    O zaman "İşleminiz başarıyla gerçekleştirilmiştir" mesajını bir kez görürüm
    Ve ekranda tek bir dekont numarası görürüm

  @TS-ESUBE-2041-003 @negatif
  Senaryo Taslağı: Tutar limit dışında olduğunda EFT başlatılmaz ve limit uyarısı gösterilir
    # Akış (hata akışı): Ana akış; Tutar limit dışında → "Tutar 1,00 TL ile 50.000,00 TL arasında olmalıdır" mesajı, EFT başlatılmaz
    # Kaynak: AC-03, BR-01, UI-02 | COND-03 | UC-HATA-LIMIT, BVA-AMT-0.99, BVA-AMT-50000.01, EP-AMT-I1, EP-AMT-I2
    # Not: Bakiye ön koşulu, yetersiz bakiye kontrolünün limit kontrolünü maskelememesi için tutar kadar olmalıdır.
    Diyelim ki gönderici hesabımda en az "<tutar>" TL kullanılabilir bakiye var
    Eğer ki Alıcı IBAN alanına "<iban>" yazarsam
    Ve Alıcı Adı Soyadı alanına "<ad_soyad>" yazarsam
    Ve Tutar alanına "<tutar>" yazarsam
    Ve Gönder butonuna basarsam
    O zaman "Tutar 1,00 TL ile 50.000,00 TL arasında olmalıdır" mesajını görürüm
    Fakat işlem başlatılmaz

    Örnekler:
      | durum                       | iban                       | ad_soyad   | tutar     |
      | Alt sınırın altı: 0,99      | TR330006100519786457841326 | Test Alıcı | 0,99      |
      | Üst sınırın üstü: 50.000,01 | TR330006100519786457841326 | Test Alıcı | 50.000,01 |

  @TS-ESUBE-2041-004 @negatif
  Senaryo Taslağı: Zorunlu alanlardan biri boş bırakıldığında EFT başlatılmaz ve zorunlu alan mesajı gösterilir
    # Akış (hata akışı): Ana akış; zorunlu alanlardan biri boş → "Lütfen zorunlu alanları doldurunuz" mesajı, EFT başlatılmaz
    # Kaynak: AC-01, BR-02, UI-01 | COND-01 | UC-HATA-ZORUNLU, EP-IBAN-EMPTY, EP-NAME-EMPTY, EP-AMT-EMPTY
    # Not: Örnekler tablosundaki boş hücre, o alana hiçbir şey yazılmayacağı anlamına gelir.
    Diyelim ki gönderici hesabımda en az "1.000,00" TL kullanılabilir bakiye var
    Eğer ki Alıcı IBAN alanına "<iban>" yazarsam
    Ve Alıcı Adı Soyadı alanına "<ad_soyad>" yazarsam
    Ve Tutar alanına "<tutar>" yazarsam
    Ve Gönder butonuna basarsam
    O zaman "Lütfen zorunlu alanları doldurunuz" mesajını görürüm
    Fakat işlem başlatılmaz

    Örnekler:
      | durum                | iban                       | ad_soyad   | tutar    |
      | Alıcı IBAN boş       |                            | Test Alıcı | 1.000,00 |
      | Alıcı Adı Soyadı boş | TR330006100519786457841326 |            | 1.000,00 |
      | Tutar boş            | TR330006100519786457841326 | Test Alıcı |          |

  @TS-ESUBE-2041-005 @negatif
  Senaryo Taslağı: IBAN TR ile başlamadığında veya 26 karakterden kısa olduğunda EFT başlatılmaz
    # Akış (hata akışı): Ana akış; Alıcı IBAN TR ile başlamıyor veya 26 karakterden kısa → "Geçersiz IBAN" mesajı, EFT başlatılmaz
    # Kaynak: AC-02 | COND-02 | UC-HATA-IBAN, EP-IBAN-I1, EP-IBAN-I2, BVA-IBAN-25
    Diyelim ki gönderici hesabımda en az "<tutar>" TL kullanılabilir bakiye var
    Eğer ki Alıcı IBAN alanına "<iban>" yazarsam
    Ve Alıcı Adı Soyadı alanına "<ad_soyad>" yazarsam
    Ve Tutar alanına "<tutar>" yazarsam
    Ve Gönder butonuna basarsam
    O zaman "Geçersiz IBAN" mesajını görürüm
    Fakat işlem başlatılmaz

    Örnekler:
      | durum                             | iban                       | ad_soyad   | tutar    |
      | TR ile başlamıyor, uzunluk 26     | DE330006100519786457841326 | Test Alıcı | 1.000,00 |
      | Uzunluk sınırın altı: 25 karakter | TR33000610051978645784132  | Test Alıcı | 1.000,00 |

  @TS-ESUBE-2041-006 @negatif
  Senaryo: IBAN alanına 26 karakterden fazlası girilemez
    # Akış (hata akışı): Ana akış; Alıcı IBAN alanına 26 karakterden uzun değer yazılır → 27. karakter girilemez, mesaj gösterilmez (Q-01 yanıtı)
    # Kaynak: AC-02, CN-01, BR-03 | COND-02 | UC-HATA-IBANUZUN, EP-IBAN-I3, BVA-IBAN-27
    # Veri: Uzunluk sınırın üstü: 27 karakter
    Eğer ki Alıcı IBAN alanına "TR3300061005197864578413261" yazarsam
    O zaman Alıcı IBAN alanında yalnızca ilk 26 karakter görünür
    Fakat hata mesajı gösterilmez

# JSON Yazım Kılavuzu (yalın JSON)

`test-scenarios/<KEY>/<KEY>.json` dosyasına **yalnızca muhakeme gerektiren
alanları** yaz. Gerisini `render_gherkin.py` doldurur ve denetler. Bu dosya
`output-schema.json` ve örnek JSON'un yerine okunur; onları okuma (script
şemaya göre doğrular ve hatayı söyler).

## Script'in doldurduğu alanlar — yazma

| Alan | Nereden gelir |
|---|---|
| `source` | `<KEY>-kart.json` (XML'den) |
| `card_inventory` alanları, ekler, bağlı kartlar, dış bağlantılar | `<KEY>-kart.json`; yalnızca **farklıysa** aynı kimlikle yaz (ör. kullanıcı eki dosya olarak verdi → `processed`) |
| Yorumların `author` ve `date` alanları | `<KEY>-kart.json` |
| Kabul kriteri alanındaki `AC-NN` metinleri | `<KEY>-kart.json`; metni tekrar yazma, yalnızca değişen alanı yaz (ör. `testability`) |
| `generated_at`, `readiness.status`, `checks[].criterion` | Hesaplanır |
| `test_conditions[].risk.level` | olasılık × etki |
| `test_scenarios[].priority`, `status` | Bağlı koşulların riski; açık bloklayıcı soru varsa `needs_clarification` |
| `coverage_summary` | Senaryolardan hesaplanır. Yalnızca kapsanmayan öğe varsa gerekçesini yaz |

Yazdığın bir değer hesaplananla çelişirse hesaplanan kullanılır ve uyarı
verilir; JSON'u bunun için yeniden yazma.

## Yazdığın iskelet

```json
{
  "schema_version": "3.1.0",
  "card_inventory": {
    "comments": [
      {"id": "C-01", "role": "developer", "status": "used", "summary": "IBAN alanı 26 karakterle sınırlı.", "basis_ids": ["CN-01"]}
    ]
  },
  "test_environment": {
    "summary": "TEST, E-Şube web, Chrome, bireysel müşteri",
    "details": [{"aspect": "ortam", "value": "TEST", "source": {"field": "environment"}}]
  },
  "readiness": {
    "summary": "Kart test edilebilir; yetersiz bakiye davranışı tanımsız.",
    "checks": [
      {"id": "R1", "result": "pass", "finding": "Kullanıcı hikâyesi var."}
    ],
    "clarification_questions": [
      {"id": "Q-01", "question": "26 karakterden uzun IBAN'da ne olmalı?", "related_check_ids": ["R7"],
       "related_basis_ids": ["AC-02", "CN-01"], "related_conflict_ids": ["CF-01"], "blocking": true,
       "addressed_to": "product_owner",
       "options": [{"id": "a", "text": "27. karakter girilemez, mesaj gösterilmez (C-01)"},
                   {"id": "b", "text": "27. karakter girilebilir ve \"Geçersiz IBAN\" gösterilir (AC-02)"}],
       "answer": {"choice": "a"}}
    ]
  },
  "test_basis": {"items": [
    {"id": "AC-02", "testability": "partially_testable", "issue": "Uzunluk aşımındaki davranış çelişkili."},
    {"id": "BR-01", "kind": "business_rule", "text": "<kaynaktaki metin, değiştirmeden>",
     "source": {"field": "description"}, "format": "rule", "testability": "testable"},
    {"id": "BR-02", "kind": "business_rule", "text": "27. karakter girilemez, mesaj gösterilmez (C-01)",
     "source": {"field": "clarification", "ref": "Q-01"}, "format": "rule", "testability": "testable", "updates": ["AC-02"]}
  ]},
  "conflicts": [],
  "test_conditions": [
    {"id": "COND-01", "description": "Başarılı EFT", "basis_ids": ["AC-04"], "techniques": ["use_case_based"],
     "risk": {"likelihood": 2, "impact": 3, "rationale": "Para çıkışı."}}
  ],
  "coverage_items": [
    {"id": "UC-ANA", "technique": "use_case_based", "flow_type": "main", "test_condition_ids": ["COND-01"],
     "description": "Giriş → EFT ekranı → bilgiler → Gönder → başarı mesajı ve dekont"}
  ],
  "feature": {"name": "EFT Para Transferi", "tags": ["@eft"],
              "background": [{"keyword": "given", "text": "E-Şube'ye bireysel müşteri olarak giriş yapmışım"}]},
  "test_scenarios": [
    {"id": "TS-ESUBE-2041-001", "title": "Geçerli bilgilerle gönderilen EFT tamamlanır", "objective": "…",
     "scenario_type": "positive", "test_level": "system", "test_type": "functional",
     "techniques": ["use_case_based"],
     "traceability": {"basis_ids": ["AC-04"], "test_condition_ids": ["COND-01"], "coverage_item_ids": ["UC-ANA"]},
     "steps": [{"keyword": "when", "text": "Gönder butonuna basarsam"},
               {"keyword": "then", "text": "\"İşleminiz başarıyla gerçekleştirilmiştir\" mesajını görürüm"}],
     "test_data": {"parameters": [], "data_sets": []},
     "tags": ["@smoke"]}
  ],
  "assumptions": [],
  "out_of_scope": []
}
```

`readiness.checks` R1–R10'un **hepsini** içerir (örnekte yalnızca R1
gösterildi).

## Sorular ve yanıtlar

- Her soruya kartta geçen yorumlardan türeyen 2–4 seçenek (`options`, `a`–`f`)
  yaz. "Bilinmiyor" ve "Diğer" seçenekleri soru sorulurken eklenir; JSON'a
  yazılmaz.
- Kullanıcının yanıtı `answer`: seçenek harfi (`{"choice": "a"}`), kendi
  metni (`{"choice": "other", "text": "…"}`) veya bilinmiyor
  (`{"choice": "unknown"}` — soru açık kalır, senaryo taslak olur).
- Yanıt davranışı belirliyorsa kaynağı `{"field": "clarification", "ref": "Q-NN"}`
  olan bir `BR` ekle; metni seçilen yanıtın metnidir. Yanıtın çözdüğü
  çelişkiyi `resolved_by_later_decision` yap ve `resolved_by` ile bu BR'ye bağla.
- Yanıtlanan soruyu senaryonun `open_question_ids` listesinde bırakabilirsin
  (izlenebilirlik); yanıtlandığı için senaryo taslak sayılmaz.

## Kapsanmayan öğe

Bir kapsam öğesi hiçbir senaryoda değilse gerekçesini yaz; yoksa script hata
verir:

```json
"coverage_summary": {"uncovered_items": [
  {"coverage_item_id": "DT-R4", "reason": "Sonuç kartta tanımsız", "question_id": "Q-02"}
]}
```

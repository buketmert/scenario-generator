#!/usr/bin/env python3
"""scenario-generator JSON çıktısını tamamlar ve doğrular; manuel test için
Türkçe Gherkin (.feature) dosyası, kart yeterlilik raporu (.md), seçim listesi
(.md) ve senaryoların ekrandan seçildiği sayfayı (.html) üretir.

Kullanım:
    python scripts/render_gherkin.py test-scenarios/KEY/KEY.json --all --sunucu --open   # hepsi + Jira'da aç ekranı
    python scripts/render_gherkin.py test-scenarios/KEY/KEY.json --all --open   # hepsi + durağan ekran
    python scripts/render_gherkin.py cikti.json cikti.feature --report rapor.md --selection secim.md --html secim.html
    python scripts/render_gherkin.py cikti.json --check            # yalnızca doğrula

Tamamlama: aynı klasörde <KEY>-kart.json varsa (parse_jira_xml.py üretir)
source, card_inventory ve kabul kriterleri oradan alınır. Risk seviyesi,
senaryo önceliği ve durumu, kart durumu ve kapsam özeti hesaplanır; LLM'in
bunları yazması gerekmez. Yazılmış ve farklıysa hesaplanan geçerlidir (uyarı).

Seçim listesi varsa işaretler korunur; yalnızca yeni senaryolar ve başlığı
değişen senaryolar varsayılana (hazır: işaretli, taslak: işaretsiz) döner.

Çıkış kodu: 0 = hata yok, 1 = doğrulama hatası, 2 = kullanım/dosya hatası.
"""

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "references" / "output-schema.json"
SCHEMA_VERSION = "3.1.0"
COVERAGE_ORDER = ["not_covered", "partially_covered", "covered"]

KEYWORDS = {"given": "Diyelim ki", "when": "Eğer ki", "then": "O zaman", "and": "Ve", "but": "Fakat"}
PHASE = {"given": 1, "when": 2, "then": 3}
PARAM_RE = re.compile(r"<([a-zçğıöşü][a-zçğıöşü0-9_]*)>")
QUOTE_RE = re.compile(r'"([^"]+)"')
RISK_ORDER = ["low", "medium", "high", "critical"]
CHECK_IDS = [f"R{i}" for i in range(1, 11)]
CHECK_CRITERIA = {
    "R1": "Amaç: ne, kimin için, neden", "R2": "Test edilecek gereksinim var",
    "R3": "Gereksinimler test edilebilir", "R4": "Veri kuralları", "R5": "Hata ve olumsuz durumlardaki davranış",
    "R6": "Roller, yetkiler, ön koşullar", "R7": "Alanlar arası tutarlılık", "R8": "Kapsam sınırı",
    "R9": "Test ortamı", "R10": "Ekler ve bağlantılar işlendi",
}
KIND_PREFIX = {"AC": "acceptance_criterion", "BR": "business_rule", "UI": "ui_detail", "CN": "constraint"}
TECHNIQUE_PREFIX = {
    "UC": "use_case_based",
    "EP": "equivalence_partitioning",
    "BVA": "boundary_value_analysis",
    "DT": "decision_table",
    "ST": "state_transition",
    "EG": "error_guessing",
    "CL": "checklist_based",
}
LABELS = {
    "pass": "geçti", "partial": "kısmi", "fail": "kaldı",
    "ready": "hazır", "not_ready": "yetersiz",
    "used": "kullanıldı", "empty": "boş", "not_provided": "sağlanmadı", "not_relevant": "ilgisiz",
    "processed": "işlendi", "not_readable": "okunamadı", "superseded": "geçersiz kılındı",
    "not_accessible": "erişilemedi", "accessed": "erişildi",
    "resolved_by_later_decision": "sonraki kararla çözüldü", "unresolved": "çözülmedi",
    "covered": "kapsandı", "partially_covered": "kısmen", "not_covered": "kapsanmadı",
    "product_owner": "ürün sahibi", "business_analyst": "iş analisti", "developer": "geliştirici",
    "tester": "test uzmanı", "designer": "tasarımcı", "other": "diğer", "unknown": "bilinmiyor",
    "critical": "kritik", "high": "yüksek", "medium": "orta", "low": "düşük",
    "positive": "pozitif", "negative": "negatif", "needs_clarification": "taslak",
    "main": "ana akış", "alternative": "alternatif akış", "exception": "hata akışı",
}
# Seçim listesinin bir satırı: "- [x] 3. TS-ESUBE-2041-003 · yüksek · ... — Başlık"
SELECTION_RE = re.compile(r"^\s*[-*]\s*\[([ xX])\]\s*(?:\d+\.\s*)?(TS-[A-Z][A-Z0-9]+-[0-9]+-[0-9]{3})\b(.*)$")


def tr(value):
    return LABELS.get(value, value)


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, where, msg):
        self.errors.append(f"[HATA] {where}: {msg}")

    def warn(self, where, msg):
        self.warnings.append(f"[UYARI] {where}: {msg}")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def risk_level(likelihood, impact):
    product = likelihood * impact
    if product == 9:
        return "critical"
    if product == 6:
        return "high"
    if product >= 3:
        return "medium"
    return "low"


def substitute(text, values):
    return PARAM_RE.sub(lambda m: "" if values.get(m.group(1)) is None else str(values[m.group(1)]), text)


def instances(sc):
    """Her veri seti için değer sözlüğü; veri seti yoksa tek boş sözlük."""
    return [ds["values"] for ds in sc["test_data"]["data_sets"]] or [{}]


def is_answered(q):
    """Kullanıcı soruyu yanıtladı mı? 'unknown' (bilinmiyor) yanıt sayılmaz, soru açık kalır."""
    return q.get("answer", {}).get("choice") not in (None, "unknown")


# ------------------------------------------------------------------ tamamlama

def load_card(input_path, explicit=None):
    """parse_jira_xml.py'nin ürettiği <KEY>-kart.json; yoksa None."""
    path = Path(explicit) if explicit else Path(input_path).with_name(Path(input_path).stem + "-kart.json")
    if path.exists():
        return load_json(path)
    if explicit:
        raise OSError(f"kart dosyası yok: {path}")
    return None


# ------------------------------------------------------------------ yalın biçim

# Yalın biçimde LLM yalnızca senaryoları ve soruları yazar (output-template.md);
# izlenebilirlik zinciri (koşul, kapsam öğesi, risk) buradan türetilir.
LEAN_KEY = "senaryolar"
STEP_PREFIXES = [("diyelim ki", "given"), ("eğer ki", "when"), ("eger ki", "when"), ("eğer", "when"),
                 ("o zaman", "then"), ("ve", "and"), ("fakat", "but"), ("ama", "but")]
FLOWS = {"ana": "main", "alternatif": "alternative", "hata": "exception"}
PRIORITY_RISK = {"kritik": (3, 3), "yüksek": (3, 2), "yuksek": (3, 2), "orta": (2, 2), "düşük": (1, 1), "dusuk": (1, 1)}


def is_lean(doc):
    return isinstance(doc, dict) and LEAN_KEY in doc


def parse_step(line, where, rep):
    """'Eğer ki Gönder butonuna basarsam' → {"keyword": "when", "text": "Gönder butonuna basarsam"}"""
    text = str(line).strip()
    low = text.lower()
    for prefix, keyword in STEP_PREFIXES:
        if low.startswith(prefix + " "):
            return {"keyword": keyword, "text": text[len(prefix):].strip()}
    rep.error(where, f"adım Diyelim ki / Eğer ki / O zaman / Ve / Fakat ile başlamalı: \"{text[:60]}\"")
    return {"keyword": "and", "text": text or "?"}


def lean_question(q, n, rep):
    qid = q.get("id") or f"Q-{n:02d}"
    options = [{"id": chr(ord("a") + i), "text": str(t)} for i, t in enumerate(q.get("secenekler", [])[:6])]
    out = {"id": qid, "question": q.get("soru", ""), "related_check_ids": ["R3"],
           "blocking": bool(q.get("bloklayici", True))}
    if options:
        out["options"] = options
    yanit = q.get("yanit")
    if yanit not in (None, ""):
        y = str(yanit).strip()
        if y.lower() in ("bilinmiyor", "unknown"):
            out["answer"] = {"choice": "unknown"}
        elif y.lower() in {o["id"] for o in options}:
            out["answer"] = {"choice": y.lower()}
        else:
            out["answer"] = {"choice": "other", "text": y}
    return out


def expand_lean(lean, card, rep):
    """Yalın JSON'u tam şemaya genişletir; izlenebilirlik alanları senaryolardan türetilir."""
    key = (card or {}).get("source", {}).get("jira_key") or lean.get("jira_key")
    if not key:
        raise OSError("yalın JSON için <KEY>-kart.json gerekli (önce parse_jira_xml.py)")
    questions = [lean_question(q, n, rep) for n, q in enumerate(lean.get("sorular", []), 1)]
    basis = list((card or {}).get("test_basis_candidates", []))
    br_no = max([int(b["id"].split("-")[1]) for b in basis if b["id"].startswith("BR-")] or [0])
    for q in questions:
        if is_answered(q):
            text = q["answer"].get("text") or next((o["text"] for o in q.get("options", [])
                                                    if o["id"] == q["answer"]["choice"]), "")
            if text:
                br_no += 1
                basis.append({"id": f"BR-{br_no:02d}", "kind": "business_rule", "text": text,
                              "source": {"field": "clarification", "ref": q["id"]},
                              "format": "rule", "testability": "testable"})
    if not basis:
        basis.append({"id": "BR-01", "kind": "business_rule", "text": card["source"]["summary"],
                      "source": {"field": "summary"}, "format": "rule", "testability": "testable"})
    basis_ids = [b["id"] for b in basis]

    reason = lean.get("yetersiz")
    checks = [{"id": r, "result": "pass", "finding": "—"} for r in ("R1", "R2", "R3", "R4", "R5", "R6", "R8")]
    if reason:
        checks[1] = {"id": "R2", "result": "fail", "finding": reason}
    env = lean.get("ortam")
    doc = {
        "schema_version": SCHEMA_VERSION,
        "test_environment": {"summary": env or "Kartta belirtilmemiş",
                             "details": [{"aspect": "ortam", "value": env, "source": {"field": "environment"}}] if env else []},
        "readiness": {"summary": reason or lean.get("ozet") or "Senaryolar karttaki bilgiyle üretildi.",
                      "checks": checks, "clarification_questions": questions},
        "test_basis": {"items": basis},
        "feature": {"name": lean.get("ozellik") or card["source"]["summary"],
                    "tags": list(lean.get("etiketler", [])),
                    "background": [parse_step(s, "geçmiş", rep) for s in lean.get("gecmis", [])]},
        "test_conditions": [], "coverage_items": [], "test_scenarios": [],
        "out_of_scope": [{"item": o.get("oge", ""), "reason": o.get("neden", "")} for o in lean.get("kapsam_disi", [])],
    }
    if not doc["feature"]["background"]:
        del doc["feature"]["background"]
    for n, s in enumerate(lean[LEAN_KEY], 1):
        sid, where = f"TS-{key}-{n:03d}", f"senaryo {n}"
        flow = FLOWS.get(str(s.get("akis", "")).lower())
        if not flow:
            rep.error(where, "akis 'ana', 'alternatif' veya 'hata' olmalı")
            flow = "alternative"
        prio = str(s.get("oncelik", "orta")).lower()
        if prio not in PRIORITY_RISK:
            rep.error(where, "oncelik 'kritik', 'yüksek', 'orta' veya 'düşük' olmalı")
            prio = "orta"
        likelihood, impact = PRIORITY_RISK[prio]
        title = s.get("baslik") or f"Senaryo {n}"
        cond, item = f"COND-{n:02d}", f"UC-{n:02d}"
        doc["test_conditions"].append({"id": cond, "description": title, "basis_ids": basis_ids,
                                       "techniques": ["use_case_based"],
                                       "risk": {"likelihood": likelihood, "impact": impact, "rationale": "—"}})
        doc["coverage_items"].append({"id": item, "technique": "use_case_based", "flow_type": flow,
                                      "test_condition_ids": [cond], "description": title})
        examples = s.get("ornekler") or []
        params = list(dict.fromkeys(k for ex in examples for k in ex if k != "durum"))
        data_sets = [{"id": f"DS-{i:02d}", "label": str(ex.get("durum") or f"Veri {i}"),
                      "values": {p: ex.get(p) for p in params}} for i, ex in enumerate(examples, 1)]
        tur = str(s.get("tur", "")).lower()
        negative = tur.startswith("neg") or (not tur and flow == "exception")
        sc = {"id": sid, "title": title, "objective": s.get("amac") or title,
              "scenario_type": "negative" if negative else "positive",
              "test_level": "system", "test_type": "functional", "techniques": ["use_case_based"],
              "traceability": {"basis_ids": basis_ids, "test_condition_ids": [cond], "coverage_item_ids": [item]},
              "steps": [parse_step(t, where, rep) for t in s.get("adimlar", [])],
              "test_data": {"parameters": [{"name": p, "description": p} for p in params], "data_sets": data_sets},
              "tags": list(s.get("etiketler", []))}
        if flow == "main" and "@smoke" not in sc["tags"]:
            sc["tags"].append("@smoke")
        for src, dst in (("sorular", "open_question_ids"), ("son_kosul", "postconditions"), ("notlar", "notes")):
            if s.get(src):
                sc[dst] = list(s[src])
        doc["test_scenarios"].append(sc)
    return doc


def merge_card(doc, card, rep, quiet=False):
    """XML'den gelen hazır veriyi JSON'la birleştirir; JSON'daki aynı kimlikli kayıt önceliklidir."""
    doc["source"] = {**card.get("source", {}), **doc.get("source", {})}
    inv, card_inv = doc.setdefault("card_inventory", {}), card.get("card_inventory", {})
    for section, key in (("fields", "field"), ("attachments", "name"), ("linked_issues", "key"), ("external_links", "name")):
        mine = {e[key]: e for e in inv.get(section, []) if isinstance(e, dict) and key in e}
        inv[section] = [{**e, **mine.pop(e[key], {})} for e in card_inv.get(section, [])] + list(mine.values())
    mine = {c["id"]: c for c in inv.get("comments", []) if isinstance(c, dict) and "id" in c}
    texts, comments = card.get("comment_texts", {}), []
    for c in card_inv.get("comments", []):
        entry = {**c, **mine.pop(c["id"], {})}
        if "summary" not in entry:
            text = (texts.get(c["id"]) or "").strip() or "(boş yorum)"
            entry["summary"] = text[:200] + ("…" if len(text) > 200 else "")
            if not quiet:
                rep.warn(c["id"], "yorum değerlendirilmedi; rolü 'unknown', özeti yorumun başı olarak yazıldı")
        entry.setdefault("role", "unknown")
        entry.setdefault("status", "used")
        entry.setdefault("basis_ids", [])
        comments.append(entry)
    inv["comments"] = comments + list(mine.values())
    basis = doc.setdefault("test_basis", {}).setdefault("items", [])
    mine = {b["id"]: b for b in basis if isinstance(b, dict) and "id" in b}
    merged = []
    for b in card.get("test_basis_candidates", []):
        own = mine.pop(b["id"], {})
        if own.get("text") and own["text"] != b["text"]:
            rep.warn(b["id"], "metin karttaki kabul kriterinden farklı; JSON'daki kullanıldı")
        merged.append({**b, **own})
    merged_ids = {m["id"] for m in merged}
    doc["test_basis"]["items"] = merged + [b for b in basis if not (isinstance(b, dict) and b.get("id") in merged_ids)]


def complete_document(doc, card, rep, quiet=False):
    """Hesaplanabilen alanları doldurur; LLM bunları yazmak zorunda değildir.

    Yazılmış bir değer hesaplanandan farklıysa hesaplanan geçerlidir ve uyarı
    verilir; böylece aritmetik bir kayma JSON'un yeniden yazılmasını gerektirmez.
    """
    doc.setdefault("schema_version", SCHEMA_VERSION)
    doc.setdefault("generated_at", datetime.now().astimezone().isoformat(timespec="seconds"))
    for key in ("conflicts", "assumptions", "out_of_scope", "test_scenarios", "coverage_items", "test_conditions"):
        doc.setdefault(key, [])
    if card:
        merge_card(doc, card, rep, quiet)
    try:
        _complete_derived(doc, rep)
    except (KeyError, TypeError, AttributeError, ValueError):
        pass  # yapı bozuk: şema doğrulaması nedenini söyler


def _complete_derived(doc, rep):
    def settle(obj, field, value, where, what):
        if obj.get(field) not in (None, value):
            rep.warn(where, f"{what} '{obj[field]}' yazılmış, hesaplanan '{value}' kullanıldı")
        obj[field] = value

    questions = {q["id"]: q for q in doc.get("readiness", {}).get("clarification_questions", [])}
    for q in questions.values():
        answer = q.get("answer")
        if answer and answer.get("choice") not in ("other", "unknown") and "text" not in answer:
            option = next((o for o in q.get("options", []) if o["id"] == answer["choice"]), None)
            if option:
                answer["text"] = option["text"]
    for cond in doc["test_conditions"]:
        r = cond.get("risk", {})
        if isinstance(r.get("likelihood"), int) and isinstance(r.get("impact"), int):
            settle(r, "level", risk_level(r["likelihood"], r["impact"]), cond["id"], "risk seviyesi")
    conds = {c["id"]: c for c in doc["test_conditions"]}
    for sc in doc["test_scenarios"]:
        levels = [conds[c]["risk"]["level"] for c in sc["traceability"]["test_condition_ids"]
                  if c in conds and "level" in conds[c].get("risk", {})]
        if levels:
            settle(sc, "priority", max(levels, key=RISK_ORDER.index), sc["id"], "öncelik")
        blocking_open = [q for q in sc.get("open_question_ids", [])
                         if q in questions and questions[q].get("blocking") and not is_answered(questions[q])]
        settle(sc, "status", "needs_clarification" if blocking_open else "ready", sc["id"], "durum")
    rd = doc.get("readiness", {})
    complete_checks(doc, rd)
    checks = {c["id"]: c["result"] for c in rd.get("checks", [])}
    if set(checks) == set(CHECK_IDS):
        if any(checks[r] == "fail" for r in ("R2", "R3", "R7", "R10")):
            status = "not_ready"
        elif any(v != "pass" for v in checks.values()):
            status = "partial"
        else:
            status = "ready"
        settle(rd, "status", status, "readiness", "kart durumu")
    doc["coverage_summary"] = compute_coverage(doc, rep)


def inventory_gaps(inv):
    """R10'u 'pass' olmaktan çıkaran kaynaklar: okunamayan/sağlanmayan ekler, açılmayan bağlantılar, eksik alanlar."""
    gaps = [a["name"] for a in inv.get("attachments", []) if a.get("status") in ("not_readable", "not_provided")]
    gaps += [l["name"] for l in inv.get("external_links", []) if l.get("status") == "not_accessible"]
    gaps += [l["key"] for l in inv.get("linked_issues", []) if l.get("status") == "not_accessible"]
    gaps += [f["field"] for f in inv.get("fields", []) if f.get("status") == "not_provided"]
    return gaps


def complete_checks(doc, rd):
    """R7, R9 ve R10 yazılmamışsa veriden hesaplanır; 'pass' kontrolünde bulgu yazılmamışsa '—' olur.

    Hesap ihtiyatlıdır: R7 ve R10 en fazla 'partial' olur. Kuralın yalnızca okunamayan
    bir ekte durması gibi 'fail' gerektiren durumu LLM kontrolü kendisi yazarak belirtir.
    """
    checks = rd.setdefault("checks", [])
    present = {c.get("id") for c in checks}
    if "R7" not in present:
        open_cf = [c["id"] for c in doc["conflicts"] if c.get("status") == "unresolved"]
        checks.append({"id": "R7", "result": "partial" if open_cf else "pass",
                       "finding": f"Çözülmemiş çelişki: {', '.join(open_cf)}." if open_cf else "Çözülmemiş çelişki yok."})
    if "R9" not in present:
        details = doc.get("test_environment", {}).get("details") or []
        if details:
            checks.append({"id": "R9", "result": "pass",
                           "finding": "Ortam: " + ", ".join(str(d.get("value")) for d in details) + "."})
        else:
            bug = doc.get("source", {}).get("issue_type") == "bug"
            checks.append({"id": "R9", "result": "fail" if bug else "partial", "finding": "Test ortamı kartta tanımlı değil."})
    if "R10" not in present:
        gaps = inventory_gaps(doc.get("card_inventory", {}))
        checks.append({"id": "R10", "result": "partial" if gaps else "pass",
                       "finding": f"İşlenemeyen kaynaklar: {', '.join(gaps)}." if gaps else "Tüm ekler ve bağlantılar işlendi."})
    for c in checks:
        if c.get("id") in CHECK_CRITERIA:
            c.setdefault("criterion", CHECK_CRITERIA[c["id"]])
        if c.get("result") == "pass":
            c.setdefault("finding", "—")
    checks.sort(key=lambda c: CHECK_IDS.index(c["id"]) if c.get("id") in CHECK_IDS else len(CHECK_IDS))


def compute_coverage(doc, rep):
    """Kapsam özeti senaryolardan hesaplanır. LLM yalnızca kapsanmayan öğelerin gerekçesini yazar."""
    given = doc.get("coverage_summary") or {}
    scenarios, items = doc["test_scenarios"], doc["coverage_items"]
    covered = {i for s in scenarios for i in s["traceability"]["coverage_item_ids"]}
    reasons = {u["coverage_item_id"]: u for u in given.get("uncovered_items", []) if "coverage_item_id" in u}
    uncovered = []
    for item in items:
        if item["id"] in covered:
            continue
        entry = reasons.pop(item["id"], None)
        if not entry or not entry.get("reason"):
            rep.error(item["id"], "hiçbir senaryoda yok; bir senaryoya bağla ya da coverage_summary.uncovered_items "
                                  "içine gerekçesini yaz")
            entry = {"coverage_item_id": item["id"], "reason": "gerekçe yazılmadı"}
        uncovered.append(entry)
    for item_id in reasons:
        rep.warn(item_id, "uncovered_items içinde ama bir senaryoda kapsanıyor; listeden çıkarıldı")
    notes = {b["basis_id"]: b for b in given.get("basis", []) if "basis_id" in b}
    basis = []
    for b in doc.get("test_basis", {}).get("items", []):
        if b.get("kind") not in ("acceptance_criterion", "business_rule"):
            continue
        linked = [s for s in scenarios if b["id"] in s["traceability"]["basis_ids"]]
        status = ("covered" if any(s["status"] == "ready" for s in linked)
                  else "partially_covered" if linked else "not_covered")
        own = notes.get(b["id"], {})
        if own.get("status") in COVERAGE_ORDER:  # LLM daha ihtiyatlıysa (ör. bir taraf eksik) onunki geçerli
            status = min(status, own["status"], key=COVERAGE_ORDER.index)
        entry = {"basis_id": b["id"], "scenario_ids": [s["id"] for s in linked], "status": status}
        if own.get("note"):
            entry["note"] = own["note"]
        basis.append(entry)
    techniques = []
    for t in dict.fromkeys(i["technique"] for i in items):
        total = [i for i in items if i["technique"] == t]
        cov = [i for i in total if i["id"] in covered]
        techniques.append({"technique": t, "total_items": len(total), "covered_items": len(cov),
                           "coverage_percent": round(100 * len(cov) / len(total), 2)})
    types, statuses = Counter(s["scenario_type"] for s in scenarios), Counter(s["status"] for s in scenarios)
    return {"basis": basis, "techniques": techniques, "uncovered_items": uncovered,
            "scenario_counts": {"total": len(scenarios), "positive": types["positive"], "negative": types["negative"],
                                "ready": statuses["ready"], "needs_clarification": statuses["needs_clarification"]}}


def card_text(input_path):
    """<KEY>-kart.md: yalın biçimde beklenen mesajlar kartın tüm metninde aranır."""
    path = Path(input_path).with_name(Path(input_path).stem + "-kart.md")
    return path.read_text(encoding="utf-8") if path.exists() else ""


def prepare(input_path, card_path, schema, rep):
    """JSON'u okur, karttan ve hesapla tamamlar, doğrular. Okuma hatasında OSError/JSONDecodeError fırlatır.

    Yalın biçimde (output-template.md) önce tam şemaya genişletilir; dönen belgede
    doc["_mod"] == "yalin" olur ve çıktılar izlenebilirlik alanlarını göstermez.
    """
    doc, card = load_json(input_path), load_card(input_path, card_path)
    lean = is_lean(doc)
    if lean:
        doc = expand_lean(doc, card, rep)
    complete_document(doc, card, rep, quiet=lean)
    check_document(doc, schema, rep, extra_text=card_text(input_path) if lean else None)
    if lean:
        doc["_mod"] = "yalin"
    return doc


# ------------------------------------------------------------------ doğrulama

def check_schema(doc, schema, rep):
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        rep.warn("şema", "jsonschema kurulu değil, şema doğrulaması atlandı (pip install jsonschema)")
        return
    for err in sorted(Draft202012Validator(schema).iter_errors(doc), key=lambda e: list(e.absolute_path)):
        path = "/".join(str(p) for p in err.absolute_path) or "(kök)"
        rep.error(f"şema {path}", err.message[:300])


def check_source(src, where, inv, rep):
    field, ref = src["field"], src.get("ref")
    if field == "comment" and ref not in inv["comments"]:
        rep.error(where, f"kaynak yorum '{ref}' card_inventory.comments içinde yok")
    elif field == "attachment":
        names = [n for n in inv["attachments"] if ref == n or ref.startswith(n + " ")]
        if not names:
            rep.error(where, f"kaynak ek '{ref}' card_inventory.attachments içinde yok")
        elif inv["attachments"][names[0]]["status"] != "processed":
            rep.error(where, f"kaynak ek '{names[0]}' işlenmemiş ({inv['attachments'][names[0]]['status']})")
    elif field == "linked_issue" and ref not in inv["linked"]:
        rep.error(where, f"kaynak kart '{ref}' card_inventory.linked_issues içinde yok")
    elif field == "clarification" and ref not in inv["answered"]:
        rep.error(where, f"kaynak soru '{ref}' yanıtlanmamış; yanıtı readiness.clarification_questions[].answer içine yaz")
    if field == "comment" and ref in inv["comments"] and inv["comments"][ref]["status"] == "superseded":
        rep.warn(where, f"kaynak yorum '{ref}' geçersiz kılınmış olarak işaretli")


def check_inventory_and_basis(doc, rep, ids, inv):
    for item in doc["test_basis"]["items"]:
        prefix = item["id"].split("-")[0]
        if KIND_PREFIX.get(prefix) != item["kind"]:
            rep.error(item["id"], f"ID ön eki '{prefix}' ile kind '{item['kind']}' uyuşmuyor")
        check_source(item["source"], item["id"], inv, rep)
        for u in item.get("updates", []):
            if u not in ids["basis"]:
                rep.error(item["id"], f"updates içinde tanımsız öğe {u}")
    for att in doc["card_inventory"]["attachments"]:
        for b in att["basis_ids"]:
            if b not in ids["basis"]:
                rep.error(f"ek {att['name']}", f"tanımsız test esası öğesi {b}")
        if att["status"] == "processed" and not att["basis_ids"]:
            rep.warn(f"ek {att['name']}", "işlendi ama test esasına öğe eklemedi; ilgisizse not_relevant yazın")
    for c in doc["card_inventory"]["comments"]:
        for b in c["basis_ids"]:
            if b not in ids["basis"]:
                rep.error(c["id"], f"tanımsız test esası öğesi {b}")
    for kind, values in (
        ("ek", list(inv["attachments"])),
        ("yorum", list(inv["comments"])),
        ("test esası öğesi", [b["id"] for b in doc["test_basis"]["items"]]),
    ):
        for value, count in Counter(values).items():
            if count > 1:
                rep.error(kind, f"{value} birden fazla kez tanımlı")
    for d in doc["test_environment"]["details"]:
        check_source(d["source"], f"test_environment {d['aspect']}", inv, rep)
    for o in doc["out_of_scope"]:
        if "source" in o:
            check_source(o["source"], f"out_of_scope '{o['item'][:30]}'", inv, rep)


def check_readiness(doc, rep, ids):
    checks = {c["id"]: c["result"] for c in doc["readiness"]["checks"]}
    if sorted(checks, key=CHECK_IDS.index) != CHECK_IDS or len(doc["readiness"]["checks"]) != 10:
        rep.error("readiness", "R1–R10 kontrollerinin her biri bir kez yer almalı")
        return

    inv = doc["card_inventory"]
    if any(c["status"] == "unresolved" for c in doc["conflicts"]) and checks["R7"] == "pass":
        rep.error("readiness R7", "çözülmemiş çelişki varken R7 'pass' olamaz")
    if not doc["test_environment"]["details"] and checks["R9"] == "pass":
        rep.error("readiness R9", "test_environment.details boşken R9 'pass' olamaz")
    gaps = inventory_gaps(inv)
    if gaps and checks["R10"] == "pass":
        rep.error("readiness R10", f"işlenemeyen kaynaklar varken R10 'pass' olamaz: {gaps}")

    for q in doc["readiness"]["clarification_questions"]:
        for b in q.get("related_basis_ids", []):
            if b not in ids["basis"]:
                rep.error(q["id"], f"tanımsız test esası öğesi {b}")
        for c in q.get("related_conflict_ids", []):
            if c not in ids["conflicts"]:
                rep.error(q["id"], f"tanımsız çelişki {c}")
        answer = q.get("answer")
        if answer:
            if answer["choice"] == "other" and not answer.get("text"):
                rep.error(q["id"], "'other' yanıtında text zorunlu")
            elif answer["choice"] not in ("other", "unknown") and answer["choice"] not in {o["id"] for o in q.get("options", [])}:
                rep.error(q["id"], f"yanıt '{answer['choice']}' seçeneklerde yok")
        if is_answered(q) and not any(b.get("source", {}).get("ref") == q["id"] for b in ids["basis"].values()):
            rep.warn(q["id"], "yanıtlandı ama hiçbir test esası öğesi yanıta dayanmıyor; davranışı değiştiriyorsa "
                              "kaynağı {field: clarification, ref: " + q["id"] + "} olan bir BR ekle")
    for cf in doc["conflicts"]:
        q = ids["questions"].get(cf.get("question_id"))
        if q and is_answered(q) and cf["status"] == "unresolved":
            rep.warn(cf["id"], f"{q['id']} yanıtlandı ama çelişki 'unresolved'; yanıttan gelen BR ile "
                               "resolved_by_later_decision yap")


def check_conflicts(doc, rep, ids):
    for cf in doc["conflicts"]:
        for b in cf["basis_ids"]:
            if b not in ids["basis"]:
                rep.error(cf["id"], f"tanımsız test esası öğesi {b}")
        if "resolved_by" in cf and cf["resolved_by"] not in ids["basis"]:
            rep.error(cf["id"], f"resolved_by tanımsız: {cf['resolved_by']}")
        if "question_id" in cf and cf["question_id"] not in ids["questions"]:
            rep.error(cf["id"], f"tanımsız soru {cf['question_id']}")


def check_steps(steps, where, rep, has_background, is_background=False):
    if not steps:
        return
    if steps[0]["keyword"] in ("and", "but"):
        rep.error(where, "ilk adım 'Ve' veya 'Fakat' olamaz")
    if is_background:
        for s in steps:
            if s["keyword"] not in ("given", "and"):
                rep.error(where, "Geçmiş yalnızca 'Diyelim ki' ve 'Ve' adımları içerebilir")
                break
        return
    if steps[0]["keyword"] == "then" and not has_background:
        rep.error(where, "senaryo 'O zaman' ile başlayamaz")
    # Uçtan uca akışta ara doğrulama olağandır (Eğer ki → O zaman → Eğer ki → O zaman);
    # akışın ortasında yeni bir ön koşul ise senaryonun iki akışı birleştirdiğini gösterir.
    phase, phases, late_given = 0, [], False
    for s in steps:
        kw = s["keyword"]
        new_phase = PHASE.get(kw, phase)
        if new_phase == 1 and phase > 1:
            late_given = True
        phase = new_phase
        phases.append(phase)
    if 3 not in phases:
        rep.error(where, "beklenen sonuç adımı ('O zaman') yok")
    elif phases[-1] != 3:
        rep.error(where, "senaryo beklenen sonuçla ('O zaman' bloğu) bitmiyor")
    if 2 not in phases:
        rep.warn(where, "eylem adımı ('Eğer ki') yok")
    if late_given:
        rep.warn(where, "akışın ortasında yeni ön koşul ('Diyelim ki') var; ön koşullar akışın başında olur")
    return phases


def flow_of(sc, items):
    """Senaryonun bağlı olduğu uçtan uca akışlar (UC kapsam öğeleri); doğru senaryoda tam bir tane."""
    return [items[i] for i in sc["traceability"]["coverage_item_ids"]
            if i in items and items[i]["technique"] == "use_case_based"]


def check_scenario(sc, doc, rep, ids, basis_texts, strict_quotes=True):
    sid = sc["id"]
    tr_ = sc["traceability"]
    is_draft = sc["status"] == "needs_clarification"
    for b in tr_["basis_ids"]:
        if b not in ids["basis"]:
            rep.error(sid, f"tanımsız test esası öğesi {b}")
    for c in tr_["test_condition_ids"]:
        if c not in ids["conds"]:
            rep.error(sid, f"tanımsız test koşulu {c}")
    for i in tr_["coverage_item_ids"]:
        if i not in ids["items"]:
            rep.error(sid, f"tanımsız kapsam öğesi {i}")
        elif ids["items"][i]["technique"] not in sc["techniques"]:
            rep.error(sid, f"{i} tekniği ({ids['items'][i]['technique']}) senaryonun techniques listesinde yok")
    for q in sc.get("open_question_ids", []):
        if q not in ids["questions"]:
            rep.error(sid, f"tanımsız soru {q}")
    for a in sc.get("assumption_ids", []):
        if a not in ids["assumptions"]:
            rep.error(sid, f"tanımsız varsayım {a}")

    has_background = bool(doc["feature"].get("background"))
    phases = check_steps(sc["steps"], sid, rep, has_background=has_background)

    flows = flow_of(sc, ids["items"])
    if len(flows) != 1:
        found = ", ".join(f["id"] for f in flows) or "yok"
        rep.error(sid, f"senaryo tam bir uçtan uca akışa (UC kapsam öğesi) bağlı olmalı; bulunan: {found}")
    if not has_background and not any(s["keyword"] == "given" for s in sc["steps"]):
        rep.warn(sid, "başlangıç durumu ('Diyelim ki') yok; uçtan uca akış giriş noktasından başlar")

    # parametreler
    params = [p["name"] for p in sc["test_data"]["parameters"]]
    if "durum" in params:
        rep.error(sid, "'durum' parametre adı Örnekler tablosunda ayrılmıştır")
    used = set()
    for s in sc["steps"]:
        used.update(PARAM_RE.findall(s["text"]))
    for name in sorted(used - set(params)):
        rep.error(sid, f"<{name}> kullanılıyor ama test_data.parameters içinde yok")
    for name in sorted(set(params) - used):
        rep.warn(sid, f"parametre '{name}' tanımlı ama adımlarda kullanılmıyor")
    if params and not sc["test_data"]["data_sets"]:
        rep.error(sid, "parametre var ama veri seti yok")
    for ds in sc["test_data"]["data_sets"]:
        missing, extra = set(params) - set(ds["values"]), set(ds["values"]) - set(params)
        if missing:
            rep.error(f"{sid} {ds['id']}", f"eksik parametre değerleri: {sorted(missing)}")
        if extra:
            rep.error(f"{sid} {ds['id']}", f"tanımsız parametreler: {sorted(extra)}")
        for k, v in ds["values"].items():
            if isinstance(v, str) and '"' in v:
                rep.error(f"{sid} {ds['id']}", f"'{k}' değeri çift tırnak içeriyor")

    # beklenen metinler kartta geçmeli
    if phases:
        for values in instances(sc):
            for s, phase in zip(sc["steps"], phases):
                if phase != 3:
                    continue
                for quoted in QUOTE_RE.findall(substitute(s["text"], values)):
                    if not any(quoted in t for t in basis_texts):
                        msg = f"beklenen metin kartta geçmiyor: \"{quoted}\""
                        (rep.error if strict_quotes and not is_draft else rep.warn)(sid, msg)


def check_document(doc, schema, rep, extra_text=None):
    check_schema(doc, schema, rep)
    if rep.errors:
        return  # yapı bozuksa anlamsal kontroller yanıltıcı olur

    questions = doc["readiness"]["clarification_questions"]
    inv = {
        "attachments": {a["name"]: a for a in doc["card_inventory"]["attachments"]},
        "comments": {c["id"]: c for c in doc["card_inventory"]["comments"]},
        "linked": {l["key"] for l in doc["card_inventory"]["linked_issues"]},
        "answered": {q["id"] for q in questions if is_answered(q)},
    }
    ids = {
        "basis": {b["id"]: b for b in doc["test_basis"]["items"]},
        "conds": {c["id"]: c for c in doc["test_conditions"]},
        "items": {i["id"]: i for i in doc["coverage_items"]},
        "questions": {q["id"]: q for q in questions},
        "assumptions": {a["id"] for a in doc["assumptions"]},
        "conflicts": {c["id"] for c in doc["conflicts"]},
    }
    # Beklenen metin karttan ya da kullanıcının seçtiği yanıttan gelebilir.
    basis_texts = [b["text"] for b in doc["test_basis"]["items"]]
    basis_texts += [q["answer"]["text"] for q in questions if is_answered(q) and q["answer"].get("text")]
    if extra_text is not None:  # yalın biçim: kartın tüm metni; bulunamayan mesaj uyarıdır
        basis_texts.append(extra_text)
    scenarios = doc["test_scenarios"]

    check_inventory_and_basis(doc, rep, ids, inv)
    check_readiness(doc, rep, ids)
    check_conflicts(doc, rep, ids)

    for cond in doc["test_conditions"]:
        for b in cond["basis_ids"]:
            if b not in ids["basis"]:
                rep.error(cond["id"], f"tanımsız test esası öğesi {b}")
    for item in doc["coverage_items"]:
        prefix = item["id"].split("-")[0]
        if TECHNIQUE_PREFIX.get(prefix) != item["technique"]:
            rep.error(item["id"], f"ön ek '{prefix}' ile technique '{item['technique']}' uyuşmuyor")
        for c in item["test_condition_ids"]:
            if c not in ids["conds"]:
                rep.error(item["id"], f"tanımsız test koşulu {c}")

    for value, count in Counter(s["id"] for s in scenarios).items():
        if count > 1:
            rep.error("senaryo", f"{value} birden fazla kez tanımlı")
    flow_use = Counter(f["id"] for s in scenarios for f in flow_of(s, ids["items"]))
    for flow_id, count in flow_use.items():
        if count > 1:
            rep.warn(flow_id, f"{count} senaryoda kullanılıyor; aynı akış aynı tür sonuçla bitiyorsa farklı veriler tek senaryonun veri satırı olur")
    flows = [i for i in doc["coverage_items"] if i["technique"] == "use_case_based"]
    if scenarios and not any(f.get("flow_type") == "main" for f in flows):
        rep.warn("kapsam öğeleri", "ana akış (UC, flow_type: main) yok")
    if doc["feature"].get("background"):
        check_steps(doc["feature"]["background"], "feature.background", rep, False, is_background=True)
    for sc in scenarios:
        check_scenario(sc, doc, rep, ids, basis_texts, strict_quotes=extra_text is None)
    # kapsam özeti complete_document'ta hesaplandı; yalnızca LLM'in yazdığı soru bağı denetlenir
    for u in doc["coverage_summary"]["uncovered_items"]:
        if "question_id" in u and u["question_id"] not in ids["questions"]:
            rep.error("uncovered_items", f"tanımsız soru {u['question_id']}")


# ------------------------------------------------------------------ .feature

def table(rows, indent):
    cells = [[str("" if c is None else c).replace("|", "\\|") for c in row] for row in rows]
    widths = [max(len(r[i]) for r in cells) for i in range(len(cells[0]))]
    return [indent + "| " + " | ".join(c.ljust(w) for c, w in zip(r, widths)) + " |" for r in cells]


def render_steps(steps, indent, values=None):
    return [f"{indent}{KEYWORDS[s['keyword']]} {substitute(s['text'], values) if values is not None else s['text']}"
            for s in steps]


def render_scenario(sc, questions, assumptions, items, comments=True, trace=True):
    """Tek senaryonun Gherkin satırları, etiketlerden son adıma kadar.

    comments=False: akış, kaynak, taslak, not, son koşul ve veri yorumları
    yazılmaz (Jira kartında bunlar ayrı alanlarda verilir).
    trace=False (yalın biçim): akış ve kaynak (izlenebilirlik) yorumları yazılmaz.
    """
    draft = sc["status"] == "needs_clarification"
    tags = [f"@{sc['id']}", "@pozitif" if sc["scenario_type"] == "positive" else "@negatif"]
    tags += [t for t in sc.get("tags", []) if t not in tags]
    if draft:
        tags.append("@taslak")
    data_sets = sc["test_data"]["data_sets"]
    outline = len(data_sets) > 1
    out = ["  " + " ".join(tags), f"  {'Senaryo Taslağı' if outline else 'Senaryo'}: {sc['title']}"]
    if comments and trace:
        for flow in flow_of(sc, items):
            out.append(f"    # Akış ({tr(flow.get('flow_type', ''))}): {flow['description']}")
        t = sc["traceability"]
        line = f"# Kaynak: {', '.join(t['basis_ids'])} | {', '.join(t['test_condition_ids'])}"
        if t["coverage_item_ids"]:
            line += f" | {', '.join(t['coverage_item_ids'])}"
        out.append(f"    {line}")
    if comments:
        if draft:
            for q in sc.get("open_question_ids", []):
                if not is_answered(questions[q]):
                    out.append(f"    # Taslak — açık soru {q}: {questions[q]['question']}")
            for a in sc.get("assumption_ids", []):
                out.append(f"    # Varsayım {a}: {assumptions[a]['statement']}")
        for note in sc.get("notes", []):
            out.append(f"    # Not: {note}")
        for post in sc.get("postconditions", []):
            out.append(f"    # Son koşul: {post}")
    if outline:
        params = [p["name"] for p in sc["test_data"]["parameters"]]
        out += render_steps(sc["steps"], "    ")
        out += ["", "    Örnekler:"]
        out += table([["durum"] + params] + [[ds["label"]] + [ds["values"].get(p) for p in params] for ds in data_sets], "      ")
    else:
        if data_sets and comments:
            out.append(f"    # Veri: {data_sets[0]['label']}")
        out += render_steps(sc["steps"], "    ", data_sets[0]["values"] if data_sets else {})
    return out


def render_feature(doc, exclude_drafts, rep):
    src, feat, env = doc["source"], doc["feature"], doc["test_environment"]
    open_q = [q["id"] for q in doc["readiness"]["clarification_questions"] if not is_answered(q)]
    questions = {q["id"]: q for q in doc["readiness"]["clarification_questions"]}
    assumptions = {a["id"]: a for a in doc["assumptions"]}
    items = {i["id"]: i for i in doc["coverage_items"]}
    status_line = f"# Kart durumu: {tr(doc['readiness']['status'])}"
    if open_q:
        status_line += f" | Açık sorular: {', '.join(open_q)}"
    out = [
        "# language: tr",
        f"# Kaynak: {src['jira_key']} — {src['summary']}",
        f"# Test ortamı: {env['summary']}",
        status_line,
        "# Bu dosya scenario-generator çıktısından üretilmiştir.",
        "",
        " ".join([f"@{src['jira_key']}"] + feat["tags"]),
        f"Özellik: {feat['name']}",
    ]
    if feat.get("description"):
        out += [f"  {line}" for line in feat["description"].splitlines()]
    if feat.get("background"):
        out += ["", "  Geçmiş:"] + render_steps(feat["background"], "    ")

    rendered = 0
    for sc in doc["test_scenarios"]:
        if sc["status"] == "needs_clarification" and exclude_drafts:
            rep.warn(sc["id"], "taslak senaryo --exclude-drafts nedeniyle üretilmedi")
            continue
        out += [""] + render_scenario(sc, questions, assumptions, items, trace=doc.get("_mod") != "yalin")
        rendered += 1
    if not rendered:
        out += ["", f"  # Üretilecek senaryo yok (kart durumu: {doc['readiness']['status']}). Yeterlilik raporuna bakın."]
    return "\n".join(out) + "\n", rendered


# ------------------------------------------------------------------ rapor

def md_table(header, rows):
    esc = lambda v: str("" if v is None else v).replace("|", "\\|").replace("\n", " ")
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(esc(c) for c in row) + " |" for row in rows]
    return lines


def render_lean_report(doc):
    """Yalın biçimin raporu: durum, sorular ve senaryo listesi; izlenebilirlik tabloları yok."""
    src, rd = doc["source"], doc["readiness"]
    counts = doc["coverage_summary"]["scenario_counts"]
    ordered = sorted(rd["clarification_questions"], key=lambda q: (not q["blocking"], q["id"]))
    open_q = [q for q in ordered if not is_answered(q)]
    answered = [q for q in ordered if is_answered(q)]
    items = {i["id"]: i for i in doc["coverage_items"]}
    out = [
        f"# Senaryo Raporu — {src['jira_key']}",
        "",
        f"**Kart:** {src['summary']}  ",
        f"**Durum:** {tr(rd['status'])} — {rd['summary']}  ",
        f"**Test ortamı:** {doc['test_environment']['summary']}  ",
        f"**Üretilen senaryo:** {counts['total']} ({counts['ready']} hazır, {counts['needs_clarification']} taslak)",
        "", "## Açık sorular", "",
    ]
    out += md_table(["ID", "Soru", "Bloklayıcı"], [[q["id"], q["question"], "evet" if q["blocking"] else "hayır"]
                                                  for q in open_q]) if open_q else ["Açık soru yok."]
    if answered:
        out += ["", "## Yanıtlanan sorular", ""]
        out += md_table(["ID", "Soru", "Yanıt"], [[q["id"], q["question"], q["answer"].get("text", "")] for q in answered])
    out += ["", "## Senaryolar", ""]
    out += md_table(["ID", "Akış", "Öncelik", "Tür", "Durum", "Başlık"],
                    [[s["id"], ", ".join(tr(f["flow_type"]) for f in flow_of(s, items)), tr(s["priority"]),
                      tr(s["scenario_type"]), tr(s["status"]), s["title"]] for s in execution_order(doc["test_scenarios"])])
    gaps = inventory_gaps(doc["card_inventory"])
    if gaps:
        out += ["", f"**İşlenemeyen kaynaklar:** {', '.join(gaps)}"]
    if doc["out_of_scope"]:
        out += ["", "## Kapsam dışı", ""] + [f"- {o['item']}: {o['reason']}" for o in doc["out_of_scope"]]
    return "\n".join(out) + "\n"


def render_report(doc):
    if doc.get("_mod") == "yalin":
        return render_lean_report(doc)
    src, rd, inv = doc["source"], doc["readiness"], doc["card_inventory"]
    scenarios = doc["test_scenarios"]
    counts = doc["coverage_summary"]["scenario_counts"]
    ordered = sorted(rd["clarification_questions"], key=lambda q: (not q["blocking"], q["id"]))
    questions = [q for q in ordered if not is_answered(q)]
    answered = [q for q in ordered if is_answered(q)]
    out = [
        f"# Kart Yeterlilik Raporu — {src['jira_key']}",
        "",
        f"**Kart:** {src['summary']}  ",
        f"**Durum:** {tr(rd['status'])} — {rd['summary']}  ",
        f"**Test ortamı:** {doc['test_environment']['summary']}  ",
        f"**Üretilen senaryo:** {counts['total']} ({counts['ready']} hazır, {counts['needs_clarification']} taslak)",
        "",
        "## Açık sorular",
        "",
    ]
    if questions:
        out += md_table(
            ["ID", "Soru", "Bloklayıcı", "Muhatap", "İlgili"],
            [[q["id"], q["question"], "evet" if q["blocking"] else "hayır", tr(q.get("addressed_to", "")),
              ", ".join(q.get("related_basis_ids", []) + q.get("related_conflict_ids", []) + q["related_check_ids"])]
             for q in questions],
        )
    else:
        out.append("Açık soru yok.")
    if answered:
        out += ["", "## Yanıtlanan sorular", "",
                "Yanıtlar kullanıcı tarafından seçildi; kart sahibiyle teyit edilmesi önerilir.", ""]
        out += md_table(["ID", "Soru", "Yanıt"],
                        [[q["id"], q["question"],
                          f"{q['answer']['choice']}) {q['answer'].get('text', '')}" if q["answer"]["choice"] != "other"
                          else f"Diğer: {q['answer']['text']}"] for q in answered])
    out += ["", "## Yeterlilik kontrolleri", ""]
    out += md_table(["ID", "Kontrol", "Sonuç", "Bulgu"],
                    [[c["id"], c["criterion"], tr(c["result"]), c["finding"]] for c in rd["checks"]])
    out += ["", "## Çelişkiler", ""]
    if doc["conflicts"]:
        out += md_table(
            ["ID", "Açıklama", "Öğeler", "Durum", "Çözüm / soru"],
            [[cf["id"], cf["description"], ", ".join(cf["basis_ids"]), tr(cf["status"]),
              cf.get("resolved_by") or cf.get("question_id", "")] for cf in doc["conflicts"]],
        )
    else:
        out.append("Çelişki yok.")
    out += ["", "## Kart envanteri", "", "### Alanlar", ""]
    out += md_table(["Alan", "Durum", "Not"], [[f["field"], tr(f["status"]), f.get("note", "")] for f in inv["fields"]])
    out += ["", "### Ekler", ""]
    if inv["attachments"]:
        out += md_table(["Ek", "Tür", "Durum", "Çıkarılan bilgi", "Öğeler"],
                        [[a["name"], a["type"], tr(a["status"]), a["summary"], ", ".join(a["basis_ids"])]
                         for a in inv["attachments"]])
    else:
        out.append("Ek yok.")
    out += ["", "### Yorumlar", ""]
    if inv["comments"]:
        out += md_table(["ID", "Yazar", "Tarih", "Rol", "Durum", "Özet", "Öğeler"],
                        [[c["id"], c["author"], c["date"], tr(c["role"]), tr(c["status"]), c["summary"],
                          ", ".join(c["basis_ids"])] for c in inv["comments"]])
    else:
        out.append("Yorum yok.")
    if inv["linked_issues"] or inv["external_links"]:
        out += ["", "### Bağlı kartlar ve dış bağlantılar", ""]
        out += md_table(["Kaynak", "Tür", "Durum", "Not"],
                        [[l["key"], l["link_type"], tr(l["status"]), l["note"]] for l in inv["linked_issues"]]
                        + [[l["name"], "dış bağlantı", tr(l["status"]), l["note"]] for l in inv["external_links"]])
    items = {i["id"]: i for i in doc["coverage_items"]}
    flows = [i for i in doc["coverage_items"] if i["technique"] == "use_case_based"]
    if flows:
        out += ["", "## Uçtan uca akışlar", ""]
        out += md_table(["Akış", "Tür", "Başlangıçtan sonuca", "Senaryo"],
                        [[f["id"], tr(f.get("flow_type", "")), f["description"],
                          ", ".join(s["id"] for s in scenarios if f in flow_of(s, items)) or "—"] for f in flows])
    out += ["", "## Kapsam", ""]
    out += md_table(["Öğe", "Senaryolar", "Durum", "Not"],
                    [[b["basis_id"], ", ".join(b["scenario_ids"]) or "—", tr(b["status"]), b.get("note", "")]
                     for b in doc["coverage_summary"]["basis"]])
    drafts = [s for s in scenarios if s["status"] == "needs_clarification"]
    uncovered = doc["coverage_summary"]["uncovered_items"]
    if drafts:
        out += ["", "**Taslak senaryolar** (yanıt bekleyen):", ""]
        out += [f"- {s['id']}: {s['title']} — {', '.join(s.get('open_question_ids', []))}" for s in drafts]
    if uncovered:
        out += ["", "**Kapsanamayan öğeler:**", ""]
        out += [f"- {u['coverage_item_id']}: {u['reason']}" + (f" ({u['question_id']})" if "question_id" in u else "")
                for u in uncovered]
    if doc["assumptions"]:
        out += ["", "## Varsayımlar", ""]
        out += [f"- {a['id']} ({a['question_id']}): {a['statement']}" for a in doc["assumptions"]]
    if doc["out_of_scope"]:
        out += ["", "## Kapsam dışı", ""]
        out += [f"- {o['item']}: {o['reason']}" for o in doc["out_of_scope"]]
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------ seçim listesi

def execution_order(scenarios):
    """Koşum sırası: önce @smoke, sonra risk seviyesi (kritikten düşüğe), sonra ID."""
    return sorted(scenarios, key=lambda s: ("@smoke" not in s.get("tags", []),
                                            -RISK_ORDER.index(s["priority"]), s["id"]))


def read_selection(path):
    """Seçim listesindeki satırlar: {senaryo ID: (işaretli mi, başlık)} ve tekrar eden ID'ler."""
    states, dupes = {}, []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        m = SELECTION_RE.match(line)
        if not m:
            continue
        sid, rest = m.group(2), m.group(3)
        if sid in states:
            dupes.append(sid)
        title = rest.split(" — ", 1)[1].strip() if " — " in rest else ""
        states[sid] = (m.group(1) != " ", title)
    return states, dupes


def selection_states(doc, previous, rep):
    """Her senaryonun işareti: önceki listedeki işaret aynı ID ve aynı başlıkla korunur.

    Başlığı değişen ID artık başka bir senaryo olabilir; onun işareti varsayılana
    döner (hazır: işaretli, taslak: işaretsiz).
    """
    states = {}
    for sc in doc["test_scenarios"]:
        checked = sc["status"] != "needs_clarification"
        if sc["id"] in previous:
            was_checked, old_title = previous[sc["id"]]
            if old_title == sc["title"]:
                checked = was_checked
            else:
                rep.warn(f"seçim {sc['id']}", "başlık değişti; işaret varsayılana döndü")
        states[sc["id"]] = checked
    for sid in sorted(set(previous) - set(states)):
        rep.warn(f"seçim {sid}", "JSON'da artık yok; listeden çıkarıldı")
    return states


def render_selection(doc, states):
    """Test Senaryosu kartına dönüştürülecek senaryoların işaretlenebilir listesi."""
    src = doc["source"]
    scenarios = execution_order(doc["test_scenarios"])
    items = {i["id"]: i for i in doc["coverage_items"]}
    out = [
        f"# Jira'ya aktarılacak senaryolar — {src['jira_key']}",
        "",
        f"**Kart:** {src['summary']}",
        "",
        "Test Senaryosu kartına dönüştürülecek senaryoların kutusunu işaretleyin (`[x]`),",
        "dönüştürülmeyecekleri boş bırakın (`[ ]`). Taslak senaryolar bloklayıcı soru",
        "yanıtlanana kadar işaretsiz gelir. Sıra koşum sırasıdır: önce `@smoke`, sonra",
        "risk seviyesi.",
        "",
    ]
    if not scenarios:
        out.append(f"Aktarılacak senaryo yok (kart durumu: {tr(doc['readiness']['status'])}).")
    for n, sc in enumerate(scenarios, 1):
        draft = sc["status"] == "needs_clarification"
        status = f"taslak ({', '.join(sc.get('open_question_ids', []))})" if draft else "hazır"
        tags = "".join(f" · {t}" for t in sc.get("tags", []))
        flow = "".join(f" · {tr(f.get('flow_type', ''))}" for f in flow_of(sc, items))
        out.append(f"- [{'x' if states[sc['id']] else ' '}] {n}. {sc['id']}{flow} · {tr(sc['priority'])} · "
                   f"{tr(sc['scenario_type'])} · {status}{tags} — {sc['title']}")
    out += ["", "Ekrandan seçim: `<KEY>-secim.html`."]
    return "\n".join(out) + "\n"


def start_selection_server(input_path, open_browser):
    """secim_sunucu.py'yi bağımsız bir süreç olarak başlatır ve hazır olana kadar bekler.

    Bağımsızdır: bu komut hemen döner, agent'ın terminali sunucuyu beklerken takılmaz.
    Sunucu çıktısı <KEY>-sunucu.log'a gider. Dönüş: (adres veya None, günlük dosyası).
    """
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    log = Path(input_path).with_name(Path(input_path).stem + "-sunucu.log")
    script = Path(__file__).resolve().parent / "secim_sunucu.py"
    cmd = [sys.executable, "-X", "utf8", str(script), str(input_path), "--port", str(port)]
    if not open_browser:
        cmd.append("--no-open")
    flags = ({"creationflags": subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP}
             if os.name == "nt" else {"start_new_session": True})
    with open(log, "w", encoding="utf-8") as out:
        subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=out, stderr=subprocess.STDOUT, close_fds=True, **flags)
    url = f"http://127.0.0.1:{port}/"
    for _ in range(50):
        try:
            urllib.request.urlopen(url, timeout=1).close()
            return url, log
        except urllib.error.HTTPError:
            return url, log
        except OSError:
            time.sleep(0.2)
    return None, log


def main():
    # Windows konsolunda Türkçe karakterlerin yazdırılabilmesi için
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="scenario-generator JSON → Türkçe Gherkin, rapor, seçim listesi ve ekranı")
    parser.add_argument("input", help="scenario-generator JSON çıktısı (test-scenarios/<KEY>/<KEY>.json)")
    parser.add_argument("output", nargs="?", help="üretilecek .feature dosyası")
    parser.add_argument("--all", action="store_true",
                        help="JSON'un yanına <KEY>.feature, <KEY>-rapor.md, <KEY>-secim.md ve <KEY>-secim.html üret")
    parser.add_argument("--report", help="üretilecek kart yeterlilik raporu (.md)")
    parser.add_argument("--selection", help="seçim listesi (.md); varsa işaretler korunur")
    parser.add_argument("--html", help="senaryoların ekrandan incelenip seçildiği sayfa (.html)")
    parser.add_argument("--sunucu", action="store_true",
                        help="dosyaları ürettikten sonra 'Jira'da aç' düğmeli seçim sunucusunu arka planda başlat")
    parser.add_argument("--open", action="store_true", help="seçim ekranını (--sunucu ile sunucuyu) tarayıcıda aç")
    parser.add_argument("--card", help="parse_jira_xml.py çıktısı <KEY>-kart.json (varsayılan: JSON'un yanındaki)")
    parser.add_argument("--check", action="store_true", help="yalnızca doğrula, dosya üretme")
    parser.add_argument("--exclude-drafts", action="store_true", help="needs_clarification senaryoları .feature'a yazma")
    args = parser.parse_args()
    if args.all:
        stem = Path(args.input).with_suffix("")
        args.output = args.output or f"{stem}.feature"
        args.report = args.report or f"{stem}-rapor.md"
        args.selection = args.selection or f"{stem}-secim.md"
        args.html = args.html or f"{stem}-secim.html"
    if not (args.check or args.output or args.report or args.selection or args.html):
        parser.error("--all, çıktı dosyası, --report, --selection, --html veya --check verilmeli")

    rep = Report()
    try:
        schema = load_json(SCHEMA_PATH)
        doc = prepare(args.input, args.card, schema, rep)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[HATA] dosya okunamadı: {exc}", file=sys.stderr)
        return 2

    written = []
    if not rep.errors and not args.check:
        if args.output:
            text, count = render_feature(doc, args.exclude_drafts, rep)
            Path(args.output).write_text(text, encoding="utf-8")
            written.append(f"{args.output}: {count} senaryo")
        if args.report:
            Path(args.report).write_text(render_report(doc), encoding="utf-8")
            written.append(f"{args.report}: yeterlilik raporu")
        previous = {}
        if args.selection and Path(args.selection).exists():
            previous, dupes = read_selection(args.selection)
            for sid in sorted(set(dupes)):
                rep.warn(f"seçim {sid}", "listede birden fazla kez geçiyor; son satırdaki işaret kullanıldı")
        states = selection_states(doc, previous, rep)
        selected = f"{sum(states.values())}/{len(states)} işaretli"
        if args.selection:
            Path(args.selection).write_text(render_selection(doc, states), encoding="utf-8")
            written.append(f"{args.selection}: seçim listesi ({selected})")
        if args.html:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            import selection_page
            record = Path(args.input).with_name(Path(args.input).stem + "-jira.json")  # jira_create.py kaydı
            kayit = load_json(record) if record.exists() else None
            Path(args.html).write_text(selection_page.selection_page(doc, states, kayit), encoding="utf-8")
            written.append(f"{args.html}: seçim ekranı ({selected})")
            if args.open and not args.sunucu:
                webbrowser.open(Path(args.html).resolve().as_uri())
        if args.sunucu:
            url, log = start_selection_server(args.input, args.open)
            written.append(f"Seçim ekranı ('Jira'da aç' ile): {url}" if url
                           else f"[UYARI] seçim sunucusu başlamadı; ayrıntı: {log}")

    for line in rep.errors + rep.warnings:
        print(line, file=sys.stderr)
    if rep.errors:
        print(f"\n{len(rep.errors)} hata. Dosya üretilmedi.", file=sys.stderr)
        return 1
    if args.check:
        print(f"Doğrulama başarılı ({len(doc['test_scenarios'])} senaryo).", file=sys.stderr)
    for w in written:
        print(w, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

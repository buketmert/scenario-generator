#!/usr/bin/env python3
"""scenario-generator JSON çıktısını doğrular; manuel test için Türkçe Gherkin
(.feature) dosyası ve kart yeterlilik raporu (.md) üretir.

Kullanım:
    python scripts/render_gherkin.py cikti.json cikti.feature --report rapor.md
    python scripts/render_gherkin.py cikti.json --check            # yalnızca doğrula
    python scripts/render_gherkin.py cikti.json cikti.feature --exclude-drafts

Çıkış kodu: 0 = hata yok, 1 = doğrulama hatası, 2 = kullanım/dosya hatası.
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "references" / "output-schema.json"

KEYWORDS = {"given": "Diyelim ki", "when": "Eğer ki", "then": "O zaman", "and": "Ve", "but": "Fakat"}
PHASE = {"given": 1, "when": 2, "then": 3}
PARAM_RE = re.compile(r"<([a-zçğıöşü][a-zçğıöşü0-9_]*)>")
QUOTE_RE = re.compile(r'"([^"]+)"')
RISK_ORDER = ["low", "medium", "high", "critical"]
CHECK_IDS = [f"R{i}" for i in range(1, 11)]
KIND_PREFIX = {"AC": "acceptance_criterion", "BR": "business_rule", "UI": "ui_detail", "CN": "constraint"}
TECHNIQUE_PREFIX = {
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
}


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
    if any(checks[r] == "fail" for r in ("R2", "R3", "R7", "R10")):
        expected = "not_ready"
    elif any(v != "pass" for v in checks.values()):
        expected = "partial"
    else:
        expected = "ready"
    if doc["readiness"]["status"] != expected:
        rep.error("readiness", f"status '{doc['readiness']['status']}' olmalı: '{expected}'")

    inv = doc["card_inventory"]
    if any(c["status"] == "unresolved" for c in doc["conflicts"]) and checks["R7"] == "pass":
        rep.error("readiness R7", "çözülmemiş çelişki varken R7 'pass' olamaz")
    if not doc["test_environment"]["details"] and checks["R9"] == "pass":
        rep.error("readiness R9", "test_environment.details boşken R9 'pass' olamaz")
    gaps = [a["name"] for a in inv["attachments"] if a["status"] in ("not_readable", "not_provided")]
    gaps += [l["name"] for l in inv["external_links"] if l["status"] == "not_accessible"]
    gaps += [l["key"] for l in inv["linked_issues"] if l["status"] == "not_accessible"]
    gaps += [f["field"] for f in inv["fields"] if f["status"] == "not_provided"]
    if gaps and checks["R10"] == "pass":
        rep.error("readiness R10", f"işlenemeyen kaynaklar varken R10 'pass' olamaz: {gaps}")

    for q in doc["readiness"]["clarification_questions"]:
        for b in q.get("related_basis_ids", []):
            if b not in ids["basis"]:
                rep.error(q["id"], f"tanımsız test esası öğesi {b}")
        for c in q.get("related_conflict_ids", []):
            if c not in ids["conflicts"]:
                rep.error(q["id"], f"tanımsız çelişki {c}")


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
    phase, phases, went_back = 0, [], False
    for s in steps:
        kw = s["keyword"]
        new_phase = PHASE.get(kw, phase)
        if new_phase < phase:
            went_back = True
        phase = new_phase
        phases.append(phase)
    if 3 not in phases:
        rep.error(where, "beklenen sonuç adımı ('O zaman') yok")
    elif phases[-1] != 3:
        rep.error(where, "senaryo beklenen sonuçla ('O zaman' bloğu) bitmiyor")
    if 2 not in phases:
        rep.warn(where, "eylem adımı ('Eğer ki') yok")
    if went_back:
        rep.warn(where, "sonuçtan sonra yeni eylem veya ön koşul var; tek davranış için senaryoyu bölmeyi düşünün")
    return phases


def check_scenario(sc, doc, rep, ids, basis_texts):
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

    levels = [ids["conds"][c]["risk"]["level"] for c in tr_["test_condition_ids"] if c in ids["conds"]]
    if levels:
        expected = max(levels, key=RISK_ORDER.index)
        if sc["priority"] != expected:
            rep.error(sid, f"priority '{sc['priority']}' olmalı: '{expected}' (bağlı koşulların en yüksek riski)")

    blocking = [q for q in sc.get("open_question_ids", []) if ids["questions"].get(q, {}).get("blocking")]
    if is_draft and not blocking:
        rep.error(sid, "needs_clarification senaryoda en az bir bloklayıcı soru olmalı")
    if not is_draft and blocking:
        rep.error(sid, f"ready senaryo bloklayıcı soruya bağlı: {blocking}")

    phases = check_steps(sc["steps"], sid, rep, has_background=bool(doc["feature"].get("background")))

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
                        (rep.warn if is_draft else rep.error)(sid, msg)


def check_document(doc, schema, rep):
    check_schema(doc, schema, rep)
    if rep.errors:
        return  # yapı bozuksa anlamsal kontroller yanıltıcı olur

    inv = {
        "attachments": {a["name"]: a for a in doc["card_inventory"]["attachments"]},
        "comments": {c["id"]: c for c in doc["card_inventory"]["comments"]},
        "linked": {l["key"] for l in doc["card_inventory"]["linked_issues"]},
    }
    ids = {
        "basis": {b["id"]: b for b in doc["test_basis"]["items"]},
        "conds": {c["id"]: c for c in doc["test_conditions"]},
        "items": {i["id"]: i for i in doc["coverage_items"]},
        "questions": {q["id"]: q for q in doc["readiness"]["clarification_questions"]},
        "assumptions": {a["id"] for a in doc["assumptions"]},
        "conflicts": {c["id"] for c in doc["conflicts"]},
    }
    basis_texts = [b["text"] for b in doc["test_basis"]["items"]]
    scenarios = doc["test_scenarios"]

    check_inventory_and_basis(doc, rep, ids, inv)
    check_readiness(doc, rep, ids)
    check_conflicts(doc, rep, ids)

    for cond in doc["test_conditions"]:
        r = cond["risk"]
        if risk_level(r["likelihood"], r["impact"]) != r["level"]:
            rep.error(cond["id"], f"risk level '{r['level']}' olmalı: '{risk_level(r['likelihood'], r['impact'])}'")
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
    if doc["feature"].get("background"):
        check_steps(doc["feature"]["background"], "feature.background", rep, False, is_background=True)
    for sc in scenarios:
        check_scenario(sc, doc, rep, ids, basis_texts)

    # kapsam özeti
    summary = doc["coverage_summary"]
    covered = {i for s in scenarios for i in s["traceability"]["coverage_item_ids"]}
    listed = {u["coverage_item_id"] for u in summary["uncovered_items"]}
    actual = set(ids["items"]) - covered
    if listed != actual:
        rep.error("coverage_summary.uncovered_items", f"listelenen {sorted(listed)}, gerçekte kapsanmayan {sorted(actual)}")
    for u in summary["uncovered_items"]:
        if "question_id" in u and u["question_id"] not in ids["questions"]:
            rep.error("uncovered_items", f"tanımsız soru {u['question_id']}")
    for t in summary["techniques"]:
        total = [i for i in ids["items"].values() if i["technique"] == t["technique"]]
        cov = [i for i in total if i["id"] in covered]
        pct = round(100 * len(cov) / len(total), 2) if total else 0
        if (t["total_items"], t["covered_items"]) != (len(total), len(cov)) or abs(t["coverage_percent"] - pct) > 0.01:
            rep.error(f"coverage_summary {t['technique']}",
                      f"yazılan {t['covered_items']}/{t['total_items']} %{t['coverage_percent']}, hesaplanan {len(cov)}/{len(total)} %{pct}")
    requirements = {b for b, item in ids["basis"].items() if item["kind"] in ("acceptance_criterion", "business_rule")}
    if {b["basis_id"] for b in summary["basis"]} != requirements:
        rep.error("coverage_summary.basis", f"her AC ve BR öğesi bir kez yer almalı: {sorted(requirements)}")
    for b in summary["basis"]:
        actual_ids = sorted(s["id"] for s in scenarios if b["basis_id"] in s["traceability"]["basis_ids"])
        if sorted(b["scenario_ids"]) != actual_ids:
            rep.error(f"coverage_summary {b['basis_id']}", f"yazılan {b['scenario_ids']}, hesaplanan {actual_ids}")
        if not actual_ids and b["status"] != "not_covered":
            rep.error(f"coverage_summary {b['basis_id']}", "senaryosu yokken status 'not_covered' olmalı")
    types = Counter(s["scenario_type"] for s in scenarios)
    statuses = Counter(s["status"] for s in scenarios)
    expected_counts = {
        "total": len(scenarios), "positive": types["positive"], "negative": types["negative"],
        "ready": statuses["ready"], "needs_clarification": statuses["needs_clarification"],
    }
    if summary["scenario_counts"] != expected_counts:
        rep.error("scenario_counts", f"yazılan {summary['scenario_counts']}, hesaplanan {expected_counts}")


# ------------------------------------------------------------------ .feature

def table(rows, indent):
    cells = [[str("" if c is None else c).replace("|", "\\|") for c in row] for row in rows]
    widths = [max(len(r[i]) for r in cells) for i in range(len(cells[0]))]
    return [indent + "| " + " | ".join(c.ljust(w) for c, w in zip(r, widths)) + " |" for r in cells]


def render_steps(steps, indent, values=None):
    return [f"{indent}{KEYWORDS[s['keyword']]} {substitute(s['text'], values) if values is not None else s['text']}"
            for s in steps]


def render_feature(doc, exclude_drafts, rep):
    src, feat, env = doc["source"], doc["feature"], doc["test_environment"]
    open_q = [q["id"] for q in doc["readiness"]["clarification_questions"]]
    questions = {q["id"]: q for q in doc["readiness"]["clarification_questions"]}
    assumptions = {a["id"]: a for a in doc["assumptions"]}
    status_line = f"# Kart durumu: {doc['readiness']['status']}"
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
        draft = sc["status"] == "needs_clarification"
        if draft and exclude_drafts:
            rep.warn(sc["id"], "taslak senaryo --exclude-drafts nedeniyle üretilmedi")
            continue
        tags = [f"@{sc['id']}", "@pozitif" if sc["scenario_type"] == "positive" else "@negatif"]
        tags += [t for t in sc.get("tags", []) if t not in tags]
        if draft:
            tags.append("@taslak")
        data_sets = sc["test_data"]["data_sets"]
        outline = len(data_sets) > 1
        t = sc["traceability"]
        trace = f"# Kaynak: {', '.join(t['basis_ids'])} | {', '.join(t['test_condition_ids'])}"
        if t["coverage_item_ids"]:
            trace += f" | {', '.join(t['coverage_item_ids'])}"
        out += ["", "  " + " ".join(tags),
                f"  {'Senaryo Taslağı' if outline else 'Senaryo'}: {sc['title']}",
                f"    {trace}"]
        if draft:
            for q in sc.get("open_question_ids", []):
                out.append(f"    # Taslak — açık soru {q}: {questions[q]['question']}")
            for a in sc.get("assumption_ids", []):
                out.append(f"    # Varsayım {a}: {assumptions[a]['statement']}")
        for note in sc.get("notes", []):
            out.append(f"    # Not: {note}")
        if outline:
            params = [p["name"] for p in sc["test_data"]["parameters"]]
            out += render_steps(sc["steps"], "    ")
            out += ["", "    Örnekler:"]
            out += table([["durum"] + params] + [[ds["label"]] + [ds["values"].get(p) for p in params] for ds in data_sets], "      ")
        else:
            if data_sets:
                out.append(f"    # Veri: {data_sets[0]['label']}")
            out += render_steps(sc["steps"], "    ", data_sets[0]["values"] if data_sets else {})
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


def render_report(doc):
    src, rd, inv = doc["source"], doc["readiness"], doc["card_inventory"]
    scenarios = doc["test_scenarios"]
    counts = doc["coverage_summary"]["scenario_counts"]
    questions = sorted(rd["clarification_questions"], key=lambda q: (not q["blocking"], q["id"]))
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


def main():
    # Windows konsolunda Türkçe karakterlerin yazdırılabilmesi için
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="scenario-generator JSON → Türkçe Gherkin + yeterlilik raporu")
    parser.add_argument("input", help="scenario-generator JSON çıktısı")
    parser.add_argument("output", nargs="?", help="üretilecek .feature dosyası")
    parser.add_argument("--report", help="üretilecek kart yeterlilik raporu (.md)")
    parser.add_argument("--check", action="store_true", help="yalnızca doğrula, dosya üretme")
    parser.add_argument("--exclude-drafts", action="store_true", help="needs_clarification senaryoları üretme")
    args = parser.parse_args()
    if not args.check and not args.output and not args.report:
        parser.error("çıktı dosyası, --report veya --check verilmeli")

    try:
        schema = load_json(SCHEMA_PATH)
        doc = load_json(args.input)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[HATA] dosya okunamadı: {exc}", file=sys.stderr)
        return 2

    rep = Report()
    check_document(doc, schema, rep)

    written = []
    if not rep.errors and not args.check:
        if args.output:
            text, count = render_feature(doc, args.exclude_drafts, rep)
            Path(args.output).write_text(text, encoding="utf-8")
            written.append(f"{args.output}: {count} senaryo")
        if args.report:
            Path(args.report).write_text(render_report(doc), encoding="utf-8")
            written.append(f"{args.report}: yeterlilik raporu")

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

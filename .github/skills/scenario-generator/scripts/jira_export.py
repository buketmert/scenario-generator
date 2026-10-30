#!/usr/bin/env python3
"""Seçim listesinde işaretli senaryolardan Jira CSV içe aktarım dosyası üretir.

Her işaretli senaryo, kaynak karta bağlantıyla bağlanacak bir Test Senaryosu
kartıdır. Agent Jira'ya bağlanmaz; dosyayı kullanıcı Jira'nın CSV içe
aktarımıyla yükler ve "Kaynak Kart" sütununu kurumdaki bağlantı türüne eşler.

Kart alanları ayrı sütunlardadır (Ön Koşullar, Test Adımları, Beklenen Sonuç,
Test Verisi); kurumun Test Senaryosu kartında bu alanlar yoksa sütunlar
eşlenmeden bırakılır, aynı içerik Description'da da vardır.

Kullanım:
    python scripts/jira_export.py cikti.json cikti-secim.md cikti-jira.csv
    python scripts/jira_export.py cikti.json cikti-secim.md cikti-jira.csv --issue-type "Test Case"

Çıkış kodu: 0 = dosya üretildi, 1 = doğrulama veya seçim hatası, 2 = kullanım/dosya hatası.
"""

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_gherkin as rg  # noqa: E402

# Jira'nın varsayılan öncelik adları; kurumda farklıysa içe aktarma sihirbazında eşlenir.
JIRA_PRIORITY = {"critical": "Highest", "high": "High", "medium": "Medium", "low": "Low"}
TECHNIQUES = {
    "use_case_based": "uçtan uca akış",
    "acceptance_criteria_based": "kabul kriterine dayalı",
    "equivalence_partitioning": "denklik paylarına ayırma",
    "boundary_value_analysis": "sınır değer analizi",
    "decision_table": "karar tablosu",
    "state_transition": "durum geçişi",
    "error_guessing": "hata tahmini",
    "checklist_based": "kontrol listesi",
}
FLOW_LABELS = {"main": "ana-akis", "alternative": "alternatif-akis", "exception": "hata-akisi"}
COLUMNS = ["Summary", "Issue Type", "Priority", "Kaynak Kart", "Akış",
           "Ön Koşullar", "Test Adımları", "Beklenen Sonuç", "Test Verisi", "Description"]


def phased_lines(steps, values):
    """Adımları Türkçe anahtar kelimeleriyle ve evreleriyle (1 ön koşul, 2 eylem, 3 sonuç) döndürür."""
    phase, out = 1, []
    for s in steps:
        phase = rg.PHASE.get(s["keyword"], phase)
        text = rg.substitute(s["text"], values) if values is not None else s["text"]
        out.append((phase, f"{rg.KEYWORDS[s['keyword']]} {text}"))
    return out


def numbered(lines):
    return "\n".join(f"{n}. {line}" for n, line in enumerate(lines, 1))


def card_fields(doc, sc):
    """Ön koşullar, uçtan uca test adımları, beklenen sonuç ve test verisi."""
    data_sets = sc["test_data"]["data_sets"]
    values = data_sets[0]["values"] if len(data_sets) == 1 else None
    background = phased_lines(doc["feature"].get("background", []), None)
    steps = phased_lines(sc["steps"], values)
    preconditions = [t for p, t in background + steps if p == 1]
    actions = [t for p, t in steps if p > 1]
    expected = [t for p, t in steps if p == 3]
    if len(data_sets) == 1:
        data = f"{data_sets[0]['label']}\n" + "\n".join(f"* {k}: {v}" for k, v in data_sets[0]["values"].items())
    elif data_sets:
        params = [p["name"] for p in sc["test_data"]["parameters"]]
        cell = lambda v: str("" if v is None or v == "" else v).replace("|", "\\|") or " "
        data = "\n".join(["||durum||" + "||".join(params) + "||"]
                         + ["|" + "|".join(cell(v) for v in [ds["label"]] + [ds["values"].get(p) for p in params]) + "|"
                            for ds in data_sets])
    else:
        data = ""
    return numbered(preconditions), numbered(actions), numbered(expected), data


def gherkin_block(doc, sc, questions, assumptions, items):
    """Kart tek başına okunabilsin diye Özellik ve Geçmiş dâhil tek senaryoluk Gherkin."""
    feat = doc["feature"]
    out = ["# language: tr", f"Özellik: {feat['name']}"]
    if feat.get("background"):
        out += ["", "  Geçmiş:"] + rg.render_steps(feat["background"], "    ")
    out += [""] + rg.render_scenario(sc, questions, assumptions, items, comments=False)
    return "\n".join(out)


def description(doc, sc, questions, assumptions, items):
    """Jira wiki biçiminde açıklama: özet alanlar, Gherkin, son koşullar, notlar, açık sorular."""
    t = sc["traceability"]
    trace = " | ".join(", ".join(ids) for ids in (t["basis_ids"], t["test_condition_ids"], t["coverage_item_ids"]) if ids)
    lines = [f"*Amaç:* {sc['objective']}"]
    for flow in rg.flow_of(sc, items):
        lines.append(f"*Akış ({rg.tr(flow['flow_type'])}):* {flow['description']}")
    lines += [
        f"*Kaynak kart:* {doc['source']['jira_key']}",
        f"*Öncelik (risk):* {rg.tr(sc['priority'])} | *Tür:* {rg.tr(sc['scenario_type'])}"
        f" | *Teknik:* {', '.join(TECHNIQUES[x] for x in sc['techniques'])}",
        f"*İzlenebilirlik:* {trace}",
        f"*Test ortamı:* {doc['test_environment']['summary']}",
        "", "{noformat}", gherkin_block(doc, sc, questions, assumptions, items), "{noformat}",
    ]
    sections = [
        ("Son koşullar", sc.get("postconditions", [])),
        ("Notlar", sc.get("notes", [])),
        ("Taslak — açık sorular", [f"{q}: {questions[q]['question']}" for q in sc.get("open_question_ids", [])]
         if sc["status"] == "needs_clarification" else []),
        ("Varsayımlar", [f"{a}: {assumptions[a]['statement']}" for a in sc.get("assumption_ids", [])]),
    ]
    for title, entries in sections:
        if entries:
            lines += ["", f"*{title}:*"] + [f"* {e}" for e in entries]
    return "\n".join(lines)


def labels(doc, sc, items):
    values = [t.lstrip("@") for t in doc["feature"]["tags"] + sc.get("tags", [])]
    values += [FLOW_LABELS[f["flow_type"]] for f in rg.flow_of(sc, items)]
    values.append("pozitif" if sc["scenario_type"] == "positive" else "negatif")
    if sc["status"] == "needs_clarification":
        values.append("taslak")
    values.append(doc["source"]["jira_key"])  # bağlantı kurulamazsa kartın senaryoları etiketle bulunur
    return list(dict.fromkeys(values))


def selected_scenarios(doc, selection_path, rep):
    """İşaretli senaryolar, koşum sırasıyla. Liste JSON'la uyuşmuyorsa hata yazar."""
    states, dupes = rg.read_selection(selection_path)
    by_id = {s["id"]: s for s in doc["test_scenarios"]}
    for sid in sorted(set(dupes)):
        rep.error(f"seçim {sid}", "listede birden fazla kez geçiyor")
    for sid in sorted(set(states) - set(by_id)):
        rep.error(f"seçim {sid}", "JSON'da böyle bir senaryo yok; liste başka bir JSON'a ait olabilir")
    for sid, (_, title) in states.items():
        if sid in by_id and title != by_id[sid]["title"]:
            rep.error(f"seçim {sid}", "başlık JSON'dakiyle aynı değil; listeyi render_gherkin.py --selection ile yenileyin")
    for sid in sorted(set(by_id) - set(states)):
        rep.warn(f"seçim {sid}", "listede yok; aktarılmadı")
    chosen = [by_id[sid] for sid, (checked, _) in states.items() if checked and sid in by_id]
    for sc in chosen:
        if sc["status"] == "needs_clarification":
            rep.warn(f"seçim {sc['id']}", "taslak senaryo aktarılıyor; bloklayıcı soru yanıtlanmadı")
    if not chosen and not rep.errors:
        rep.error("seçim", "işaretli senaryo yok")
    return rg.execution_order(chosen)


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="İşaretli senaryolar → Jira Test Senaryosu kartları (CSV)")
    parser.add_argument("input", help="scenario-generator JSON çıktısı")
    parser.add_argument("selection", help="render_gherkin.py --selection ile üretilmiş seçim listesi (.md)")
    parser.add_argument("output", help="üretilecek CSV dosyası")
    parser.add_argument("--issue-type", default="Test Senaryosu",
                        help="oluşturulacak Jira kart türü (varsayılan: Test Senaryosu)")
    args = parser.parse_args()

    try:
        schema = rg.load_json(rg.SCHEMA_PATH)
        doc = rg.load_json(args.input)
        Path(args.selection).read_text(encoding="utf-8")
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[HATA] dosya okunamadı: {exc}", file=sys.stderr)
        return 2

    rep = rg.Report()
    rg.check_document(doc, schema, rep)
    chosen = [] if rep.errors else selected_scenarios(doc, args.selection, rep)

    if not rep.errors:
        questions = {q["id"]: q for q in doc["readiness"]["clarification_questions"]}
        assumptions = {a["id"]: a for a in doc["assumptions"]}
        items = {i["id"]: i for i in doc["coverage_items"]}
        rows = [(sc, labels(doc, sc, items)) for sc in chosen]
        width = max(len(lbl) for _, lbl in rows)
        with open(args.output, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            writer.writerow(COLUMNS + ["Labels"] * width)
            for sc, lbl in rows:
                flow = ", ".join(rg.tr(fl["flow_type"]) for fl in rg.flow_of(sc, items))
                writer.writerow([f"[{sc['id']}] {sc['title']}", args.issue_type, JIRA_PRIORITY[sc["priority"]],
                                 doc["source"]["jira_key"], flow, *card_fields(doc, sc),
                                 description(doc, sc, questions, assumptions, items)]
                                + lbl + [""] * (width - len(lbl)))

    for line in rep.errors + rep.warnings:
        print(line, file=sys.stderr)
    if rep.errors:
        print(f"\n{len(rep.errors)} hata. CSV üretilmedi.", file=sys.stderr)
        return 1
    print(f"{args.output}: {len(chosen)} {args.issue_type} kartı — {', '.join(s['id'] for s in chosen)}",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Seçim listesinde işaretli senaryolardan Jira CSV içe aktarım dosyası üretir.

Her işaretli senaryo, kaynak kartla ilişkilendirilecek bir Jira kaydıdır
(varsayılan tür: Test). Agent Jira'ya bağlanmaz; dosyayı kullanıcı Jira'nın
CSV içe aktarımıyla yükler ve "Kaynak Kart" sütununu kurumdaki ilişkiye
(Parent veya bir bağlantı türü) eşler.

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
    "acceptance_criteria_based": "kabul kriterine dayalı",
    "equivalence_partitioning": "denklik paylarına ayırma",
    "boundary_value_analysis": "sınır değer analizi",
    "decision_table": "karar tablosu",
    "state_transition": "durum geçişi",
    "error_guessing": "hata tahmini",
    "checklist_based": "kontrol listesi",
}


def gherkin_block(doc, sc, questions, assumptions):
    """Kayıt tek başına okunabilsin diye Özellik ve Geçmiş dâhil tek senaryoluk Gherkin."""
    feat = doc["feature"]
    out = ["# language: tr", f"Özellik: {feat['name']}"]
    if feat.get("background"):
        out += ["", "  Geçmiş:"] + rg.render_steps(feat["background"], "    ")
    out += [""] + rg.render_scenario(sc, questions, assumptions, comments=False)
    return "\n".join(out)


def description(doc, sc, questions, assumptions):
    """Jira wiki biçiminde açıklama: özet alanlar, Gherkin, son koşullar, notlar, açık sorular."""
    t = sc["traceability"]
    trace = " | ".join(", ".join(ids) for ids in (t["basis_ids"], t["test_condition_ids"], t["coverage_item_ids"]) if ids)
    lines = [
        f"*Amaç:* {sc['objective']}",
        f"*Kaynak kart:* {doc['source']['jira_key']}",
        f"*Öncelik (risk):* {rg.tr(sc['priority'])} | *Tür:* {rg.tr(sc['scenario_type'])}"
        f" | *Teknik:* {', '.join(TECHNIQUES[x] for x in sc['techniques'])}",
        f"*İzlenebilirlik:* {trace}",
        f"*Test ortamı:* {doc['test_environment']['summary']}",
    ]
    data_sets = sc["test_data"]["data_sets"]
    if len(data_sets) == 1:
        lines.append(f"*Veri:* {data_sets[0]['label']}")
    lines += ["", "{noformat}", gherkin_block(doc, sc, questions, assumptions), "{noformat}"]
    sections = [
        ("Son koşullar", sc.get("postconditions", [])),
        ("Notlar", sc.get("notes", [])),
        ("Taslak — açık sorular", [f"{q}: {questions[q]['question']}" for q in sc.get("open_question_ids", [])]
         if sc["status"] == "needs_clarification" else []),
        ("Varsayımlar", [f"{a}: {assumptions[a]['statement']}" for a in sc.get("assumption_ids", [])]),
    ]
    for title, items in sections:
        if items:
            lines += ["", f"*{title}:*"] + [f"* {item}" for item in items]
    return "\n".join(lines)


def labels(doc, sc):
    values = [t.lstrip("@") for t in doc["feature"]["tags"] + sc.get("tags", [])]
    values.append("pozitif" if sc["scenario_type"] == "positive" else "negatif")
    if sc["status"] == "needs_clarification":
        values.append("taslak")
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
    parser = argparse.ArgumentParser(description="İşaretli senaryolar → Jira CSV içe aktarım dosyası")
    parser.add_argument("input", help="scenario-generator JSON çıktısı")
    parser.add_argument("selection", help="render_gherkin.py --selection ile üretilmiş seçim listesi (.md)")
    parser.add_argument("output", help="üretilecek CSV dosyası")
    parser.add_argument("--issue-type", default="Test", help="oluşturulacak Jira kayıt türü (varsayılan: Test)")
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
        rows = [(sc, labels(doc, sc)) for sc in chosen]
        width = max(len(lbl) for _, lbl in rows)
        with open(args.output, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            writer.writerow(["Summary", "Issue Type", "Priority", "Kaynak Kart", "Description"] + ["Labels"] * width)
            for sc, lbl in rows:
                writer.writerow([f"[{sc['id']}] {sc['title']}", args.issue_type, JIRA_PRIORITY[sc["priority"]],
                                 doc["source"]["jira_key"], description(doc, sc, questions, assumptions)]
                                + lbl + [""] * (width - len(lbl)))

    for line in rep.errors + rep.warnings:
        print(line, file=sys.stderr)
    if rep.errors:
        print(f"\n{len(rep.errors)} hata. CSV üretilmedi.", file=sys.stderr)
        return 1
    print(f"{args.output}: {len(chosen)} senaryo ({args.issue_type}) — {', '.join(s['id'] for s in chosen)}",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

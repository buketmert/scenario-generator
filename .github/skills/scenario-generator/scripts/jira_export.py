#!/usr/bin/env python3
"""Seçim listesinde işaretli senaryolardan Jira CSV içe aktarım dosyası üretir.

Her işaretli senaryo, kaynak karta bağlantıyla bağlanacak bir Test Senaryosu
kartıdır. Agent Jira'ya bağlanmaz; dosyayı kullanıcı Jira'nın CSV içe
aktarımıyla yükler ve "Kaynak Kart" sütununu kurumdaki bağlantı türüne eşler.

Kart alanları ayrı sütunlardadır (Ön Koşullar, Test Adımları, Beklenen Sonuç,
Test Verisi); kurumun Test Senaryosu kartında bu alanlar yoksa sütunlar
eşlenmeden bırakılır, aynı içerik Description'da da vardır.

Ekrandan seçim: render_gherkin.py --html (veya --all) bu modüldeki
selection_page() ile bir sayfa üretir. CSV satırları orada da burada
hesaplanır; sayfadaki betik yalnızca işaretli satırları birleştirip indirir.

Kullanım:
    python scripts/jira_export.py cikti.json cikti-secim.md cikti-jira.csv
    python scripts/jira_export.py cikti.json cikti-secim.md cikti-jira.csv --issue-type "Test Case"

Çıkış kodu: 0 = dosya üretildi, 1 = doğrulama veya seçim hatası, 2 = kullanım/dosya hatası.
"""

import argparse
import csv
import html
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
    linked_q = [questions[q] for q in sc.get("open_question_ids", [])]
    sections = [
        ("Son koşullar", sc.get("postconditions", [])),
        ("Notlar", sc.get("notes", [])),
        ("Netleştirmeler (kullanıcı yanıtı)", [f"{q['id']}: {q['question']} → {q['answer'].get('text', '')}"
                                               for q in linked_q if rg.is_answered(q)]),
        ("Taslak — açık sorular", [f"{q['id']}: {q['question']}" for q in linked_q if not rg.is_answered(q)]),
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


def csv_row(doc, sc, issue_type, questions, assumptions, items):
    """Bir Test Senaryosu kartının CSV hücreleri ve etiketleri (etiket sütunları ayrıca hizalanır)."""
    flow = ", ".join(rg.tr(fl["flow_type"]) for fl in rg.flow_of(sc, items))
    cells = [f"[{sc['id']}] {sc['title']}", issue_type, JIRA_PRIORITY[sc["priority"]], doc["source"]["jira_key"],
             flow, *card_fields(doc, sc), description(doc, sc, questions, assumptions, items)]
    return cells, labels(doc, sc, items)


def lookups(doc):
    return ({q["id"]: q for q in doc["readiness"]["clarification_questions"]},
            {a["id"]: a for a in doc["assumptions"]},
            {i["id"]: i for i in doc["coverage_items"]})


PAGE_CSS = """
:root { --bg:#f6f7f9; --panel:#ffffff; --text:#1d2330; --muted:#5d6676; --line:#dfe3ea; --accent:#1f5fbf;
  --accent-text:#ffffff; --on:#eaf1fd; --warn-bg:#fff4e0; --warn:#8a5300; --draft:#b45309; --code:#f0f2f5; }
@media (prefers-color-scheme: dark) { :root { --bg:#14171c; --panel:#1c2027; --text:#e6e9ef; --muted:#9aa3b2;
  --line:#2e343e; --accent:#5b9bff; --accent-text:#0b1220; --on:#1d2a3f; --warn-bg:#3a2a12; --warn:#ffc46b;
  --draft:#f5a524; --code:#242a33; } }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--text); font:15px/1.5 system-ui, "Segoe UI", sans-serif; }
main { max-width:960px; margin:0 auto; padding:24px 16px 48px; }
h1 { font-size:1.35rem; margin:0 0 4px; } .sub { color:var(--muted); margin:0 0 16px; }
.bar { position:sticky; top:0; z-index:1; display:flex; flex-wrap:wrap; gap:8px; align-items:center;
  background:var(--bg); padding:10px 0; border-bottom:1px solid var(--line); margin-bottom:12px; }
button { font:inherit; border:1px solid var(--line); background:var(--panel); color:var(--text);
  border-radius:6px; padding:6px 12px; cursor:pointer; }
button.primary { background:var(--accent); color:var(--accent-text); border-color:var(--accent); margin-left:auto; }
button:disabled { opacity:.5; cursor:not-allowed; }
#sayi { color:var(--muted); } #uyari { width:100%; background:var(--warn-bg); color:var(--warn);
  padding:6px 10px; border-radius:6px; }
ol { list-style:none; margin:0; padding:0; display:grid; gap:8px; }
li { background:var(--panel); border:1px solid var(--line); border-radius:8px; }
li.on { background:var(--on); border-color:var(--accent); }
.row { display:flex; gap:12px; padding:12px; cursor:pointer; align-items:flex-start; }
.row input { width:18px; height:18px; margin-top:3px; flex:none; }
.num { color:var(--muted); min-width:1.5em; } .main { display:grid; gap:4px; min-width:0; }
.title { font-weight:600; overflow-wrap:anywhere; }
.meta { display:flex; flex-wrap:wrap; gap:6px; font-size:.85rem; color:var(--muted); }
.meta code, pre { background:var(--code); border-radius:4px; }
.meta code { padding:0 4px; } .badge { border:1px solid var(--line); border-radius:999px; padding:0 8px; }
.badge.draft { color:var(--draft); border-color:var(--draft); }
details { padding:0 12px 12px 54px; } summary { cursor:pointer; color:var(--accent); }
pre { padding:10px; overflow:auto; font-size:.85rem; white-space:pre; }
.hint { color:var(--muted); font-size:.9rem; margin-top:20px; }
"""

PAGE_JS = """
(() => {
  const data = JSON.parse(document.getElementById('veri').textContent);
  const boxes = [...document.querySelectorAll('input[type=checkbox][value]')];
  const count = document.getElementById('sayi');
  const button = document.getElementById('indir');
  const warn = document.getElementById('uyari');
  const quote = s => '"' + String(s).replace(/"/g, '""') + '"';
  // Hücreler Python'da (jira_export.csv_row) hesaplandı; burada yalnızca seçilenler birleştirilir.
  function buildCsv(ids) {
    const width = Math.max(0, ...ids.map(id => data.labels[id].length));
    const lines = [data.header.concat(Array(width).fill('Labels')).map(quote).join(',')];
    for (const id of ids) {
      const labels = data.labels[id];
      lines.push(data.rows[id].concat(labels, Array(width - labels.length).fill('')).map(quote).join(','));
    }
    return lines.join('\\r\\n') + '\\r\\n';
  }
  window.buildCsv = buildCsv;
  const selected = () => boxes.filter(b => b.checked).map(b => b.value);
  function refresh() {
    const ids = selected();
    count.textContent = ids.length + ' / ' + boxes.length + ' senaryo seçili';
    button.disabled = !ids.length;
    button.textContent = 'Jira CSV indir (' + ids.length + ')';
    const drafts = boxes.filter(b => b.checked && b.hasAttribute('data-draft')).length;
    warn.hidden = !drafts;
    warn.textContent = drafts + ' taslak senaryo seçili: bloklayıcı sorusu yanıtlanmadı.';
    for (const b of boxes) b.closest('li').classList.toggle('on', b.checked);
  }
  document.querySelectorAll('[data-sec]').forEach(el => el.addEventListener('click', () => {
    for (const b of boxes) b.checked = el.dataset.sec === 'all' || (el.dataset.sec === 'ready' && !b.hasAttribute('data-draft'));
    refresh();
  }));
  boxes.forEach(b => b.addEventListener('change', refresh));
  button.addEventListener('click', () => {
    const blob = new Blob([buildCsv(selected())], { type: 'text/csv;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = data.key + '-jira.csv';
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  });
  refresh();
})();
"""


def selection_page(doc, states, issue_type="Test Senaryosu"):
    """Senaryoların ekrandan seçildiği, dış kaynak kullanmayan tek dosyalık sayfa."""
    e = html.escape
    questions, assumptions, items = lookups(doc)
    key, rd = doc["source"]["jira_key"], doc["readiness"]
    data = {"key": key, "header": COLUMNS, "rows": {}, "labels": {}}
    cards = []
    for n, sc in enumerate(rg.execution_order(doc["test_scenarios"]), 1):
        data["rows"][sc["id"]], data["labels"][sc["id"]] = csv_row(doc, sc, issue_type, questions, assumptions, items)
        draft = sc["status"] == "needs_clarification"
        badges = [rg.tr(f["flow_type"]) for f in rg.flow_of(sc, items)]
        badges += [rg.tr(sc["priority"]), rg.tr(sc["scenario_type"])] + sc.get("tags", [])
        meta = "".join(f'<span class="badge">{e(b)}</span>' for b in badges)
        if draft:
            open_q = [q for q in sc.get("open_question_ids", []) if not rg.is_answered(questions[q])]
            meta += f'<span class="badge draft">taslak · {e(", ".join(open_q))}</span>'
        post = "".join(f"<p>Son koşul: {e(p)}</p>" for p in sc.get("postconditions", []))
        cards.append(
            f'<li><label class="row"><input type="checkbox" value="{e(sc["id"])}"'
            f'{" checked" if states.get(sc["id"]) else ""}{" data-draft" if draft else ""}>'
            f'<span class="num">{n}.</span><span class="main"><span class="title">{e(sc["title"])}</span>'
            f'<span class="meta"><code>{e(sc["id"])}</code>{meta}</span></span></label>'
            f'<details><summary>Ayrıntı</summary><p>{e(sc["objective"])}</p>'
            f'<pre>{e(gherkin_block(doc, sc, questions, assumptions, items))}</pre>{post}</details></li>')
    open_q = [q["id"] for q in rd["clarification_questions"] if not rg.is_answered(q)]
    sub = f"Kart durumu: {rg.tr(rd['status'])} · {len(cards)} senaryo"
    if open_q:
        sub += f" · açık soru: {', '.join(open_q)}"
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    body = "\n".join(cards) if cards else f"<p>Seçilecek senaryo yok (kart durumu: {e(rg.tr(rd['status']))}).</p>"
    return (
        '<!doctype html>\n<html lang="tr">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{e(key)} · Senaryo seçimi</title>\n<style>{PAGE_CSS}</style>\n</head>\n<body>\n<main>\n"
        f"<h1>{e(key)} — {e(doc['source']['summary'])}</h1>\n<p class=\"sub\">{e(sub)}</p>\n"
        '<div class="bar"><button type="button" data-sec="all">Tümü</button>'
        '<button type="button" data-sec="ready">Hazırlar</button>'
        '<button type="button" data-sec="none">Hiçbiri</button><span id="sayi"></span>'
        '<button type="button" id="indir" class="primary">Jira CSV indir</button>'
        '<div id="uyari" hidden></div></div>\n'
        f"<ol>\n{body}\n</ol>\n"
        f'<p class="hint">Her seçili senaryo bir <b>{e(issue_type)}</b> kartıdır. CSV\'yi Jira\'da Issues → Import '
        "issues from CSV ile yükleyin (UTF-8); Kaynak Kart sütununu kaynak karta bağlayan bağlantı türüne eşleyin.</p>\n"
        f'</main>\n<script type="application/json" id="veri">{payload}</script>\n<script>{PAGE_JS}</script>\n'
        "</body>\n</html>\n")


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
    parser.add_argument("--card", help="parse_jira_xml.py çıktısı <KEY>-kart.json (varsayılan: JSON'un yanındaki)")
    args = parser.parse_args()

    rep = rg.Report()
    try:
        schema = rg.load_json(rg.SCHEMA_PATH)
        Path(args.selection).read_text(encoding="utf-8")
        doc = rg.prepare(args.input, args.card, schema, rep)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[HATA] dosya okunamadı: {exc}", file=sys.stderr)
        return 2

    chosen = [] if rep.errors else selected_scenarios(doc, args.selection, rep)

    if not rep.errors:
        rows = [csv_row(doc, sc, args.issue_type, *lookups(doc)) for sc in chosen]
        width = max(len(lbl) for _, lbl in rows)
        with open(args.output, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            writer.writerow(COLUMNS + ["Labels"] * width)
            for cells, lbl in rows:
                writer.writerow(cells + lbl + [""] * (width - len(lbl)))

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

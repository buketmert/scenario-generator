"""Senaryoların ekrandan incelenip seçildiği, dış kaynak kullanmayan tek dosyalık sayfa.

render_gherkin.py --html (veya --all) durağan sayfayı, secim_sunucu.py ise
"Jira'da aç" düğmeli sayfayı bu modülle üretir. Sayfa senaryoları koşum
sırasıyla listeler; her satırda akış türü, öncelik, pozitif/negatif ve taslak
işareti, "Ayrıntı" altında amaç, Geçmiş dâhil Gherkin ve son koşullar vardır.
İlk işaretler <KEY>-secim.md'dekilerdir; Jira'da açılmış senaryolar kartın
bağlantısıyla gösterilir ve yeniden seçilemez.
"""

import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_gherkin as rg  # noqa: E402

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
button.primary { background:var(--accent); color:var(--accent-text); border-color:var(--accent); }
button:disabled { opacity:.5; cursor:not-allowed; }
#sayi { color:var(--muted); margin-left:auto; } #uyari, .ayar { width:100%; background:var(--warn-bg); color:var(--warn);
  padding:6px 10px; border-radius:6px; }
#durum { width:100%; color:var(--muted); } #durum:empty { display:none; }
.jira { font-size:.9rem; } .jira a { color:var(--accent); font-weight:600; } .jira .hata { color:var(--warn); }
li.acik { opacity:.85; } .hint { color:var(--muted); font-size:.9rem; margin-top:20px; }
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
"""

PAGE_JS = """
(() => {
  const boxes = [...document.querySelectorAll('input[type=checkbox][value]')];
  const count = document.getElementById('sayi');
  const warn = document.getElementById('uyari');
  const button = document.getElementById('ac');
  const status = document.getElementById('durum');
  const open = () => boxes.filter(b => !b.disabled);
  const chosen = () => open().filter(b => b.checked);
  function refresh() {
    const inJira = boxes.length - open().length;
    count.textContent = chosen().length + ' / ' + open().length + ' senaryo seçili' + (inJira ? ' · ' + inJira + ' Jira\\'da' : '');
    const drafts = chosen().filter(b => b.hasAttribute('data-draft')).length;
    warn.hidden = !drafts;
    warn.textContent = drafts + ' taslak senaryo seçili: bloklayıcı sorusu yanıtlanmadı.';
    for (const b of boxes) b.closest('li').classList.toggle('on', b.checked);
    if (button) {
      button.disabled = button.hasAttribute('data-kapali') || !chosen().length;
      button.textContent = 'Jira\\'da aç (' + chosen().length + ')';
    }
  }
  function mark(result) {
    const box = boxes.find(b => b.value === result.id);
    if (!box) return;
    const li = box.closest('li');
    let line = li.querySelector('.jira');
    if (!line) {
      line = document.createElement('span');
      line.className = 'jira';
      li.querySelector('.main').appendChild(line);
    }
    line.textContent = '';
    if (result.key) {
      const a = document.createElement('a');
      a.href = result.url; a.target = '_blank'; a.rel = 'noopener'; a.textContent = result.key;
      line.append('Jira: ', a);
      box.checked = false; box.disabled = true; li.classList.add('acik');
    }
    if (result.mesaj) {
      const m = document.createElement('span');
      m.className = 'hata'; m.textContent = ' ' + result.mesaj;
      line.append(m);
    }
  }
  document.querySelectorAll('[data-sec]').forEach(el => el.addEventListener('click', () => {
    for (const b of open()) b.checked = el.dataset.sec === 'all' || (el.dataset.sec === 'ready' && !b.hasAttribute('data-draft'));
    refresh();
  }));
  boxes.forEach(b => b.addEventListener('change', refresh));
  if (button) button.addEventListener('click', async () => {
    const ids = chosen().map(b => b.value);
    button.disabled = true;
    status.textContent = ids.length + ' Test Senaryosu kartı açılıyor…';
    try {
      const response = await fetch('/api/ac', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Secim-Anahtari': button.dataset.anahtar },
        body: JSON.stringify({ ids }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.hata || ('HTTP ' + response.status));
      data.sonuclar.forEach(mark);
      const ok = data.sonuclar.filter(r => r.durum === 'acildi').length;
      const failed = data.sonuclar.filter(r => r.durum === 'hata' || r.durum === 'baglanamadi').length;
      status.textContent = ok + ' kart açıldı' + (failed ? ', ' + failed + ' senaryoda sorun var (satırlarda yazıyor).' : '.');
    } catch (error) {
      status.textContent = 'Kartlar açılamadı: ' + error.message;
    }
    refresh();
  });
  refresh();
})();
"""


def gherkin_block(doc, sc, questions, assumptions, items):
    """Senaryo tek başına okunabilsin diye Özellik ve Geçmiş dâhil tek senaryoluk Gherkin."""
    feat = doc["feature"]
    out = ["# language: tr", f"Özellik: {feat['name']}"]
    if feat.get("background"):
        out += ["", "  Geçmiş:"] + rg.render_steps(feat["background"], "    ")
    out += [""] + rg.render_scenario(sc, questions, assumptions, items, comments=False)
    return "\n".join(out)


def selection_page(doc, states, kayit=None, sunucu=None):
    """kayit: <KEY>-jira.json (Jira'da açılmış senaryolar). sunucu: {"anahtar": ..., "uyari": ...};
    verilirse sayfa "Jira'da aç" düğmesiyle secim_sunucu.py'ye bağlanır."""
    e = html.escape
    kayit = kayit or {}
    questions = {q["id"]: q for q in doc["readiness"]["clarification_questions"]}
    assumptions = {a["id"]: a for a in doc["assumptions"]}
    items = {i["id"]: i for i in doc["coverage_items"]}
    key, rd = doc["source"]["jira_key"], doc["readiness"]
    cards = []
    for n, sc in enumerate(rg.execution_order(doc["test_scenarios"]), 1):
        draft = sc["status"] == "needs_clarification"
        badges = [rg.tr(f["flow_type"]) for f in rg.flow_of(sc, items)]
        badges += [rg.tr(sc["priority"]), rg.tr(sc["scenario_type"])] + sc.get("tags", [])
        meta = "".join(f'<span class="badge">{e(b)}</span>' for b in badges)
        if draft:
            open_q = [q for q in sc.get("open_question_ids", []) if not rg.is_answered(questions[q])]
            meta += f'<span class="badge draft">taslak · {e(", ".join(open_q))}</span>'
        post = "".join(f"<p>Son koşul: {e(p)}</p>" for p in sc.get("postconditions", []))
        created = kayit.get(sc["id"])
        if created:
            box, li_attr = " disabled", ' class="acik"'
            jira = (f'<span class="jira">Jira: <a href="{e(created["url"])}" target="_blank" rel="noopener">'
                    f'{e(created["key"])}</a></span>')
        else:
            box, li_attr, jira = " checked" if states.get(sc["id"]) else "", "", ""
        cards.append(
            f'<li{li_attr}><label class="row"><input type="checkbox" value="{e(sc["id"])}"'
            f'{box}{" data-draft" if draft else ""}>'
            f'<span class="num">{n}.</span><span class="main"><span class="title">{e(sc["title"])}</span>'
            f'<span class="meta"><code>{e(sc["id"])}</code>{meta}</span>{jira}</span></label>'
            f'<details><summary>Ayrıntı</summary><p>{e(sc["objective"])}</p>'
            f'<pre>{e(gherkin_block(doc, sc, questions, assumptions, items))}</pre>{post}</details></li>')
    open_q = [q["id"] for q in rd["clarification_questions"] if not rg.is_answered(q)]
    sub = f"Kart durumu: {rg.tr(rd['status'])} · {len(cards)} senaryo"
    if open_q:
        sub += f" · açık soru: {', '.join(open_q)}"
    body = "\n".join(cards) if cards else f"<p>Seçilecek senaryo yok (kart durumu: {e(rg.tr(rd['status']))}).</p>"
    if sunucu:
        closed = " data-kapali" if sunucu.get("uyari") else ""
        action = (f'<button type="button" id="ac" class="primary" data-anahtar="{e(sunucu["anahtar"])}"{closed}>'
                  "Jira'da aç</button>")
        notice = f'<div class="ayar">{e(sunucu["uyari"])}</div>' if sunucu.get("uyari") else ""
        hint = ""
    else:
        action, notice = "", ""
        hint = ('<p class="hint">Seçilenleri Jira\'da Test Senaryosu kartı olarak açmak için seçim sunucusunu başlatın: '
                f"<code>python &lt;skill-klasörü&gt;/scripts/secim_sunucu.py test-scenarios/{e(key)}/{e(key)}.json</code></p>\n")
    return (
        '<!doctype html>\n<html lang="tr">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{e(key)} · Senaryo seçimi</title>\n<style>{PAGE_CSS}</style>\n</head>\n<body>\n<main>\n"
        f"<h1>{e(key)} — {e(doc['source']['summary'])}</h1>\n<p class=\"sub\">{e(sub)}</p>\n"
        '<div class="bar"><button type="button" data-sec="all">Tümü</button>'
        '<button type="button" data-sec="ready">Hazırlar</button>'
        f'<button type="button" data-sec="none">Hiçbiri</button><span id="sayi"></span>{action}'
        f'<div id="uyari" hidden></div>{notice}<div id="durum" role="status"></div></div>\n'
        f"<ol>\n{body}\n</ol>\n{hint}"
        f"</main>\n<script>{PAGE_JS}</script>\n</body>\n</html>\n")

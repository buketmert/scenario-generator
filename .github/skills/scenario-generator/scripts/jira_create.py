#!/usr/bin/env python3
"""Seçilen senaryoları Jira'da Test Senaryosu kartı olarak açar ve kaynak karta bağlar.

Jira'ya LLM değil bu script bağlanır; jeton yalnızca ortam değişkeninden okunur,
hiçbir dosyaya yazılmaz ve ekrana basılmaz.

Ayar  : test-scenarios/jira-ayar.json (örnek: examples/jira-ayar.ornek.json)
Jeton : Jira Server / Data Center → JIRA_PAT (kişisel erişim jetonu)
        Jira Cloud               → JIRA_EMAIL ve JIRA_API_TOKEN

Kullanım:
    python scripts/jira_create.py test-scenarios/KEY/KEY.json --kesfet     # Jira'yı tanı, ayar öner
    python scripts/jira_create.py test-scenarios/KEY/KEY.json --deneme     # gönderilecek alanları göster
    python scripts/jira_create.py test-scenarios/KEY/KEY.json              # seçim listesinde işaretlileri aç
    python scripts/jira_create.py test-scenarios/KEY/KEY.json --ids TS-KEY-001,TS-KEY-003

Açılan kartlar <KEY>-jira.json kaydına yazılır; aynı senaryo ikinci kez açılmaz.
Çıkış kodu: 0 = hepsi açıldı veya zaten açıktı, 1 = en az biri açılamadı, 2 = ayar/dosya hatası.
"""

import argparse
import base64
import json
import os
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_gherkin as rg  # noqa: E402

DEFAULTS = {
    "url": None,
    "kimlik": "pat",
    "proje": None,
    "kart_turu": "Test Senaryosu",
    "baglanti": {"tur": "Relates", "test_karti": "outward"},
    "etiketler": True,
    "oncelik": False,
    "oncelik_adlari": {"critical": "Highest", "high": "High", "medium": "Medium", "low": "Low"},
    "alanlar": {"on_kosullar": None, "test_adimlari": None, "beklenen_sonuc": None, "test_verisi": None},
    "zaman_asimi_sn": 30,
}
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
# Test kartının kaynak kartı test ettiğini anlatan bağlantı açıklamaları (keşif için)
TESTS_OUTWARD = ("tests", "test eder", "test ediyor")
TESTS_INWARD = ("is tested by", "test edilir", "tarafından test edilir")
# Kurum alanlarını adından tahmin etmek için (yalnızca --kesfet önerisi; ayar kullanıcıyındır)
FIELD_HINTS = {"on_kosullar": ("ön koşul", "on kosul", "precondition"),
               "test_adimlari": ("adım", "adim", "step"),
               "beklenen_sonuc": ("beklenen", "expected"),
               "test_verisi": ("test veri", "test data")}


class AyarHatasi(Exception):
    pass


class JiraHatasi(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


# ------------------------------------------------------------------ ayar ve istemci

def config_path(json_path, explicit=None):
    return Path(explicit) if explicit else Path(json_path).resolve().parent.parent / "jira-ayar.json"


def load_config(path, url=None, required=True):
    cfg = json.loads(json.dumps(DEFAULTS))
    if path and Path(path).exists():
        own = rg.load_json(path)
        for key, value in own.items():
            cfg[key] = {**cfg[key], **value} if isinstance(cfg.get(key), dict) and isinstance(value, dict) else value
    elif required and not url:
        raise AyarHatasi(f"Jira ayarı yok: {path}. Örnek: examples/jira-ayar.ornek.json; "
                         "önce --kesfet --url <jira-adresi> ile Jira'yı tanıtın.")
    if url:
        cfg["url"] = url
    if required and not cfg.get("url"):
        raise AyarHatasi(f"{path} içinde 'url' yok.")
    return cfg


def jira_message(raw):
    try:
        body = json.loads(raw)
    except (ValueError, TypeError):
        return (raw or b"").decode("utf-8", "replace")[:300] if isinstance(raw, bytes) else str(raw)[:300]
    parts = list(body.get("errorMessages", [])) + [f"{k}: {v}" for k, v in body.get("errors", {}).items()]
    return "; ".join(parts) or json.dumps(body, ensure_ascii=False)[:300]


class Jira:
    def __init__(self, cfg, env=None):
        env = os.environ if env is None else env
        self.base = cfg["url"].rstrip("/")
        self.timeout = cfg.get("zaman_asimi_sn", 30)
        if cfg.get("kimlik") == "cloud":
            email, token = env.get("JIRA_EMAIL"), env.get("JIRA_API_TOKEN")
            if not (email and token):
                raise AyarHatasi("JIRA_EMAIL ve JIRA_API_TOKEN ortam değişkenleri gerekli (Jira Cloud).")
            self.auth = "Basic " + base64.b64encode(f"{email}:{token}".encode()).decode()
        else:
            token = env.get("JIRA_PAT")
            if not token:
                raise AyarHatasi("JIRA_PAT ortam değişkeni yok. Jira'da Profil → Kişisel Erişim Jetonları'ndan "
                                 "bir jeton oluşturup bu değişkene koyun.")
            self.auth = "Bearer " + token

    def request(self, method, path, body=None):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method, headers={
            "Authorization": self.auth, "Accept": "application/json", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            message = jira_message(exc.read())
            if exc.code == 401:
                message = f"Jira kimliği doğrulamadı (401); jeton geçersiz veya süresi dolmuş. {message}"
            elif exc.code == 403:
                message = f"Yetki yok (403). {message}"
            raise JiraHatasi(exc.code, message) from None
        except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as exc:
            reason = getattr(exc, "reason", exc)
            raise JiraHatasi(None, f"Jira'ya ulaşılamadı ({self.base}): {reason}") from None


# ------------------------------------------------------------------ kart içeriği

def phased_lines(steps, values):
    """Adımlar Türkçe anahtar kelimeleriyle; evre 1 ön koşul, 2 eylem, 3 sonuç."""
    phase, out = 1, []
    for s in steps:
        phase = rg.PHASE.get(s["keyword"], phase)
        text = rg.substitute(s["text"], values) if values is not None else s["text"]
        out.append((phase, f"{rg.KEYWORDS[s['keyword']]} {text}"))
    return out


def numbered(lines):
    return "\n".join(f"{n}. {line}" for n, line in enumerate(lines, 1))


def card_fields(doc, sc):
    """Ön koşullar, uçtan uca test adımları, beklenen sonuç ve test verisi (Jira wiki biçimi)."""
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
    """Jira wiki biçiminde açıklama: özet alanlar, adımlar, Gherkin, son koşullar, netleştirmeler."""
    t = sc["traceability"]
    trace = " | ".join(", ".join(ids) for ids in (t["basis_ids"], t["test_condition_ids"], t["coverage_item_ids"]) if ids)
    pre, actions, expected, data = card_fields(doc, sc)
    lean = doc.get("_mod") == "yalin"  # yalın biçim: izlenebilirlik ve teknik satırı yok
    lines = [] if lean and sc["objective"] == sc["title"] else [f"*Amaç:* {sc['objective']}"]
    for flow in rg.flow_of(sc, items):
        lines.append(f"*Akış:* {rg.tr(flow['flow_type'])}" if lean
                     else f"*Akış ({rg.tr(flow['flow_type'])}):* {flow['description']}")
    lines += [
        f"*Kaynak kart:* {doc['source']['jira_key']}",
        f"*Öncelik:* {rg.tr(sc['priority'])} | *Tür:* {rg.tr(sc['scenario_type'])}" if lean else
        f"*Öncelik (risk):* {rg.tr(sc['priority'])} | *Tür:* {rg.tr(sc['scenario_type'])}"
        f" | *Teknik:* {', '.join(TECHNIQUES[x] for x in sc['techniques'])}",
    ]
    if not lean:
        lines.append(f"*İzlenebilirlik:* {trace}")
    lines += [
        f"*Test ortamı:* {doc['test_environment']['summary']}",
        "", "*Ön koşullar:*", pre or "-", "", "*Test adımları:*", actions or "-",
        "", "*Beklenen sonuç:*", expected or "-",
    ]
    if data:
        lines += ["", "*Test verisi:*", data]
    lines += ["", "{noformat}", gherkin_block(doc, sc, questions, assumptions, items), "{noformat}"]
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
    values += [doc["source"]["jira_key"], sc["id"]]  # kart ve senaryo Jira'da etiketle de bulunur
    return list(dict.fromkeys(values))


def lookups(doc):
    return ({q["id"]: q for q in doc["readiness"]["clarification_questions"]},
            {a["id"]: a for a in doc["assumptions"]},
            {i["id"]: i for i in doc["coverage_items"]})


def project_of(doc, cfg):
    return cfg.get("proje") or doc["source"]["jira_key"].rsplit("-", 1)[0]


def issue_fields(doc, sc, cfg):
    questions, assumptions, items = lookups(doc)
    fields = {"project": {"key": project_of(doc, cfg)}, "issuetype": {"name": cfg["kart_turu"]},
              "summary": f"[{sc['id']}] {sc['title']}", "description": description(doc, sc, questions, assumptions, items)}
    if cfg.get("etiketler"):
        fields["labels"] = labels(doc, sc, items)
    if cfg.get("oncelik"):
        fields["priority"] = {"name": cfg["oncelik_adlari"][sc["priority"]]}
    for name, value in zip(("on_kosullar", "test_adimlari", "beklenen_sonuc", "test_verisi"), card_fields(doc, sc)):
        field_id = (cfg.get("alanlar") or {}).get(name)
        if field_id:
            fields[field_id] = value
    return fields


def link_body(cfg, test_key, source_key):
    """'outward': Test Senaryosu kartı bağlantının çıkış ucudur ("<test> tests <kaynak>" gibi)."""
    link = cfg["baglanti"]
    test, source = {"key": test_key}, {"key": source_key}
    if link.get("test_karti", "outward") == "outward":
        return {"type": {"name": link["tur"]}, "outwardIssue": test, "inwardIssue": source}
    return {"type": {"name": link["tur"]}, "outwardIssue": source, "inwardIssue": test}


def check_link_direction(jira, cfg, test_key, source_key):
    """Kurulan bağlantının yönünü, kaynak kartta görünen açıklamadan denetler.

    Jira, bir kartın bağlantılarında karşı kartı `inwardIssue` alanında veriyorsa
    iç (inward) açıklamayı, `outwardIssue` alanında veriyorsa çıkış açıklamasını
    gösterir. Doğru sonuç, kaynak kartta "<kaynak> is tested by <test>"
    görünmesidir. API'nin alanları nasıl yorumladığından bağımsızdır; ters çıkarsa
    `baglanti.test_karti` çevrilir. Dönüş: (True | False | None, açıklama).
    None: denetlenemedi ya da bağlantı türü "tests / is tested by" değil.
    """
    try:
        data = jira.request("GET", f"/rest/api/2/issue/{urllib.parse.quote(source_key)}?fields=issuelinks")
    except JiraHatasi as exc:
        return None, f"bağlantı yönü denetlenemedi: {exc}"
    wanted = cfg["baglanti"]["tur"].lower()
    for link in (data.get("fields") or {}).get("issuelinks", []):
        ltype = link.get("type") or {}
        if ltype.get("name", "").lower() != wanted:
            continue
        for side in ("inwardIssue", "outwardIssue"):
            if (link.get(side) or {}).get("key") != test_key:
                continue
            label = (ltype.get("inward") if side == "inwardIssue" else ltype.get("outward")) or ""
            note = f"{source_key} kartında '{label} {test_key}' görünüyor"
            if label.strip().lower() in TESTS_INWARD:
                return True, note
            if label.strip().lower() in TESTS_OUTWARD:
                return False, note
            return None, note  # "tests" türü değil (Relates gibi): yön anlamsız
    return None, f"{source_key} kartında {test_key} bağlantısı bulunamadı"


# ------------------------------------------------------------------ oluşturma

def record_path(json_path):
    p = Path(json_path)
    return p.with_name(p.stem + "-jira.json")


def load_record(path):
    return rg.load_json(path) if Path(path).exists() else {}


def create_cards(doc, ids, cfg, jira, record_file, dry_run=False):
    """Seçilen senaryoları açar. Her sonuç: id, durum (acildi | zaten | deneme | hata | baglanamadi), key, url, mesaj."""
    record = load_record(record_file)
    by_id = {s["id"]: s for s in doc["test_scenarios"]}
    unknown = [i for i in ids if i not in by_id]
    results = [{"id": i, "durum": "hata", "mesaj": "JSON'da böyle bir senaryo yok"} for i in unknown]
    source_key = doc["source"]["jira_key"]
    stop = None
    direction_checked = False
    for sc in rg.execution_order([by_id[i] for i in ids if i in by_id]):
        sid = sc["id"]
        if sid in record:
            results.append({"id": sid, "durum": "zaten", **{k: record[sid][k] for k in ("key", "url")}})
            continue
        fields = issue_fields(doc, sc, cfg)
        if dry_run:
            results.append({"id": sid, "durum": "deneme", "alanlar": fields})
            continue
        if stop:
            results.append({"id": sid, "durum": "hata", "mesaj": stop})
            continue
        try:
            key = jira.request("POST", "/rest/api/2/issue", {"fields": fields})["key"]
        except JiraHatasi as exc:
            results.append({"id": sid, "durum": "hata", "mesaj": str(exc)})
            if exc.status in (None, 401, 403):  # erişim veya kimlik sorunu: kalanları denemenin anlamı yok
                stop = str(exc)
            continue
        url = f"{jira.base}/browse/{key}"
        record[sid] = {"key": key, "url": url, "acildi": datetime.now().astimezone().isoformat(timespec="seconds"),
                       "baglandi": False}
        Path(record_file).write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        try:
            jira.request("POST", "/rest/api/2/issueLink", link_body(cfg, key, source_key))
            ok, note = (None, "")
            if not direction_checked:  # yön her çalıştırmada ilk bağlantıda bir kez denetlenir
                direction_checked = True
                ok, note = check_link_direction(jira, cfg, key, source_key)
            if ok is False:
                other = "inward" if cfg["baglanti"].get("test_karti", "outward") == "outward" else "outward"
                record[sid]["ters_baglandi"] = True
                stop = (f"Bağlantı ters yönde kuruldu ({note}). jira-ayar.json'da baglanti.test_karti "
                        f"değerini '{other}' yapın ve {key} bağlantısını Jira'da düzeltin.")
                results.append({"id": sid, "durum": "baglanamadi", "key": key, "url": url, "mesaj": stop})
            else:
                record[sid]["baglandi"] = True
                results.append({"id": sid, "durum": "acildi", "key": key, "url": url})
        except JiraHatasi as exc:
            results.append({"id": sid, "durum": "baglanamadi", "key": key, "url": url,
                            "mesaj": f"Kart açıldı ama {source_key} kartına bağlanamadı: {exc}"})
        Path(record_file).write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return results


# ------------------------------------------------------------------ keşif

def discover(jira, project, issue_type):
    """Jira'nın sürümünü, bağlantı türlerini ve kart türünün alanlarını okuyup ayar önerir."""
    lines, suggestion = [], {"url": jira.base}
    info = jira.request("GET", "/rest/api/2/serverInfo")
    me = jira.request("GET", "/rest/api/2/myself")
    lines.append(f"Jira {info.get('version', '?')} ({info.get('deploymentType', '?')}); bağlanan: "
                 f"{me.get('displayName') or me.get('name') or '?'}")
    suggestion["kimlik"] = "cloud" if info.get("deploymentType") == "Cloud" else "pat"
    link_types = jira.request("GET", "/rest/api/2/issueLinkType").get("issueLinkTypes", [])
    lines.append("Bağlantı türleri: " + "; ".join(f"{t['name']} ({t['outward']} / {t['inward']})" for t in link_types))
    tests = next((t for t in link_types if t["outward"].strip().lower() in TESTS_OUTWARD), None)
    if not tests:  # çıkış açıklaması farklı yazılmışsa iç açıklamasından veya adından tanı
        tests = next((t for t in link_types if t["inward"].strip().lower() in TESTS_INWARD
                      or t["name"].strip().lower() in ("test", "tests")), None)
    relates = next((t for t in link_types if t["name"].lower() == "relates"), None)
    chosen = tests or relates or (link_types[0] if link_types else None)
    if chosen:
        side = "inward" if tests and tests["outward"].strip().lower() in TESTS_INWARD else "outward"
        suggestion["baglanti"] = {"tur": chosen["name"], "test_karti": side}
    if not tests:
        lines.append(f"[UYARI] 'tests / is tested by' bağlantı türü bulunamadı; '{chosen['name'] if chosen else '—'}' "
                     "önerildi. Test kartları bu türle bağlanır; Jira yöneticisinden 'tests' türünü isteyin.")
    try:
        types = jira.request("GET", f"/rest/api/2/issue/createmeta/{urllib.parse.quote(project)}/issuetypes")
        types = types.get("values", types.get("issueTypes", []))
    except JiraHatasi:
        types = jira.request("GET", f"/rest/api/2/project/{urllib.parse.quote(project)}").get("issueTypes", [])
    lines.append(f"{project} kart türleri: " + ", ".join(t["name"] for t in types))
    match = next((t for t in types if t["name"].lower() == issue_type.lower()), None)
    if not match:
        near = [t["name"] for t in types if "test" in t["name"].lower()]
        lines.append(f"[UYARI] '{issue_type}' kart türü {project} projesinde yok. Testle ilgili türler: {near or 'yok'}")
        return lines, suggestion
    suggestion["kart_turu"] = match["name"]
    try:
        meta = jira.request("GET", f"/rest/api/2/issue/createmeta/{urllib.parse.quote(project)}/issuetypes/{match['id']}")
        fields = meta.get("values", meta.get("fields", []))
    except JiraHatasi:
        old = jira.request("GET", "/rest/api/2/issue/createmeta?" + urllib.parse.urlencode(
            {"projectKeys": project, "issuetypeIds": match["id"], "expand": "projects.issuetypes.fields"}))
        raw = old["projects"][0]["issuetypes"][0]["fields"]
        fields = [{"fieldId": k, **v} for k, v in raw.items()]
    ids = {f.get("fieldId") or f.get("key") for f in fields}
    suggestion["etiketler"] = "labels" in ids
    suggestion["oncelik"] = "priority" in ids
    lines.append(f"'{match['name']}' oluşturma ekranındaki alanlar:")
    mapping = {}
    for f in fields:
        fid, name = f.get("fieldId") or f.get("key"), f.get("name", "")
        lines.append(f"   {'*' if f.get('required') else ' '} {fid}: {name}")
        if fid.startswith("customfield_"):
            for target, hints in FIELD_HINTS.items():
                if target not in mapping and any(h in name.lower() for h in hints):
                    mapping[target] = fid
    standard = {"project", "issuetype", "summary", "description", "labels", "priority", "reporter"}
    missing = [f.get("name") for f in fields if f.get("required") and (f.get("fieldId") or f.get("key")) not in standard
               and (f.get("fieldId") or f.get("key")) not in mapping.values()]
    if missing:
        lines.append(f"[UYARI] Doldurulmayan zorunlu alanlar: {', '.join(missing)}; bu alanlar olmadan kart açılamaz.")
    suggestion["alanlar"] = {k: mapping.get(k) for k in DEFAULTS["alanlar"]}
    return lines, suggestion


# ------------------------------------------------------------------ komut satırı

def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Seçilen senaryolar → Jira Test Senaryosu kartları")
    parser.add_argument("input", help="scenario-generator JSON çıktısı (test-scenarios/<KEY>/<KEY>.json)")
    parser.add_argument("--ids", help="açılacak senaryolar, virgülle (varsayılan: <KEY>-secim.md'de işaretliler)")
    parser.add_argument("--ayar", help="Jira ayar dosyası (varsayılan: test-scenarios/jira-ayar.json)")
    parser.add_argument("--url", help="Jira adresi (ayar dosyasındakinin yerine; --kesfet için)")
    parser.add_argument("--kesfet", action="store_true", help="Jira'yı tanı ve ayar öner; kart açmaz")
    parser.add_argument("--kaydet", action="store_true", help="--kesfet önerisini ayar dosyasına yaz (yoksa)")
    parser.add_argument("--deneme", action="store_true", help="kart açmadan gönderilecek alanları göster")
    args = parser.parse_args()

    rep = rg.Report()
    try:
        schema = rg.load_json(rg.SCHEMA_PATH)
        doc = rg.prepare(args.input, None, schema, rep)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[HATA] dosya okunamadı: {exc}", file=sys.stderr)
        return 2
    if rep.errors:
        print("\n".join(rep.errors), file=sys.stderr)
        print("JSON hatalı; önce render_gherkin.py ile düzeltin.", file=sys.stderr)
        return 2

    path = config_path(args.input, args.ayar)
    try:
        cfg = load_config(path, args.url, required=not args.deneme)
        jira = None if args.deneme else Jira(cfg)
    except AyarHatasi as exc:
        print(f"[HATA] {exc}", file=sys.stderr)
        return 2

    if args.kesfet:
        try:
            lines, suggestion = discover(jira, project_of(doc, cfg), cfg["kart_turu"])
        except JiraHatasi as exc:
            print(f"[HATA] {exc}", file=sys.stderr)
            return 1
        print("\n".join(lines))
        text = json.dumps(suggestion, ensure_ascii=False, indent=2)
        print(f"\nÖnerilen ayar ({path}):\n{text}")
        if args.kaydet:
            if path.exists():
                print(f"[UYARI] {path} zaten var; üzerine yazılmadı.", file=sys.stderr)
            else:
                path.write_text(text + "\n", encoding="utf-8")
                print(f"{path} yazıldı.", file=sys.stderr)
        return 0

    if args.ids:
        ids = [i.strip() for i in args.ids.split(",") if i.strip()]
    else:
        selection = Path(args.input).with_name(Path(args.input).stem + "-secim.md")
        if not selection.exists():
            print(f"[HATA] {selection} yok; --ids verin ya da önce render_gherkin.py --all çalıştırın.", file=sys.stderr)
            return 2
        states, _ = rg.read_selection(selection)
        ids = [sid for sid, (checked, _) in states.items() if checked]
    if not ids:
        print("[HATA] açılacak senaryo seçilmedi.", file=sys.stderr)
        return 2

    results = create_cards(doc, ids, cfg, jira, record_path(args.input), dry_run=args.deneme)
    for r in results:
        if r["durum"] == "deneme":
            print(json.dumps({"id": r["id"], "fields": r["alanlar"]}, ensure_ascii=False, indent=2))
        else:
            print(f"{r['id']}: {r['durum']}" + (f" {r['key']} {r['url']}" if r.get("key") else "")
                  + (f" — {r['mesaj']}" if r.get("mesaj") else ""), file=sys.stderr)
    return 1 if any(r["durum"] in ("hata", "baglanamadi") for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())

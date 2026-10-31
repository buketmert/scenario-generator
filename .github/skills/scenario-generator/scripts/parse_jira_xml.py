#!/usr/bin/env python3
"""Jira XML dışa aktarımını (kart → Dışa aktar → XML) iki dosyaya çevirir:

- <KEY>-kart.md   : LLM'in okuyacağı sade metin (HTML çözülmüş, yorum ve kabul
                    kriteri kimlikleri verilmiş). Ham XML'den çok daha kısadır.
- <KEY>-kart.json : render_gherkin.py'nin JSON'u tamamlamak için kullandığı
                    hazır veri: source, card_inventory ve
                    kabul kriterleri (test_basis adayları). LLM bunları JSON'a
                    yeniden yazmaz.

--from-jira ile XML dosyası yerine kart Jira REST'ten okunur: script aynı
eşlemeyi REST yanıtına uygular (alanlar, yorumlar, ekler, bağlantılar).
Ek içeriği indirilmez; bağlı kartların yalnızca özeti tek aramayla okunur ve
envanter notuna yazılır. Jira'ya yalnızca bu modda bağlanılır; ayar
test-scenarios/jira-ayar.json'dan, jeton yalnızca ortam değişkeninden okunur
(JIRA_PAT ya da JIRA_EMAIL + JIRA_API_TOKEN) ve hiçbir dosyaya yazılmaz.

--yazdir: kart metnini ve JSON yazım kılavuzunu (references/output-template.md)
çıktıya da basar. Agent ikisini bu tek araç çağrısının sonucunda alır; ayrı
okuma turlarına gerek kalmaz (yerel modelde her tur bağlamın tamamını yeniden
işler).

Kullanım:
    python scripts/parse_jira_xml.py kart.xml --yazdir           # agent'ın kullandığı biçim
    python scripts/parse_jira_xml.py kart.xml                    # test-scenarios/<KEY>/ altına yazar
    python scripts/parse_jira_xml.py kart.xml --out-dir ciktilar
    python scripts/parse_jira_xml.py --from-jira MYTKM7-6655     # XML yerine Jira REST'ten okur
    python scripts/parse_jira_xml.py --from-jira K1,K2 --yazdir  # birden fazla kart

Çıkış kodu: 0 = dosyalar üretildi, 1 = --from-jira ile en az bir kart okunamadı,
2 = dosya okunamadı, XML'de kart yok veya Jira ayarı/jetonu yok.
"""

import argparse
import json
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jira_create as jc  # noqa: E402

TYPE_MAP = {
    "story": "story", "hikaye": "story", "hikâye": "story", "kullanıcı hikayesi": "story",
    "task": "task", "görev": "task", "gorev": "task",
    "bug": "bug", "hata": "bug", "defect": "bug",
    "sub-task": "sub_task", "subtask": "sub_task", "alt görev": "sub_task", "alt gorev": "sub_task",
    "epic": "epic",
    "cross-functional": "cross_functional", "cross functional": "cross_functional",
    "crossfunctional": "cross_functional", "çapraz fonksiyonel": "cross_functional",
}
AC_NAMES = ("acceptance criteria", "kabul kriter")
SKIPPED_CUSTOM_FIELDS = {"rank"}  # sıralama anahtarı; test esası değil
EXTENSION_TYPES = {
    "image": {"png", "jpg", "jpeg", "gif", "bmp", "svg", "webp"},
    "pdf": {"pdf"},
    "document": {"doc", "docx", "odt", "rtf", "txt", "md", "ppt", "pptx"},
    "spreadsheet": {"xls", "xlsx", "csv", "ods"},
    "log": {"log", "har", "json", "xml"},
    "video": {"mp4", "mov", "avi", "webm", "mkv"},
    "archive": {"zip", "rar", "7z", "gz", "tar"},
}
NOT_PROVIDED_ATTACHMENT = "XML'de yalnızca ek adı var; içerik paylaşılmadı."
GWT_RE = re.compile(r"\b(given|when|then|diyelim ki|eğer ki|o zaman)\b", re.IGNORECASE)


class HtmlText(HTMLParser):
    """Jira'nın ürettiği HTML'i yapısını koruyarak düz metne çevirir; bağlantıları toplar."""

    BLOCK = {"p", "div", "br", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "pre"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.links, self.lists, self.skip = [], [], [], 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("script", "style"):
            self.skip += 1
        elif tag in self.BLOCK:
            self.parts.append("\n")
        elif tag in ("ul", "ol"):
            self.lists.append([tag, 0])
        elif tag == "li":
            kind = self.lists[-1] if self.lists else ["ul", 0]
            kind[1] += 1
            self.parts.append("\n" + ("  " * max(len(self.lists) - 1, 0))
                              + (f"{kind[1]}. " if kind[0] == "ol" else "- "))
        elif tag in ("td", "th"):
            self.parts.append(" | ")
        elif tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        elif tag == "img":
            src = attrs.get("src") or ""
            self.parts.append(f"[görsel: {src.rsplit('/', 1)[-1] or 'adsız'}]")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip -= 1
        elif tag in ("ul", "ol") and self.lists:
            self.lists.pop()
            self.parts.append("\n")
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(re.sub(r"\s+", " ", data))

    def text(self):
        lines = [line.strip() for line in "".join(self.parts).splitlines()]
        out = "\n".join(line for line in lines if line)
        return out.strip()


def html_to_text(raw):
    parser = HtmlText()
    parser.feed(raw or "")
    parser.close()
    return parser.text(), parser.links


def list_items(raw):
    """HTML içindeki üst düzey liste maddeleri (kabul kriterleri için); liste yoksa paragraflar."""
    text, _ = html_to_text(raw)
    items = [re.sub(r"^(\d+\.|-)\s+", "", line) for line in text.splitlines()
             if re.match(r"^(\d+\.|-)\s+", line)]
    return items or [line for line in text.splitlines() if line.strip()]


def child_text(el, tag):
    found = el.find(tag)
    return (found.text or "").strip() if found is not None else None


def inner_html(el):
    """el'in iç içeriğini bir HTML dizesi olarak yeniden kurar.

    Jira'nın bazı kurulumları description/comment/customfieldvalue içeriğini
    HTML varlıklarıyla kaçışlamak (&lt;p&gt;) yerine gerçek XML alt öğeleri
    (<p>, <br/>, <ul>…) olarak yazar; bu durumda ElementText.text yalnızca ilk
    alt öğeden önceki metni verir ve geri kalanı sessizce kaybolur. Bu
    fonksiyon alt öğeleri etiketleriyle birlikte dizeye geri yazarak
    html_to_text'in (HTMLParser tabanlı) yapıyı doğru okumasını sağlar.
    """
    def serialize(e):
        attrs = "".join(f' {k}="{v}"' for k, v in e.attrib.items())
        s = f"<{e.tag}{attrs}>" + (e.text or "")
        for c in e:
            s += serialize(c) + (c.tail or "")
        return s + f"</{e.tag}>"

    if el is None:
        return ""
    out = el.text or ""
    for child in el:
        out += serialize(child) + (child.tail or "")
    return out


def child_inner_html(el, tag):
    found = el.find(tag)
    return inner_html(found) if found is not None else None


def jira_date(value):
    try:
        return parsedate_to_datetime(value).date().isoformat()
    except (TypeError, ValueError, IndexError):
        return (value or "")[:10]


def attachment_type(name):
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    return next((kind for kind, exts in EXTENSION_TYPES.items() if ext in exts), "other")


def field_status(present, value):
    if not present:
        return "not_provided"
    return "used" if value else "empty"


def parse_item(item):
    key = child_text(item, "key")
    summary = child_text(item, "summary") or ""
    type_name = child_text(item, "type") or ""
    description_raw = child_inner_html(item, "description")
    environment = child_text(item, "environment")
    priority = child_text(item, "priority")
    labels = [(l.text or "").strip() for l in item.findall("labels/label") if (l.text or "").strip()]
    components = [(c.text or "").strip() for c in item.findall("component") if (c.text or "").strip()]
    affects = [(v.text or "").strip() for v in item.findall("version") if (v.text or "").strip()]
    fixes = [(v.text or "").strip() for v in item.findall("fixVersion") if (v.text or "").strip()]
    reporter, assignee = child_text(item, "reporter"), child_text(item, "assignee")
    description, links = html_to_text(description_raw)

    # yorumlar: eskiden yeniye, C-01'den başlayarak
    raw_comments = []
    for c in item.findall("comments/comment"):
        text, c_links = html_to_text(inner_html(c))
        links += c_links
        created = c.get("created") or ""
        try:
            order = parsedate_to_datetime(created).timestamp()
        except (TypeError, ValueError, IndexError):
            order = 0
        raw_comments.append((order, c.get("author") or "bilinmiyor", jira_date(created), text))
    raw_comments.sort(key=lambda c: c[0])
    comments = [{"id": f"C-{n:02d}", "author": a, "date": d, "text": t}
                for n, (_, a, d, t) in enumerate(raw_comments, 1)]

    # özel alanlar
    acceptance, custom = None, []
    linked = []
    for cf in item.findall("customfields/customfield"):
        name = child_text(cf, "customfieldname") or cf.get("id") or "adsız alan"
        values = [inner_html(v) for v in cf.findall("customfieldvalues/customfieldvalue")]
        if name.lower() in SKIPPED_CUSTOM_FIELDS:
            continue
        if name.lower() == "epic link":
            linked += [{"key": v.strip(), "link_type": "epic"} for v in values if v.strip()]
            continue
        if any(n in name.lower() for n in AC_NAMES) and acceptance is None:
            acceptance = {"name": name, "items": [i for v in values for i in list_items(v)]}
            continue
        texts = []
        for v in values:
            t, v_links = html_to_text(v)
            links += v_links
            if t:
                texts.append(t)
        custom.append({"name": name, "value": "\n".join(texts)})

    parent = child_text(item, "parent")
    if parent:
        linked.append({"key": parent, "link_type": "parent"})
    for lt in item.findall("issuelinks/issuelinktype"):
        for direction in ("outwardlinks", "inwardlinks"):
            for group in lt.findall(direction):
                kind = group.get("description") or child_text(lt, "name") or "bağlantı"
                for ik in group.findall("issuelink/issuekey"):
                    if (ik.text or "").strip():
                            entry = {"key": ik.text.strip(), "link_type": kind}
                            if ik.get("summary"):  # --from-jira: bağlı kartın özeti tek JQL aramasıyla okundu
                                entry["summary"] = ik.get("summary")
                            linked.append(entry)
    subtasks = [(s.text or "").strip() for s in item.findall("subtasks/subtask") if (s.text or "").strip()]
    linked += [{"key": s, "link_type": "subtask"} for s in subtasks]

    attachments = [{"name": a.get("name"), "type": attachment_type(a.get("name") or ""),
                    "size": int(a.get("size") or 0)} for a in item.findall("attachments/attachment") if a.get("name")]
    external = sorted({l for l in links if l.startswith(("http://", "https://")) and "/secure/attachment/" not in l})

    type_key = type_name.strip().lower()
    issue_type = TYPE_MAP.get(type_key, "other")
    custom_used = [c for c in custom if c["value"]]
    fields = [
        {"field": "summary", "status": field_status(True, summary)},
        {"field": "issue_type", "status": field_status(True, type_name), "note": type_name or "—"},
        {"field": "description", "status": field_status(description_raw is not None, description)},
        {"field": "acceptance_criteria", "status": "used" if acceptance and acceptance["items"] else "not_provided",
         **({"note": f"Özel alan: {acceptance['name']}"} if acceptance else
            {"note": "Ayrı alan yok; açıklamada aranmalı"})},
        {"field": "environment", "status": field_status(environment is not None, environment)},
        {"field": "priority", "status": field_status(priority is not None, priority)},
        {"field": "labels", "status": field_status(True, labels)},
        {"field": "components", "status": field_status(True, components)},
        {"field": "affects_versions", "status": field_status(True, affects)},
        {"field": "fix_versions", "status": field_status(True, fixes)},
        {"field": "reporter", "status": field_status(reporter is not None, reporter)},
        {"field": "assignee", "status": field_status(assignee is not None, assignee)},
        {"field": "subtasks", "status": field_status(True, subtasks)},
        {"field": "custom_fields", "status": field_status(True, custom_used),
         **({"note": ", ".join(c["name"] for c in custom_used)} if custom_used else {})},
    ]
    basis = [{"id": f"AC-{n:02d}", "kind": "acceptance_criterion", "text": text,
              "source": {"field": "acceptance_criteria"},
              "format": "given_when_then" if GWT_RE.search(text) else "rule", "testability": "testable"}
             for n, text in enumerate(acceptance["items"] if acceptance else [], 1)]

    card = {
        "source": {k: v for k, v in {
            "jira_key": key, "issue_type": issue_type, "summary": summary,
            "url": child_text(item, "link"), "components": components, "labels": labels,
            "jira_priority": priority}.items() if v},
        "card_inventory": {
            "fields": fields,
            "attachments": [{"name": a["name"], "type": a["type"], "status": "not_provided",
                             "summary": NOT_PROVIDED_ATTACHMENT, "basis_ids": []} for a in attachments],
            "comments": [{"id": c["id"], "author": c["author"], "date": c["date"]} for c in comments],
            "linked_issues": [{"key": l["key"], "link_type": l["link_type"], "status": "not_accessible",
                               "note": f"{l['link_type']}; " + (f"özeti: {l['summary']}"
                                                                if l.get("summary") else "XML'de yalnızca anahtar var")}
                              for l in linked],
            "external_links": [{"name": url, "status": "not_accessible",
                                "note": "XML modunda bağlantı açılmaz"} for url in external],
        },
        "test_basis_candidates": basis,
        "comment_texts": {c["id"]: c["text"] for c in comments},
    }
    return key, card, {
        "type_name": type_name, "status": child_text(item, "status"), "priority": priority,
        "description": description, "environment": environment, "labels": labels, "components": components,
        "affects": affects, "fixes": fixes, "reporter": reporter, "assignee": assignee,
        "acceptance": acceptance, "custom": custom, "comments": comments, "attachments": attachments,
        "linked": linked, "external": external, "summary": summary,
    }


# ------------------------------------------------------------------ Jira REST modu

def _inner(val):
    """REST alanındaki Jira wiki/HTML içeriğini xml tanıdığı hale getirir: alt etiketleri
    kaçışlayarak string'e çevirir; parse_item'ın inner_html'i yapısını aynı şekilde çözer."""
    if val is None:
        return ""
    if isinstance(val, dict):
        return "&".join(f"{_escape(k)}={_escape(str(v))}" for k, v in val.items())
    return _escape(str(val))


def _escape(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


JIRA_EPOCH = datetime(1970, 1, 1)


def _jira_datetime(ms):
    """REST'in epoch milisaniyesini XML dışa aktarımdaki RFC 2822 biçimine çevirir."""
    try:
        stamp = JIRA_EPOCH.fromtimestamp(int(ms) / 1000)
    except (TypeError, ValueError, OSError, OverflowError):
        return ""
    return stamp.strftime("%a, %d %b %Y %H:%M:%S %z") + " +0300"  # %z platforma göre; tarih hâli jira_date'te


def _rest_field(value):
    """REST alan değerini XML dışa aktarımdaki görünen metin haline çevirir."""
    if value is None:
        return None
    if isinstance(value, dict):
        return str(value.get("name") or value.get("value") or value.get("displayName") or value.get("key") or "")
    if isinstance(value, list):
        return " ".join(str(_rest_field(v) or "") for v in value).strip() or None
    return str(value)


def _item_from_rest(data, jira):
    """Jira REST karşılığını parse_item'ın okuduğu XML dışa aktarım <item> yapısına çevirir.

    Eşleme: kart → Dışa aktar → XML ile aynı alan adları; ek içerik ve eklerin
    indirilmesi yoktur (yalnızca ad, boyut, yazar, tarih). Bağlı kartların
    özeti tek JQL aramasıyla okunur ve <issuelinktype> açıklamalarına yazılır;
    parse_item bunları not olarak taşır, envanterde durum not_accessible kalır.
    """
    f = data.get("fields") or {}
    item = ET.Element("item")
    def add(tag, text):
        el = ET.SubElement(item, tag)
        el.text = "" if text is None else str(text)
    add("key", data.get("key"))
    add("summary", _rest_field(f.get("summary")))
    add("type", _rest_field(f.get("issuetype")))
    add("description", _inner(f.get("description")))
    add("environment", _inner(f.get("environment")))
    if f.get("priority") is not None:
        add("priority", _rest_field(f.get("priority")))
    labels = ET.SubElement(item, "labels")
    for lab in f.get("labels") or []:
        ET.SubElement(labels, "label").text = lab
    for comp in f.get("components") or []:
        add("component", _rest_field(comp))
    for v in f.get("versions") or []:
        add("version", _rest_field(v))
    for v in f.get("fixVersions") or []:
        add("fixVersion", _rest_field(v))
    if f.get("reporter") is not None:
        add("reporter", _rest_field(f.get("reporter")))
    if f.get("assignee") is not None:
        add("assignee", _rest_field(f.get("assignee")))
    if f.get("status") is not None:
        add("status", _rest_field(f.get("status")))

    # yorumlar: eskiden yeniye (REST yenisini önce verir)
    comments_el = ET.SubElement(item, "comments")
    for c in sorted(f.get("comment", {}).get("comments", []), key=lambda c: c.get("created", 0)):
        el = ET.SubElement(comments_el, "comment", {
            "author": _rest_field((c.get("author") or {}).get("name") or c.get("author")),
            "created": _jira_datetime(c.get("created")),
        })
        el.text = _inner(c.get("body"))

    attachments = ET.SubElement(item, "attachments")
    for a in f.get("attachment") or []:
        ET.SubElement(attachments, "attachment", {
            "name": a.get("filename") or a.get("name") or "adsız",
            "size": str(a.get("size") or 0),
            "author": _rest_field((a.get("author") or {}).get("name") or a.get("author")),
            "created": _jira_datetime(a.get("created")),
        })

    links_el = ET.SubElement(item, "issuelinks")
    for lt in f.get("issuelinks") or []:
        ltype = lt.get("type") or {}
        type_el = ET.SubElement(links_el, "issuelinktype")
        add_el = ET.SubElement(type_el, "name")
        add_el.text = ltype.get("name") or ""
        for side, tag in (("outwardIssue", "outwardlinks"), ("inwardIssue", "inwardlinks")):
            if lt.get(side):
                dir_el = ET.SubElement(type_el, tag, {"description": ltype.get(side == "outwardIssue" and "outward" or "inward") or ""})
                ik = ET.SubElement(ET.SubElement(dir_el, "issuelink"), "issuekey")
                ik.text = (lt.get(side) or {}).get("key")
    subtasks = ET.SubElement(item, "subtasks")
    for st in f.get("subtasks") or []:
        ET.SubElement(subtasks, "subtask").text = st.get("key") or ""
    return item


def _customfields_from_rest(data, jira):
    """Kartın özel alanlarını adıyla okuyup <customfield> öğelerine çevirir."""
    f = data.get("fields") or {}
    root = ET.Element("customfields")
    if not f:
        return root
    names = {}
    try:
        try:
            edit_meta = jira.request("GET", "/rest/api/2/issue/" + urllib.parse.quote(data.get("key", "")) + "/editmeta")
            for fid, meta in (edit_meta.get("fields") or {}).items():
                if fid.startswith("customfield_"):
                    names[fid] = meta.get("name") or fid
        except jc.JiraHatasi:
            pass  # editmeta boş/yasak olabilir; alan adları /field uçtan alınır
        if not names:
            for field in jira.request("GET", "/rest/api/2/field"):
                fid = field.get("id") or ""
                if fid.startswith("customfield_"):
                    names[fid] = field.get("name") or fid
    except jc.JiraHatasi:
        pass  # meta okunamadıysa özel alanlar kimliğiyle yazılır
    for fid, value in f.items():
        if not (isinstance(fid, str) and fid.startswith("customfield_")) or value in (None, [], ""):
            continue
        cf = ET.SubElement(root, "customfield", {"id": fid})
        name_el = ET.SubElement(cf, "customfieldname")
        name_el.text = names.get(fid, fid)
        values_el = ET.SubElement(cf, "customfieldvalues")
        for v in (value if isinstance(value, list) else [value]):
            el = ET.SubElement(values_el, "customfieldvalue")
            el.text = _inner(v)
    return root


def fetch_cards(keys, cfg):
    """Kartları REST'ten okur; döner: [(key, item_öğesi)], hata mesajları."""
    jira = jc.Jira(cfg)
    out, errors = [], []
    for key in keys:
        try:
            data = jira.request("GET", f"/rest/api/2/issue/{urllib.parse.quote(key)}")
        except jc.JiraHatasi as exc:
            errors.append(f"{key}: {exc}")
            continue
        item = _item_from_rest(data, jira)
        item.append(_customfields_from_rest(data, jira))
        _add_link_summaries(jira, item, data.get("key", ""))
        out.append((data.get("key", key), item))
    return out, errors


def _add_link_summaries(jira, item, key):
    """Bağlı kartların özetlerini tek JQL aramasıyla okur ve bağlantı öğelerine yazar.

    Ek içerik veya ek indirme yoktur; yalnızca anahtar → özet eşlemesidir.
    """
    linked = []
    for lt in item.findall("issuelinks/issuelinktype"):
        for direction in ("outwardlinks", "inwardlinks"):
            for group in lt.findall(direction):
                for ik in group.findall("issuelink/issuekey"):
                    if (ik.text or "").strip():
                        linked.append(ik)
    subtasks = [st for st in item.findall("subtasks/subtask") if (st.text or "").strip()]
    todo = [el for el in linked + subtasks if (el.text or "").strip() != key]
    keys = sorted({el.text.strip() for el in todo})
    if not keys:
        return
    summaries = {}
    try:
        jql = "key in (" + ", ".join(keys) + ")"
        data = jira.request("GET", "/rest/api/2/search?" + urllib.parse.urlencode(
            {"jql": jql, "fields": "summary", "maxResults": min(len(keys), 100)}))
        for issue in data.get("issues", []):
            s = (issue.get("fields") or {}).get("summary")
            if s:
                summaries[issue.get("key", "")] = s
    except jc.JiraHatasi:
        pass  # arama erişimi yoksa özet yok; kart not_accessible kalır
    if not summaries:
        return
    for el in linked:
        if (el.text or "").strip() in summaries:
            el.set("summary", summaries[el.text.strip()])


def render_markdown(key, info, basis):
    j = lambda xs: ", ".join(xs) if xs else "—"
    out = [
        f"# {key} — {info['summary']}",
        "",
        "> scripts/parse_jira_xml.py ile XML'den üretildi. Kart bilgileri `" + key + "-kart.json` içinde hazır;",
        "> JSON'a yalnızca senaryoları ve soruları yaz (aşağıdaki yazım kılavuzu).",
        "",
        f"- **Tür:** {info['type_name'] or '—'} · **Öncelik:** {info['priority'] or '—'} · **Durum:** {info['status'] or '—'}",
        f"- **Bileşenler:** {j(info['components'])} · **Etiketler:** {j(info['labels'])}",
        f"- **Etkilenen sürüm:** {j(info['affects'])} · **Düzeltme sürümü:** {j(info['fixes'])}",
        f"- **Raporlayan:** {info['reporter'] or '—'} · **Atanan:** {info['assignee'] or '—'}",
        f"- **Ortam (environment):** {info['environment'] or ('boş' if info['environment'] is not None else 'XML de yok')}",
        "",
        "## Açıklama",
        "",
        info["description"] or "(boş)",
        "",
    ]
    if basis:
        out += [f"## Kabul kriterleri (özel alan: {info['acceptance']['name']})", ""]
        out += [f"- **{b['id']}:** {b['text']}" for b in basis]
    else:
        out += ["## Kabul kriterleri", "", "Ayrı bir kabul kriteri alanı yok; açıklamada aranmalı."]
    if info["custom"]:
        out += ["", "## Diğer özel alanlar", ""]
        for c in info["custom"]:
            value = c["value"].replace("\n", " / ") if c["value"] else "(boş)"
            out.append(f"- **{c['name']}:** {value}")
    out += ["", "## Yorumlar (eskiden yeniye)", ""]
    if info["comments"]:
        for c in info["comments"]:
            out += [f"### {c['id']} · {c['author']} · {c['date']}", "", c["text"] or "(boş)", ""]
    else:
        out += ["Yorum yok.", ""]
    out += ["## Ekler (içerik XML'de yok; envanterde not_provided)", ""]
    out += [f"- {a['name']} ({a['type']}, {round(a['size'] / 1024)} KB)" for a in info["attachments"]] or ["Ek yok."]
    out += ["", "## Bağlı kartlar (bağlantı özeti REST'ten okunduysa notta)", ""]
    out += [f"- {l['key']} ({l['link_type']})" + (f" — {l['summary']}" if l.get("summary") else "")
            for l in info["linked"]] or ["Bağlı kart yok."]
    if info["external"]:
        out += ["", "## Dış bağlantılar (açılmaz; envanterde not_accessible)", ""]
        out += [f"- {u}" for u in info["external"]]
    return "\n".join(out) + "\n"


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Jira XML → <KEY>-kart.md + <KEY>-kart.json")
    parser.add_argument("xml", nargs="?", help="Jira XML dışa aktarımı (--from-jira yoksa zorunlu)")
    parser.add_argument("--from-jira", help="XML yerine kartı Jira REST'ten okur: kart anahtarı(ları), "
                        "virgülle. Ayar test-scenarios/jira-ayar.json, jeton ortam değişkeninden")
    parser.add_argument("--ayar", help="Jira ayar dosyası (varsayılan: <out-dir>/jira-ayar.json)")
    parser.add_argument("--out-dir", default="test-scenarios",
                        help="çıktı kökü; her kart <out-dir>/<KEY>/ altına yazılır (varsayılan: test-scenarios)")
    parser.add_argument("--yazdir", action="store_true",
                        help="kart metnini ve JSON yazım kılavuzunu çıktıya da bas (agent tek turda okur)")
    args = parser.parse_args()

    if args.from_jira:
        keys = [k.strip() for k in args.from_jira.split(",") if k.strip()]
        if not keys:
            print("[HATA] --from-jira için kart anahtarı verin (ör. --from-jira MYTKM7-6655).", file=sys.stderr)
            return 2
        cfg_path = Path(args.ayar) if args.ayar else Path(args.out_dir) / "jira-ayar.json"
        try:
            cfg = jc.load_config(cfg_path, required=True)
        except jc.AyarHatasi as exc:
            print(f"[HATA] {exc}", file=sys.stderr)
            return 2
        try:
            cards, errors = fetch_cards(keys, cfg)
        except jc.AyarHatasi as exc:  # jeton yok
            print(f"[HATA] {exc}", file=sys.stderr)
            return 2
        items = cards
        if errors:
            print("\n".join(f"[HATA] {e}" for e in errors), file=sys.stderr)
            if not items:
                return 1
    else:
        if not args.xml:
            parser.error("XML dosyası gerekli (ya da --from-jira <KART-ANAHTARI>)")
        try:
            root = ET.parse(args.xml).getroot()
        except (OSError, ET.ParseError) as exc:
            print(f"[HATA] XML okunamadı: {exc}", file=sys.stderr)
            return 2
        items = root.findall("./channel/item") or root.findall(".//item")
        if not items:
            print("[HATA] XML'de kart (<item>) yok; Jira'da kart → Dışa aktar → XML ile alınmış dosyayı verin.", file=sys.stderr)
            return 2
    failures = 0 if args.from_jira else None
    for entry in items:
        if args.from_jira:
            key, item = entry
        else:
            item = entry
            key = (item.findtext("key") or "").strip()
        if not key:
            print("[HATA] <key> öğesi olmayan bir kart atlandı.", file=sys.stderr)
            continue
        card_key, card, info = parse_item(item)
        if not card_key:
            print(f"[HATA] {key}: kart okunamadı; <key> öğesi yok.", file=sys.stderr)
            if args.from_jira:
                failures += 1
            continue
        folder = Path(args.out_dir) / card_key
        folder.mkdir(parents=True, exist_ok=True)
        text = render_markdown(card_key, info, card["test_basis_candidates"])
        (folder / f"{card_key}-kart.json").write_text(json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (folder / f"{card_key}-kart.md").write_text(text, encoding="utf-8")
        inv = card["card_inventory"]
        print(f"{folder / (card_key + '-kart.md')}: {len(card['test_basis_candidates'])} kabul kriteri, "
              f"{len(inv['comments'])} yorum, {len(inv['attachments'])} ek, {len(inv['linked_issues'])} bağlı kart",
              file=sys.stderr)
        if args.yazdir:
            print(f"===== {folder / (card_key + '.json')} dosyasına yazılacak kart =====\n\n{text}")
    if args.yazdir:
        guide = Path(__file__).resolve().parent.parent / "references" / "output-template.md"
        print(f"===== JSON yazım kılavuzu ({guide.name}) =====\n\n{guide.read_text(encoding='utf-8')}")
    if failures:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Seçim ekranını yerel bir sunucudan açar; ekrandaki "Jira'da aç" düğmesi
seçilen senaryoları Jira'da Test Senaryosu kartı olarak açar ve kaynak karta bağlar.

- Sunucu yalnızca 127.0.0.1'e bağlanır; başka makineden erişilemez.
- Her başlatmada sayfaya rastgele bir anahtar gömülür; anahtarı taşımayan istek
  reddedilir. Böylece tarayıcıda açık başka bir sayfa bu sunucuyu tetikleyemez.
- Jira'ya jira_create.py bağlanır; jeton ortam değişkeninden okunur (JIRA_PAT ya
  da JIRA_EMAIL + JIRA_API_TOKEN) ve sayfaya hiç gönderilmez.
- Seçim <KEY>-secim.md'ye, açılan kartlar <KEY>-jira.json'a yazılır.
- --sure-dk dakika boyunca istek gelmezse sunucu kendiliğinden kapanır.

Kullanım:
    python scripts/secim_sunucu.py test-scenarios/KEY/KEY.json                # tarayıcıda açar
    python scripts/secim_sunucu.py test-scenarios/KEY/KEY.json --port 8799 --no-open

Çıkış kodu: 0 = sunucu kapandı, 2 = JSON okunamadı veya hatalı.
"""

import argparse
import json
import secrets
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jira_create as jc  # noqa: E402
import render_gherkin as rg  # noqa: E402
import selection_page as sp  # noqa: E402

MAX_BODY = 64 * 1024


class Session:
    def __init__(self, json_path, doc, config_file):
        self.json_path = Path(json_path)
        self.doc = doc
        self.selection_file = self.json_path.with_name(self.json_path.stem + "-secim.md")
        self.record_file = jc.record_path(self.json_path)
        self.token = secrets.token_urlsafe(24)
        self.lock = threading.Lock()
        self.last_seen = time.monotonic()
        self.warning, self.cfg, self.jira = None, None, None
        try:
            self.cfg = jc.load_config(config_file)
            self.jira = jc.Jira(self.cfg)
        except jc.AyarHatasi as exc:
            self.warning = f"Jira'da açma kapalı: {exc}"

    def states(self):
        previous = rg.read_selection(self.selection_file)[0] if self.selection_file.exists() else {}
        return rg.selection_states(self.doc, previous, rg.Report())

    def page(self):
        return sp.selection_page(self.doc, self.states(), jc.load_record(self.record_file),
                                 {"anahtar": self.token, "uyari": self.warning})

    def create(self, ids):
        states = {s["id"]: s["id"] in ids for s in self.doc["test_scenarios"]}
        self.selection_file.write_text(rg.render_selection(self.doc, states), encoding="utf-8")
        return jc.create_cards(self.doc, ids, self.cfg, self.jira, self.record_file)


def make_handler(session, allowed_hosts):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def send(self, code, body, ctype="application/json; charset=utf-8"):
            data = body.encode("utf-8") if isinstance(body, str) else json.dumps(body, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def trusted_host(self):
            # DNS yeniden bağlama saldırısına karşı yalnızca kendi adresimizden gelen istekler
            return self.headers.get("Host", "") in allowed_hosts

        def do_GET(self):
            session.last_seen = time.monotonic()
            if not self.trusted_host():
                return self.send(403, {"hata": "izin verilmeyen adres"})
            if self.path.split("?")[0] not in ("/", "/index.html"):
                return self.send(404, {"hata": "bulunamadı"})
            self.send(200, session.page(), "text/html; charset=utf-8")

        def do_POST(self):
            session.last_seen = time.monotonic()
            if not self.trusted_host() or self.path != "/api/ac":
                return self.send(404, {"hata": "bulunamadı"})
            origin = self.headers.get("Origin")
            if self.headers.get("X-Secim-Anahtari") != session.token or (
                    origin and origin.split("://", 1)[-1] not in allowed_hosts):
                return self.send(403, {"hata": "geçersiz anahtar; sayfayı yenileyin"})
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY:
                return self.send(413, {"hata": "istek çok büyük"})
            try:
                ids = json.loads(self.rfile.read(length) or b"{}").get("ids")
            except (ValueError, AttributeError):
                ids = None
            if not isinstance(ids, list) or not ids or not all(isinstance(i, str) for i in ids):
                return self.send(400, {"hata": "seçili senaryo yok"})
            if session.warning:
                return self.send(409, {"hata": session.warning})
            with session.lock:
                results = session.create(ids)
            self.send(200, {"sonuclar": results})

    return Handler


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Seçim ekranı + Jira'da Test Senaryosu kartı açma")
    parser.add_argument("input", help="scenario-generator JSON çıktısı (test-scenarios/<KEY>/<KEY>.json)")
    parser.add_argument("--port", type=int, default=0, help="yerel port (varsayılan: boş bir port)")
    parser.add_argument("--ayar", help="Jira ayar dosyası (varsayılan: test-scenarios/jira-ayar.json)")
    parser.add_argument("--no-open", action="store_true", help="tarayıcıyı açma")
    parser.add_argument("--sure-dk", type=float, default=60, help="bu kadar dakika istek gelmezse kapan (varsayılan 60)")
    args = parser.parse_args()

    rep = rg.Report()
    try:
        doc = rg.prepare(args.input, None, rg.load_json(rg.SCHEMA_PATH), rep)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[HATA] dosya okunamadı: {exc}", file=sys.stderr)
        return 2
    if rep.errors:
        print("\n".join(rep.errors) + "\nJSON hatalı; önce render_gherkin.py ile düzeltin.", file=sys.stderr)
        return 2

    session = Session(args.input, doc, jc.config_path(args.input, args.ayar))
    server = ThreadingHTTPServer(("127.0.0.1", args.port), None)
    port = server.server_address[1]
    server.RequestHandlerClass = make_handler(session, {f"127.0.0.1:{port}", f"localhost:{port}"})
    url = f"http://127.0.0.1:{port}/"

    def idle_watch():
        while True:
            time.sleep(5)
            if time.monotonic() - session.last_seen > args.sure_dk * 60:
                server.shutdown()
                return

    threading.Thread(target=idle_watch, daemon=True).start()
    print(f"Seçim ekranı: {url}  (kapatmak için Ctrl+C)", flush=True)
    if session.warning:
        print(f"[UYARI] {session.warning}", flush=True)
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    print("Seçim sunucusu kapandı.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

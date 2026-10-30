#!/usr/bin/env python3
"""Sestaví web bacagroove.com do složky dist/.

Data: site.json (texty, odkazy, píseň na úvod, pořadí písní)
      + _data/<slug>.json a <slug>/cover.jpg z repozitáře bgo-listen (směřovací stránky).
Použití: python3 build.py --listen ../bgo-listen [--preview]
  --preview  bez měření (GoatCounter, Meta pixel) – pro náhled mimo ostrou doménu.
"""
import argparse, html, json, shutil
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent
LOGO_H = {"spotify": 34, "youtube": 24, "ytmusic": 28, "apple": 26}
NAMES = {"spotify": "Spotify", "youtube": "YouTube", "ytmusic": "YouTube Music", "apple": "Apple Music"}
ANDROID_PKG = {"spotify": "com.spotify.music", "youtube": "com.google.android.youtube",
               "ytmusic": "com.google.android.apps.youtube.music", "apple": "com.apple.android.music"}
SOCIAL_SVG = {}  # doplněno níže


def e(s):
    return html.escape(str(s), quote=True)


def intent(url, p):
    rest = url.split("://", 1)[1]
    return f"intent://{rest}#Intent;scheme=https;package={ANDROID_PKG[p]};end"


def cover(listen, slug, out, size=480):
    src = listen / slug / "cover.jpg"
    dst = out / "covers" / f"{slug}.jpg"
    dst.parent.mkdir(parents=True, exist_ok=True)
    im = Image.open(src).convert("RGB")
    w, h = im.size
    s = min(w, h)
    im = im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s)).resize((size, size), Image.LANCZOS)
    im.save(dst, "JPEG", quality=84, optimize=True, progressive=True)
    return f"covers/{slug}.jpg"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--listen", default=str(ROOT.parent / "bgo-listen"))
    ap.add_argument("--out", default=str(ROOT / "dist"))
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--theme", default=None, help="složka v themes/ (výchozí: site.json theme)")
    a = ap.parse_args()
    listen, out = Path(a.listen), Path(a.out)
    site = json.loads((ROOT / "site.json").read_text())
    if out.exists():
        shutil.rmtree(out)
    (out / "assets").mkdir(parents=True)
    for f in (ROOT / "assets").iterdir():
        if f.suffix in (".svg", ".png", ".jpg", ".webp") and f.name != "artist.png":
            shutil.copy(f, out / "assets" / f.name)
    Image.open(ROOT / "assets" / "artist.png").convert("RGB").save(out / "assets" / "artist.jpg", "JPEG", quality=86, optimize=True)

    def song(slug):
        d = json.loads((listen / "_data" / f"{slug}.json").read_text())
        d["img"] = cover(listen, slug, out)
        d["url"] = f"{site['listen_base']}/{slug}/"
        return d

    feat = song(site["featured"]["slug"])
    songs = [song(s) for s in site["songs"] if s != feat["slug"]]
    vid = site["video"]
    poster = cover(listen, vid["poster_slug"], out, 720)
    base = f"https://{site['domain']}"

    # --- platformy
    rows = []
    for p, url in site["platforms"].items():
        attrs = f'data-p="{p}" data-a="{e(intent(url, p))}"'
        if p == "spotify":
            attrs += ' data-s="spotify:artist:' + url.rstrip("/").rsplit("/", 1)[1] + '"'
        btn = ("PŘEHRÁT VIDEO", "WATCH") if p == "youtube" else ("POSLOUCHAT", "LISTEN")
        cls = "row row-main" if p == "spotify" else "row"
        rows.append(
            f'<a class="{cls}" {attrs} href="{e(url)}" rel="noopener">'
            f'<img class="logo logo-{p}" src="assets/{p}.svg" alt="{NAMES[p]}" height="{LOGO_H[p]}">'
            f'<span class="play"><span data-en="{btn[1]}">{btn[0]}</span><i class="tri" aria-hidden="true"></i></span></a>')

    tiles = "\n".join(
        f'<a class="tile" href="{e(s["url"])}" data-song="{s["slug"]}"><img src="{s["img"]}" alt="" loading="lazy" width="480" height="480">'
        f'<span class="tname">{e(s["title"])}</span></a>' for s in songs)

    social = "".join(
        f'<a href="{e(u)}" rel="noopener" aria-label="{k.capitalize()}" title="{k.capitalize()}">{SOCIAL_SVG[k]}</a>'
        for k, u in site["social"].items())

    ld = {"@context": "https://schema.org", "@type": "MusicGroup", "name": site["title"], "url": base + "/",
          "image": base + "/assets/artist.jpg", "description": site["description"], "genre": ["Folk", "Jazz"],
          "email": site["contact"]["email"],
          "sameAs": list(site["platforms"].values()) + [u for k, u in site["social"].items() if k != "youtube"]}

    measure = "" if a.preview else (
        f'<script data-goatcounter="{e(site["goatcounter"])}" async src="https://gc.zgo.at/count.js"></script>\n'
        "<script>!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};"
        "if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];"
        "s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');"
        f"fbq('init','{site['pixel']}');fbq('track','PageView');</script>")

    page = TEMPLATE
    repl = {
        "TITLE": e(site["title"]), "TAGLINE": e(site["tagline"]), "DESC": e(site["description"]),
        "BASE": base, "ROWS": "\n".join(rows), "TILES": tiles, "SOCIAL": social,
        "FEAT_URL": e(feat["url"]), "FEAT_IMG": feat["img"], "FEAT_TITLE": e(feat["title"]), "FEAT_SLUG": feat["slug"],
        "FEAT_TAG": e(site["featured"]["tag"]), "FEAT_TAG_EN": e(site["featured"]["tag_en"]),
        "VID_URL": e(f"https://www.youtube.com/watch?v={vid['id']}"), "VID_POSTER": poster,
        "VID_TITLE": e(vid["title"]), "VID_LABEL": e(vid["label"]), "VID_LABEL_EN": e(vid["label_en"]),
        "VID_INTENT": e(intent(f"https://www.youtube.com/watch?v={vid['id']}", "youtube")),
        "ABOUT": e(site["about"]), "ABOUT_EN": e(site["about_en"]),
        "CNAME": e(site["contact"]["name"]), "EMAIL": e(site["contact"]["email"]),
        "LD": json.dumps(ld, ensure_ascii=False), "MEASURE": measure,
        "HEAD": "" if a.preview else HEAD_FULL,
    }
    theme = a.theme or site.get("theme", "les")
    tdir = ROOT / "themes" / theme
    for part in ("head", "art", "tail"):
        f = tdir / f"{part}.html"
        repl["THEME_" + part.upper()] = f.read_text() if f.exists() else ""
    for k, v in repl.items():
        page = page.replace("{{" + k + "}}", v)
    page = page.replace("{{" + "BASE" + "}}", base)
    (out / "index.html").write_text(page)

    if not a.preview:
        (out / "CNAME").write_text(site["domain"] + "\n")
        (out / ".nojekyll").write_text("")
        redirect = lambda u: (f'<!doctype html><meta charset="utf-8"><title>{e(site["title"])}</title>'
                              f'<meta http-equiv="refresh" content="0; url={e(u)}"><link rel="canonical" href="{e(u)}">'
                              f'<a href="{e(u)}">{e(u)}</a>')
        (out / "youtube-music").mkdir()
        (out / "youtube-music" / "index.html").write_text(redirect(site["platforms"]["ytmusic"]))
        (out / "404.html").write_text(redirect(base + "/"))
        (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n")
        (out / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            f"<url><loc>{base}/</loc></url></urlset>\n")
    print("hotovo:", out)


HEAD_FULL = """<!doctype html><html lang="cs"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<link rel="canonical" href="{{BASE}}/">
<meta property="og:type" content="website"><meta property="og:url" content="{{BASE}}/">
<meta property="og:title" content="{{TITLE}} | {{TAGLINE}}"><meta property="og:description" content="{{DESC}}">
<meta property="og:image" content="{{BASE}}/assets/artist.jpg"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="assets/artist.jpg">
"""

TEMPLATE = """{{HEAD}}<title>{{TITLE}}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<meta name="description" content="{{DESC}}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<script type="application/ld+json">{{LD}}</script>
<style>
/* Rozcestník: jeden sloupec jako směřovací stránky, na počítači hrdina vedle tlačítek; noční les Beskyd, mosaz jako jediný akcent */
:root{
  --night:#10140e; --moss:#1a2116; --moss-2:#222b1d; --line:#35422e;
  --wool:#efe9dc; --mute:#a7ae9b; --brass:#d8a54f;
  --display:"Alegreya Sans SC","Alegreya Sans",Georgia,serif;
  --body:"Alegreya Sans",-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  color-scheme:dark;
}
*{box-sizing:border-box;margin:0;padding:0}
html{background:var(--night)}
body{position:relative;background:var(--night);color:var(--wool);font-family:var(--body);font-size:17px;line-height:1.5;-webkit-font-smoothing:antialiased;
  padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:0 28px}
body::after{content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;
  background:radial-gradient(ellipse 90% 55% at 50% -5%,#33452c 0%,transparent 70%),radial-gradient(ellipse 60% 40% at 100% 100%,#241d10 0%,transparent 70%)}
a{color:inherit}
a:focus-visible,button:focus-visible{outline:3px solid var(--brass);outline-offset:3px;border-radius:10px}
.wrap{max-width:1040px;margin:0 auto}

.top{display:flex;align-items:center;justify-content:space-between;gap:12px;padding-block:18px}
.top img{height:38px;width:auto;display:block}
.lang{display:flex;border:1px solid var(--line);border-radius:999px;overflow:hidden}
.lang button{background:none;border:0;color:var(--mute);font:600 13px/1 var(--body);letter-spacing:.08em;padding:8px 12px;cursor:pointer}
.lang button[aria-pressed="true"]{background:var(--moss-2);color:var(--wool)}

.hero{display:grid;grid-template-columns:1fr;gap:28px;padding-block:8px 36px}
@media(min-width:880px){.hero{grid-template-columns:minmax(0,1.05fr) minmax(0,1fr);gap:48px;align-items:center;padding-block:28px 56px}}
.portrait{position:relative;max-width:100%}
.portrait img{display:block;width:100%;max-width:100%;aspect-ratio:1/1;object-fit:cover;border-radius:22px;filter:contrast(1.05)}
.portrait figcaption{position:absolute;left:18px;bottom:16px;font:500 13px/1 var(--body);letter-spacing:.14em;text-transform:uppercase;color:var(--wool);
  background:rgba(16,20,14,.62);backdrop-filter:blur(6px);padding:8px 11px;border-radius:999px}
.ident{display:flex;flex-direction:column;gap:22px;min-width:0}
h1{font-family:var(--display);font-weight:800;font-size:clamp(44px,8.4vw,78px);line-height:.92;letter-spacing:-.01em;text-wrap:balance}
h1 span{display:block;color:var(--brass)}
.tag{font-family:var(--display);font-weight:500;font-size:20px;color:var(--mute);letter-spacing:.04em}

.list{display:flex;flex-direction:column;gap:10px}
.row{display:flex;align-items:center;justify-content:space-between;gap:12px;min-height:62px;padding:12px 16px;border:1px solid var(--line);border-radius:14px;
  background:rgba(26,33,22,.72);text-decoration:none;transition:background .15s,border-color .15s}
.row:hover{background:var(--moss-2);border-color:#4a5a40}
.row-main{min-height:72px;border-color:#4f6a3f;background:linear-gradient(90deg,rgba(30,215,96,.10),rgba(26,33,22,.72) 60%)}
.logo{display:block;width:auto;max-width:60%;object-fit:contain;object-position:left center}
.logo-apple{filter:invert(1)}
.play{display:flex;align-items:center;gap:8px;flex:none;font:700 13px/1 var(--body);letter-spacing:.06em;border:1px solid #6d7764;border-radius:8px;padding:9px 12px;white-space:nowrap}
.row-main .play{background:var(--wool);color:var(--night);border-color:var(--wool)}
.tri{width:0;height:0;border-left:10px solid currentColor;border-top:6px solid transparent;border-bottom:6px solid transparent}

h2{font-family:var(--display);font-weight:800;font-size:28px;line-height:1.1;letter-spacing:.01em;text-wrap:balance}
.eyebrow{font:700 12px/1 var(--body);letter-spacing:.16em;text-transform:uppercase;color:var(--brass)}
section{padding-block:30px;border-top:1px solid var(--line)}
.sec-head{display:flex;align-items:baseline;justify-content:space-between;gap:16px;margin-bottom:18px}

.duo{display:grid;grid-template-columns:1fr;gap:16px}
@media(min-width:760px){.duo{grid-template-columns:1fr 1fr}}
.card{display:grid;grid-template-columns:120px minmax(0,1fr);gap:16px;align-items:center;padding:14px;border-radius:18px;background:var(--moss);border:1px solid var(--line);text-decoration:none;transition:background .15s}
.card:hover{background:var(--moss-2)}
.card img{width:120px;height:120px;object-fit:cover;border-radius:12px;display:block}
.card .meta{display:flex;flex-direction:column;gap:8px;min-width:0}
.card h3{font-family:var(--display);font-weight:800;font-size:26px;line-height:1.05}
.go{font:700 13px/1 var(--body);letter-spacing:.06em;color:var(--wool);display:inline-flex;align-items:center;gap:8px}
.go .tri{color:var(--brass)}
.vid .thumb{position:relative;width:120px;height:120px}
.vid .thumb::after{content:"";position:absolute;inset:0;margin:auto;width:44px;height:44px;border-radius:50%;background:rgba(16,20,14,.7) no-repeat center/18px
  url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 12'%3E%3Cpath d='M0 0l10 6-10 6z' fill='%23efe9dc'/%3E%3C/svg%3E")}

.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
@media(min-width:620px){.grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(min-width:960px){.grid{grid-template-columns:repeat(6,minmax(0,1fr))}}
.tile{display:flex;flex-direction:column;gap:8px;text-decoration:none;min-width:0}
.tile img{width:100%;max-width:100%;aspect-ratio:1/1;object-fit:cover;border-radius:12px;display:block;transition:transform .2s}
.tile:hover img{transform:translateY(-3px)}
.tname{font-weight:700;font-size:16px;line-height:1.25}

.about{display:grid;grid-template-columns:1fr;gap:24px}
@media(min-width:760px){.about{grid-template-columns:minmax(0,1.4fr) minmax(0,1fr);gap:48px}}
.about p{max-width:60ch;font-size:19px;color:var(--wool)}
.contact{display:flex;flex-direction:column;gap:6px;min-width:0}
.contact .who{color:var(--mute);font-size:15px}
.contact a{font-weight:700;font-size:19px;text-decoration:none;border-bottom:1px solid var(--brass);align-self:flex-start;word-break:break-all;user-select:all}

.social{display:flex;flex-wrap:wrap;justify-content:center;gap:28px;padding-block:28px 10px;border-top:1px solid var(--line)}
.social svg{width:26px;height:26px;fill:var(--mute);display:block;transition:fill .15s}
.social a:hover svg{fill:var(--wool)}
footer{text-align:center;color:var(--mute);font-size:13px;padding-top:8px}
@media(max-width:380px){.row{padding:12px}.play{font-size:12px;padding:8px 9px}.card{grid-template-columns:96px minmax(0,1fr)}.card img,.vid .thumb{width:96px;height:96px}}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
</style>
{{THEME_HEAD}}
{{THEME_ART}}
<div class="wrap">
<header class="top">
  <img src="assets/logo.png" alt="Bača Groove Orchestra" width="458" height="214" style="width:81px">
</header>

<div class="hero">
  <figure class="portrait"><img src="assets/artist.jpg" alt="Bača s beraními rohy, sluchátky a slunečními brýlemi" data-en-alt="Bača with ram horns, headphones and sunglasses" width="486" height="486">
    <figcaption>Beskydy · folk · jazz</figcaption></figure>
  <div class="ident">
    <div><h1>Bača Groove <span>Orchestra</span></h1></div>
    <p class="tag">{{TAGLINE}}</p>
    <nav class="list" aria-label="Poslech">
{{ROWS}}
    </nav>
  </div>
</div>

<section>
  <div class="duo">
    <a class="card" href="{{FEAT_URL}}" data-song="{{FEAT_SLUG}}"><img src="{{FEAT_IMG}}" alt="" width="480" height="480">
      <span class="meta"><span class="eyebrow" data-en="{{FEAT_TAG_EN}}">{{FEAT_TAG}}</span><h3>{{FEAT_TITLE}}</h3><span class="go"><span data-en="LISTEN">POSLECHNI SI</span><i class="tri"></i></span></span></a>
    <a class="card vid" href="{{VID_URL}}" data-a="{{VID_INTENT}}" data-video="1" rel="noopener"><span class="thumb"><img src="{{VID_POSTER}}" alt="" width="720" height="720"></span>
      <span class="meta"><span class="eyebrow" data-en="{{VID_LABEL_EN}}">{{VID_LABEL}}</span><h3>{{VID_TITLE}}</h3><span class="go"><span data-en="WATCH ON YOUTUBE">PŘEHRÁT NA YOUTUBE</span><i class="tri"></i></span></span></a>
  </div>
</section>

<section>
  <div class="sec-head"><h2 data-en="Songs">Písně</h2><span class="eyebrow" data-en="Tap to listen">Klikni a poslouchej</span></div>
  <div class="grid">
{{TILES}}
  </div>
</section>

<section class="about">
  <div><h2 data-en="About the band" style="margin-bottom:12px">O kapele</h2><p data-en="{{ABOUT_EN}}">{{ABOUT}}</p></div>
  <div class="contact"><span class="eyebrow" data-en="Contact">Kontakt</span><span class="who">{{CNAME}}</span><a href="mailto:{{EMAIL}}">{{EMAIL}}</a></div>
</section>

<nav class="social" aria-label="Sítě">{{SOCIAL}}</nav>
<footer>© 2026 Bača Groove Orchestra</footer>
</div>
{{MEASURE}}
{{THEME_TAIL}}
<script>
(function(){
  var SRC=((new URLSearchParams(location.search)).get("utm_source")||"direct").toLowerCase().replace(/[^a-z0-9-]/g,"").slice(0,20)||"direct";
  var nodes=[].slice.call(document.querySelectorAll("[data-en]"));
  nodes.forEach(function(n){n.setAttribute("data-cs",n.getAttribute("data-en")===null?"":n.textContent);});
  function setLang(l){
    document.documentElement.lang=l;
    nodes.forEach(function(n){n.textContent=n.getAttribute(l==="en"?"data-en":"data-cs");});
    var im=document.querySelector("[data-en-alt]");if(im){if(!im.dataset.csAlt)im.dataset.csAlt=im.alt;im.alt=l==="en"?im.getAttribute("data-en-alt"):im.dataset.csAlt;}
  }
  // jazyk podle prohlížeče jako na směřovacích stránkách: čeština a slovenština česky, jinak anglicky
  setLang(/^(cs|sk)/i.test(navigator.language||"cs")?"cs":"en");

  function count(path,title){try{if(window.goatcounter&&goatcounter.count)goatcounter.count({path:path,title:title,event:true});}catch(e){}}
  document.querySelectorAll("a.row,a.card,a.tile").forEach(function(a){
    a.addEventListener("click",function(ev){
      var p=a.getAttribute("data-p"),s=a.getAttribute("data-song");
      if(p){count("click/web/"+p+"/"+SRC,"Web → "+p+" ("+SRC+")");try{if(window.fbq)fbq('trackCustom','StreamClick',{platform:p,content_name:'web'});}catch(e){}}
      else if(s)count("click/web/song/"+s+"/"+SRC,"Web → "+s);
      else if(a.getAttribute("data-video"))count("click/web/video/"+SRC,"Web → video");
      if(s||ev.metaKey||ev.ctrlKey)return;
      var href=a.href,u=navigator.userAgent||"",A=/Android/i.test(u),I=/iPhone|iPad|iPod/i.test(u),M=/FBAN|FBAV|FB_IAB|Instagram/i.test(u),
          sp=a.getAttribute("data-s"),i=a.getAttribute("data-a"),G=/Instagram/i.test(u)&&sp;
      var go=href;if(A&&i)go=i;else if(I&&M&&sp&&!G)go=sp;
      if(go===href)return;
      ev.preventDefault();setTimeout(function(){location.href=go;setTimeout(function(){location.href=href},1000);},150);
    });
  });
})();
</script>
"""

if __name__ == "__main__":
    SOCIAL_SVG.update(json.loads((ROOT / "assets" / "social.json").read_text()))
    main()

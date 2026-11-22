#!/usr/bin/env python3
"""Генератор на статичен сайт за независим консултант на dōTERRA.

Употреба:  python3 build.py <папка-с-данни> <изходна-папка> [--preview]
  <папка-с-данни> съдържа products.json и images/
  --preview  прави версия за онлайн преглед (начална страница home.html)
"""
import json, os, re, shutil, sys, html, hashlib
_AD=os.path.join(os.path.dirname(os.path.abspath(__file__)),"assets")
def _v(f):
    try: return hashlib.md5(open(os.path.join(_AD,f),"rb").read()).hexdigest()[:8]
    except OSError: return "1"
from collections import OrderedDict
from urllib.parse import quote

# ---------------------------------------------------------------------------
# НАСТРОЙКИ – попълнете тук данните на консултанта
# Празните стойности се показват на сайта като жълто маркирани полета.
# ---------------------------------------------------------------------------
CONFIG = {
    "name": "Петя",          # напр. "Петя Иванова"
    "brand": "Капка грижа всеки ден",
    "tagline": "Малки ритуали с етерични масла за всеки ден",
    "phone": "",             # напр. "+359 888 123 456"
    "email": "",
    "viber": "",             # номер за Viber, ако е различен
    "facebook": "https://www.facebook.com/petya.ganozova",
    "instagram": "https://www.instagram.com/pety_sy/",
    "shop_url": "",          # личен линк към онлайн магазина на dōTERRA (с нейния ID)
    "enroll_url": "",        # линк за регистрация (членство/консултант) под нея
    "referral_id": "",       # нейният номер в dōTERRA (показва се при регистрацията)
    # По желание: директни линкове към конкретни продукти, по номер (id) от products.json.
    # Ако продукт няма линк тук, бутонът „Купи“ води към shop_url.
    "product_links": {
        # 27: "https://www.doterra.com/...",
    },
    "city": "",
    "photo": "",             # път до нейна снимка, напр. "assets/petya.jpg"
    # Отзиви: [{"name": "Мария, София", "text": "..."}]
    "testimonials": [],
    "site_url": "",          # напр. "https://example.bg" (за SEO/sitemap)
}

SITE_FONTS = ("https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500"
              "&family=Marck+Script&family=Onest:wght@400;500;600&display=swap")

LOGO_SVG = ('<svg class="logo-mark" viewBox="0 0 64 64" aria-hidden="true">'
            '<circle cx="32" cy="32" r="30" fill="none" stroke="currentColor" stroke-width="1.6" opacity=".55"/>'
            '<path d="M32 9c7 9 13 16.5 13 24.5a13 13 0 0 1-26 0C19 25.5 25 18 32 9z" fill="none" stroke="var(--terra)" stroke-width="2.4"/>'
            '<path d="M32 44c-1-8 2-15 9-19-1 8-4 15-9 19z" fill="var(--olive)"/>'
            '<path d="M32 44c0-7-3-12-8-15 0 7 3 12 8 15z" fill="var(--olive)" opacity=".75"/>'
            '<path d="M32 55.5l-2.6-2.4c-1.8-1.6-1.3-3.9.6-4.1 1-.1 1.6.5 2 1 .4-.5 1-1.1 2-1 1.9.2 2.4 2.5.6 4.1z" fill="var(--terra)"/>'
            '</svg>')

GROUPS = [
    ("eterichni-masla", "Етерични масла",
     "Единични масла, смеси, рол-он формати и комплекти за начинаещи и напреднали.",
     ["Единични етерични масла", "Смеси от етерични масла", "Смеси Touch (рол-он)",
      "Комплекти и колекции", "Колекция за деца"]),
    ("produktovi-linii", "Продуктови линии",
     "Серии, изградени около една смес: от етеричното масло до продукти за дома и тялото.",
     ["On Guard продукти", "Deep Blue продукти", "dōTERRA Serenity продукти",
      "dōTERRA Air продукти", "HD Clear", "Smart & Sassy", "Healing Hands"]),
    ("grizha", "Грижа за кожата, косата и тялото",
     "Козметика с етерични масла: лице, тяло, коса и лична хигиена.",
     ["Veráge грижа за кожата", "Основна грижа за кожата", "dōTERRA СПА",
      "Salon Essentials (грижа за косата)", "Лична грижа"]),
    ("dobavki", "Хранителни добавки",
     "Ежедневни комплекси, добавки за храносмилането, за жени и за деца.",
     ["Lifelong Vitality", "Храносмилане", "Специализирани хранителни добавки",
      "dōTERRA за жени", "Хранителни добавки за деца"]),
    ("difuzeri", "Дифузери и основни продукти",
     "Дифузери, базово кокосово масло, капсули и други помощни продукти.",
     ["Дифузери", "Основна употреба"]),
]

FEATURED_IDS = [27, 28, 37, 20, 32, 51, 74, 66, 81, 1]

# Иконки (линейни SVG, оцветяват се с CSS)
def _ic(d):
    return ('<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" '
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + d + '</svg>')
ICONS = {
    "chat": _ic('<path d="M4 5h16v11H9l-5 4z"/><path d="M12 8c1.5 1.2 1.8 3 .3 4.5-1.5-1.5-1.2-3.3-.3-4.5z"/>'),
    "tag": _ic('<path d="M3 12V4h8l10 10-8 8z"/><circle cx="7.5" cy="8.5" r="1.4"/><path d="M11 14l4-4"/>'),
    "heart": _ic('<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/>'),
    "book": _ic('<path d="M4 5c3-1 6-1 8 1 2-2 5-2 8-1v14c-3-1-6-1-8 1-2-2-5-2-8-1z"/><path d="M12 6v14"/>'),
    "clock": _ic('<circle cx="12" cy="12" r="8"/><path d="M12 8v4l3 2"/>'),
    "people": _ic('<circle cx="9" cy="9" r="3"/><circle cx="17" cy="10" r="2.4"/><path d="M3 19c0-3 3-5 6-5s6 2 6 5"/><path d="M15 15c3 0 6 1 6 4"/>'),
    "moon": _ic('<path d="M19 15A8 8 0 0 1 9 5a8 8 0 1 0 10 10z"/>'),
    "home": _ic('<path d="M4 11l8-7 8 7v9H4z"/><path d="M10 20v-5h4v5"/>'),
    "leaf": _ic('<path d="M5 19C5 10 11 5 20 5c0 9-5 15-14 14z"/><path d="M5 19l8-8"/>'),
    "star": _ic('<path d="M12 4l2.4 5 5.6.6-4.2 3.8 1.2 5.6L12 16.3 7 19l1.2-5.6L4 9.6 9.6 9z"/>'),
    "sprout": _ic('<path d="M12 20v-8"/><path d="M12 12C12 8 9 6 5 6c0 4 3 6 7 6z"/><path d="M12 14c0-3 2.5-5 6-5 0 3-2.5 5-6 5z"/>'),
}
ICONS.update({
    "instagram": _ic('<rect x="4" y="4" width="16" height="16" rx="5"/><circle cx="12" cy="12" r="3.6"/><circle cx="16.9" cy="7.1" r=".6" fill="currentColor"/>'),
    "facebook": _ic('<path d="M14 8h2.5V4.5H14c-2.5 0-4 1.6-4 4V11H7.5v3.5H10V20h3.5v-5.5H16l.5-3.5h-3V8.8c0-.5.3-.8.5-.8z"/>'),
    "viber": _ic('<path d="M12 3.5c-5 0-8 2.6-8 7.3 0 2.6.9 4.4 2.6 5.5V20l3-2.2c.8.1 1.6.2 2.4.2 5 0 8-2.6 8-7.3S17 3.5 12 3.5z"/><path d="M9.5 8.5c.4-.4 1-.3 1.2.2l.5 1.1c.1.3 0 .6-.2.8l-.4.4c.4.9 1.2 1.7 2.1 2.1l.4-.4c.2-.2.5-.3.8-.2l1.1.5c.5.2.6.8.2 1.2-.8.9-2.2.9-3.6-.1a8 8 0 0 1-2.4-2.4c-.9-1.3-.6-2.5.3-3.2z"/>'),
    "search": _ic('<circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.2-4.2"/>'),
    "bag": _ic('<path d="M5 8h14l-1 12H6z"/><path d="M9 8V6.5a3 3 0 0 1 6 0V8"/>'),
    "gift": _ic('<rect x="4" y="9" width="16" height="11" rx="1.5"/><path d="M3 9h18M12 9v11"/><path d="M12 9c-2-4-6-4-6-1.5S10 9 12 9zm0 0c2-4 6-4 6-1.5S14 9 12 9z"/>'),
    "drop": _ic('<path d="M12 3.5c3.5 4.5 6 8 6 11a6 6 0 0 1-12 0c0-3 2.5-6.5 6-11z"/>'),
    "chev": _ic('<path d="M9 6l6 6-6 6"/>'),
    "chevl": _ic('<path d="M15 6l-6 6 6 6"/>'),
    "down": _ic('<path d="M6 9l6 6 6-6"/>'),
})

# „Пазарувай по продуктова линия“ – като в магазина на dōTERRA (категория, кратко име, фон)
LINES = [
    ("On Guard продукти", "On Guard", "peach"), ("Deep Blue продукти", "Deep Blue", "sky"),
    ("dōTERRA Serenity продукти", "Serenity", "lav"), ("dōTERRA Air продукти", "dōTERRA Air", "sky"),
    ("Veráge грижа за кожата", "Veráge", "peach"), ("dōTERRA СПА", "dōTERRA СПА", "sage"),
    ("Salon Essentials (грижа за косата)", "Грижа за косата", "lav"), ("Lifelong Vitality", "Lifelong Vitality", "sage"),
    ("Колекция за деца", "За деца", "peach"), ("Смеси Touch (рол-он)", "Рол-он смеси", "lav"),
    ("Дифузери", "Дифузери", "sky"),
]
# „Пазарувай по повод“ – думи за търсене в каталога
PURPOSES = [("Спокойствие", "спокой"), ("Ободряване", "ободр"), ("Свежест", "свеж"), ("Почистване у дома", "почиств"),
            ("Грижа за кожата", "кожата"), ("Коса", "коса"), ("Деца", "деца"), ("Цитрусови аромати", "цитрус"),
            ("Рол-он", "рол-он"), ("Масаж", "масаж"), ("Готвене", "готв"), ("Дифузери", "дифузер")]

BUNDLE_ICON = {"vecher": "moon", "dom": "home", "sezon": "leaf", "deca": "star", "nachalo": "sprout"}

def deco(r, name, cls):
    return f'<img class="deco {cls}" src="{r}assets/ill/{name}.svg" alt="" aria-hidden="true" loading="lazy">'

# Начална страница и „Започни оттук“ ------------------------------------------
TOP10 = [27, 28, 37, 20, 51, 32, 81, 74, 63, 79]
TOP10_WHY = {
    27: "Мек, цветен аромат за спокойни вечери. Най-универсалното масло.",
    28: "Свеж цитрус за сутрин и за ухание в кухнята.",
    37: "Ободряващ, хладен аромат за следобедите и пътуванията.",
    20: "Топъл, дървесен аромат, който обичам в грижата за кожата.",
    51: "Сладък, весел аромат, който всички вкъщи харесват.",
    32: "Свежо масло с много приложения в грижата за кожата и дома.",
    81: "Готова смес за уютни вечери, когато искате да забавите темпото.",
    74: "Топли подправки и портокал, любим аромат за есента и зимата.",
    63: "Слънчева цитрусова смес за настроение у дома.",
    79: "Свежа смес, която освежава аромата в дома.",
}
BUNDLES = [
    {"slug": "vecher", "kicker": "вечер", "title": "Спокойна вечер", "ids": [27, 81, 9, 121],
     "text": "Меки, топли аромати за спокойния край на деня. Дифузерът създава уют, докато четете или се приготвяте за сън."},
    {"slug": "dom", "kicker": "дом", "title": "Свеж дом", "ids": [63, 79, 28, 123],
     "text": "Чисти, цитрусови аромати за кухнята, хола и когато чакате гости."},
    {"slug": "sezon", "kicker": "есен и зима", "title": "Сезонна грижа", "ids": [74, 101, 51, 32],
     "text": "Топли подправки и цитруси, които много семейства обичат през студените месеци, в дифузер или в рол-он за чантата."},
    {"slug": "deca", "kicker": "деца", "title": "За децата", "ids": [113, 115, 119, 95],
     "text": "Нежни рол-он смеси, готови за употреба, за ритуала преди лягане и за времето за домашни. Използвайте според указанията на етикета."},
    {"slug": "nachalo", "kicker": "първи стъпки", "title": "За начинаещи", "ids": [1, 121, 124],
     "text": "Трите най-популярни масла в малки шишенца, дифузер и базово масло за разреждане. Всичко за първия месец."},
]
QUIZ_IDS = [27, 95, 81, 9, 28, 63, 79, 51, 37, 72, 69, 20, 80, 32, 113, 115, 119, 74, 101, 1, 121]

# ---------------------------------------------------------------------------
TR = dict(zip("абвгдежзийклмнопрстуфхцчшщъьюя",
              ["a","b","v","g","d","e","zh","z","i","y","k","l","m","n","o","p","r","s","t",
               "u","f","h","ts","ch","sh","sht","a","y","yu","ya"]))

def slugify(s):
    s = s.lower().replace("ō", "o").replace("á", "a").replace("&", "i")
    out = "".join(TR.get(c, c) for c in s)
    return re.sub(r"[^a-z0-9]+", "-", out).strip("-")

LATIN_FIX = {
    "DDR": "DDR", "HD": "HD", "CPTG": "CPTG", "CRS": "CRS", "VMZ": "VMz", "VMz": "VMz",
    "GX": "GX", "PB": "PB", "IQ": "IQ", "JR": "Jr", "A2Z": "a2z", "MITO2MAX": "Mito2Max",
    "DIGESTTAB": "DigestTab", "DiGESTTAB": "DigestTab", "CLARYCALM": "ClaryCalm",
    "PASTTENSE": "PastTense", "INTUNE": "InTune", "TERRASHIELD": "TerraShield",
    "AROMATOUCH": "AromaTouch", "ZENGEST": "ZenGest", "TRIEASE": "TriEase",
    "TERRAZYME": "TerraZyme", "SPA": "Spa", "XEO": "xEO", "VEO": "vEO",
}
CYR = re.compile(r"[А-Яа-яЁё]")

def nice(s):
    """Превръща ГЛАВНИ БУКВИ от каталога в четим текст."""
    if not s:
        return s
    s = s.replace("ИЛАНГ - ИЛАНГ", "ИЛАНГ-ИЛАНГ")
    parts = re.split(r"(\s+|[|(),\"„“/+-])", s)
    out, first = [], True
    for w in parts:
        if not w or re.fullmatch(r"\s+|[|(),\"„“/+-]", w):
            out.append(w); continue
        core = w.rstrip("™")
        tm = w[len(core):]
        if "ōTERRA" in core or core in ("xEO", "vEO", "VMz"):
            out.append(w)
        elif CYR.search(core):
            if core.isupper() or core == core.upper():
                core = core.lower()
                if first:
                    core = core[:1].upper() + core[1:]
                if core.lower() == "спа":
                    core = "СПА"
            out.append(core + tm)
        else:
            key = core.upper()
            if key in LATIN_FIX:
                core = LATIN_FIX[key]
            elif key in ("TO", "OF", "AND") and not first:
                core = core.lower()
            elif core.isupper():
                core = core[:1] + core[1:].lower()
            out.append(core + tm)
        first = False
    return "".join(out)

def esc(s):
    return html.escape(s or "", quote=True)

# ---------------------------------------------------------------------------
def load(src):
    prods = json.load(open(os.path.join(src, "products.json"), encoding="utf-8"))
    for p in prods:
        p["slug"] = os.path.splitext(os.path.basename(p["image"]))[0]
        p["dname"] = nice(p["name"])
        p["dtype"] = nice(p["type"])
        p["imgfile"] = os.path.basename(p["image"])
        p["imgsrc"] = os.path.join(src, p["image"])
        cut = os.path.join(src, "izrezani", p["slug"] + ".webp")
        if os.path.exists(cut):  # снимка без бял фон
            p["imgfile"], p["imgsrc"] = p["slug"] + ".webp", cut
        p["touch"] = None
        seen = re.compile(r"\s*Вижте стр\.\s*\d+\s*за\s+(.+?Touch)\s*$")
        nb = []
        for b in p["benefits"]:
            m = seen.search(b)
            if m:
                p["touch"] = m.group(1)
                b = b[:m.start()].strip()
            if b:
                nb.append(b)
        p["benefits"] = nb
    touch = [x for x in prods if x["category"] == "Смеси Touch (рол-он)"]
    for p in prods:
        if p["touch"]:
            key = p["touch"].replace("dōTERRA", "").replace("Touch", "").strip().upper()
            hit = [t for t in touch if t["name"].replace("dōTERRA", "").replace("™", "").strip().upper().split(" (")[0] == key]
            p["touch"] = hit[0] if hit else None
    return prods

# ---------------------------------------------------------------------------
# НОВИНИ: всяка публикация е един .md файл в <папка-с-данни>/novini/
# Горе в файла, между две линии ---, се пишат заглавие, дата и т.н.:
#   ---
#   title: Продукт на месеца
#   date: 2026-12-01
#   summary: Едно изречение за списъка с новини.
#   image: snimki/lavandula.jpg     (по желание, снимка от novini/snimki/)
#   products: 27, 28                (по желание, номера на продукти)
#   ---
#   Текстът на публикацията. Празен ред = нов абзац. ## Подзаглавие, - списък,
#   **удебелен**, [линк](https://...).
MONTHS = ["януари", "февруари", "март", "април", "май", "юни", "юли", "август",
          "септември", "октомври", "ноември", "декември"]

def inline_md(t):
    t = esc(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![*\w])\*(?!\s)(.+?)\*", r"<i>\1</i>", t)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+|[\w./#-]+)\)",
               lambda m: f'<a href="{m.group(2)}"' + (' target="_blank" rel="noopener"' if m.group(2).startswith("http") else "") + f'>{m.group(1)}</a>', t)
    return t

def md_to_html(txt):
    out, para, items = [], [], []
    def flush():
        if para: out.append("<p>" + inline_md(" ".join(para)) + "</p>"); para.clear()
        if items: out.append("<ul>" + "".join(f"<li>{inline_md(i)}</li>" for i in items) + "</ul>"); items.clear()
    for line in txt.splitlines():
        l = line.strip()
        if not l: flush(); continue
        m = re.match(r"(#{2,3})\s+(.*)", l)
        if m: flush(); out.append(f"<h{len(m.group(1))}>{inline_md(m.group(2))}</h{len(m.group(1))}>"); continue
        m = re.match(r"[-*]\s+(.*)", l)
        if m:
            if para: flush()
            items.append(m.group(1)); continue
        if items: flush()
        para.append(l)
    flush()
    return "\n".join(out)

def load_news(src, prods):
    d = os.path.join(src, "novini")
    news = []
    if not os.path.isdir(d):
        return news
    for f in sorted(os.listdir(d)):
        if not f.endswith(".md"):
            continue
        raw = open(os.path.join(d, f), encoding="utf-8").read()
        meta, text = {}, raw
        m = re.match(r"---\s*\n(.*?)\n---\s*\n?(.*)", raw, re.S)
        if m:
            text = m.group(2)
            for line in m.group(1).splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip().lower()] = v.strip().strip('"')
        if meta.get("draft", "").lower() in ("true", "da", "да", "yes"):
            continue
        date = meta.get("date", "")[:10]
        try:
            y, mo, dd = (int(x) for x in date.split("-"))
            date_bg = f"{dd} {MONTHS[mo - 1]} {y}"
        except Exception:
            date_bg = date
        slug = slugify(os.path.splitext(f)[0])
        n = {"slug": slug, "title": meta.get("title", slug), "date": date, "date_bg": date_bg,
             "summary": meta.get("summary", ""), "html": md_to_html(text),
             "example": meta.get("example", "").lower() in ("true", "da", "да", "yes"),
             "products": [int(x) for x in re.findall(r"\d+", meta.get("products", ""))],
             "img": "", "imgsrc": ""}
        img = meta.get("image", "")
        if img and os.path.exists(os.path.join(d, img)):
            n["imgsrc"] = os.path.join(d, img)
            n["img"] = "novini/snimki/" + os.path.basename(img)
        elif n["products"]:
            hit = [p for p in prods if p["id"] == n["products"][0]]
            if hit:
                n["img"] = "images/" + hit[0]["imgfile"]
        news.append(n)
    news.sort(key=lambda n: n["date"], reverse=True)
    return news

class Site:
    def __init__(self, prods, out, preview):
        self.p, self.out, self.preview = prods, out, preview
        self.home = "home.html" if preview else "index.html"
        self.cat_slug = {}
        for gslug, gname, gdesc, cats in GROUPS:
            for c in cats:
                self.cat_slug[c] = slugify(c)
        missing = {p["category"] for p in prods} - set(self.cat_slug)
        assert not missing, missing
        self.by_cat = OrderedDict((c, []) for g in GROUPS for c in g[3])
        for p in prods:
            self.by_cat[p["category"]].append(p)

    # -- helpers -------------------------------------------------------------
    def ph(self, key, label):
        v = CONFIG.get(key)
        return esc(v) if v else f'<span class="ph">{esc(label)}</span>'

    def buy_url(self, p=None):
        if p is not None:
            u = CONFIG.get("product_links", {}).get(p["id"])
            if u:
                return u
        return CONFIG["shop_url"]

    def ext_btn(self, url, label, r, fallback, cls="btn"):
        """Бутон към личен линк; ако линкът още липсва, води към обяснителна страница."""
        if url:
            return f'<a class="{cls}" href="{esc(url)}" target="_blank" rel="noopener">{label}</a>'
        return f'<a class="{cls}" href="{r}{fallback}" title="Линкът още не е добавен">{label}</a>'

    def missing_links_note(self, keys=("shop_url",)):
        if all(CONFIG.get(k) for k in keys):
            return ""
        return '<p class="note"><span class="ph">Тук бутонът ще води към личния линк на Петя в dōTERRA, щом го добавим.</span></p>'

    def brand(self):
        return CONFIG["brand"] or CONFIG["name"] or ""

    def fab(self, r):
        items = []
        vu = self.viber_url()
        items.append(f'<a href="{vu or r + "kontakti.html"}"><b>Viber</b><span>{esc(CONFIG.get("viber") or CONFIG.get("phone")) or "номерът предстои"}</span></a>')
        if CONFIG["phone"]:
            items.append(f'<a href="tel:{esc(re.sub(r"[^0-9+]", "", CONFIG["phone"]))}"><b>Обади се</b><span>{esc(CONFIG["phone"])}</span></a>')
        if CONFIG["instagram"]:
            items.append(f'<a href="{esc(CONFIG["instagram"])}" target="_blank" rel="noopener"><b>Instagram</b><span>съобщение в Instagram</span></a>')
        if CONFIG["email"]:
            items.append(f'<a href="mailto:{esc(CONFIG["email"])}"><b>Имейл</b><span>{esc(CONFIG["email"])}</span></a>')
        bu = self.buy_url()
        items.append(f'<a class="fab-buy" href="{esc(bu) if bu else r + "stani-chlen.html#kupuvane"}"{" target=_blank rel=noopener" if bu else ""}><b>Купи с моя линк</b><span>официален магазин dōTERRA</span></a>')
        return (f'<details class="fab"><summary aria-label="Връзка с Петя"><span class="fab-dot"></span>Пиши ми</summary>'
                f'<div class="fab-menu"><p>Здравейте! Пишете ми, ще ви отговоря лично.</p>{"".join(items)}</div></details>')

    def page(self, path, title, body, depth, desc="", active=""):
        r = "../" * depth
        brand = self.brand()
        brand_html = esc(brand) if brand else '<span class="ph">Име / марка</span>'
        nav = [(self.home, "Начало", "home"),
               ("zapochni.html", "Започни оттук", "zapochni"),
               ("novini.html", "Новини", "novini"),
               ("raboti-s-men.html", "Работи с мен", "raboti"),
               ("za-men.html", "За мен", "za-men"),
               ("kontakti.html", "Контакт", "kontakti")]
        cur = ' aria-current="page"'
        navh = (f'<a href="{r}{self.home}"{cur if active == "home" else ""}>Начало</a>'
                + self.mega(r, active == "katalog")
                + "".join(f'<a href="{r}{h}"{cur if k == active else ""}>{t}</a>' for h, t, k in nav[1:])
                + f'<a href="{r}stani-chlen.html" class="nav-cta"{cur if active == "stani-chlen" else ""}>Пазарувай с мен</a>')
        full_title = f"{title} | {brand}" if brand else title
        shop = CONFIG["shop_url"]
        doc = f"""<!doctype html>
<html lang="bg" data-theme="light">
<meta name="color-scheme" content="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(desc or CONFIG['tagline'])}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{SITE_FONTS}">
<link rel="stylesheet" href="{r}assets/style.css?v={_v('style.css')}">
</head>
<body>
<a class="skip" href="#main">Към съдържанието</a>
<div class="util"><div class="wrap util-in">
  <p>{ICONS["drop"]}<span>С вас е <b>{esc(CONFIG["name"])}</b>, независим консултант на dōTERRA</span></p>
  <div class="util-links"><a href="{r}zapochni.html#test">Кое масло е за мен?</a><a href="{r}podarak.html">Безплатен наръчник</a><a href="{r}stani-chlen.html#chlenstvo">Цена за членове</a>{self.socials(r, "util-soc")}</div>
</div></div>
<header class="top"><div class="wrap top-in">
  <a class="logo" href="{r}{self.home}">{LOGO_SVG}<span><b>{brand_html}</b><small>с Петя · независим консултант на dōTERRA</small></span></a>
  <form class="top-search" action="{r}katalog.html" method="get" role="search"><label class="sr" for="top-q">Търсене в каталога</label><input id="top-q" name="q" type="search" placeholder="Търсете продукт: лавандула, рол-он…" autocomplete="off">{ICONS["search"]}</form>
  <a class="top-buy" href="{r}stani-chlen.html">{ICONS["bag"]}<span>Пазарувай</span></a>
  <button class="menu-btn" type="button" aria-expanded="false" aria-controls="nav" id="menu-btn">Меню</button>
</div>
<div class="nav-row"><div class="wrap"><nav id="nav" class="nav">{navh}</nav></div></div>
</header>
<main id="main">
{"" if path == self.home else '<div class="main-deco" aria-hidden="true">' + deco(r, "eucalyptus", "md-euc") + deco(r, "lavender", "md-lav") + deco(r, "lemon", "md-lemon") + '</div>'}
{body}
</main>
<section class="foot-cta"><div class="wrap foot-cta-in">
  <div class="fc-me">{self.portrait_html(r, "fc-photo")}<div><p class="script">винаги насреща</p><p class="fc-t">Имате въпрос? Пишете ми, отговарям лично.</p></div></div>
  <div class="actions">{self.viber_btn(r)}{self.socials(r, "big-soc", labels=True)}</div>
</div></section>
<footer class="foot"><div class="wrap foot-in">
  <div class="foot-col">
    <p class="foot-brand">{brand_html}</p>
    <p>{self.ph('name','Име Фамилия')}, независим консултант (Wellness Advocate) на dōTERRA{(', ' + esc(CONFIG['city'])) if CONFIG['city'] else ''}.</p>
    <p>Тел.: {self.ph('phone','телефон')} · Имейл: {self.ph('email','имейл')}</p>
    {self.socials(r, "foot-soc")}
  </div>
  <div class="foot-col"><p class="foot-h">Магазин</p>
    {''.join(f'<a href="{r}grupa/{g[0]}.html">{esc(g[1])}</a>' for g in GROUPS)}
    <a href="{r}katalog.html">Целият каталог</a>
  </div>
  <div class="foot-col"><p class="foot-h">Пазаруване</p>
    <a href="{r}stani-chlen.html">Как да поръчам</a>
    <a href="{r}stani-chlen.html#chlenstvo">Стани член</a>
    <a href="{r}zapochni.html">Започни оттук</a>
    <a href="{r}zapochni.html#komplekti">Готови комплекти</a>
    <a href="{r}kontakti.html">Контакт</a>
  </div>
  <div class="foot-col"><p class="foot-h">Петя</p>
    <a href="{r}za-men.html">За мен</a>
    <a href="{r}novini.html">Новини</a>
    <a href="{r}podarak.html">Безплатен наръчник</a>
    <a href="{r}raboti-s-men.html">Работи с мен</a>
    <a href="{r}poveritelnost.html">Поверителност</a>
  </div>
  <div class="legal">
    <p>Това е личен сайт на независим консултант и не е официален сайт на dōTERRA. dōTERRA, CPTG Certified Pure Tested Grade и имената на продуктите са търговски марки на dōTERRA Holdings, LLC.</p>
    <p>Информацията тук е с образователна цел и не е медицински съвет. Продуктите не са предназначени да диагностицират, лекуват или предотвратяват заболявания. При бременност, кърмене, хронични състояния или прием на лекарства се консултирайте с лекар.</p>
  </div>
</div></footer>
{self.fab(r)}
<script src="{r}assets/site.js?v={_v('site.js')}"></script>
</body>
</html>
"""
        full = os.path.join(self.out, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(doc)

    def card(self, p, r):
        """Карта на продукт като в магазина: снимка, име, разфасовка и бутон „Купи“."""
        meta = " · ".join(x for x in [p["dtype"], p["size"]] if x)
        latin = f'<span class="latin">{esc(p["latin_name"])}</span>' if p["latin_name"] else ""
        url = f'{r}produkti/{p["slug"]}.html'
        buy = self.buy_url(p)
        buy_h = (f'<a class="card-buy" href="{esc(buy)}" target="_blank" rel="noopener">{ICONS["bag"]}Купи</a>' if buy
                 else f'<a class="card-buy" href="{r}stani-chlen.html#kupuvane" title="Линкът още не е добавен">{ICONS["bag"]}Купи</a>')
        kw = " ".join([p["category"], p["description"]] + p["benefits"]).lower()
        return (f'<article class="card" data-cat="{esc(self.cat_slug[p["category"]])}" data-k="{esc(kw)}">'
                f'<a class="card-img" href="{url}" tabindex="-1" aria-hidden="true"><img src="{r}images/{p["imgfile"]}" alt="" loading="lazy"></a>'
                f'<div class="card-body"><a class="card-name" href="{url}">{esc(p["dname"])}</a>{latin}'
                f'<span class="card-meta">{esc(meta)}</span>'
                f'<div class="card-foot"><a class="card-more" href="{url}">Виж</a>{buy_h}</div></div></article>')

    # -- нови общи блокове (редизайн в стила на магазина) ---------------------
    def socials(self, r, cls, labels=False):
        items = []
        if CONFIG.get("instagram"):
            items.append((CONFIG["instagram"], "instagram", "Instagram", "@" + CONFIG["instagram"].rstrip("/").rsplit("/", 1)[-1]))
        if CONFIG.get("facebook"):
            items.append((CONFIG["facebook"], "facebook", "Facebook", "Петя във Facebook"))
        vu = self.viber_url()
        if vu and not labels:
            items.append((vu, "viber", "Viber", ""))
        out = []
        for u, ic, name, sub in items:
            ext = "" if u.startswith("viber:") else ' target="_blank" rel="noopener"'
            if labels:
                out.append(f'<a class="soc soc-{ic}" href="{esc(u)}"{ext}>{ICONS[ic]}<span><b>{name}</b><small>{esc(sub)}</small></span></a>')
            else:
                out.append(f'<a class="soc soc-{ic}" href="{esc(u)}"{ext} aria-label="{name}">{ICONS[ic]}</a>')
        return f'<div class="{cls}">{"".join(out)}</div>' if out else ""

    def portrait_html(self, r, cls):
        photo = CONFIG.get("photo")
        inner = (f'<img src="{r}{esc(photo)}" alt="{esc(CONFIG["name"])}">' if photo
                 else f'<span class="ph">Снимка</span>')
        return f'<span class="{cls}">{inner}</span>'

    def mega(self, r, current):
        cols = []
        for gslug, gname, gdesc, cats in GROUPS:
            links = "".join(f'<a href="{r}kategoriya/{self.cat_slug[c]}.html">{esc(c)}</a>' for c in cats)
            cols.append(f'<div class="mega-col"><a class="mega-h" href="{r}grupa/{gslug}.html">{esc(gname)}</a>{links}</div>')
        me = (f'<div class="mega-me">{self.portrait_html(r, "mm-photo")}<b>Не знаете какво да изберете?</b>'
              f'<span>Пишете ми и ще ви помогна да намерите вашите продукти.</span>'
              f'<a href="{r}zapochni.html#test">Направете теста →</a><a href="{r}kontakti.html#pitane">Пишете ми →</a></div>')
        return (f'<div class="mega-wrap"><button type="button" class="mega-btn" aria-expanded="false"'
                f'{" data-current" if current else ""}>Магазин{ICONS["down"]}</button>'
                f'<div class="mega"><div class="mega-in">{"".join(cols)}{me}</div>'
                f'<a class="mega-all" href="{r}katalog.html">Целият каталог: {len(self.p)} продукта →</a></div></div>')

    def rail(self, items_html, cls="rail"):
        """Хоризонтална лента със стрелки (като слайдерите в магазина)."""
        return (f'<div class="rail-wrap"><button type="button" class="rail-btn prev" aria-label="Назад">{ICONS["chevl"]}</button>'
                f'<div class="{cls}">{items_html}</div>'
                f'<button type="button" class="rail-btn next" aria-label="Напред">{ICONS["chev"]}</button></div>')

    # -- pages ---------------------------------------------------------------
    # -- общи блокове --------------------------------------------------------------
    def viber_url(self):
        num = re.sub(r"[^\d+]", "", CONFIG.get("viber") or CONFIG.get("phone") or "")
        if not num:
            return ""
        if not num.startswith("+"):
            num = "+359" + num.lstrip("0")
        return "viber://chat?number=" + num.replace("+", "%2B")

    def viber_btn(self, r, cls="btn viber", label="Пиши ми във Viber"):
        u = self.viber_url()
        if u:
            return f'<a class="{cls}" href="{u}">{label}</a>'
        return f'<a class="{cls}" href="{r}kontakti.html" title="Номерът още не е добавен">{label}</a>'

    def bundle(self, b, r):
        byid = {p["id"]: p for p in self.p}
        items = [byid[i] for i in b["ids"] if i in byid]
        imgs = "".join(f'<img src="{r}images/{p["imgfile"]}" alt="" loading="lazy">' for p in items[:3])
        lis = "".join(f'<li><a href="{r}produkti/{p["slug"]}.html">{esc(p["dname"])}</a>'
                      f'{(" <small>" + esc(p["size"]) + "</small>") if p["size"] else ""}</li>' for p in items)
        return (f'<article class="bundle" id="{b["slug"]}"><div class="bundle-imgs">{imgs}</div>'
                f'<div class="bundle-txt"><p class="script kick">{ICONS[BUNDLE_ICON.get(b["slug"], "leaf")]}{esc(b["kicker"])}</p><h3 class="h3">{esc(b["title"])}</h3>'
                f'<p>{esc(b["text"])}</p><ul class="bundle-list">{lis}</ul>'
                f'<div class="actions">{self.ext_btn(self.buy_url(), "Поръчай с моя линк", r, "stani-chlen.html#kupuvane")}'
                f'<a class="btn ghost" href="{r}kontakti.html#pitane">Питай ме</a></div></div></article>')

    def testimonials(self):
        t = CONFIG.get("testimonials") or []
        if t:
            cards = "".join(f'<figure class="quote"><blockquote>„{esc(x["text"])}“</blockquote><figcaption>{esc(x["name"])}</figcaption></figure>' for x in t)
        else:
            cards = "".join(f'<figure class="quote"><blockquote><span class="ph">Отзив от клиент {i}: 1–3 изречения с нейни думи.</span></blockquote><figcaption><span class="ph">Име, град</span></figcaption></figure>' for i in (1, 2, 3))
        return f'<div class="quotes">{cards}</div>'

    def lead_form(self, r, kind="narachnik"):
        if kind == "narachnik":
            return f"""
<form class="lead-form" name="narachnik" method="POST" data-netlify="true" data-done="{r}assets/narachnik.pdf">
  <input type="hidden" name="form-name" value="narachnik">
  <label><span>Име</span><input name="ime" autocomplete="given-name" required></label>
  <label><span>Имейл или Viber номер</span><input name="kontakt" required placeholder="you@mail.bg или 0888 123 456"></label>
  <label class="check"><input type="checkbox" name="saglasie" required> <span>Съгласен/на съм Петя да ми пише с идеи и промоции. Мога да се откажа по всяко време.</span></label>
  <button class="btn" type="submit">Изпрати ми наръчника</button>
  <p class="form-msg" role="status" hidden></p>
</form>"""
        return f"""
<form class="lead-form" name="sreshta" method="POST" data-netlify="true">
  <input type="hidden" name="form-name" value="sreshta">
  <label><span>Име</span><input name="ime" autocomplete="name" required></label>
  <label><span>Телефон, Viber или имейл</span><input name="kontakt" required></label>
  <label><span>Кога ви е удобно?</span><select name="koga"><option>Сутрин</option><option>Следобед</option><option>Вечер</option><option>През уикенда</option></select></label>
  <label><span>Как предпочитате да се срещнем?</span><select name="nachin"><option>Онлайн разговор</option><option>Телефон / Viber</option><option>На живо</option></select></label>
  <label><span>Въпрос или бележка (по желание)</span><textarea name="belezhka" rows="3"></textarea></label>
  <label class="check"><input type="checkbox" name="saglasie" required> <span>Съгласен/на съм Петя да се свърже с мен за срещата.</span></label>
  <button class="btn" type="submit">Запази среща</button>
  <p class="form-msg" role="status" hidden></p>
</form>"""

    def guide_block(self, r):
        return f"""
<section class="guide"><div class="wrap guide-in">
  <div class="guide-cover" aria-hidden="true">{deco(r, "lavender", "gc-lav")}{deco(r, "blossom", "gc-bl")}<span class="script">подарък</span><b>5 малки ритуала с етерични масла</b><small>наръчник за начинаещи</small></div>
  <div class="guide-txt">
    <p class="eyebrow">Безплатен наръчник</p>
    <h2>5 малки ритуала с етерични масла</h2>
    <p>Кратък PDF наръчник: как се използват маслата безопасно, 5 лесни ритуала за сутрин, вечер и дома, и с кои 3 масла е добре да започнете.</p>
    {self.lead_form(r)}
  </div>
</div></section>"""

    # -- начална страница -----------------------------------------------------------
    def build_home(self):
        r = ""
        byid = {p["id"]: p for p in self.p}
        tiles = []
        for gslug, gname, gdesc, cats in GROUPS:
            items = [p for c in cats for p in self.by_cat[c]]
            imgs = "".join(f'<img src="images/{p["imgfile"]}" alt="" loading="lazy">' for p in items[:3])
            tiles.append(f'<a class="tile" href="grupa/{gslug}.html"><span class="tile-imgs">{imgs}</span>'
                         f'<span class="tile-txt"><b>{esc(gname)}</b><span>{esc(gdesc)}</span>'
                         f'<span class="count">{len(items)} продукта</span></span></a>')
        news = self.news[:3]
        news_h = (f"""
<section class="wrap block">
  <div class="head-row"><h2>Новини и малки ритуали</h2><a href="novini.html">Всички публикации →</a></div>
  <div class="posts">{''.join(self.post_card(n, r) for n in news)}</div>
</section>""" if news else "")
        photo = CONFIG.get("photo")
        portrait = (f'<img src="{esc(photo)}" alt="{esc(CONFIG["name"])}">' if photo else '<span class="ph">Снимка на Петя</span>')

        # промо карти (като банерите в началото на магазина)
        pm = next((n for n in self.news if "produkt" in n["slug"]), self.news[0] if self.news else None)
        promos = []
        if pm:
            pimg = byid[pm["products"][0]]["imgfile"] if pm["products"] else ""
            promos.append(("peach", "продукт на месеца", pm["title"].split(":")[-1].strip(), pm["summary"],
                           f'novini/{pm["slug"]}.html', "Прочетете", pimg))
        promos.append(("lav", "подарък", "5 малки ритуала", "Безплатен наръчник за начинаещи с етерични масла.",
                       "podarak.html", "Вземете наръчника", byid[63]["imgfile"]))
        promos.append(("sage", "по-ниска цена", "Пазарувайте като член", "Цена за членове и точки за безплатни продукти. Показвам ви как.",
                       "stani-chlen.html#chlenstvo", "Как става", byid[1]["imgfile"]))
        promo_h = "".join(
            f'<a class="promo promo-{c}" href="{h}"><span class="promo-txt"><span class="script">{esc(k)}</span>'
            f'<b>{esc(t)}</b><span>{esc(d)}</span><span class="promo-go">{esc(go)} →</span></span>'
            f'{f"""<img src="images/{img}" alt="" loading="lazy">""" if img else ""}</a>'
            for c, k, t, d, h, go, img in promos)

        fav_h = self.rail("".join(self.card(byid[i], r) for i in TOP10 if i in byid), "rail cards-rail")
        lines = []
        for cat, label, tone in LINES:
            items = self.by_cat.get(cat) or []
            if not items:
                continue
            imgs = "".join(f'<img src="images/{p["imgfile"]}" alt="">' for p in items[:2])
            lines.append(f'<a class="line line-{tone}" href="kategoriya/{self.cat_slug[cat]}.html"><span class="line-imgs">{imgs}</span>'
                         f'<span class="line-txt"><b>{esc(label)}</b><small>{len(items)} продукта</small></span></a>')
        lines_h = self.rail("".join(lines), "rail lines-rail")
        purp_h = "".join(f'<a class="purpose" href="katalog.html?q={quote(q)}">{esc(t)}</a>' for t, q in PURPOSES)

        body = f"""
<section class="hero me-hero"><div class="wrap hero-in">
  <div class="hero-txt">
    <p class="script">{esc(self.brand())}</p>
    <h1>Здравейте, аз съм {esc(CONFIG['name'])}.<br>Ще ви помогна да откриете етеричните масла.</h1>
    <p class="lead">Не е нужно да разбирате от масла. Кажете ми какво търсите и ще ви предложа с какво да започнете, как да го използвате и как да го поръчате на по-добра цена.</p>
    <div class="actions">{self.viber_btn(r)}<a class="btn ghost" href="zapochni.html#test">Кое масло е за мен?</a></div>
    <div class="hero-follow"><span>Последвайте ме:</span>{self.socials(r, "hero-soc", labels=True)}</div>
  </div>
  <div class="me-photo">
    {deco(r, "lavender", "h-lav")}{deco(r, "lemon", "h-lemon")}{deco(r, "mint", "h-mint")}{deco(r, "drop", "h-drop")}
    <div class="portrait">{portrait}</div>
    <div class="me-badge"><b>{esc(CONFIG['name'])}</b><span>Независим консултант на dōTERRA</span></div>
  </div>
</div></section>

<section class="wrap promos">{promo_h}</section>

<section class="wrap block">
  <div class="helps">
    <div>{ICONS["chat"]}<b>Съвет преди покупка</b><span>Пишете ми и заедно избираме продуктите според вас, а не според рекламата.</span></div>
    <div>{ICONS["tag"]}<b>По-добра цена</b><span>Показвам ви как да пазарувате като член и да трупате точки за безплатни продукти.</span></div>
    <div>{ICONS["heart"]}<b>Помощ и след това</b><span>Идеи, рецепти и малки ритуали, за да използвате продуктите с удоволствие.</span></div>
  </div>
</section>

<section class="wrap block">
  <div class="head-row"><div><p class="script">моят избор</p><h2>Любимите масла на Петя</h2></div><a href="zapochni.html#top10">Защо ги избрах →</a></div>
  {fav_h}
</section>

<section class="wrap block">
  <div class="head-row"><h2>Пазарувайте по продуктова линия</h2><a href="katalog.html">Целият каталог →</a></div>
  {lines_h}
</section>

<section class="wrap block purposes-sec">
  <h2>Пазарувайте по повод</h2>
  <div class="purposes">{purp_h}</div>
</section>

<section class="band"><div class="wrap block start">
  <div class="start-txt">
    <p class="script">започнете оттук</p>
    <h2>Не знаете кое масло да изберете?</h2>
    <p class="lead">Отговорете на 4 кратки въпроса и ще ви предложа 3 продукта, подходящи за вас. Отнема по-малко от минута.</p>
    <div class="actions"><a class="btn" href="zapochni.html#test">Направи теста</a><a class="btn ghost" href="zapochni.html#top10">Топ 10 масла</a></div>
  </div>
  <div class="start-imgs" aria-hidden="true">{deco(r, "orange", "s-orange")}{deco(r, "mint", "s-mint")}{''.join(f'<img src="images/{byid[i]["imgfile"]}" alt="">' for i in [28, 27, 37, 51])}</div>
</div></section>

<section class="wrap block">
  <div class="head-row"><h2>Готови комплекти</h2><a href="zapochni.html#komplekti">Всички комплекти →</a></div>
  <p class="lead">Подбрах ги така, че да работят добре заедно. Можете да ги поръчате наведнъж с моя линк.</p>
  <div class="bundles">{''.join(self.bundle(b, r) for b in BUNDLES[:2])}</div>
</section>

<section class="member"><div class="wrap member-in">
  <div class="member-txt">
    <p class="script">пазарувайте с мен</p>
    <h2>Цена за членове и подаръци за редовни поръчки</h2>
    <p>Като член на dōTERRA плащате по-ниска цена от тази на дребно, а с програмата за лоялност трупате точки за безплатни продукти. Няма задължение да продавате. Ще ви помогна с регистрацията и първата поръчка.</p>
  </div>
  <ul class="member-list">
    <li>{ICONS["tag"]}<b>По-ниска цена</b><span>за всички продукти</span></li>
    <li>{ICONS["gift"]}<b>Точки и подаръци</b><span>при редовни поръчки</span></li>
    <li>{ICONS["heart"]}<b>Лична помощ</b><span>от мен, преди и след покупката</span></li>
  </ul>
  <div class="actions"><a class="btn" href="stani-chlen.html#chlenstvo">Как да стана член</a><a class="btn ghost" href="kontakti.html#pitane">Попитайте ме</a></div>
</div></section>

<section class="wrap block">
  <h2>Какво казват клиентите</h2>
  {self.testimonials()}
</section>

{self.guide_block(r)}
{news_h}

<section class="wrap block work-teaser">
  {deco(r, "eucalyptus", "wt-euc")}
  <div>
    <p class="script">работи с мен</p>
    <h2>Харесват ви продуктите и искате да ги споделяте?</h2>
    <p>Можете да станете независим консултант в моя екип. Ще ви покажа как работя, ще ви обуча и ще съм до вас в началото.</p>
  </div>
  <div class="actions"><a class="btn" href="raboti-s-men.html">Научете повече</a><a class="btn ghost" href="raboti-s-men.html#sreshta">Запазете среща</a></div>
</section>

<section class="wrap block">
  <div class="head-row"><h2>Целият каталог</h2><a href="katalog.html">Всички {len(self.p)} продукта →</a></div>
  <div class="tiles">{''.join(tiles)}</div>
</section>
"""
        self.page(self.home, "Етерични масла с Петя", body, 0, active="home")

    # -- започни оттук ----------------------------------------------------------------
    def build_start(self):
        r = ""
        byid = {p["id"]: p for p in self.p}
        top = [byid[i] for i in TOP10]
        top_h = "".join(
            f'<li><a class="top-item" href="produkti/{p["slug"]}.html"><span class="top-img"><img src="images/{p["imgfile"]}" alt="" loading="lazy"></span>'
            f'<span><b>{esc(p["dname"])}</b><span>{esc(TOP10_WHY[p["id"]])}</span></span></a></li>' for p in top)
        qdata = {str(p["id"]): {"n": p["dname"], "s": p["slug"], "i": p["imgfile"], "m": " · ".join(x for x in [p["dtype"], p["size"]] if x)}
                 for p in self.p if p["id"] in QUIZ_IDS}
        quiz_json = json.dumps({"p": qdata, "buy": self.buy_url() or "stani-chlen.html#kupuvane",
                                "ext": bool(self.buy_url()), "viber": self.viber_url() or "kontakti.html"}, ensure_ascii=False)
        body = f"""
<section class="wrap block">
  <p class="eyebrow">Започнете оттук</p>
  <h1>С какво да започна?</h1>
  <p class="lead">Три лесни начина да откриете своите масла: кратък тест, моят топ 10 и готови комплекти. Ако се колебаете, просто ми пишете.</p>
  <div class="actions"><a class="btn ghost" href="#test">Тест</a><a class="btn ghost" href="#top10">Топ 10</a><a class="btn ghost" href="#komplekti">Комплекти</a>{self.viber_btn(r)}</div>
</section>

<section class="band" id="test"><div class="wrap block">
  <p class="script">кратък тест</p>
  <h2>Кое масло е за вас?</h2>
  <div class="quiz" id="quiz" data-quiz='{esc(quiz_json)}'>
    <noscript><p>Тестът има нужда от JavaScript. Пишете ми и ще ви помогна лично.</p></noscript>
  </div>
</div></section>

<section class="wrap block" id="top10">
  <p class="script">моят избор</p>
  <h2>Топ 10 масла за начало</h2>
  <p class="lead">Маслата, които използвам най-често у дома и които препоръчвам на всеки, който тепърва започва.</p>
  <ol class="top10">{top_h}</ol>
  <div class="actions">{self.ext_btn(self.buy_url(), "Пазарувай с моя линк", r, "stani-chlen.html#kupuvane")}<a class="btn ghost" href="katalog.html">Целият каталог</a></div>
</section>

<section class="wrap block" id="komplekti">
  <p class="script">готови комплекти</p>
  <h2>Комплекти по повод</h2>
  <div class="bundles">{''.join(self.bundle(b, r) for b in BUNDLES)}</div>
  <p class="note">Комплектите са мой подбор, а не официални пакети на dōTERRA. Поръчвате продуктите поотделно в една поръчка с моя линк.</p>
</section>"""
        self.page("zapochni.html", "Започнете оттук", body, 0,
                  desc="Тест „Кое масло е за вас“, топ 10 масла за начало и готови комплекти.", active="zapochni")

    # -- работи с мен -----------------------------------------------------------------
    def build_work(self):
        r = ""
        body = f"""
<section class="wrap block">
  <p class="eyebrow">Работи с мен</p>
  <h1>Станете консултант в моя екип</h1>
  <p class="lead">Ако продуктите ви харесват и обичате да ги споделяте, можете да ги препоръчвате и вие като независим консултант на dōTERRA. Работите по свое време, от вкъщи, а аз ви помагам в началото.</p>
  <div class="actions"><a class="btn" href="#sreshta">Запазете среща с мен</a>{self.viber_btn(r, "btn ghost", "Попитайте ме във Viber")}</div>
</section>

<section class="band"><div class="wrap block">
  <h2>Какво получавате</h2>
  <div class="helps">
    <div>{ICONS["tag"]}<b>Цена за членове</b><span>Пазарувате продуктите за себе си на по-ниска цена и трупате точки.</span></div>
    <div>{ICONS["book"]}<b>Обучение от мен</b><span>Показвам ви как говоря за продуктите, как помагам на клиентите и как организирам поръчките.</span></div>
    <div>{ICONS["clock"]}<b>Гъвкаво време</b><span>Няма задължителни часове и норми. Вие решавате колко време да отделяте.</span></div>
    <div>{ICONS["people"]}<b>Общност</b><span>Срещи, идеи и подкрепа от хора, които също обичат маслата.</span></div>
  </div>
</div></section>

<section class="wrap block">
  <h2>Как става</h2>
  <ol class="steps">
    <li><b>Кратка среща</b><span>Говорим 20–30 минути онлайн или на живо. Разказвам ви как работя и отговарям на въпросите ви.</span></li>
    <li><b>Регистрация с моя линк</b><span>Избирате „консултант“ при регистрацията и посочвате мен като спонсор.</span></li>
    <li><b>Първа поръчка</b><span>Заедно избираме продуктите, с които да започнете и които да познавате добре.</span></li>
    <li><b>Първите стъпки</b><span>Обучение, материали и редовни разговори с мен, докато се почувствате уверени.</span></li>
  </ol>
</section>

<section class="wrap block narrow">
  <h2>Въпроси</h2>
  <div class="faq">
    <details><summary>Колко струва да започна?</summary><p><span class="ph">Таксата за регистрация и какво включва стартовият комплект.</span></p></details>
    <details><summary>Колко мога да спечеля?</summary><p>Зависи изцяло от вашето време и усилия, и не мога да ви обещая конкретна сума. dōTERRA публикува официален отчет за доходите на консултантите. На срещата ще ви го покажа и ще ви обясня честно как работи.</p></details>
    <details><summary>Трябва ли да купувам всеки месец?</summary><p><span class="ph">Условията за месечни поръчки и активност според dōTERRA България.</span></p></details>
    <details><summary>Мога ли да спра, когато поискам?</summary><p>Да. Няма договор, който да ви задължава да продължите.</p></details>
    <details><summary>Трябва ли да имам опит с продажби?</summary><p>Не. Повечето хора в екипа започват, защото просто харесват продуктите. Ще ви покажа всичко стъпка по стъпка.</p></details>
  </div>
</section>

<section class="band" id="sreshta"><div class="wrap block narrow">
  <p class="script">да се запознаем</p>
  <h2>Запазете среща с мен</h2>
  <p>Оставете ми контакт и удобно време. Ще ви пиша, за да се уговорим. Срещата е без ангажимент.</p>
  {self.lead_form(r, "sreshta")}
</div></section>
<p class="wrap note">Независимите консултанти не са служители на dōTERRA. Доходите зависят от личните усилия и не са гарантирани.</p>"""
        self.page("raboti-s-men.html", "Работи с мен", body, 0,
                  desc="Как да станете независим консултант на dōTERRA в екипа на Петя.", active="raboti")

    # -- наръчник ----------------------------------------------------------------------
    def build_gift(self):
        r = ""
        body = f"""
<section class="wrap block">
  <p class="eyebrow">Подарък</p>
  <h1>Безплатен наръчник</h1>
</section>
{self.guide_block(r)}"""
        self.page("podarak.html", "Безплатен наръчник", body, 0, desc="Безплатен наръчник „5 малки ритуала с етерични масла“.")

    def build_catalog(self):
        r = ""
        chips = ['<button type="button" class="chip" aria-pressed="true" data-f="">Всички</button>']
        sections = []
        for gslug, gname, _, cats in GROUPS:
            for c in cats:
                cs = self.cat_slug[c]
                chips.append(f'<button type="button" class="chip" aria-pressed="false" data-f="{cs}">{esc(nice(c) if c.isupper() else c)}</button>')
                sections.append(f'<section class="cat-sec" data-sec="{cs}"><div class="head-row"><h2>{esc(c)}</h2>'
                                f'<a href="kategoriya/{cs}.html">{len(self.by_cat[c])} продукта →</a></div>'
                                f'<div class="grid">{"".join(self.card(p, r) for p in self.by_cat[c])}</div></section>')
        body = f"""
<section class="wrap block">
  <p class="eyebrow">Каталог</p>
  <h1>Всички продукти</h1>
  <div class="filters">
    <label class="search"><span class="sr">Търсене</span><input id="q" type="search" placeholder="Търсене: лавандула, рол-он, Deep Blue…" autocomplete="off"></label>
    <div class="chips" id="chips">{''.join(chips)}</div>
  </div>
  <p class="empty" id="empty" hidden>Няма намерени продукти. Опитайте с друга дума.</p>
  {''.join(sections)}
</section>"""
        self.page("katalog.html", "Каталог на продуктите", body, 0,
                  desc="Пълен каталог на продуктите dōTERRA с описания на български.", active="katalog")

    def build_groups(self):
        for gslug, gname, gdesc, cats in GROUPS:
            r = "../"
            secs = "".join(
                f'<section class="cat-sec"><div class="head-row"><h2>{esc(c)}</h2>'
                f'<a href="{r}kategoriya/{self.cat_slug[c]}.html">{len(self.by_cat[c])} продукта →</a></div>'
                f'<div class="grid">{"".join(self.card(p, r) for p in self.by_cat[c])}</div></section>'
                for c in cats)
            body = f"""
<section class="wrap block">
  <nav class="crumbs" aria-label="Навигация"><a href="{r}{self.home}">Начало</a> / <a href="{r}katalog.html">Каталог</a></nav>
  <h1>{esc(gname)}</h1><p class="lead">{esc(gdesc)}</p>
  {secs}
</section>"""
            self.page(f"grupa/{gslug}.html", gname, body, 1, desc=gdesc, active="katalog")

    def build_categories(self):
        for gslug, gname, gdesc, cats in GROUPS:
            for c in cats:
                r = "../"
                body = f"""
<section class="wrap block">
  <nav class="crumbs" aria-label="Навигация"><a href="{r}{self.home}">Начало</a> / <a href="{r}grupa/{gslug}.html">{esc(gname)}</a></nav>
  <h1>{esc(c)}</h1>
  <div class="grid">{"".join(self.card(p, r) for p in self.by_cat[c])}</div>
</section>"""
                self.page(f"kategoriya/{self.cat_slug[c]}.html", c, body, 1, active="katalog")

    def build_products(self):
        gof = {c: g for g in GROUPS for c in g[3]}
        for p in self.p:
            r = "../"
            g = gof[p["category"]]
            cs = self.cat_slug[p["category"]]
            facts = []
            if p["dtype"]: facts.append(("Вид", p["dtype"]))
            if p["latin_name"]: facts.append(("Растение", f'<i class="latin">{esc(p["latin_name"])}</i>'))
            if p["size"]: facts.append(("Разфасовка", esc(p["size"])))
            facts.append(("Категория", f'<a href="{r}kategoriya/{cs}.html">{esc(p["category"])}</a>'))
            facts_h = "".join(f"<div><dt>{k}</dt><dd>{v if k != 'Вид' else esc(v)}</dd></div>" for k, v in facts)
            bens = "".join(f"<li>{esc(b)}</li>" for b in p["benefits"])
            ben_title = "Включва" if p["category"] == "Комплекти и колекции" or p["description"].rstrip().endswith(":") else "Употреба и ползи"
            desc = esc(p["description"]) if p["description"] else ""
            related = [x for x in self.by_cat[p["category"]] if x["id"] != p["id"]][:4]
            rel_h = (f'<section class="block"><h2>Още от „{esc(p["category"])}“</h2><div class="grid">'
                     f'{"".join(self.card(x, r) for x in related)}</div></section>') if related else ""
            order_q = f'{r}kontakti.html#pitane'
            shop = self.ext_btn(self.buy_url(p), "Купи с моя линк", r, "stani-chlen.html#kupuvane")
            title = p["dname"] + (f" – {p['dtype'].lower()}" if p["dtype"] else "")
            meta_desc = (p["description"] or p["dname"])[:155]
            body = f"""
<article class="wrap block product">
  <nav class="crumbs" aria-label="Навигация"><a href="{r}{self.home}">Начало</a> / <a href="{r}grupa/{g[0]}.html">{esc(g[1])}</a> / <a href="{r}kategoriya/{cs}.html">{esc(p['category'])}</a></nav>
  <div class="prod">
    <div class="prod-img"><img src="{r}images/{p['imgfile']}" alt="{esc(p['dname'])}"></div>
    <div class="prod-txt">
      {f'<p class="eyebrow">{esc(p["dtype"])}</p>' if p["dtype"] else ''}
      <h1>{esc(p['dname'])}</h1>
      {f'<p class="latin big">{esc(p["latin_name"])}</p>' if p["latin_name"] else ''}
      {f'<p class="desc">{desc}</p>' if desc else ''}
      {f'<h2 class="h3">{ben_title}</h2><ul class="bens">{bens}</ul>' if bens else ''}
      {f'<p class="touch-link">Има и рол-он версия: <a href="{r}produkti/{p["touch"]["slug"]}.html">{esc(p["touch"]["dname"])} Touch</a></p>' if p["touch"] else ''}
      <dl class="facts">{facts_h}</dl>
      <div class="buy-box">
        <div class="bb-me">{self.portrait_html(r, "bb-photo")}<span><b>Поръчвате с {esc(CONFIG["name"])}</b><small>независим консултант на dōTERRA</small></span>{self.socials(r, "bb-soc")}</div>
        <div class="actions">{shop}<a class="btn ghost" href="{order_q}">Попитай за продукта</a></div>
        <p>Поръчката става в официалния онлайн магазин на dōTERRA. Като пазарувате с моя линк, оставате мой клиент и съм насреща със съвети след покупката.
        Като член плащате по-ниска цена: <a href="{r}stani-chlen.html#chlenstvo">как става</a>.</p>
        {self.missing_links_note()}
      </div>
      <p class="note">Описанието е по официалния каталог на dōTERRA. Не е медицински съвет.</p>
    </div>
  </div>
  {rel_h}
</article>"""
            self.page(f"produkti/{p['slug']}.html", title, body, 1, desc=meta_desc, active="katalog")

    def build_static(self):
        links = []
        if CONFIG["phone"]: links.append(f'<li><b>Телефон</b><span class="sel">{esc(CONFIG["phone"])}</span></li>')
        else: links.append('<li><b>Телефон</b><span class="ph">телефон</span></li>')
        if CONFIG["viber"] or CONFIG["phone"]: links.append(f'<li><b>Viber</b><span class="sel">{esc(CONFIG["viber"] or CONFIG["phone"])}</span></li>')
        links.append(f'<li><b>Имейл</b>{("<span class=sel>" + esc(CONFIG["email"]) + "</span>") if CONFIG["email"] else "<span class=ph>имейл</span>"}</li>')
        for k, lab in (("facebook", "Facebook"), ("instagram", "Instagram")):
            links.append(f'<li><b>{lab}</b>' + (f'<a href="{esc(CONFIG[k])}" target="_blank" rel="noopener">{esc(CONFIG[k])}</a>' if CONFIG[k] else f'<span class="ph">линк към {lab}</span>') + '</li>')
        body = f"""
<section class="wrap block narrow">
  <p class="eyebrow">Контакт</p>
  <h1>Свържете се с мен</h1>
  <p>Искате да поръчате, но не знаете откъде да започнете? Вижте <a href="stani-chlen.html">как се пазарува с моя линк и как става членството</a>, или ми пишете директно.</p>
  <h2 id="pitane" class="h3">Пишете ми</h2>
  <p>Пишете ми за съвет кой продукт да изберете, за отстъпки и промоции, или ако искате помощ с първата поръчка.</p>
  <div class="actions">{self.viber_btn("")}{self.ext_btn(self.buy_url(), "Купи с моя линк", "", "stani-chlen.html#kupuvane", "btn ghost")}</div>
  <ul class="contact">{''.join(links)}</ul>
</section>"""
        self.page("kontakti.html", "Контакт", body, 0, active="kontakti")

        body = f"""
<section class="wrap block narrow">
  <p class="eyebrow">За мен</p>
  <h1>{self.ph('name','Име Фамилия')}</h1>
  <div class="portrait wide"><span class="ph">Ваша снимка</span></div>
  <p><span class="ph">Тук идва вашата история: как открихте етеричните масла, кои продукти използвате най-често у дома, какво обучение сте преминали и как помагате на клиентите си. 2–4 кратки абзаца са достатъчни.</span></p>
  <h2>Какво мога да направя за вас</h2>
  <ul class="bens">
    <li>Да ви помогна да изберете продукти според вашите нужди и бюджет.</li>
    <li>Да ви покажа как да поръчвате на цена за членове.</li>
    <li>Да ви дам идеи и рецепти за безопасна ежедневна употреба.</li>
  </ul>
  <div class="actions">{self.viber_btn("")}<a class="btn ghost" href="kontakti.html">Други начини за връзка</a></div>
  <h2>Последвайте ме</h2>
  <p>Във Facebook и Instagram споделям идеи, рецепти и промоциите на месеца.</p>
  {self.socials("", "big-soc", labels=True)}
  <h2>Моменти от моя ден</h2>
  <div class="gallery"><span class="ph">снимка 1</span><span class="ph">снимка 2</span><span class="ph">снимка 3</span></div>
  <h2>Какво казват клиентите</h2>
  {self.testimonials()}
</section>"""
        self.page("za-men.html", "За мен", body, 0, active="za-men")

        body = f"""
<section class="wrap block narrow">
  <h1>Политика за поверителност</h1>
  <p><span class="ph">Този текст е шаблон и трябва да се прегледа. Ако сайтът няма форма за контакт, бисквитки за анализ или бюлетин, политиката може да е кратка.</span></p>
  <h2 class="h3">Администратор на лични данни</h2>
  <p>{self.ph('name','Име Фамилия')}, имейл: {self.ph('email','имейл')}.</p>
  <h2 class="h3">Какви данни обработваме</h2>
  <p>Само данните, които ни изпратите сами по телефон, имейл или социални мрежи (име, телефон, имейл), с цел да отговорим на запитването ви. Поръчките се обработват от dōTERRA в техния онлайн магазин по тяхната политика за поверителност.</p>
  <h2 class="h3">Бисквитки</h2>
  <p>Сайтът не използва бисквитки за проследяване. Шрифтовете се зареждат от Google Fonts.</p>
  <h2 class="h3">Вашите права</h2>
  <p>Имате право на достъп, корекция и изтриване на данните си, както и право на жалба до Комисията за защита на личните данни (www.cpdp.bg).</p>
</section>"""
        self.page("poveritelnost.html", "Политика за поверителност", body, 0)


    # -- пазаруване и членство ---------------------------------------------------
    def build_join(self):
        r = ""
        shop = self.ext_btn(self.buy_url(), "Пазарувай с моя линк", r, "kontakti.html")
        enroll = self.ext_btn(CONFIG["enroll_url"], "Регистрирай се с моя линк", r, "kontakti.html")
        rid = CONFIG.get("referral_id")
        rid_h = (f'<b class="sel">{esc(rid)}</b>' if rid else '<span class="ph">номер в dōTERRA</span>')
        body = f"""
<section class="wrap block">
  <p class="eyebrow">Пазарувай с мен</p>
  <h1>Как се поръчва dōTERRA</h1>
  <p class="lead">Продуктите на dōTERRA се продават само в официалния им онлайн магазин. Аз съм независим консултант: когато поръчвате с моя линк или се регистрирате под мен, аз съм вашият човек за съвети, идеи и помощ с поръчките.</p>
  {self.missing_links_note(("shop_url", "enroll_url"))}
  <div class="paths">
    <div class="path" id="kupuvane">
      <p class="script">клиент</p>
      <h2 class="h3">Пазарувам без регистрация</h2>
      <p>Поръчвате на цена на дребно, когато поискате. Без такси и без ангажимент.</p>
      <ul class="bens"><li>Подходящо за първа или еднократна поръчка</li><li>Доставка до адрес</li></ul>
      {shop}
    </div>
    <div class="path featured" id="chlenstvo">
      <p class="script">член</p>
      <h2 class="h3">Пазарувам на по-ниска цена</h2>
      <p>С регистрация като член купувате на цена за членове и можете да трупате точки за безплатни продукти чрез програмата за лоялност. Няма задължение да продавате.</p>
      <ul class="bens"><li>По-ниска цена от тази на дребно</li><li>Точки и подаръци при редовни поръчки</li><li>Моя лична помощ с първата поръчка</li></ul>
      {enroll}
    </div>
    <div class="path" id="konsultant">
      <p class="script">консултант</p>
      <h2 class="h3">Искам да споделям продуктите</h2>
      <p>Ако продуктите ви харесат и искате да ги препоръчвате на други хора, можете да станете независим консултант в моя екип. Ще ви покажа как работя и ще ви помагам в началото.</p>
      <ul class="bens"><li>Същата регистрация, с избор „консултант“</li><li>Обучение и подкрепа от мен</li></ul>
      <a class="btn ghost" href="kontakti.html#pitane">Пиши ми за подробности</a>
    </div>
  </div>
</section>

<section class="band"><div class="wrap block">
  <h2>Регистрацията стъпка по стъпка</h2>
  <ol class="steps">
    <li><b>Отворете моя линк</b><span>Натиснете „Регистрирай се с моя линк“ по-горе. Отваря се официалният сайт на dōTERRA.</span></li>
    <li><b>Изберете вид регистрация</b><span>Член, ако искате само по-ниски цени. Консултант, ако искате и да препоръчвате продуктите.</span></li>
    <li><b>Проверете, че съм посочена аз</b><span>В полето за препоръчал / спонсор трябва да стои моето име или номер: {rid_h}.</span></li>
    <li><b>Изберете първа поръчка</b><span>Ако не знаете с какво да започнете, пишете ми и ще направим списък заедно.</span></li>
  </ol>
</div></section>

<section class="wrap block narrow">
  <h2>Често задавани въпроси</h2>
  <div class="faq">
    <details><summary>Трябва ли да продавам, ако стана член?</summary><p>Не. Членството е, за да пазарувате на по-ниска цена. Продажбите не са задължителни.</p></details>
    <details><summary>Колко струва регистрацията?</summary><p><span class="ph">Актуалната такса за регистрация в България и какво включва.</span></p></details>
    <details><summary>Има ли минимална поръчка или месечен ангажимент?</summary><p><span class="ph">Условията за минимална поръчка и програмата за лоялност според dōTERRA България.</span></p></details>
    <details><summary>Защо да поръчам точно с вашия линк?</summary><p>Цената е същата, но така сте в моя екип: помагам ви да изберете продукти, давам идеи за употреба и ви казвам за промоциите всеки месец.</p></details>
    <details><summary>Как стига поръчката до мен?</summary><p>dōTERRA изпраща поръчката директно до вашия адрес. <span class="ph">Срок и цена на доставка.</span></p></details>
  </div>
  <div class="actions">{shop}<a class="btn ghost" href="kontakti.html#pitane">Имам въпрос</a></div>
</section>"""
        self.page("stani-chlen.html", "Пазарувай с мен и стани член", body, 0,
                  desc="Как да поръчате продукти dōTERRA с моя линк и как да станете член с по-ниски цени.", active="stani-chlen")

    # -- новини ------------------------------------------------------------------
    def post_card(self, n, r):
        img = (f'<span class="post-img"><img src="{r}{n["img"]}" alt="" loading="lazy"></span>' if n["img"] else "")
        tag = '<span class="ph">пример</span> ' if n["example"] else ""
        return (f'<a class="post" href="{r}novini/{n["slug"]}.html">{img}<span class="post-body">'
                f'<time datetime="{n["date"]}">{esc(n["date_bg"])}</time>'
                f'<b>{tag}{esc(n["title"])}</b><span>{esc(n["summary"])}</span></span></a>')

    def build_news(self):
        r = ""
        cards = "".join(self.post_card(n, r) for n in self.news)
        body = f"""
<section class="wrap block">
  <p class="eyebrow">Новини</p>
  <h1>Новини, промоции и идеи</h1>
  <p class="lead">Промоции на месеца, нови продукти, събития и малки ритуали за всеки ден.</p>
  {f'<div class="posts">{cards}</div>' if cards else '<p class="empty">Все още няма публикации.</p>'}
</section>"""
        self.page("novini.html", "Новини", body, 0, desc="Новини, промоции и идеи с етерични масла.", active="novini")
        byid = {p["id"]: p for p in self.p}
        for n in self.news:
            r = "../"
            prods = [byid[i] for i in n["products"] if i in byid]
            prod_h = (f'<section class="block"><h2>Продукти от публикацията</h2><div class="grid">'
                      f'{"".join(self.card(x, r) for x in prods)}</div></section>') if prods else ""
            img = f'<img class="post-hero" src="{r}{n["img"]}" alt="">' if n["img"] else ""
            ex = ('<p class="note"><span class="ph">Това е примерна публикация. Петя ще я замени със своя.</span></p>'
                  if n["example"] else "")
            body = f"""
<article class="wrap block narrow post-page">
  <nav class="crumbs" aria-label="Навигация"><a href="{r}{self.home}">Начало</a> / <a href="{r}novini.html">Новини</a></nav>
  <time datetime="{n["date"]}" class="eyebrow">{esc(n["date_bg"])}</time>
  <h1>{esc(n["title"])}</h1>
  {ex}
  {img}
  <div class="prose">{n["html"]}</div>
  <div class="actions">{self.ext_btn(self.buy_url(), "Пазарувай с моя линк", r, "stani-chlen.html#kupuvane")}<a class="btn ghost" href="{r}novini.html">Още новини</a></div>
  {prod_h}
</article>"""
            self.page(f"novini/{n['slug']}.html", n["title"], body, 1, desc=n["summary"], active="novini")

    def make_guide(self, assets_src, img_out):
        """Прави assets/narachnik.pdf (нужни са Node.js и Playwright)."""
        import subprocess, tempfile
        here = os.path.join(os.path.dirname(assets_src), "narachnik")
        byid = {p["id"]: p for p in self.p}
        ph = '<span class="ph">{}</span>'
        data = {"text": {"brand": esc(self.brand()), "name": esc(CONFIG["name"]),
                         "instagram": esc(CONFIG["instagram"].replace("https://www.", "")) or ph.format("Instagram"),
                         "viber": esc(CONFIG.get("viber") or CONFIG.get("phone")) or ph.format("номер"),
                         "site": esc(CONFIG["site_url"].replace("https://", "")) or ph.format("адрес на сайта")},
                "img": {str(i): byid[i]["imgfile"] for i in (20, 27, 28, 37, 79)}}
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        try:
            subprocess.run(["node", os.path.join(here, "make_pdf.js"), img_out,
                            os.path.join(self.out, "assets", "narachnik.pdf"), f.name], check=True, timeout=120)
        except Exception as e:
            print("ВНИМАНИЕ: наръчникът (PDF) не беше направен:", e)
        finally:
            os.unlink(f.name)

    def build_assets(self, assets_src, data_src):
        os.makedirs(os.path.join(self.out, "assets"), exist_ok=True)
        for f in ("style.css", "site.js"):
            shutil.copy(os.path.join(assets_src, f), os.path.join(self.out, "assets", f))
        ill = os.path.join(self.out, "assets", "ill")
        if os.path.isdir(ill):
            shutil.rmtree(ill)
        shutil.copytree(os.path.join(assets_src, "ill"), ill)
        img_out = os.path.join(self.out, "images")
        os.makedirs(img_out, exist_ok=True)
        for p in self.p:
            shutil.copy(p["imgsrc"], os.path.join(img_out, p["imgfile"]))
        self.make_guide(assets_src, img_out)
        for n in self.news:
            if n.get("imgsrc"):
                os.makedirs(os.path.join(self.out, "novini", "snimki"), exist_ok=True)
                shutil.copy(n["imgsrc"], os.path.join(self.out, n["img"]))
        if CONFIG["site_url"]:
            base = CONFIG["site_url"].rstrip("/")
            urls = [f"{base}/"] + [f"{base}/{u}" for u in ["katalog.html", "za-men.html", "kontakti.html", "stani-chlen.html", "novini.html"]]
            urls += [f"{base}/novini/{n['slug']}.html" for n in self.news]
            urls += [f"{base}/grupa/{g[0]}.html" for g in GROUPS]
            urls += [f"{base}/kategoriya/{s}.html" for s in self.cat_slug.values()]
            urls += [f"{base}/produkti/{p['slug']}.html" for p in self.p]
            with open(os.path.join(self.out, "sitemap.xml"), "w", encoding="utf-8") as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
                f.write("".join(f"<url><loc>{esc(u)}</loc></url>\n" for u in urls))
                f.write("</urlset>\n")


def main():
    src, out = sys.argv[1], sys.argv[2]
    preview = "--preview" in sys.argv
    here = os.path.dirname(os.path.abspath(__file__))
    prods = load(src)
    s = Site(prods, out, preview)
    s.news = load_news(src, prods)
    s.build_assets(os.path.join(here, "assets"), src)
    s.build_home(); s.build_catalog(); s.build_groups(); s.build_categories()
    s.build_products(); s.build_static(); s.build_join(); s.build_news()
    s.build_start(); s.build_work(); s.build_gift()
    print("ok", len(prods), "products ->", out)

if __name__ == "__main__":
    main()

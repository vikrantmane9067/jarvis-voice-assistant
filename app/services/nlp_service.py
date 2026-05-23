"""JARVIS NLP Service v3.0 — Table-driven intent classifier, patterns pre-compiled."""
from __future__ import annotations
import random, re
from typing import Any

# ── Response Banks ──────────────────────────────────
JOKES  = ["Light attracts bugs — devs prefer dark mode.","SQL query walks into a bar: 'Can I join you?'",
          "Only 10 types of people: binary understanders and others.","JS dev was sad — he didn't Node how to Express himself.",
          "How do you comfort a JS bug? You console it.","Why do Java devs wear glasses? They can't C#.",
          "I have a UDP joke, but you might not get it."]
QUOTES = ["The only way to do great work is to love what you do. — Jobs",
          "Talk is cheap. Show me the code. — Torvalds",
          "First solve the problem, then write the code. — Johnson",
          "Good code is its own best documentation. — McConnell"]
_GREET = ["Hello! JARVIS online. What shall I execute?","Hey! All systems ready. Fire away!","Greetings! Your AI command center is live."]
_THANKS= ["You're welcome!","My pleasure!","Anytime! 🚀","Glad I could help!"]
_MISS  = ["Say 'help' to see all commands.","Try: 'search ...', 'open ...', or 'weather in ...'","I didn't catch that. Say 'help' for the full list."]
HELP_MSG = ("🔍 Search | 🌤️ Weather | 📰 News | 🖥️ Open Apps | 🎵 Media | ⏰ Reminders | "
            "📝 Notes | 🔊 Volume | 📸 Screenshot | 💻 System | 🌍 Translate | "
            "📖 Define | 🔄 Convert | 🎲 Dice | 🪙 Coin | 😄 Jokes | 🔌 Power | 📁 Files | 🛠️ Git | 🧮 Calc")

# ── Unit Alias Lookup ───────────────────────────────
_UA = {"c":"celsius","f":"fahrenheit","k":"kelvin","kilometer":"km","kilometers":"km","mile":"miles",
       "meter":"meters","metre":"meters","metres":"meters","foot":"feet","centimeter":"cm",
       "centimeters":"cm","inch":"inches","kilogram":"kg","kilograms":"kg","pound":"pounds",
       "gram":"grams","ounce":"ounces","kph":"kmh","km/h":"kmh"}
def _unit(u): u=u.lower().strip(); return _UA.get(u.rstrip("s"), _UA.get(u,u))

# ── Action Extractors ───────────────────────────────
def _loc(_,p):
    m=re.search(r"weather\s+(?:in|for|at)\s+([a-zA-Z ]+)",p); return {"location":m.group(1).strip() if m else "world"}

def _translate(_,p):
    lm=re.search(r"(?:to|into|in)\s+([a-zA-Z]+)(?:\s+language)?",p)
    tm=re.search(r'translate\s+["\']?(.+?)["\']?\s+(?:to|into|in)',p,re.I)
    lang=lm.group(1).capitalize() if lm else "Spanish"
    text=tm.group(1) if tm else re.sub(r"\b(translate|to|in|into|language)\b","",p).strip()
    return {"text":text,"target_lang":lang}

def _define(_,p):
    m=re.search(r"(?:define|meaning\s*of|definition\s*of|what\s*does)\s+['\"]?(\w+)",p,re.I)
    return {"word":m.group(1) if m else re.sub(r"\b(define|definition|meaning|of|what|does|mean)\b","",p).strip()}

def _convert(_,p):
    _UP=r"(km|kilometer|mile|foot|feet|meter|cm|inch|kg|pound|gram|ounce|celsius|fahrenheit|kelvin|kmh|mph)"
    # Match "X unit" (from) and "to/in unit" (to)
    fm=re.search(rf"([\d.]+)\s*{_UP}",p,re.I)
    # Support both "X km to miles" and "how many miles in X km" (reverse lookup)
    tm=re.search(rf"\b(?:to|into)\s*{_UP}",p,re.I)
    if not tm:
        # "how many UNIT in X UNIT2" — target unit is first word unit
        tm=re.search(rf"how\s+many\s+{_UP}",p,re.I)
    nm=re.search(r"([\d.]+)",p)
    from_unit = _unit(fm.group(2) if fm else "km")
    to_unit   = _unit(tm.group(1) if tm else "miles")
    # If both parsed to same unit (ambiguous), swap
    if from_unit == to_unit and fm and tm:
        to_unit = _unit(fm.group(2))
        from_unit = _unit(tm.group(1))
    return {"value": float(fm.group(1) if fm else (nm.group(1) if nm else "1")),
            "from_unit": from_unit, "to_unit": to_unit}

def _query(_,p): return {"query":re.sub(r"\b(search|find|google|look.?up|search.?for|online)\b","",p).strip() or p}
def _open(_,p): parts=p.replace("open ","").split(" in ",1); return {"app":parts[0].strip(),"browser":parts[1].strip() if len(parts)>1 else None}
def _timer(_,p): m=re.search(r"(\d+)\s*(second|minute|hour|min|sec|hr)",p); return {"duration":int(m.group(1)) if m else 5,"unit":m.group(2) if m else "minute"}
def _safe_eval(p):
    # Normalise word-form math operators before stripping non-numeric chars
    expr = p.lower()
    expr = re.sub(r"\btimes\b|\bmultiplied\s+by\b",   "*", expr)
    expr = re.sub(r"\bdivided\s+by\b|\bdivide\s+by\b","/", expr)
    expr = re.sub(r"\bplus\b",                         "+", expr)
    expr = re.sub(r"\bminus\b",                        "-", expr)
    expr = re.sub(r"\bsquared\b",                      "**2", expr)
    expr = re.sub(r"\bcubed\b",                        "**3", expr)
    clean = re.sub(r"[^0-9.+\-*/() ]", "", expr).strip()
    try:
        r = eval(clean)  # noqa: S307  (intentionally limited to numeric ops)
        return str(int(r) if isinstance(r, float) and r.is_integer() else round(r, 4))
    except: return "?"

# ── Rule Table ──────────────────────────────────────
# (pattern, intent, confidence, response_or_fn, action_fn)
_RAW = [
    (r"\b(shut\s*down|power\s*off|turn\s*off.*(computer|pc|system))\b","shutdown",0.96,"⚠️ Shutting down in 30s. Say 'cancel shutdown' to abort.",lambda _,__:{"action":"shutdown"}),
    (r"\b(restart|reboot)\b","restart",0.95,"⚠️ Restarting in 30s. Say 'cancel shutdown' to abort.",lambda _,__:{"action":"restart"}),
    (r"\bcancel\s*(shut\s*down|restart|reboot)\b","cancel_shutdown",0.97,"Shutdown/restart cancelled.",lambda _,__:{"action":"cancel_shutdown"}),
    (r"\b(sleep|hibernate|suspend)\b","sleep",0.93,"Putting system to sleep.",lambda _,__:{"action":"sleep"}),
    (r"\b(lock\s*(the\s*)?(screen|computer|pc)|lock\s*screen)\b","lock_screen",0.94,"Locking screen now.",None),
    (r"\b(screenshot|screen\s*capture|take\s*a?\s*screenshot|snap\s*screen)\b","screenshot",0.95,"Taking screenshot now.",None),
    (r"\b(volume\s*up|increase\s*volume|louder|turn\s*up)\b","volume_up",0.93,"Turning volume up.",None),
    (r"\b(volume\s*down|decrease\s*volume|quieter|lower\s*volume)\b","volume_down",0.93,"Turning volume down.",None),
    (r"\b(mute|unmute|silence)\b","mute",0.94,"Toggling mute.",None),
    (r"\b(system\s*info|system\s*status|about.*(computer|pc|system)|specs)\b","system_info",0.94,"Fetching system info...",None),
    (r"\b(battery|power\s*level|charge)\b","battery_status",0.93,"Checking battery...",None),
    (r"\b(ip\s*address|my\s*ip|network\s*address|what.*my.*ip)\b","ip_address",0.93,"Fetching IP address...",None),
    (r"\b(disk\s*(usage|space)|storage|how\s*much\s*space)\b","disk_usage",0.92,"Checking disk usage...",None),
    (r"\b(what.*time|current\s*time|tell.*time)\b","time",0.96,"Checking current time.",None),
    (r"\b(what.*date|today.*date|current\s*date|what\s*day)\b","date",0.96,"Checking today's date.",None),
    (r"\bweather\b","weather",0.94,"Fetching weather...",_loc),
    (r"\b(translate|translation)\b","translate",0.91,lambda _,p:f"🌍 Translating to {_translate(_,p)['target_lang']}...",_translate),
    (r"\b(define|definition|meaning\s*of|what\s*does\s*.+\s*mean)\b","define",0.90,lambda _,p:f"📖 Defining '{_define(_,p)['word']}'...",_define),
    (r"\b(convert|how\s*many|in\s+(km|miles|feet|meters|celsius|fahrenheit|pounds|kg))\b","convert_units",0.90,"🔄 Converting...",_convert),
    (r"\b(flip\s*(a\s*)?coin|coin\s*flip|heads\s*or\s*tails)\b","coin_flip",0.97,lambda _,__:f"Flipping... {random.choice(['Heads! 🪙','Tails! 🪙'])}",None),
    (r"\b(roll\s*(a?\s*)?d?\s*dice?|d(4|6|8|10|12|20|100)|roll\s+a?\s*d\d+)\b","roll_dice",0.97,
     lambda m,p: (lambda s: f"🎲 Rolled d{s}: **{random.randint(1,s)}**")(int((re.search(r'\bd(\d+)\b',p,re.I) or re.match(r'.*','')).group(1)) if re.search(r'\bd(\d+)\b',p,re.I) else 6),None),
    (r"\b(search|find|google|look\s*up|search\s*for)\b","web_search",0.92,lambda _,p:f"🔍 Searching: {_query(_,p)['query']}",_query),
    (r"\b(news|headlines?|latest\s*news|top\s*stories)\b","news",0.91,"📰 Opening latest news headlines.",None),
    (r"\bopen\b","open_app",0.90,lambda _,p:f"Opening {p.replace('open ','').split(' in ')[0].strip()} now.",_open),
    (r"\bplay\s+([a-zA-Z0-9 ._-]+)","play_media",0.89,lambda m,_:f"🎵 Playing {m.group(1).strip()}.",lambda m,_:{"media":m.group(1).strip()}),
    (r"\b(remind|reminder|alarm|set\s*a?\s*reminder)\b","set_reminder",0.90,"⏰ Reminder set!",lambda _,p:{"task":p}),
    (r"\b(set\s*a?\s*timer|timer\s*for|start\s*timer|countdown)\b","set_timer",0.91,lambda _,p:f"⏱️ Timer set for {_timer(_,p)['duration']} {_timer(_,p)['unit']}(s).",_timer),
    (r"\b(create\s*(?:a\s*)?note|take\s*(?:a\s*)?note|note\s*down|write\s*down)\b","create_note",0.90,"📝 Note saved.",lambda _,p:{"note":re.sub(r"\b(create|take|note|down|write)\b","",p).strip()}),
    (r"\b(add\s*(?:a\s*)?todo|add\s*to\s*(?:my\s*)?(?:to-?do|task)\s*list|new\s*task)\b","todo_add",0.90,"✅ Added to todo list.",lambda _,p:{"task":re.sub(r"\b(add|todo|to.?do|task|list|new)\b","",p).strip()}),
    (r"\b(list\s*files|show\s*files|directory|ls|dir)\b","list_files",0.90,"📁 Listing files...",lambda _,p:{"path":(re.search(r"(?:in|at|of)\s+(.+)",p) or type("o",(),{"group":lambda _,i:"."})()).group(1).strip()}),
    (r"\b(create\s*(?:a\s*)?file|new\s*file|make\s*(?:a\s*)?file)\b","create_file",0.89,"📄 Creating file.",lambda _,p:{"filename":(re.search(r"(?:named?|called?)\s+([^\s]+)",p) or type("o",(),{"group":lambda _,i:"jarvis_note.txt"})()).group(1)}),
    (r"\b(git\s*status|check\s*git)\b","git_status",0.91,"🛠️ Checking git status...",None),
    # Clipboard: READ must be matched BEFORE write (more specific pattern first)
    (r"\b(read.*clipboard|get.*clipboard|what.*clipboard|clipboard.*content|show.*clipboard|paste\s*from\s*clipboard)\b","clipboard_read",0.92,
     "📋 Reading clipboard...",None),
    (r"\b(copy|set|write|put|save)\b.{0,30}\b(clipboard)\b|\bclipboard\b.{0,10}\b(copy|write|set|save)\b","clipboard_write",0.91,
     lambda _,p:f"📋 Copying to clipboard: {re.sub(r'\b(copy|set|write|clipboard|to|the)\b','',p).strip()[:50]}",
     lambda _,p:{"text":re.sub(r"\b(copy|set|write|put|save|clipboard|to|the|my)\b","",p).strip()}),
    (r"\b(pip\s*install|install\s*package)\b","pip_install",0.90,lambda _,p:f"📦 Installing {re.sub(r'pip.?install|install.?package','',p).strip()}...",lambda _,p:{"package":re.sub(r"\b(pip.?install|install.?package)\b","",p).strip()}),
    (r"\b(run\s*command|execute|terminal|cmd)\b","run_command",0.88,"💻 Running command...",lambda _,p:{"command":re.sub(r"\b(run.?command|execute|terminal|cmd|run)\b","",p).strip()}),
    (r"(\d+\s*(plus|minus|times|multiplied|divided|\+|\-|\*|/))|(\d+\s+){0,2}(plus|minus|times|divided\s+by)|(\d+\s+(squared|cubed))|(\d+\s*\*\*\s*\d+)","calculator",0.95,lambda _,p:f"🧮 = {_safe_eval(p)}",None),
    (r"\b(joke|funny|make\s*me\s*laugh|humor)\b","joke",0.95,lambda _,__:random.choice(JOKES),None),
    (r"\b(quote|inspiration|motivat|inspire)\b","quote",0.95,lambda _,__:random.choice(QUOTES),None),
    (r"\b(hello|hi|hey|good\s*(morning|afternoon|evening)|greetings|namaste)\b","greeting",0.96,lambda _,__:random.choice(_GREET),None),
    (r"\b(help|what\s*can\s*you\s*do|capabilities|commands|features)\b","help",0.99,HELP_MSG,None),
    (r"\b(who\s*(are\s*you|r\s*u)|your\s*name|what\s*are\s*you)\b","identity",0.98,"I am JARVIS — Just A Rather Very Intelligent System. v3.0, your AI command center.",None),
    (r"\b(thank|thanks|thx|appreciate)\b","thanks",0.95,lambda _,__:random.choice(_THANKS),None),
]
RULES = [(re.compile(p,re.I),*rest) for p,*rest in _RAW]


def classify_command(text: str) -> dict[str, Any]:
    prompt = re.sub(r"^(hey|ok)\s*jarvis[,\s]+","",text.strip(),flags=re.I).lower()
    if not prompt: return {"intent":"idle","response":"Say or type a command.","confidence":0.0,"action_data":{}}
    for pattern, intent, confidence, resp_tmpl, action_fn in RULES:
        if m := pattern.search(prompt):
            return {"intent":intent,"response":resp_tmpl(m,prompt) if callable(resp_tmpl) else resp_tmpl,
                    "confidence":confidence,"action_data":action_fn(m,prompt) if action_fn else {}}
    return {"intent":"chat","response":random.choice(_MISS),"confidence":0.60,"action_data":{}}

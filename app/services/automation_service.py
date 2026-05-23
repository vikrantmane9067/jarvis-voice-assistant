"""JARVIS Automation Service v3.0 — Compact, full-featured system control."""
from __future__ import annotations
import ctypes, datetime, os, platform, shutil, socket, subprocess
from pathlib import Path
from typing import Any

WIN = platform.system() == "Windows"

# ── Desktop Path ────────────────────────────────────
def _desktop() -> Path:
    if WIN:
        try:
            import winreg
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")
            p = Path(os.path.expandvars(winreg.QueryValueEx(k, "Desktop")[0]))
            winreg.CloseKey(k)
            if p.exists(): return p
        except Exception: pass
    for c in [Path.home()/"OneDrive"/"Desktop", Path.home()/"Desktop"]:
        if c.exists(): return c
    d = Path.home()/"Desktop"; d.mkdir(parents=True, exist_ok=True); return d


# ── System Info ─────────────────────────────────────
def get_system_info() -> dict[str, Any]:
    try:
        import psutil
        m, d = psutil.virtual_memory(), psutil.disk_usage("C:\\" if WIN else "/")
        up = datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time())
        return {"os": f"{platform.system()} {platform.release()}", "machine": platform.machine(),
                "processor": platform.processor() or "N/A", "cpu_cores": psutil.cpu_count(logical=True),
                "cpu_percent": psutil.cpu_percent(interval=0.5),
                "ram_total_gb": round(m.total/1e9,2), "ram_used_gb": round(m.used/1e9,2), "ram_percent": m.percent,
                "disk_total_gb": round(d.total/1e9,2), "disk_used_gb": round(d.used/1e9,2), "disk_percent": d.percent,
                "uptime": str(up).split(".")[0]}
    except ImportError: return {"error": "psutil not installed"}

def get_disk_usage() -> dict[str, Any]:
    try:
        import psutil
        drives = []
        for p in psutil.disk_partitions():
            try:
                u = psutil.disk_usage(p.mountpoint)
                drives.append({"drive": p.device, "mountpoint": p.mountpoint, "fstype": p.fstype,
                    "total_gb": round(u.total/1e9,2), "used_gb": round(u.used/1e9,2),
                    "free_gb": round(u.free/1e9,2), "percent": u.percent})
            except PermissionError: continue
        return {"drives": drives}
    except ImportError: return {"error": "psutil not installed"}

def get_battery_status() -> dict[str, Any]:
    try:
        import psutil
        b = psutil.sensors_battery()
        if b: return {"percent": b.percent, "plugged_in": b.power_plugged,
                      "time_left": str(datetime.timedelta(seconds=b.secsleft)) if b.secsleft > 0 else "Charging"}
        return {"error": "No battery detected (desktop PC)"}
    except ImportError: return {"error": "psutil not installed"}

def get_ip_address() -> dict[str, str]:
    local = "N/A"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(("8.8.8.8", 80))
        local = s.getsockname()[0]; s.close()
    except Exception: pass
    public = "N/A"
    try:
        import requests; public = requests.get("https://api.ipify.org?format=json", timeout=3).json().get("ip","N/A")
    except Exception: pass
    return {"local_ip": local, "public_ip": public}

def get_cpu_ram_live() -> dict[str, Any]:
    try:
        import psutil
        m = psutil.virtual_memory()
        return {"cpu_percent": psutil.cpu_percent(interval=0.3), "ram_percent": m.percent,
                "ram_used_gb": round(m.used/1e9,2), "ram_total_gb": round(m.total/1e9,2)}
    except ImportError: return {"cpu_percent": 0, "ram_percent": 0, "ram_used_gb": 0, "ram_total_gb": 0}

def get_current_datetime() -> dict[str, str]:
    n = datetime.datetime.now()
    return {"date": n.strftime("%A, %B %d, %Y"), "time": n.strftime("%I:%M %p"),
            "day": n.strftime("%A"), "timestamp": n.isoformat()}


# ── Media / UI Controls ─────────────────────────────
def take_screenshot() -> str:
    try:
        from PIL import ImageGrab
        p = _desktop() / f"jarvis_screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        ImageGrab.grab().save(str(p)); return f"Screenshot saved to {p}"
    except ImportError: return "Pillow not installed."
    except Exception as e: return f"Screenshot failed: {e}"

def control_volume(action: str) -> str:
    if not WIN: return "Volume control is only supported on Windows."
    vk = {"mute": 0xAD, "up": 0xAF, "down": 0xAE}.get(action)
    if not vk: return "Unknown volume action."
    for _ in range(5 if action != "mute" else 1):
        ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
        ctypes.windll.user32.keybd_event(vk, 0, 0x0002, 0)
    return {"up": "Volume increased.", "down": "Volume decreased.", "mute": "Muted/unmuted."}[action]

def lock_screen() -> str:
    if not WIN: return "Lock screen only supported on Windows."
    try: ctypes.windll.user32.LockWorkStation(); return "Screen locked."
    except Exception as e: return f"Failed: {e}"

def power_action(action: str) -> str:
    if not WIN: return f"Power action '{action}' only supported on Windows."
    cmds = {"shutdown": ["shutdown","/s","/t","30"], "restart": ["shutdown","/r","/t","30"],
            "cancel_shutdown": ["shutdown","/a"], "sleep": None}
    try:
        if action == "sleep":
            subprocess.run(["powershell","-Command",
                "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Application]::SetSuspendState('Suspend',$false,$false)"], timeout=5)
            return "Going to sleep."
        if cmd := cmds.get(action):
            (subprocess.run if action == "cancel_shutdown" else subprocess.Popen)(cmd, **({"timeout":5,"capture_output":True} if action=="cancel_shutdown" else {}))
            return {"shutdown":"Shutting down in 30s.","restart":"Restarting in 30s.","cancel_shutdown":"Cancelled."}[action]
        return "Unknown power action."
    except Exception as e: return f"Power action failed: {e}"


# ── File System ─────────────────────────────────────
def list_directory(path: str = ".") -> str:
    try:
        t = Path(path).expanduser().resolve()
        if not t.exists(): return f"Not found: {t}"
        items = sorted(t.iterdir())[:30]
        if not items: return f"Empty: {t}"
        def sz(f):
            s = f.stat().st_size
            return f" ({s}B)" if s<1024 else f" ({s//1024}KB)" if s<1048576 else f" ({s//1048576}MB)"
        return f"Contents of {t}:\n" + "\n".join(f"{'📁' if i.is_dir() else '📄'} {i.name}{sz(i) if i.is_file() else ''}" for i in items)
    except Exception as e: return f"Could not list: {e}"

def create_file(filename: str, content: str = "") -> str:
    try:
        p = _desktop() / filename
        p.write_text(content or f"Created by JARVIS at {datetime.datetime.now()}")
        return f"File created: {p}"
    except Exception as e: return f"Could not create file: {e}"

def run_shell_command(cmd: str) -> str:
    if any(b in cmd.lower() for b in ["format","del /","rmdir /s","rm -rf","drop table","truncate"]):
        return "Blocked for safety."
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        out = (r.stdout or r.stderr).strip()
        return out[:1000] if out else "Command executed (no output)."
    except subprocess.TimeoutExpired: return "Timed out after 15s."
    except Exception as e: return f"Command failed: {e}"

def git_status(path: str = ".") -> str:
    if not shutil.which("git"): return "Git not found in PATH."
    try:
        r = subprocess.run(["git","status","--short"], capture_output=True, text=True, cwd=path, timeout=10)
        if r.returncode != 0: return f"Git error: {r.stderr.strip()}"
        return f"Git Status:\n{r.stdout.strip()}" if r.stdout.strip() else "Working tree clean."
    except Exception as e: return f"Git failed: {e}"

def open_application(app_name: str, browser: str | None = None) -> str:
    import webbrowser
    n = app_name.lower().strip()
    WEB = {"youtube":"https://youtube.com","google":"https://google.com","facebook":"https://facebook.com",
           "twitter":"https://twitter.com","x":"https://twitter.com","instagram":"https://instagram.com",
           "gmail":"https://gmail.com","github":"https://github.com","linkedin":"https://linkedin.com",
           "reddit":"https://reddit.com","stackoverflow":"https://stackoverflow.com",
           "chatgpt":"https://chat.openai.com","whatsapp":"https://web.whatsapp.com",
           "spotify":"https://open.spotify.com","netflix":"https://netflix.com",
           "amazon":"https://amazon.in","flipkart":"https://flipkart.com"}
    EXE = {"notepad":"notepad.exe","calculator":"calc.exe","calc":"calc.exe","word":"winword.exe",
           "excel":"excel.exe","powerpoint":"powerpnt.exe","ppt":"powerpnt.exe","paint":"mspaint.exe",
           "explorer":"explorer.exe","file explorer":"explorer.exe","cmd":"cmd.exe",
           "command prompt":"cmd.exe","terminal":"wt.exe","powershell":"powershell.exe",
           "task manager":"taskmgr.exe","settings":"ms-settings:","control panel":"control.exe",
           "snipping tool":"snippingtool.exe","photos":"ms-photos:","store":"ms-windows-store:",
           "mail":"outlookmail:","calendar":"outlookcal:","maps":"bingmaps:","clock":"ms-clock:","camera":"microsoft.windows.camera:"}
    url = next((v for k,v in WEB.items() if k in n), None)
    if not url and any(x in n for x in [".com",".org",".net",".in","http"]):
        url = app_name if "http" in app_name else f"https://{app_name}"
    if url:
        try: webbrowser.open(url); return f"🌐 Opened {app_name} in browser."
        except Exception as e: return f"Could not open: {e}"
    for k, exe in EXE.items():
        if k in n:
            try: os.startfile(exe); return f"🖥️ Opened {app_name}."
            except Exception as e: return f"Could not open: {e}"
    try: subprocess.Popen(f'cmd /c start "" "{app_name}"', shell=True); return f"🖥️ Opened {app_name}."
    except Exception as e: return f"Could not open: {e}"


# ── Language / Clipboard / Units ────────────────────
def translate_text(text: str, target_lang: str = "Spanish") -> str:
    CODES = {"spanish":"es","french":"fr","german":"de","italian":"it","portuguese":"pt","russian":"ru",
             "japanese":"ja","chinese":"zh","arabic":"ar","hindi":"hi","korean":"ko","dutch":"nl",
             "turkish":"tr","swedish":"sv","polish":"pl","greek":"el","hebrew":"he","thai":"th",
             "vietnamese":"vi","urdu":"ur"}
    try:
        import requests
        code = CODES.get(target_lang.lower(), target_lang.lower()[:2])
        t = requests.get("https://api.mymemory.translated.net/get",
            params={"q":text,"langpair":f"en|{code}"}, timeout=6).json().get("responseData",{}).get("translatedText","")
        return f"🌍 **{text}** → **{t}** ({target_lang})" if t and t.lower()!=text.lower() else f"Could not translate '{text}'."
    except Exception as e: return f"Translation failed: {e}"

def define_word(word: str) -> str:
    try:
        import requests
        data = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word.strip().lower()}", timeout=6).json()
        if not isinstance(data, list): return f"No definition for '{word}'."
        parts = [f"**{m['partOfSpeech']}**: {m['definitions'][0]['definition']}" +
                 (f" *(e.g., \"{m['definitions'][0]['example']}\")* " if m['definitions'][0].get('example') else "")
                 for m in data[0].get("meanings",[])[:2] if m.get("definitions")]
        return f"📖 **{data[0].get('word',word)}** — " + " | ".join(parts) if parts else f"No definition for '{word}'."
    except Exception as e: return f"Definition failed: {e}"

def get_clipboard_content() -> str:
    if not WIN: return "Clipboard only supported on Windows."
    try:
        c = subprocess.run(["powershell","-command","Get-Clipboard"], capture_output=True, text=True, timeout=5).stdout.strip()
        return f"📋 {c[:200]}{'...' if len(c)>200 else ''}" if c else "Clipboard is empty."
    except Exception as e: return f"Clipboard read failed: {e}"

def set_clipboard_content(text: str) -> str:
    if not WIN: return "Clipboard only supported on Windows."
    try:
        subprocess.run(["powershell","-command",f"Set-Clipboard -Value '{text}'"], capture_output=True, text=True, timeout=5)
        return f"📋 Copied: {text[:100]}"
    except Exception as e: return f"Clipboard write failed: {e}"

def convert_units(value: float, from_unit: str, to_unit: str) -> str:
    C = {("celsius","fahrenheit"):lambda x:x*9/5+32, ("fahrenheit","celsius"):lambda x:(x-32)*5/9,
         ("celsius","kelvin"):lambda x:x+273.15, ("kelvin","celsius"):lambda x:x-273.15,
         ("fahrenheit","kelvin"):lambda x:(x-32)*5/9+273.15, ("kelvin","fahrenheit"):lambda x:(x-273.15)*9/5+32,
         ("km","miles"):lambda x:x*.621371, ("miles","km"):lambda x:x*1.60934,
         ("meters","feet"):lambda x:x*3.28084, ("feet","meters"):lambda x:x/3.28084,
         ("cm","inches"):lambda x:x*.393701, ("inches","cm"):lambda x:x*2.54,
         ("kg","pounds"):lambda x:x*2.20462, ("pounds","kg"):lambda x:x/2.20462,
         ("grams","ounces"):lambda x:x*.035274, ("ounces","grams"):lambda x:x/.035274,
         ("kmh","mph"):lambda x:x*.621371, ("mph","kmh"):lambda x:x*1.60934,
         ("liters","gallons"):lambda x:x*.264172, ("gallons","liters"):lambda x:x/.264172}
    fn = C.get((from_unit.lower(), to_unit.lower()))
    if not fn: return f"❓ Cannot convert {from_unit} → {to_unit}."
    r = round(fn(value), 4); r = int(r) if isinstance(r,float) and r==int(r) else r
    return f"🔄 {value} {from_unit} = **{r} {to_unit}**"

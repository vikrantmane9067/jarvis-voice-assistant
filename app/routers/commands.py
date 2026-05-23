"""JARVIS Commands Router v3.0 — Dispatch-table driven, O(1) lookup."""
from datetime import datetime
from uuid import uuid4

import webbrowser
import requests as http
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CommandLog, CommandSession
from app.schemas.command import CommandRequest, CommandResponse
from app.services.auth_service import get_current_user
from app.services.nlp_service import classify_command
from app.services.automation_service import (
    get_system_info, get_disk_usage, get_battery_status, get_ip_address,
    get_cpu_ram_live, get_current_datetime, take_screenshot, control_volume,
    lock_screen, power_action, list_directory, create_file, open_application,
    run_shell_command, git_status, translate_text, define_word,
    get_clipboard_content, set_clipboard_content, convert_units,
)

router = APIRouter()

# ── Response Formatters ─────────────────────────────
def _sysinfo():
    i = get_system_info()
    return i.get("error") or (f"💻 {i['os']} | CPU: {i['cpu_cores']}c @ {i['cpu_percent']}% | "
                              f"RAM: {i['ram_used_gb']}/{i['ram_total_gb']}GB | Up: {i['uptime']}")

def _disk():
    i = get_disk_usage()
    return i.get("error") or "💾 " + " | ".join(f"{d['drive']} {d['used_gb']}/{d['total_gb']}GB ({d['percent']}%)" for d in i["drives"])

def _battery():
    i = get_battery_status()
    return i.get("error") or f"🔋 {i['percent']}% | {'Plugged in' if i['plugged_in'] else 'On battery'} | {i['time_left']}"

def _weather(ad):
    try: return http.get(f"https://wttr.in/{ad.get('location','Delhi')}?format=3", timeout=5).text.strip()
    except: return "Could not fetch weather."

def _ts(): return datetime.utcnow().strftime("%H%M%S")

# ── Intent Dispatch Table ───────────────────────────
HANDLERS = {
    "weather":         lambda ad,t: f"🌤️ {_weather(ad)}",
    "open_app":        lambda ad,t: open_application(ad.get("app",""), ad.get("browser")),
    "play_media":      lambda ad,t: f"🎵 Playing {ad.get('media','')} on YouTube.",
    "web_search":      lambda ad,t: (webbrowser.open(f"https://google.com/search?q={ad.get('query',t)}"), f"🔍 Searching: {ad.get('query',t)}")[1],
    "news":            lambda ad,t: (webbrowser.open("https://news.google.com"), "📰 Opening latest news.")[1],
    "set_reminder":    lambda ad,t: f"⏰ Reminder set: {ad.get('task', t)}",
    "set_timer":       lambda ad,t: f"⏱️ Timer set for {ad.get('duration',5)} {ad.get('unit','minute')}(s).",
    "create_note":     lambda ad,t: f"📝 {create_file(f'note_{_ts()}.txt', ad.get('note',''))}",
    "todo_add":        lambda ad,t: f"✅ {create_file(f'todo_{_ts()}.txt', 'TODO: ' + ad.get('task',''))}",
    "shutdown":        lambda ad,t: f"🔌 {power_action('shutdown')}",
    "restart":         lambda ad,t: f"🔌 {power_action('restart')}",
    "cancel_shutdown": lambda ad,t: f"🔌 {power_action('cancel_shutdown')}",
    "sleep":           lambda ad,t: f"🔌 {power_action('sleep')}",
    "lock_screen":     lambda ad,t: f"🔒 {lock_screen()}",
    "screenshot":      lambda ad,t: f"📸 {take_screenshot()}",
    "volume_up":       lambda ad,t: f"🔊 {control_volume('up')}",
    "volume_down":     lambda ad,t: f"🔉 {control_volume('down')}",
    "mute":            lambda ad,t: f"🔇 {control_volume('mute')}",
    "system_info":     lambda ad,t: _sysinfo(),
    "disk_usage":      lambda ad,t: _disk(),
    "battery_status":  lambda ad,t: _battery(),
    "ip_address":      lambda ad,t: f"🌐 Local: {get_ip_address().get('local_ip','?')} | Public: {get_ip_address().get('public_ip','?')}",
    "time":            lambda ad,t: f"🕐 {get_current_datetime()['time']}",
    "date":            lambda ad,t: f"📅 {get_current_datetime()['date']}",
    "translate":       lambda ad,t: translate_text(ad.get("text","hello"), ad.get("target_lang","Spanish")),
    "define":          lambda ad,t: define_word(ad.get("word","")),
    "convert_units":   lambda ad,t: convert_units(float(ad.get("value",1)), ad.get("from_unit","km"), ad.get("to_unit","miles")),
    "list_files":      lambda ad,t: f"📁 {list_directory(ad.get('path','.'))}",
    "create_file":     lambda ad,t: f"📄 {create_file(ad.get('filename','jarvis_note.txt'))}",
    "git_status":      lambda ad,t: f"🛠️ {git_status()}",
    "pip_install":     lambda ad,t: ("📦 " + run_shell_command("pip install " + ad.get("package",""))) if ad.get("package") else "Specify a package.",
    "run_command":     lambda ad,t: ("💻 " + run_shell_command(ad.get("command",""))) if ad.get("command") else "Specify a command.",
    "clipboard_read":  lambda ad,t: get_clipboard_content(),
    "clipboard_write": lambda ad,t: set_clipboard_content(ad.get("text","")),
}

# ── Session Helper ──────────────────────────────────
def _session(db, user_id, token):
    if token:
        s = db.query(CommandSession).filter(CommandSession.session_token == token).first()
        if s: return s
    s = CommandSession(user_id=user_id, session_token=token or uuid4().hex)
    db.add(s); db.commit(); db.refresh(s); return s

# ── Routes ──────────────────────────────────────────
@router.post("/commands/process", response_model=CommandResponse)
def process_command(request: CommandRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    t0 = datetime.utcnow()
    session = _session(db, current_user.id, request.session_token)
    result  = classify_command(request.text)
    intent, ad = result["intent"], result.get("action_data", {})
    try:
        if h := HANDLERS.get(intent): result["response"] = h(ad, request.text)
    except Exception as e: result["response"] = f"Action failed: {e}"
    latency = int((datetime.utcnow() - t0).total_seconds() * 1000)
    db.add(CommandLog(session_id=session.id, raw_input=request.text, detected_intent=intent,
                      confidence_score=result["confidence"], response_text=result["response"],
                      status="success", latency_ms=latency))
    db.commit()
    return CommandResponse(response=result["response"], intent=intent, confidence=result["confidence"],
                           latency_ms=latency, action_data=ad, session_token=session.session_token)

@router.get("/commands/history")
def get_history(limit: int = Query(15, ge=1, le=100), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    sid = select(CommandSession.id).where(CommandSession.user_id == current_user.id)
    logs = db.query(CommandLog).filter(CommandLog.session_id.in_(sid)).order_by(CommandLog.created_at.desc()).limit(limit).all()
    return [{"input":l.raw_input,"intent":l.detected_intent,"confidence":l.confidence_score,
             "response":l.response_text,"status":l.status,"latency_ms":l.latency_ms,
             "created_at":l.created_at.isoformat() if l.created_at else ""} for l in logs]

@router.get("/commands/system-stats")
def system_stats(current_user=Depends(get_current_user)):
    s, b, dt = get_cpu_ram_live(), get_battery_status(), get_current_datetime()
    return {**s,"battery_percent":b.get("percent",-1),"battery_plugged":b.get("plugged_in",False),
            "time":dt["time"],"date":dt["date"],"day":dt["day"]}

@router.get("/commands/stats")
def command_stats(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    sid = select(CommandSession.id).where(CommandSession.user_id == current_user.id)
    q = db.query(CommandLog).filter(CommandLog.session_id.in_(sid))
    top = (q.with_entities(CommandLog.detected_intent, func.count(CommandLog.id).label("c"))
             .group_by(CommandLog.detected_intent).order_by(func.count(CommandLog.id).desc()).limit(20).all())
    return {"total_commands":q.count(),
            "avg_latency_ms":round(q.with_entities(func.avg(CommandLog.latency_ms)).scalar() or 0,1),
            "avg_confidence":round((q.with_entities(func.avg(CommandLog.confidence_score)).scalar() or 0)*100,1),
            "intent_breakdown":[{"intent":r[0],"count":r[1]} for r in top]}

@router.get("/commands/export")
def export_history(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    sid = select(CommandSession.id).where(CommandSession.user_id == current_user.id)
    logs = db.query(CommandLog).filter(CommandLog.session_id.in_(sid)).order_by(CommandLog.created_at.asc()).all()
    return {"user":current_user.username,"exported_at":datetime.utcnow().isoformat(),"total":len(logs),
            "commands":[{"input":l.raw_input,"intent":l.detected_intent,"confidence":l.confidence_score,
                         "response":l.response_text,"latency_ms":l.latency_ms,
                         "created_at":l.created_at.isoformat() if l.created_at else ""} for l in logs]}

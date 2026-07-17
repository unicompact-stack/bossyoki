"""HTTP дашборд — новый дизайн с нуля."""

import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse

DASHBOARD_HTML = '''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BossYoki — Трекер задач</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#f8f9fa;--card:#fff;--accent:#6366f1;--accent2:#8b5cf6;--green:#10b981;--red:#ef4444;--yellow:#f59e0b;--text:#1e293b;--muted:#94a3b8;--border:#e2e8f0}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);min-height:100vh}
.topbar{background:linear-gradient(135deg,var(--accent),var(--accent2));padding:20px 32px;color:#fff;display:flex;justify-content:space-between;align-items:center}
.topbar h1{font-size:22px;font-weight:700;letter-spacing:-.5px}
.topbar .live{display:flex;align-items:center;gap:8px;font-size:13px;opacity:.9}
.topbar .dot{width:8px;height:8px;border-radius:50%;background:#34d399;animation:blink 1.5s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
.wrap{max-width:1080px;margin:0 auto;padding:24px 20px}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:28px}
.card{background:var(--card);border-radius:14px;padding:20px;box-shadow:0 1px 3px rgba(0,0,0,.06);transition:transform .15s}
.card:hover{transform:translateY(-2px)}
.card .num{font-size:32px;font-weight:700;line-height:1}
.card .label{font-size:12px;color:var(--muted);margin-top:6px;text-transform:uppercase;letter-spacing:.5px}
.card.c1 .num{color:var(--accent)}
.card.c2 .num{color:var(--green)}
.card.c3 .num{color:var(--yellow)}
.card.c4 .num{color:var(--red)}
.section{background:var(--card);border-radius:14px;padding:24px;margin-bottom:20px;box-shadow:0 1px 3px rgba(0,0,0,.06)}
.section-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}
.section-head h2{font-size:16px;font-weight:600}
.badge{background:var(--accent);color:#fff;font-size:11px;font-weight:600;padding:2px 8px;border-radius:10px}
.task-row{display:flex;align-items:center;gap:12px;padding:12px 16px;border-radius:10px;margin-bottom:8px;background:var(--bg);transition:background .15s}
.task-row:hover{background:#eef2ff}
.task-row.done{opacity:.45}
.task-row.done .task-title{text-decoration:line-through}
.pri{width:10px;height:10px;border-radius:50%;flex-shrink:0}
.pri.high{background:var(--red)}
.pri.med{background:var(--yellow)}
.pri.low{background:var(--green)}
.task-title{flex:1;font-size:14px;font-weight:500}
.task-meta{font-size:12px;color:var(--muted);white-space:nowrap}
.task-id{font-size:11px;color:var(--muted);font-weight:600;min-width:28px}
.btn{border:none;border-radius:8px;padding:6px 14px;font-size:12px;font-weight:600;cursor:pointer;transition:all .15s}
.btn-done{background:var(--green);color:#fff}
.btn-done:hover{background:#059669}
.btn-check{background:transparent;color:var(--green);font-size:16px}
.chat-list{max-height:320px;overflow-y:auto}
.chat-msg{padding:10px 14px;border-radius:10px;margin-bottom:6px;font-size:13px;line-height:1.5}
.chat-user{background:#eef2ff;border-left:3px solid var(--accent)}
.chat-bot{background:#f0fdf4;border-left:3px solid var(--green)}
.chat-who{font-size:11px;font-weight:600;color:var(--muted);margin-bottom:2px}
.empty{text-align:center;padding:32px;color:var(--muted);font-size:14px}
.footer{text-align:center;padding:16px;font-size:11px;color:var(--muted)}
</style>
</head>
<body>
<div class="topbar">
  <h1>BossYoki</h1>
  <div class="live"><div class="dot"></div><span id="status">Подключение...</span></div>
</div>
<div class="wrap">
  <div class="grid" id="stats"></div>
  <div class="section">
    <div class="section-head"><h2>Мои задачи</h2><span class="badge" id="task-count">0</span></div>
    <div id="tasks"><div class="empty">Загрузка...</div></div>
  </div>
  <div class="section">
    <div class="section-head"><h2>Последние сообщения</h2></div>
    <div class="chat-list" id="messages"><div class="empty">Загрузка...</div></div>
  </div>
</div>
<div class="footer">BossYoki &middot; Трекер задач &middot; SQLite + GitHub</div>
<script>
const P={high:'pri high',medium:'pri med',low:'pri low'};
const I={high:'🔴',medium:'🟡',low:'🟢'};
function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
function load(){
  fetch('/api/data').then(r=>r.json()).then(d=>{
    document.getElementById('status').textContent='Актуально: '+new Date().toLocaleTimeString('ru');
    document.getElementById('stats').innerHTML=
      '<div class="card c1"><div class="num">'+d.stats.active+'</div><div class="label">Активных</div></div>'+
      '<div class="card c2"><div class="num">'+d.stats.done+'</div><div class="label">Выполнено</div></div>'+
      '<div class="card c3"><div class="num">'+d.stats.today+'</div><div class="label">На сегодня</div></div>'+
      '<div class="card c4"><div class="num">'+d.stats.overdue+'</div><div class="label">Просрочено</div></div>';
    document.getElementById('task-count').textContent=d.tasks.length;
    if(!d.tasks.length){document.getElementById('tasks').innerHTML='<div class="empty">Нет задач. Добавь через VK-бота.</div>';return}
    let h='';d.tasks.forEach(t=>{
      let cls=t.status=='done'?'done':'';
      let btn=t.status=='active'?'<button class="btn btn-done" onclick="done('+t.id+')">✓ Готово</button>':'<span style="color:var(--green)">✓</span>';
      let meta=(t.deadline||'')+(t.time?' в '+t.time:'');
      h+='<div class="task-row '+cls+'"><span class="task-id">#'+t.id+'</span><span class="'+P[t.priority]+'"></span><span class="task-title">'+esc(t.title)+'</span><span class="task-meta">'+meta+'</span>'+btn+'</div>';
    });
    document.getElementById('tasks').innerHTML=h;
    if(!d.messages.length){document.getElementById('messages').innerHTML='<div class="empty">Нет сообщений</div>';return}
    let m='';d.messages.forEach(x=>{
      let cls=x.role=='user'?'chat-user':'chat-bot';
      let who=x.role=='user'?'Вы':'Босс Йоки';
      m+='<div class="chat-msg '+cls+'"><div class="chat-who">'+who+' · '+x.date+' '+x.time+'</div>'+esc(x.message)+'</div>';
    });
    document.getElementById('messages').innerHTML=m;
  }).catch(()=>{
    document.getElementById('status').textContent='Бот оффлайн';
    document.getElementById('tasks').innerHTML='<div class="empty">Бот не отвечает</div>';
  });
}
function done(id){
  fetch('/api/complete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task_id:id})})
  .then(r=>r.json()).then(()=>load());
}
load();setInterval(load,15000);
</script>
</body>
</html>'''


class DashboardHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, db=None, user_id=None, **kwargs):
        self._db = db
        self._user_id = user_id
        super().__init__(*args, **kwargs)

    def do_GET(self):
        path = urlparse(self.path).path
        try:
            if path == '/api/data':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                data = self._db.get_api_data(self._user_id)
                self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
            else:
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(DASHBOARD_HTML.encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length)) if length else {}

            if path == '/api/complete':
                task_id = body.get('task_id')
                if task_id:
                    success = self._db.complete_task(self._user_id, int(task_id))
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({'ok': success}).encode())
                else:
                    self.send_response(400)
                    self.end_headers()
            else:
                self.send_response(404)
                self.end_headers()
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        pass

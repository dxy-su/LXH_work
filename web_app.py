import json
import os
import random
from datetime import datetime
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

DEFAULT_CONFIG = {
    "start_time": "09:00", "end_time": "18:00", "daily_salary": 300.0,
    "workdays": [0, 1, 2, 3, 4], "api_base_url": "https://api.deepseek.com",
    "api_model": "deepseek-chat",
}


def load_config():
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)
        config = {**DEFAULT_CONFIG, **data}
        config["daily_salary"] = float(config["daily_salary"])
        config["workdays"] = [int(x) for x in config["workdays"]]
        return config
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return DEFAULT_CONFIG.copy()


@app.get("/")
def index():
    images = [
        name for name in os.listdir(BASE_DIR)
        if name.lower().endswith((".jpg", ".jpeg", ".png", ".gif"))
    ]
    return render_template("index.html", images=images)


@app.get("/api/config")
def config():
    return jsonify(load_config())


@app.post("/api/config")
def save_config():
    current = load_config()
    data = request.get_json(silent=True) or {}
    try:
        start, end = str(data.get("start_time", current["start_time"])), str(data.get("end_time", current["end_time"]))
        salary = float(data.get("daily_salary", current["daily_salary"]))
        workdays = [int(x) for x in data.get("workdays", current["workdays"])]
        datetime.strptime(start, "%H:%M"); datetime.strptime(end, "%H:%M")
        if salary < 0 or end <= start or not all(0 <= x <= 6 for x in workdays):
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"error": "设置无效"}), 400
    current.update({"start_time": start, "end_time": end, "daily_salary": salary, "workdays": workdays})
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(current, f, ensure_ascii=False, indent=2)
    return jsonify(current)


@app.get("/media/<path:name>")
def media(name):
    from flask import send_from_directory
    return send_from_directory(BASE_DIR, name)

@app.get("/api/encouragement")
def encouragement():
    messages = (
        "今天也辛苦了，稳稳走好自己的路。",
        "别怕，我在，慢慢走也能抵达前方。",
        "累了就歇一会儿，明天依然有光。",
        "先好好吃饭，剩下的路我们一起走。",
        "你已经做得很好，今天也值得被肯定。",
        "风雨会过去，你守住的希望不会熄灭。",
        "下班去散散心，今天的你辛苦了。",
        "没关系，我陪着你，一切都会好起来。",
    )
    current = request.args.get("current", "")
    choices = tuple(message for message in messages if message != current) or messages
    return jsonify({"text": random.choice(choices)})


@app.get("/sw.js")
def service_worker():
    from flask import Response
    script = """const CACHE='work-timer-v3';
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(['/','/static/style.css','/static/app.js','/static/manifest.json']))));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k))))));
self.addEventListener('fetch',e=>{
  if(e.request.url.includes('/api/')) return;
  e.respondWith(fetch(e.request).then(r=>{const copy=r.clone();caches.open(CACHE).then(c=>c.put(e.request,copy));return r}).catch(()=>caches.match(e.request)));
});
"""
    return Response(script, mimetype="application/javascript")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)

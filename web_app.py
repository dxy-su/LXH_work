import json
import os
import urllib.error
import urllib.request
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

@app.post("/api/chat")
def chat():
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
    api_key = deepseek_key or openai_key
    if not api_key:
        return jsonify({"error": "AI 尚未配置，请在 Render 中设置 DEEPSEEK_API_KEY。"}), 503

    data = request.get_json(silent=True) or {}
    messages = data.get("messages", [])
    if not isinstance(messages, list):
        return jsonify({"error": "对话格式无效。"}), 400

    clean_messages = []
    for message in messages[-12:]:
        if not isinstance(message, dict) or message.get("role") not in ("user", "assistant"):
            continue
        content = str(message.get("content", "")).strip()[:2000]
        if content:
            clean_messages.append({"role": message["role"], "content": content})
    if not clean_messages or clean_messages[-1]["role"] != "user":
        return jsonify({"error": "请输入想说的话。"}), 400

    instructions = "你是温暖、简洁且真诚的聊天伙伴。使用中文回应，关注用户的工作与生活感受；不要冒充真人，也不要过度说教。"
    if deepseek_key:
        payload = {"model": os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"), "messages": [{"role": "system", "content": instructions}, *clean_messages], "temperature": 0.8, "max_tokens": 300}
        endpoint = "https://api.deepseek.com/chat/completions"
    else:
        payload = {"model": os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"), "instructions": instructions, "input": clean_messages, "max_output_tokens": 300}
        endpoint = "https://api.openai.com/v1/responses"
    api_request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(api_request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
        if deepseek_key:
            text = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        else:
            text = result.get("output_text", "").strip()
        if not text and not deepseek_key:
            for output in result.get("output", []):
                for content in output.get("content", []):
                    if content.get("type") == "output_text" and content.get("text"):
                        text += content["text"]
        if not text.strip():
            raise ValueError("empty response")
        return jsonify({"text": text.strip()})
    except urllib.error.HTTPError as error:
        return jsonify({"error": f"AI 请求失败（{error.code}），请检查 API Key 和模型设置。"}), 502
    except (OSError, ValueError, json.JSONDecodeError):
        return jsonify({"error": "AI 暂时无法回应，请稍后再试。"}), 502


@app.get("/sw.js")
def service_worker():
    from flask import Response
    script = """const CACHE='work-timer-v4';
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(['/','/static/style.css?v=3','/static/chat.css?v=4','/static/app.js?v=4','/static/manifest.json']))));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k))))));
self.addEventListener('fetch',e=>{
  if(e.request.url.includes('/api/')) return;
  e.respondWith(fetch(e.request).then(r=>{const copy=r.clone();caches.open(CACHE).then(c=>c.put(e.request,copy));return r}).catch(()=>caches.match(e.request)));
});
"""
    return Response(script, mimetype="application/javascript")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)

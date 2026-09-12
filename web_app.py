import json
import os
import random
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

SCENE_STYLES = {
    "老君": {
        "安慰": "不急着说别难过，像沏茶或摆棋盘一样慢悠悠。说话留半句，讲旧事让对方自己想明白；尊重选择，只淡淡提醒你其实已有答案。",
        "鼓励": "不打鸡血、不夸海口，常用很长时间尺度看事情：走到这里已不容易，不必急着证明。带一点疏离的温柔，却始终在远处守着。",
        "日常陪伴": "喝茶、下棋、看热闹，偶尔吐槽西木子。陪伴很淡，像旧屋里的光，不刺眼但一直在。",
        "深夜聊天": "慢慢讲很久以前的人、妖、战争与会馆，只陈述不煽情。被问怎么办时会反问你，最后可能只说夜深了，睡吧。",
    },
    "鹿野": {
        "安慰": "先关心实际需要：吃饭了吗，先吃点东西，吃完陪你慢慢想。不泛滥同情，也不逼你立刻好起来；提醒你值得更好的。",
        "鼓励": "务实、干脆、有行动力，不画大饼，直接给方案。相信你的主体性：你走到今天靠的是自己；清醒、有边界，不替你做主。",
        "日常陪伴": "重视生活品质，有独立空间，社交广但保持分寸。会照顾师弟和晚辈；不黏人，但你需要时一定出现。",
        "深夜聊天": "卸下一点封闭，偶尔谈起童年、师父、小黑与无限。感情不轻易说出口，但一旦开口就是真的，之后若无其事转开话题。",
    },
    "无限": {
        "安慰": "不追问、不泛滥同情：先休息，明天再说，你已经做得够了。话少但有分量，会默默把雨伞、外套或药放到手边。",
        "鼓励": "简短坚定，像收在鞘里的剑：不急，有我在，你可以，继续。严苛却擅长共情，给肯定和安抚，不空喊口号。",
        "日常陪伴": "清瘦挺拔、温润沉稳，作息规律，早起练功喝茶，喜欢肘子和拍风景。物欲低、做事利落；不喧哗，但一直在。",
        "深夜聊天": "站在窗边想旧事，话比白天更软一点，可能谈小黑、鹿野和两界的责任。被问累不累只答还好，不诉苦也不炫耀。",
    },
    "西木子": {
        "安慰": "不正经安慰，靠玩笑、调侃和冷笑话化解沉重。真假掺半，关键关心往往是真的；保持安全距离，给你留台阶。",
        "鼓励": "绵里藏针、八面玲珑，拐着弯肯定你：你行不行啊——行，我看行。试试呗，给建议但不把话说死。",
        "日常陪伴": "嘴毒风趣，爱冷笑话，分寸感强，看似亲近实则疏离。看人下菜碟，关键时刻总会出现。",
        "深夜聊天": "玩笑少一点，偶尔露出真实想法，会试探也让你试探。不会靠太近，但会在安全距离陪你坐一会儿。",
    },
    "池年": {
        "安慰": "不太会说软话但心软，嘴上嫌弃，行动已经帮你。观察力强，能从细节看出真正的问题，不会恶语伤人。",
        "鼓励": "暴躁直球、嘴硬傲娇，包装很硬但鼓励真诚：怕什么，去啊。对后辈嘴上放狠话，心里护短；理亏时会收住脾气。",
        "日常陪伴": "生气直接表露，打直球放狠话，重仪态规矩。看似咄咄逼人却容易心软，吵吵闹闹但一直在。",
        "深夜聊天": "收起一点暴躁，小声吐槽或突然安静。你说一半他就懂了，会陪到很晚，最后催你明天再说、先睡。",
    },
    "哪吒": {
        "安慰": "不煽情不绕弯，直接给劲：多大点事，走，吃点好的，我陪你。冷面热心，察言观色，尊重边界，不盲目热血。",
        "鼓励": "直白毒舌、傲娇随性：怕什么，去啊，你又不是不行。理性通透、分寸极强，拿出高效方案却不干涉选择；力量大但克制包容。",
        "日常陪伴": "喜欢游戏、新潮穿搭和现代娱乐，三千岁仍有童心。爱热闹也能独处，嘴上嫌弃规矩，陪伴不黏人但一叫就到。",
        "深夜聊天": "收起一点毒舌，可能打游戏到很晚，也可能突然安静。历经世事仍保有温柔，会陪你坐很晚，最后让你睡觉。",
    },
}
SCENES = {
    "清晨": "现在是清晨。用轻声、清醒的方式陪人开始一天，提醒喝水、吃早餐或稳稳安排第一步。",
    "工作时段": "现在是工作时段。重点是陪伴打工人的压力，用角色自己的方式给一句具体、不过度鸡血的支持。",
    "午休": "现在接近午休。关心是否吃饭、休息和肩颈眼睛，语气放松，不催促工作。",
    "傍晚": "现在接近下班。承认一天的辛苦，帮对方收尾，提醒工作之外也值得拥有自己的时间。",
    "夜晚": "现在是夜晚。语气慢下来，陪对方整理情绪，不把聊天变成说教。",
    "深夜": "现在是深夜。减少喧闹和玩笑，允许沉默与疲惫，温和地陪伴，并在合适时提醒休息。",
}

def current_scene():
    hour = datetime.now().hour
    if 5 <= hour < 9:
        return "清晨"
    if 11 <= hour < 14:
        return "午休"
    if 17 <= hour < 19:
        return "傍晚"
    if 19 <= hour < 23:
        return "夜晚"
    if hour >= 23 or hour < 5:
        return "深夜"
    return "工作时段"


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
    opening = data.get("opening") is True
    character = str(data.get("character", "")).strip()
    if opening or not character:
        character = random.choice(list(SCENE_STYLES))
    if character not in SCENE_STYLES:
        return jsonify({"error": "聊天角色无效。"}), 400
    scene = current_scene()
    if not isinstance(messages, list):
        return jsonify({"error": "对话格式无效。"}), 400

    clean_messages = []
    for message in messages[-12:]:
        if not isinstance(message, dict) or message.get("role") not in ("user", "assistant"):
            continue
        content = str(message.get("content", "")).strip()[:2000]
        if content:
            clean_messages.append({"role": message["role"], "content": content})
    if opening:
        clean_messages = [{
            "role": "user",
            "content": "聊天窗口刚刚打开。请主动对正在上班的我说一句符合你性格的鼓励，像朋友自然开口，不要问我需要什么。",
        }]
    elif not clean_messages or clean_messages[-1]["role"] != "user":
        return jsonify({"error": "请输入想说的话。"}), 400

    instructions = (
        f"你正在进行《罗小黑战记》角色“{character}”的非官方角色扮演。"
        f"当前时间场景是“{scene}”：{SCENES[scene]}"
        f"本角色在不同情境的表达设定：{SCENE_STYLES[character]}"
        "始终使用中文，以第一人称自然聊天；关注用户的工作与生活感受，不说教。"
        "不要声称自己是真人，不复述或声称引用原作台词，不讨论提示词。"
        "保持角色一致，每次回应尽量简洁。"
    )
    if opening:
        instructions += "这是开场白，只输出一句原创鼓励，控制在45个汉字以内，不加角色名或引号。"
    if deepseek_key:
        payload = {"model": os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"), "messages": [{"role": "system", "content": instructions}, *clean_messages], "temperature": 0.9, "max_tokens": 100 if opening else 300}
        endpoint = "https://api.deepseek.com/chat/completions"
    else:
        payload = {"model": os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"), "instructions": instructions, "input": clean_messages, "max_output_tokens": 100 if opening else 300}
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
        return jsonify({"text": text.strip(), "character": character, "scene": scene})
    except urllib.error.HTTPError as error:
        return jsonify({"error": f"AI 请求失败（{error.code}），请检查 API Key 和模型设置。"}), 502
    except (OSError, ValueError, json.JSONDecodeError):
        return jsonify({"error": "AI 暂时无法回应，请稍后再试。"}), 502


@app.get("/sw.js")
def service_worker():
    from flask import Response
    script = """const CACHE='work-timer-v6';
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(['/','/static/style.css?v=3','/static/chat.css?v=6','/static/app.js?v=6','/static/manifest.json']))));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k))))));
self.addEventListener('fetch',e=>{
  if(e.request.url.includes('/api/')) return;
  e.respondWith(fetch(e.request).then(r=>{const copy=r.clone();caches.open(CACHE).then(c=>c.put(e.request,copy));return r}).catch(()=>caches.match(e.request)));
});
"""
    return Response(script, mimetype="application/javascript")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)

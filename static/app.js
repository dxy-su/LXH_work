const $=id=>document.getElementById(id),days=['一','二','三','四','五','六','日'];let cfg,installEvent,timer;
if('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js');
async function load(){cfg=await fetch('/api/config').then(r=>r.json());$('start').value=cfg.start_time;$('end').value=cfg.end_time;$('salary').value=cfg.daily_salary;$('days').innerHTML=days.map((d,i)=>`<label><input type="checkbox" value="${i}" ${cfg.workdays.includes(i)?'checked':''}>周${d}</label>`).join('');tick();}
function tick(){if(!cfg)return;let n=new Date(),d=n.getDay()===0?6:n.getDay()-1,[sh,sm]=cfg.start_time.split(':').map(Number),[eh,em]=cfg.end_time.split(':').map(Number),now=n.getHours()*60+n.getMinutes()+n.getSeconds()/60,s=sh*60+sm,e=eh*60+em;$('weekday').textContent=`周${days[d]} · ${cfg.workdays.includes(d)?'工作日':'休息日'}`;if(!cfg.workdays.includes(d)) setDisplay('--:--:--','今天休息 · 好好放松',0);else if(now<s)setDisplay(format((s-now)*60),'还未上班 · 先喝杯水吧',0);else if(now<e)setDisplay(format((e-now)*60),'工作进行中 · 距离下班',Math.min(1,(now-s)/(e-s))*cfg.daily_salary);else setDisplay('已下班！','今日工作完成 · 辛苦了',cfg.daily_salary);clearTimeout(timer);timer=setTimeout(tick,1000)}
function format(sec){sec=Math.max(0,Math.floor(sec));return [Math.floor(sec/3600),Math.floor(sec/60)%60,sec%60].map(x=>String(x).padStart(2,'0')).join(':')}
function setDisplay(count,status,money){$('countdown').textContent=count;$('status').textContent=status;$('income').textContent='¥'+money.toFixed(2)}
function rotate(){if(window.IMAGES.length)$('hero').src='/media/'+encodeURIComponent(window.IMAGES[Math.floor(Math.random()*window.IMAGES.length)]);} 
const ENCOURAGEMENT_PROMPTS={common:['点击聆听来自妖灵会馆的一句问候','点一下，听听会馆里谁在蛐蛐你','会馆八卦，点击收听','灵质空间有话，点开听听','今天也辛苦了，收一条会馆来信','有人在会馆提到你，点击听听看','妖灵会馆广播中，点击接收','点开这封来自会馆的口头信件','今日份的会馆絮语，请查收','别急着忙，先听听会馆有什么新消息'],day:['工作进行中，点击听一句会馆打气','摸鱼一分钟，听听谁来给你撑腰','会馆午间频道，点击收听一声问候','打工人的临时补给，点开就有'],night:['夜深了，点击听执行者说一句晚安','下班后的会馆还亮着灯，点击听听','夜间灵质频道开启，点一下再休息','今晚谁在会馆替你留灯，点击收听']};
let lastEncouragement='';
function refreshEncouragement(){const hour=new Date().getHours(),pool=(hour>=19||hour<5)?ENCOURAGEMENT_PROMPTS.night:(hour>=9&&hour<19)?ENCOURAGEMENT_PROMPTS.day:ENCOURAGEMENT_PROMPTS.common,choices=pool.filter(text=>text!==lastEncouragement),text=choices[Math.floor(Math.random()*choices.length)]||pool[0];lastEncouragement=text;$('encouragement').textContent=text;$('encouragement').title=text}
$('settings').onclick=()=>{$('dialog').showModal()};$('cancel').onclick=()=>$('dialog').close();$('save').onclick=async()=>{const payload={start_time:$('start').value,end_time:$('end').value,daily_salary:$('salary').value,workdays:[...document.querySelectorAll('#days input:checked')].map(x=>+x.value)};const res=await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});if(!res.ok){alert('设置无效，请检查时间和日薪');return}cfg=await res.json();$('dialog').close();tick()};
// Keep the full transcript in the UI; the server selects the latest context for the AI.
let chatHistory=[],currentCharacter='',openingRequest=0;
function addMessage(role,text,error=false){const item=document.createElement('div');item.className=`message ${role}${error?' error':''}`;item.textContent=text;$('chat-messages').appendChild(item);$('chat-messages').scrollTop=$('chat-messages').scrollHeight;return item}
async function startCharacterChat(){
  currentCharacter='';
  $('chat-title').textContent='妖灵会馆来信';
  chatHistory=[];
  $('chat-messages').replaceChildren();
  $('chat-input').disabled=true;$('chat-send').disabled=true;
  const requestId=++openingRequest,waiting=addMessage('assistant','正在接收来自妖灵会馆的问候…');
  try{
    const response=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({character:currentCharacter,messages:[],opening:true}),cache:'no-store'});
    const data=await response.json();
    if(requestId!==openingRequest)return;
    waiting.remove();
    if(!response.ok)throw new Error(data.error||'AI 暂时无法回应。');
    currentCharacter=data.character||'妖灵会馆';$('chat-title').textContent=`${currentCharacter}的问候`;
    addMessage('assistant',data.text);chatHistory.push({role:'assistant',content:data.text});
  }catch(error){if(requestId===openingRequest){waiting.remove();addMessage('assistant',error.message,true)}}
  finally{if(requestId===openingRequest){$('chat-input').disabled=false;$('chat-send').disabled=false;$('chat-input').focus()}}
}
$('encouragement').onclick=()=>{refreshEncouragement();if(!$('chat-dialog').open)$('chat-dialog').showModal();startCharacterChat()};
$('chat-close').onclick=()=>$('chat-dialog').close();
$('chat-form').onsubmit=async event=>{event.preventDefault();const input=$('chat-input'),text=input.value.trim();if(!text)return;addMessage('user',text);chatHistory.push({role:'user',content:text});input.value='';input.disabled=true;$('chat-send').disabled=true;const waiting=addMessage('assistant',`${currentCharacter}正在回复…`);try{const response=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({character:currentCharacter,messages:chatHistory}),cache:'no-store'});const data=await response.json();waiting.remove();if(!response.ok)throw new Error(data.error||'AI 暂时无法回应。');addMessage('assistant',data.text);chatHistory.push({role:'assistant',content:data.text})}catch(error){waiting.remove();addMessage('assistant',error.message,true)}finally{input.disabled=false;$('chat-send').disabled=false;input.focus()}};
window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();installEvent=e;$('install').hidden=false});$('install').onclick=()=>installEvent?.prompt();refreshEncouragement();rotate();setInterval(rotate,3600000);load();

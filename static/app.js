const $=id=>document.getElementById(id),days=['一','二','三','四','五','六','日'];let cfg,installEvent,timer;
if('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js');
async function load(){cfg=await fetch('/api/config').then(r=>r.json());$('start').value=cfg.start_time;$('end').value=cfg.end_time;$('salary').value=cfg.daily_salary;$('days').innerHTML=days.map((d,i)=>`<label><input type="checkbox" value="${i}" ${cfg.workdays.includes(i)?'checked':''}>周${d}</label>`).join('');tick();}
function tick(){if(!cfg)return;let n=new Date(),d=n.getDay()===0?6:n.getDay()-1,[sh,sm]=cfg.start_time.split(':').map(Number),[eh,em]=cfg.end_time.split(':').map(Number),now=n.getHours()*60+n.getMinutes()+n.getSeconds()/60,s=sh*60+sm,e=eh*60+em;$('weekday').textContent=`周${days[d]} · ${cfg.workdays.includes(d)?'工作日':'休息日'}`;if(!cfg.workdays.includes(d)) setDisplay('--:--:--','今天休息 · 好好放松',0);else if(now<s)setDisplay(format((s-now)*60),'还未上班 · 先喝杯水吧',0);else if(now<e)setDisplay(format((e-now)*60),'工作进行中 · 距离下班',Math.min(1,(now-s)/(e-s))*cfg.daily_salary);else setDisplay('已下班！','今日工作完成 · 辛苦了',cfg.daily_salary);clearTimeout(timer);timer=setTimeout(tick,1000)}
function format(sec){sec=Math.max(0,Math.floor(sec));return [Math.floor(sec/3600),Math.floor(sec/60)%60,sec%60].map(x=>String(x).padStart(2,'0')).join(':')}
function setDisplay(count,status,money){$('countdown').textContent=count;$('status').textContent=status;$('income').textContent='¥'+money.toFixed(2)}
function rotate(){if(window.IMAGES.length)$('hero').src='/media/'+encodeURIComponent(window.IMAGES[Math.floor(Math.random()*window.IMAGES.length)]);} 
$('settings').onclick=()=>{$('dialog').showModal()};$('cancel').onclick=()=>$('dialog').close();$('save').onclick=async()=>{const payload={start_time:$('start').value,end_time:$('end').value,daily_salary:$('salary').value,workdays:[...document.querySelectorAll('#days input:checked')].map(x=>+x.value)};const res=await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});if(!res.ok){alert('设置无效，请检查时间和日薪');return}cfg=await res.json();$('dialog').close();tick()};
// Keep the full transcript in the UI; the server selects the latest context for the AI.
let chatHistory=[],currentCharacter='小黑',openingRequest=0;
function addMessage(role,text,error=false){const item=document.createElement('div');item.className=`message ${role}${error?' error':''}`;item.textContent=text;$('chat-messages').appendChild(item);$('chat-messages').scrollTop=$('chat-messages').scrollHeight;return item}
async function startCharacterChat(){
  currentCharacter=$('character').value;
  $('chat-title').textContent=`和${currentCharacter}聊聊`;
  chatHistory=[];
  $('chat-messages').replaceChildren();
  $('chat-input').disabled=true;$('chat-send').disabled=true;
  const requestId=++openingRequest,waiting=addMessage('assistant',`${currentCharacter}正在和你打招呼…`);
  try{
    const response=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({character:currentCharacter,messages:[],opening:true}),cache:'no-store'});
    const data=await response.json();
    if(requestId!==openingRequest)return;
    waiting.remove();
    if(!response.ok)throw new Error(data.error||'AI 暂时无法回应。');
    addMessage('assistant',data.text);chatHistory.push({role:'assistant',content:data.text});
  }catch(error){if(requestId===openingRequest){waiting.remove();addMessage('assistant',error.message,true)}}
  finally{if(requestId===openingRequest){$('chat-input').disabled=false;$('chat-send').disabled=false;$('chat-input').focus()}}
}
$('encouragement').onclick=()=>{if(!$('chat-dialog').open)$('chat-dialog').showModal();startCharacterChat()};
$('character').onchange=startCharacterChat;
$('chat-close').onclick=()=>$('chat-dialog').close();
$('chat-form').onsubmit=async event=>{event.preventDefault();const input=$('chat-input'),text=input.value.trim();if(!text)return;addMessage('user',text);chatHistory.push({role:'user',content:text});input.value='';input.disabled=true;$('chat-send').disabled=true;const waiting=addMessage('assistant',`${currentCharacter}正在回复…`);try{const response=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({character:currentCharacter,messages:chatHistory}),cache:'no-store'});const data=await response.json();waiting.remove();if(!response.ok)throw new Error(data.error||'AI 暂时无法回应。');addMessage('assistant',data.text);chatHistory.push({role:'assistant',content:data.text})}catch(error){waiting.remove();addMessage('assistant',error.message,true)}finally{input.disabled=false;$('chat-send').disabled=false;input.focus()}};
window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();installEvent=e;$('install').hidden=false});$('install').onclick=()=>installEvent?.prompt();rotate();setInterval(rotate,3600000);load();

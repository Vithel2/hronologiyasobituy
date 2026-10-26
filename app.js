'use strict';
const $=s=>document.querySelector(s), canvas=$('#screen'),ctx=canvas.getContext('2d');
const initial={version:1,title:'ХРОНОЛОГИЯ СОБЫТИЙ',start:'12:00:00',duration:60,accent:'#dedede',note:'Хронология событий\nУчебный пример',image:null,events:[{at:0,text:'Начало наблюдения. Открыта запись событий.',quote:'Запись началась.'},{at:8,text:'Участник А входит в центральный зал.',quote:'— Встречаемся у центрального входа.'},{at:19,text:'Получено первое сообщение. Уточняется место встречи.',quote:'— Я на месте. Вижу указатель.'},{at:32,text:'Участник Б проходит через западный коридор.',quote:'— Подхожу со стороны коридора.'},{at:45,text:'Участники встречаются в центральном зале.',quote:'— Встреча состоялась.'},{at:56,text:'Наблюдение завершено. Все события зафиксированы.',quote:'Конец записи.'}]};
let p=structuredClone(initial),t=0,playing=false,last=0,recording=false,imageAsset=null,videoAsset=null,videoURL=null,recorder=null;
try{const saved=localStorage.getItem('chronicle-project');if(saved)p=validate(JSON.parse(saved));}catch{}
if(p.accent.toLowerCase()==='#c9ed94')p.accent=initial.accent;
function validate(o){if(!o||!Array.isArray(o.events)||o.events.length>200)throw Error('Неверный формат проекта');return {version:1,title:String(o.title||'ХРОНОЛОГИЯ').slice(0,70),start:/^\d{2}:\d{2}:\d{2}$/.test(o.start)?o.start:'12:00:00',duration:Math.max(5,Math.min(3600,Number(o.duration)||60)),accent:/^#[0-9a-f]{6}$/i.test(o.accent)?o.accent:'#dedede',note:String(o.note||'').slice(0,350),approximate:!!o.approximate,zeroAt:Math.max(0,Math.min(3600,Number(o.zeroAt)||0)),image:typeof o.image==='string'&&o.image.startsWith('data:image/')?o.image:null,events:o.events.map(e=>({at:Math.max(0,Math.min(3600,Number(e.at)||0)),text:String(e.text||'').slice(0,350),quote:String(e.quote||'').slice(0,250),approx:!!e.approx,quoteDuration:Math.max(0,Math.min(60,Number(e.quoteDuration)||0))}))};}
function persist(){try{localStorage.setItem('chronicle-project',JSON.stringify(p));$('#status').textContent='Проект сохранён в этом браузере';}catch{$('#status').textContent='Скачайте проект для сохранения';}}
function sorted(){return p.events.toSorted((a,b)=>a.at-b.at)}
function clock(sec,full=false){sec=Math.floor(sec);const h=Math.floor(sec/3600)%24,m=Math.floor(sec/60)%60,s=sec%60;return(full?String(h).padStart(2,'0')+':':'')+String(m).padStart(2,'0')+':'+String(s).padStart(2,'0')}
function absolute(at){const [h,m,s]=p.start.split(':').map(Number);return clock(h*3600+m*60+s+at,true)}
function text(s,x,y,size=24,color='#e6e6e6',font='Arial',weight='normal'){ctx.fillStyle=color;ctx.font=`${weight} ${size}px ${font}`;ctx.fillText(s,x,y)}
function lines(s,x,y,width,size=24,color='#c6c6c6',max=8){ctx.font=`${size}px Arial`;let count=0;for(const para of s.split('\n')){let line='';for(const word of para.split(' ')){if(ctx.measureText(line+word).width>width&&line){text(line,x,y+count*size*1.35,size,color);count++;line='';if(count>=max)return count;}line+=word+' ';}text(line,x,y+count*size*1.35,size,color);count++;if(count>=max)break;}return count;}
function line(x,y,x2,y2,color='#3f3f3f',w=2){ctx.strokeStyle=color;ctx.lineWidth=w;ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x2,y2);ctx.stroke()}
function box(x,y,w,h,color){ctx.fillStyle=color;ctx.fillRect(x,y,w,h)}
function dot(x,y,label){ctx.fillStyle=p.accent;ctx.beginPath();ctx.arc(x,y,10,0,Math.PI*2);ctx.fill();ctx.strokeStyle=p.accent;ctx.lineWidth=2;ctx.beginPath();ctx.arc(x,y,19+Math.sin(t*3)*3,0,Math.PI*2);ctx.stroke();text(label,x+28,y+7,20,p.accent)}
function fit(asset,x,y,w,h){const aw=asset.videoWidth||asset.naturalWidth,ah=asset.videoHeight||asset.naturalHeight;if(!aw||!ah)return;const scale=Math.min(w/aw,h/ah);ctx.drawImage(asset,x+(w-aw*scale)/2,y+(h-ah*scale)/2,aw*scale,ah*scale)}
function draw(){
 box(0,0,1920,1080,'#080808');
 const border='#808080', ink='#eeeeee', muted='#b0b0b0';
 ctx.save();ctx.beginPath();ctx.rect(20,20,1332,872);ctx.clip();
 if(imageAsset)fit(imageAsset,20,20,1332,872);
 else{
  ctx.fillStyle='#1c1c1c';ctx.fillRect(180,165,960,610);
  ctx.strokeStyle='#dedede';ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(180,165);ctx.lineTo(870,165);ctx.lineTo(870,390);ctx.lineTo(1140,390);ctx.lineTo(1140,775);ctx.lineTo(290,775);ctx.lineTo(290,350);ctx.lineTo(180,350);ctx.closePath();ctx.stroke();
  line(470,350,470,775,'#dedede',3);line(675,350,675,615,'#dedede',3);line(290,350,675,350,'#dedede',3);line(290,615,675,615,'#dedede',3);line(870,520,1140,520,'#dedede',3);
  text('Зал 1',320,395,28,ink);text('Зал 2',510,395,28,ink);text('Выход',200,320,25,ink);text('Центральный зал',740,680,28,ink);
  if(t>=8)dot(360+Math.min(1,(t-8)/37)*430,570,'А');if(t>=32)dot(1060-Math.min(1,(t-32)/13)*220,600,'Б');
 }
 if(videoAsset&&videoAsset.readyState>=2)fit(videoAsset,60,65,300,534);
 ctx.restore();
 ctx.strokeStyle=border;ctx.lineWidth=7;ctx.strokeRect(16,16,1888,1048);
 line(1360,16,1360,1064,border,7);line(16,900,1904,900,border,7);line(1360,718,1904,718,border,7);line(720,900,720,1064,border,7);
 text('Хронология',1372,47,29,muted,'Arial','bold');
 const active=sorted().filter(e=>e.at<=t);let shown=[],height=0;
 for(const e of active.toReversed()){
  const label=(e.approx?'≈ ':'')+absolute(e.at)+' '+e.text;
  ctx.font='25px Arial';let n=1,l='';for(const word of label.split(' ')){if(ctx.measureText(l+word).width>510&&l){n++;l=''}l+=word+' '}
  const h=n*32+10;if(height+h>638)break;shown.unshift({label,h});height+=h;
 }
 let y=80;for(const row of shown){lines(row.label,1372,y,510,25,ink,18);y+=row.h;}
 text('Доп. информация',1372,751,28,muted,'Arial','bold');lines(p.note||'',1372,783,510,23,ink,4);
 text('Стенограмма',27,932,28,muted,'Arial','bold');
 const quoted=active.at(-1);const liveQuote=quoted?.quote&&(!quoted.quoteDuration||t<quoted.at+quoted.quoteDuration)?quoted.quote:'';
 lines(liveQuote,29,970,670,27,ink,3);
 text('Временная шкала основных событий',733,932,26,muted,'Arial','bold');
 ctx.save();ctx.beginPath();ctx.rect(727,943,626,119);ctx.clip();
 const center=1040,base=1010,scale=6;line(728,base,1352,base,'#bcbcbc',2);
 for(let sec=Math.floor((t-60)/5)*5;sec<t+60;sec+=5){if(sec<0)continue;const x=center+(sec-t)*scale;line(x,base-(sec%10===0?43:22),x,base+(sec%10===0?43:22),'#8b8b8b',2)}
 for(const e of sorted()){const x=center+(e.at-t)*scale;line(x,base-40,x,base+40,e.at<=t?'#eeeeee':'#707070',4)}
 line(center,944,center,1063,'#ffffff',5);ctx.restore();
 text('Время'+(p.approximate?' ≈':''),1372,932,28,muted,'Arial','bold');text(absolute(t),1380,1025,104,'#ffffff','monospace');
 const zero=Number(p.zeroAt)||0,delta=t-zero;const elapsed=clock(Math.abs(delta),true)+(zero?(delta<0?' до сигнала':' с сигнала'):' с начала записи');
 text(elapsed,1390,1054,23,muted,'Arial','bold');
 $('#position').textContent=clock(t);$('#seek').value=t;
}
function loadImage(){imageAsset=null;if(p.image){const img=new Image();img.onload=()=>{imageAsset=img;draw()};img.onerror=()=>{$('#message').textContent='Не удалось прочитать изображение.'};img.src=p.image}}
function renderEvents(){const list=$('#event-list');list.replaceChildren();$('#count').textContent=String(p.events.length).padStart(2,'0');p.events.forEach((e,i)=>{const card=document.createElement('div');card.className='event';card.innerHTML='<div class="event-top"><i class="dot"></i><input type="number" min="0" max="3600" aria-label="Время события"><span>СЕК.</span><button class="delete" title="Удалить событие">×</button></div><textarea maxlength="350" aria-label="Описание события"></textarea><textarea class="quote" maxlength="250" placeholder="Стенограмма / реплика" aria-label="Реплика"></textarea>';const [time,body,quote]=card.querySelectorAll('input,textarea');time.value=e.at;body.value=e.text;quote.value=e.quote;time.oninput=()=>{e.at=Math.max(0,Math.min(3600,+time.value||0));persist();draw()};body.oninput=()=>{e.text=body.value;persist();draw()};quote.oninput=()=>{e.quote=quote.value;persist();draw()};card.querySelector('button').onclick=()=>{p.events.splice(i,1);renderEvents();persist();draw()};list.append(card)})}
function hydrate(){for(const key of ['title','start','duration','accent','note'])$('#'+key).value=p[key];$('#seek').max=p.duration;$('#length').textContent=clock(p.duration);renderEvents();loadImage();draw()}
function pause(){playing=false;$('#play').textContent='▶';videoAsset?.pause()}
async function syncVideo(){if(!videoAsset)return;videoAsset.currentTime=Math.min(t,Math.max(0,videoAsset.duration-.05));videoAsset.playbackRate=recording?1:+$('#speed').value;if(playing&&t<videoAsset.duration)try{await videoAsset.play()}catch{}}
$('#play').onclick=()=>{if(recording)return;if(playing)pause();else{if(t>=p.duration)t=0;playing=true;last=performance.now();$('#play').textContent='Ⅱ';syncVideo()}};
$('#reset').onclick=()=>{if(recording)return;pause();t=0;syncVideo();draw()};$('#seek').oninput=()=>{if(recording)return;t=+$('#seek').value;syncVideo();draw()};$('#speed').onchange=()=>syncVideo();
for(const key of ['title','start','duration','accent','note'])$('#'+key).oninput=()=>{const value=$('#'+key).value;p[key]=key==='duration'?Math.max(5,Math.min(3600,+value||60)):value;if(key==='start'&&value.length===5)p.start=value+':00';t=Math.min(t,p.duration);$('#seek').max=p.duration;$('#length').textContent=clock(p.duration);persist();draw()};
$('#add').onclick=()=>{if(p.events.length>=200)return;p.events.push({at:Math.min(p.duration,Math.round(t)),text:'Новое событие',quote:''});renderEvents();persist();$('#event-list').lastElementChild.scrollIntoView({block:'nearest'})};
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>{document.querySelectorAll('[data-tab]').forEach(x=>x.classList.toggle('active',x===b));for(const id of ['events','settings'])$('#'+id).hidden=id!==b.dataset.tab});
function download(blob,name){const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),10000)}
$('#save').onclick=()=>download(new Blob([JSON.stringify(p,null,2)],{type:'application/json'}),'chronicle-project.json');$('#open').onclick=()=>$('#project-file').click();$('#project-file').onchange=async e=>{try{const next=validate(JSON.parse(await e.target.files[0].text()));pause();p=next;t=0;clearVideo();hydrate();persist();$('#message').textContent='Проект открыт.'}catch{$('#message').textContent='Не удалось открыть проект: нужен JSON проекта «Хроника».'}e.target.value=''};
$('#image').onchange=e=>{const file=e.target.files[0];if(!file)return;if(file.size>12*1024*1024){$('#message').textContent='Выберите изображение размером до 12 МБ.';return}const reader=new FileReader();reader.onload=()=>{p.image=reader.result;loadImage();persist()};reader.readAsDataURL(file)};$('#remove-image').onclick=()=>{p.image=null;imageAsset=null;$('#image').value='';persist();draw()};
function clearVideo(){videoAsset?.pause();videoAsset=null;if(videoURL)URL.revokeObjectURL(videoURL);videoURL=null;$('#video').value=''}
$('#video').onchange=e=>{const file=e.target.files[0];if(!file)return;clearVideo();videoURL=URL.createObjectURL(file);videoAsset=document.createElement('video');videoAsset.muted=true;videoAsset.playsInline=true;videoAsset.onloadeddata=()=>{syncVideo();draw();$('#message').textContent='Видео добавлено. Звук в экспорт не включается.'};videoAsset.onerror=()=>{$('#message').textContent='Этот видеоформат не поддерживается браузером.';clearVideo()};videoAsset.src=videoURL};$('#remove-video').onclick=()=>{clearVideo();draw()};
$('#export').onclick=()=>{if(recording){recorder.stop();return}if(!canvas.captureStream||typeof MediaRecorder==='undefined'){$('#message').textContent='Для экспорта откройте редактор в актуальном Chrome или Firefox.';return}const mime=['video/webm;codecs=vp9','video/webm;codecs=vp8','video/webm'].find(x=>MediaRecorder.isTypeSupported(x));if(!mime){$('#message').textContent='Браузер не поддерживает запись WebM.';return}pause();t=0;draw();const stream=canvas.captureStream(30),chunks=[];try{recorder=new MediaRecorder(stream,{mimeType:mime,videoBitsPerSecond:8000000})}catch{stream.getTracks().forEach(x=>x.stop());$('#message').textContent='Не удалось запустить запись.';return}recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};recorder.onstop=()=>{pause();recording=false;stream.getTracks().forEach(x=>x.stop());download(new Blob(chunks,{type:mime}),'chronicle.webm');document.querySelectorAll('aside input,aside textarea,aside button,.header-actions button,#seek,#speed,#play,#reset').forEach(e=>e.disabled=false);$('#export').textContent='↓ Экспорт видео';$('#message').textContent='Видео скачано в WebM, 1920 × 1080, без звука.'};recording=true;playing=true;last=performance.now();document.querySelectorAll('aside input,aside textarea,aside button,.header-actions button,#seek,#speed,#play,#reset').forEach(e=>e.disabled=true);$('#export').textContent='■ Завершить запись';$('#message').textContent='Идёт экспорт в реальном времени. Оставьте вкладку открытой.';recorder.start(1000);syncVideo()};
function frame(now){if(playing){t=Math.min(p.duration,t+(now-last)/1000*(recording?1:+$('#speed').value));if(t>=p.duration){pause();if(recording&&recorder.state==='recording'){draw();recorder.stop()}}}last=now;draw();requestAnimationFrame(frame)}hydrate();requestAnimationFrame(frame);

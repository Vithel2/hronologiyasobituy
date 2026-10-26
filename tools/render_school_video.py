"""Render the approved chronology from local media; source files are never uploaded."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright
import argparse, base64, io, json, math, subprocess

parser=argparse.ArgumentParser()
parser.add_argument('--materials',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--server',default='http://127.0.0.1:8000')
parser.add_argument('--start-time',default='09:25:11')
parser.add_argument('--end-time',default='09:46:32')
parser.add_argument('--first-video-offset',type=float,default=735)
parser.add_argument('--second-video-time',default='09:38:06')
parser.add_argument('--exit-time',default='09:38:10')
parser.add_argument('--prepare-only',action='store_true')
args=parser.parse_args();root=args.output.resolve();root.mkdir(parents=True,exist_ok=True)
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
MONO='/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
def font(n):return ImageFont.truetype(FONT,n)
def seconds(clock):
 h,m,s=map(float,clock.split(':'));return h*3600+m*60+s
files=list(args.materials.rglob('*'))
a=next(f for f in files if f.suffix=='.mp4' and 'Первое' in f.name)
b=next(f for f in files if f.suffix=='.mp4' and 'Второе' in f.name)
audio=next(f for f in files if f.suffix=='.mp3')
def duration(path):
 return float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(path)],capture_output=True,text=True,check=True).stdout)
# Count decoded samples instead of relying on MP3 bitrate-based duration estimates.
proc=subprocess.Popen(['ffmpeg','-v','error','-i',str(audio),'-ac','1','-ar','48000','-f','s16le','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
count=0
while data:=proc.stdout.read(4*1024*1024):count+=len(data)
error=proc.stderr.read().decode();status=proc.wait()
if status:raise RuntimeError(error)
length=count/(48000*2);origin=seconds(args.start_time) if args.start_time else seconds(args.end_time)-length
start=f'{int(origin)//3600:02d}:{int(origin)//60%60:02d}:{int(origin)%60:02d}'
first=args.first_video_offset;second=seconds(args.second_video_time)-origin;exit_at=seconds(args.exit_time)-origin
first_end=first+duration(a);second_end=second+duration(b)
assert 0<713<first<second<length and 0<exit_at<length
project={'version':1,'title':'Эвакуация школы','start':start,'startFraction':origin-math.floor(origin),'duration':length,'accent':'#eeeeee','approximate':True,'zeroAt':713,'note':'Плановая эвакуация, 8 класс\nМОБУ СОШ д. Сергиополь\n21 октября 2026 года','captions':[{'at':735,'until':739,'text':'— Эвакуация.'}],'events':[
 {'at':713,'approx':True,'label':'Сигнал','text':'Звучит сигнал эвакуации.','quote':''},
 {'at':first,'approx':True,'label':'Видео 1','text':'8-й класс находится в школе.','quote':''},
 {'at':second,'label':'Видео 2','text':'Ученики идут по улице в сторону катка.','quote':''},
 {'at':exit_at,'approx':True,'label':'Выход 8 кл.','text':'8-й класс выходит через выход внизу лестницы.','quote':''}]}
(root/'project.json').write_text(json.dumps(project,ensure_ascii=False,indent=2))
(root/'timing.json').write_text(json.dumps({'decoded_duration':length,'start':start,'origin':origin,'file_modified_time':args.end_time,'calculated_end_seconds':origin+length,'signal_offset':713,'first_offset':first,'second_offset':second,'exit_offset':exit_at,'first_end':first_end,'second_end':second_end},ensure_ascii=False,indent=2))
def panel(at):
 im=Image.new('RGB',(1332,872),'#080808');d=ImageDraw.Draw(im)
 d.text((540,82),'Схема маршрута',font=font(28),fill='#a9a9a9')
 d.rectangle((480,170,1015,440),outline='#cccccc',width=3)
 d.text((665,196),'Школа',font=font(35),fill='#eeeeee')
 # Only the reported staircase and exit; no invented rooms or floors.
 points=[(650,265)]
 for i in range(5):points.extend([(670+i*20,265+i*22),(670+i*20,287+i*22)])
 d.line(points,fill='#dedede',width=3)
 d.text((795,307),'Лестница',font=font(25),fill='#dddddd')
 d.line((748,375,748,440),fill='#bcbcbc',width=3)
 d.line((718,438,778,438),fill='#080808',width=6)
 d.text((790,442),'Выход',font=font(25),fill='#dddddd')
 d.line((748,440,748,650,1020,650),fill='#bcbcbc',width=3)
 d.text((655,695),'Улица',font=font(32),fill='#eeeeee')
 for x in range(1020,1260,24):d.line((x,650,min(x+12,1260),650),fill='#a0a0a0',width=3)
 d.line((1243,638,1260,650,1243,662),fill='#cccccc',width=3)
 d.text((1050,695),'К катку',font=font(31),fill='#eeeeee')
 if first<=at<first_end:d.ellipse((728,335,748,355),fill='#ffffff')
 elif second<=at<second_end:d.ellipse((833,640,853,660),fill='#ffffff')
 if exit_at<=at<exit_at+5:d.ellipse((738,438,758,458),fill='#ffffff')
 if first<=at<first_end or second<=at<second_end:d.rectangle((36,41,342,583),outline='#777777',width=2)
 buf=io.BytesIO();im.save(buf,format='PNG');return 'data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode()
changes=sorted({0,713,735,739,first,first_end,second,second_end,exit_at,exit_at+5})
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=browser.new_page();page.goto(args.server)
 page.evaluate('window.requestAnimationFrame=()=>0;pause()');page.wait_for_timeout(100)
 page.evaluate('data=>{p=data;imageAsset=null;videoAsset=null}',project)
 for i,at in enumerate(changes):
  encoded=page.evaluate('''async data=>{t=data.at;const im=new Image();im.src=data.src;await im.decode();imageAsset=im;draw();box(1370,940,522,120,'#080808');box(727,943,626,119,'#080808');return canvas.toDataURL('image/png').split(',')[1]}''',{'at':at,'src':panel(at)})
  (root/f'background-{i}.png').write_bytes(base64.b64decode(encoded))
 browser.close()
with (root/'slides.txt').open('w') as f:
 for i,at in enumerate(changes):
  end=changes[i+1] if i+1<len(changes) else length
  f.write(f"file '{root}/background-{i}.png'\nduration {end-at:.6f}\n")
 f.write(f"file '{root}/background-{len(changes)-1}.png'\n")
# Red event ticks and staggered labels remain distinct from grey time divisions.
strip=Image.new('RGBA',(int(length*6)+1200,122),(0,0,0,0));d=ImageDraw.Draw(strip)
d.line((0,68,strip.width,68),fill='#bcbcbc',width=2)
for sec in range(0,math.ceil(length)+60,5):
 x=600+sec*6;h=36 if sec%10==0 else 18
 d.line((x,68-h,x,68+h),fill='#939393',width=2)
for i,event in enumerate(project['events']):
 x=round(600+event['at']*6);color='#dc3636'
 d.line((x,36,x,100),fill=color,width=4)
 d.polygon([(x-6,25),(x+6,25),(x,34)],fill=color)
 label=event['label'];label_font=font(19);w=d.textlength(label,font=label_font)
 d.text((x-w/2,0 if i%2==0 else 99),label,font=label_font,fill=color)
strip.save(root/'scale.png')
(root/'clock.txt').write_text('%{pts:gmtime:'+f'{origin:.6f}'+r':%H\:%M\:%S}')
(root/'before.txt').write_text('00:%{eif:floor(max(0,713-t)/60):d:2}:%{eif:mod(floor(max(0,713-t)),60):d:2} до сигнала')
(root/'after.txt').write_text('%{eif:floor((t-713)/3600):d:2}:%{eif:mod(floor((t-713)/60),60):d:2}:%{eif:mod(floor(t-713),60):d:2} с сигнала')
clock=f'drawtext=fontfile={MONO}:textfile={root}/clock.txt:x=1380:y=950:fontsize=104:fontcolor=white'
elapsed=(f"drawtext=fontfile={FONT}:textfile={root}/before.txt:x=1390:y=1035:fontsize=23:fontcolor=0xb0b0b0:enable='lt(t,713)',"+f"drawtext=fontfile={FONT}:textfile={root}/after.txt:x=1390:y=1035:fontsize=23:fontcolor=0xb0b0b0:enable='gte(t,713)'")
filters=(f"[0:v]fps=15[bg];[1:v]scale=300:534,setsar=1,setpts=PTS-STARTPTS+{first}/TB[v1];[2:v]scale=300:534,setsar=1,setpts=PTS-STARTPTS+{second}/TB[v2];"
f"[bg][v1]overlay=60:65:eof_action=pass:enable='gte(t,{first})*lt(t,{first_end})'[a];[a][v2]overlay=60:65:eof_action=pass:enable='gte(t,{second})*lt(t,{second_end})'[b];"
f"movie=filename={root}/scale.png,loop=loop=-1:size=1:start=0,setpts=N/(15*TB),crop=626:122:x='286+6*t':y=0[scale];[b]drawbox=x=1038:y=944:w=5:h=119:color=white:t=fill[cursor];[cursor][scale]overlay=727:943[c];[c]"+clock+","+elapsed+"[out]")
cmd=['ffmpeg','-hide_banner','-loglevel','warning','-y','-f','concat','-safe','0','-i',str(root/'slides.txt'),'-i',str(a),'-i',str(b),'-i',str(audio),'-filter_complex_threads','2','-filter_complex',filters,'-map','[out]','-map','3:a','-t',str(length),'-c:v','libx264','-threads','4','-preset','veryfast','-crf','23','-pix_fmt','yuv420p','-r','15','-c:a','aac','-b:a','128k','-movflags','+faststart',str(root/'sergiopol-full.mp4')]
(root/'render-command.json').write_text(json.dumps(cmd,ensure_ascii=False,indent=2))
print(json.dumps({'start':start,'duration':length,'first':first,'second':second,'exit':exit_at},ensure_ascii=False),flush=True)
if args.prepare_only:raise SystemExit(0)
print('Rendering full version',flush=True);subprocess.run(cmd,check=True)
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss','693','-i',str(root/'sergiopol-full.mp4'),'-t','120','-c:v','libx264','-threads','4','-preset','veryfast','-crf','21','-c:a','copy','-movflags','+faststart',str(root/'sergiopol-short.mp4')],check=True)
print('Both versions complete',flush=True)

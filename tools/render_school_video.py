"""Render the approved school chronology from locally supplied media. No media uploads."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright
import argparse, base64, io, json, subprocess

parser=argparse.ArgumentParser()
parser.add_argument('--materials',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--server',default='http://127.0.0.1:8000')
args=parser.parse_args();root=args.output.resolve();root.mkdir(parents=True,exist_ok=True)
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
MONO='/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
def font(n):return ImageFont.truetype(FONT,n)
length=1279.953
project={'version':1,'title':'Эвакуация школы','start':'09:25:30','duration':length,'accent':'#eeeeee','approximate':True,'zeroAt':713,'note':'Плановая эвакуация\nМОБУ СОШ д. Сергиополь\n21 октября 2026 года','events':[
 {'at':713,'approx':True,'text':'Звучит сигнал эвакуации.','quote':''},
 {'at':735,'text':'Ученики находятся в школе.','quote':'— Эвакуация.','quoteDuration':4},
 {'at':804,'text':'Ученики идут по улице в сторону катка.','quote':''}]}
(root/'project.json').write_text(json.dumps(project,ensure_ascii=False,indent=2))
def panel(stage):
 im=Image.new('RGB',(1332,872),'#080808');d=ImageDraw.Draw(im)
 # A topological route, not an invented floor plan.
 d.text((540,82),'Схема маршрута',font=font(28),fill='#a9a9a9')
 d.rectangle((480,170,1015,440),outline='#cccccc',width=3)
 d.text((665,275),'Школа',font=font(35),fill='#eeeeee')
 # Opening and route to the street.
 d.line((718,438,778,438),fill='#080808',width=6)
 d.line((748,440,748,650,1020,650),fill='#bcbcbc',width=3)
 d.text((655,695),'Улица',font=font(32),fill='#eeeeee')
 # Arrow denotes direction only; it does not assert arrival at the rink.
 for x in range(1020,1260,24):d.line((x,650,min(x+12,1260),650),fill='#a0a0a0',width=3)
 d.line((1243,638,1260,650,1243,662),fill='#cccccc',width=3)
 d.text((1050,695),'К катку',font=font(31),fill='#eeeeee')
 if stage==2:
  d.ellipse((728,335,748,355),fill='#ffffff')
 elif stage==4:d.ellipse((833,640,853,660),fill='#ffffff')
 if stage in [2,4]:d.rectangle((36,41,342,583),outline='#777777',width=2)
 b=io.BytesIO();im.save(b,format='PNG');return 'data:image/png;base64,'+base64.b64encode(b.getvalue()).decode()
changes=[(0,0),(713,1),(735,2),(739,2),(751.569,3),(804,4),(808.072,5)]
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=browser.new_page();page.goto(args.server)
 page.evaluate('window.requestAnimationFrame=()=>0;pause()');page.wait_for_timeout(100)
 page.evaluate('data=>{p=data;imageAsset=null;videoAsset=null}',project)
 for i,(start,stage) in enumerate(changes):
  encoded=page.evaluate('''async data=>{t=data.start;const im=new Image();im.src=data.src;await im.decode();imageAsset=im;draw();box(1370,940,522,120,'#080808');box(727,943,626,119,'#080808');return canvas.toDataURL('image/png').split(',')[1]}''',{'start':start,'src':panel(stage)})
  (root/f'background-{i}.png').write_bytes(base64.b64decode(encoded))
 browser.close()
with (root/'slides.txt').open('w') as f:
 for i,(start,_) in enumerate(changes):
  end=changes[i+1][0] if i+1<len(changes) else length
  f.write(f"file '{root}/background-{i}.png'\nduration {end-start:.6f}\n")
 f.write(f"file '{root}/background-{len(changes)-1}.png'\n")
# Scrolling ticks with a fixed centre cursor, as in the reference.
strip=Image.new('RGBA',(int(length*6)+1200,122),(0,0,0,255));d=ImageDraw.Draw(strip)
d.line((0,68,strip.width,68),fill='#bcbcbc',width=2)
for sec in range(0,1300,5):
 x=600+sec*6;h=43 if sec%10==0 else 22
 d.line((x,68-h,x,68+h),fill='#939393',width=2)
for event in project['events']:
 x=600+event['at']*6;d.line((x,25,x,111),fill='#eeeeee',width=4)
strip.save(root/'scale.png')
files=list(args.materials.rglob('*'))
a=next(f for f in files if f.suffix=='.mp4' and 'Первое' in f.name)
b=next(f for f in files if f.suffix=='.mp4' and 'Второе' in f.name)
audio=next(f for f in files if f.suffix=='.mp3')
# Show an elapsed clock relative to the signal, in the same block as the time.
clock="drawtext=fontfile="+MONO+":text='%{pts\\:gmtime\\:33930\\:%H\\\\\\:%M\\\\\\:%S}':x=1380:y=950:fontsize=104:fontcolor=white"
(root/'before.txt').write_text('00:%{eif:floor(max(0,713-t)/60):d:2}:%{eif:mod(floor(max(0,713-t)),60):d:2} до сигнала')
(root/'after.txt').write_text('%{eif:floor((t-713)/3600):d:2}:%{eif:mod(floor((t-713)/60),60):d:2}:%{eif:mod(floor(t-713),60):d:2} с сигнала')
elapsed=(f"drawtext=fontfile={FONT}:textfile={root}/before.txt:x=1390:y=1035:fontsize=23:fontcolor=0xb0b0b0:enable='lt(t,713)',"+f"drawtext=fontfile={FONT}:textfile={root}/after.txt:x=1390:y=1035:fontsize=23:fontcolor=0xb0b0b0:enable='gte(t,713)'")
filters=("[0:v]fps=15[bg];[1:v]scale=300:534,setsar=1,setpts=PTS-STARTPTS+735/TB[v1];[2:v]scale=300:534,setsar=1,setpts=PTS-STARTPTS+804/TB[v2];"
"[bg][v1]overlay=60:65:eof_action=pass:enable='gte(t,735)*lt(t,751.569)'[a];[a][v2]overlay=60:65:eof_action=pass:enable='gte(t,804)*lt(t,808.072)'[b];"
f"movie=filename={root}/scale.png,loop=loop=-1:size=1:start=0,setpts=N/(15*TB),crop=626:122:x='286+6*t':y=0[scale];[b][scale]overlay=727:943[c];[c]drawbox=x=1038:y=944:w=5:h=119:color=white:t=fill,"+clock+","+elapsed+"[out]")
cmd=['ffmpeg','-hide_banner','-loglevel','warning','-y','-f','concat','-safe','0','-i',str(root/'slides.txt'),'-i',str(a),'-i',str(b),'-i',str(audio),'-filter_complex_threads','2','-filter_complex',filters,'-map','[out]','-map','3:a','-t',str(length),'-c:v','libx264','-threads','4','-preset','veryfast','-crf','23','-pix_fmt','yuv420p','-r','15','-c:a','aac','-b:a','128k','-movflags','+faststart',str(root/'sergiopol-full.mp4')]
(root/'render-command.json').write_text(json.dumps(cmd,ensure_ascii=False,indent=2))
print('Rendering full version',flush=True);subprocess.run(cmd,check=True)
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss','693','-i',str(root/'sergiopol-full.mp4'),'-t','120','-c:v','libx264','-threads','4','-preset','veryfast','-crf','21','-c:a','copy','-movflags','+faststart',str(root/'sergiopol-short.mp4')],check=True)
print('Both versions complete',flush=True)

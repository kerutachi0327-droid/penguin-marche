#!/usr/bin/env python3
"""
ペンギンマルシェ Instagram Reel v5
- 9:16 1080x1920
- 縦画像24枚全使用 × 1.5秒 = 約48秒
- BGM: BPM128 ポップダンス風（ノリノリ洋楽系）
"""
import os, random, wave, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

W, H = 1080, 1920
FPS = 30
IMG_SEC = 1.5
FADE_FRAMES = 6

FONT_PATH = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
PHOTO_DIR = b'/sessions/optimistic-awesome-mccarthy/mnt/\xe3\x81\xb8\xe3\x82\x9a\xe3\x82\x93\xe3\x81\xbe\xe3\x82\x8b14/'.decode('utf-8')
ANNOUNCE_IMG = '/sessions/optimistic-awesome-mccarthy/mnt/uploads/LINE_ALBUM_告知画像_260922_1.jpg'
OUT_MP4 = '/sessions/optimistic-awesome-mccarthy/mnt/outputs/penguin_reel_v5.mp4'
OUT_WAV = '/sessions/optimistic-awesome-mccarthy/mnt/outputs/bgm_v5.wav'

SR = 44100
HOT=(255,60,130); PINK=(255,150,200); YELLOW=(255,220,0)
PURPLE=(160,60,220); TEAL=(0,200,180); WHITE=(255,255,255); DARK=(30,20,40)

pop_texts = [
    ("★ 素敵な\nブース！",HOT,WHITE), ("♡ キラキラ！",PINK,DARK),
    ("♪ ありがとう♡",TEAL,WHITE), ("◆ 変身体験★",PURPLE,YELLOW),
    ("★ かわいい！！",HOT,WHITE), ("◎ 素敵な出会い",TEAL,WHITE),
    ("◆ 夢の世界へ",PURPLE,YELLOW), ("♡ エレガント♡",PINK,WHITE),
    ("♪ 美味しい！",(220,120,50),WHITE), ("★ 輝いてます",HOT,WHITE),
    ("▶ 楽しい！",TEAL,WHITE), ("♡ 笑顔♡",PINK,DARK),
    ("◆ ハンドメイド♡",PURPLE,WHITE), ("★ かわいい！",HOT,YELLOW),
    ("♪ 最高の1日",TEAL,WHITE), ("◎ また来てね！",PINK,DARK),
    ("◆ 才能爆発！！",PURPLE,WHITE), ("★ ありがとう！",HOT,WHITE),
    ("♡ また会おう！",PINK,DARK), ("▶ ペンギン♡",TEAL,WHITE),
    ("★ 素晴らしい！",HOT,WHITE), ("◎ 最高！！",TEAL,WHITE),
    ("♪ 幸せ！",PINK,DARK), ("◆ 大成功！",PURPLE,YELLOW),
]

def load_font(size): return ImageFont.truetype(FONT_PATH, size)

def get_vertical_images(folder):
    imgs=[]
    for name in sorted(os.listdir(folder)):
        if not name.lower().endswith(('.jpg','.jpeg','.png')): continue
        path=os.path.join(folder,name)
        try:
            with Image.open(path) as img:
                w,h=img.size
                if h>w: imgs.append(path)
        except: pass
    return imgs

def fill_frame(img_path):
    img=Image.open(img_path).convert('RGB')
    iw,ih=img.size
    scale=max(W/iw,H/ih)
    nw,nh=int(iw*scale),int(ih*scale)
    img=img.resize((nw,nh),Image.BILINEAR)
    x0,y0=(nw-W)//2,(nh-H)//2
    return img.crop((x0,y0,x0+W,y0+H))

def make_photo_frame(img_path,fi,total_f,pop_idx,zoom_in=True):
    base=fill_frame(img_path)
    t=fi/max(total_f-1,1)
    scale=1.0+0.04*(t if zoom_in else 1-t)
    nw,nh=int(W*scale),int(H*scale)
    z=base.resize((nw,nh),Image.BILINEAR)
    x0,y0=(nw-W)//2,(nh-H)//2
    frame=z.crop((x0,y0,x0+W,y0+H))
    draw=ImageDraw.Draw(frame)

    pop_text,tc,bc=pop_texts[pop_idx%len(pop_texts)]
    font=load_font(68)
    lines=pop_text.split('\n')
    ld=[]
    for ln in lines:
        bb=draw.textbbox((0,0),ln,font=font)
        ld.append((bb[2]-bb[0],bb[3]-bb[1]))
    tw=max(w for w,h in ld); th=sum(h for w,h in ld)+8*(len(lines)-1)
    pad=30; bw,bh=tw+pad*2,th+pad*2
    pos=['bottom-right','top-left','bottom-left','top-right'][pop_idx%4]
    m=50
    pm={'bottom-right':(W-bw-m,H-bh-m-150),'top-left':(m,m+90),
        'bottom-left':(m,H-bh-m-150),'top-right':(W-bw-m,m+90)}
    bx,by=pm[pos]
    draw.rounded_rectangle([bx,by,bx+bw,by+bh],radius=22,fill=bc)
    cy=by+pad
    for i,(ln,(lw,lh)) in enumerate(zip(lines,ld)):
        draw.text((bx+pad+(tw-lw)//2,cy),ln,font=font,fill=tc)
        cy+=lh+8

    font2=load_font(36)
    draw.rectangle([0,H-84,W,H],fill=(20,10,30))
    msg="ペンギンマルシェ｜第14回 振り返り"
    bb=draw.textbbox((0,0),msg,font=font2)
    draw.text(((W-(bb[2]-bb[0]))//2,H-66),msg,font=font2,fill=WHITE)
    return np.array(frame,dtype=np.uint8)

def make_announce_frame(img_path,fi,total_f,is_open=True):
    img=Image.open(img_path).convert('RGB')
    iw,ih=img.size
    scale=min(W/iw,H/ih)
    nw,nh=int(iw*scale),int(ih*scale)
    img=img.resize((nw,nh),Image.BILINEAR)
    frame=Image.new('RGB',(W,H),DARK)
    frame.paste(img,((W-nw)//2,(H-nh)//2))
    draw=ImageDraw.Draw(frame)
    if not is_open:
        font=load_font(54)
        msg="第15回 2026.11.1"
        bb=draw.textbbox((0,0),msg,font=font)
        draw.text(((W-(bb[2]-bb[0]))//2,H-210),msg,font=font,fill=YELLOW)
        font2=load_font(42)
        sub="ペンギンマルシェ"
        bb2=draw.textbbox((0,0),sub,font=font2)
        draw.text(((W-(bb2[2]-bb2[0]))//2,H-145),sub,font=font2,fill=WHITE)
    else:
        font=load_font(46)
        msg="第14回 開催の様子"
        bb=draw.textbbox((0,0),msg,font=font)
        draw.text(((W-(bb[2]-bb[0]))//2,H-185),msg,font=font,fill=WHITE)
    return np.array(frame,dtype=np.uint8)

# ── BGM: BPM128 ポップダンス風（洋楽ノリ） ──────────────
def make_pop_bgm(duration):
    n_total=int(SR*duration)
    mix=np.zeros(n_total)
    BPM=128; beat=60.0/BPM; bar=beat*4

    # 音名→周波数
    def f(name):
        base={'C':261.63,'D':293.66,'E':329.63,'F':349.23,
              'G':392.00,'A':440.00,'B':493.88}
        n=name.rstrip('0123456789')
        oct=int(name[-1]) if name[-1].isdigit() else 4
        return base[n]*(2**(oct-4))

    def tone(freq,dur,vol=0.3,decay=0.3,wave='sine',attack=0.01):
        n2=int(SR*dur); t=np.linspace(0,dur,n2,False)
        if wave=='sine': w=np.sin(2*np.pi*freq*t)
        elif wave=='saw': w=2*(t*freq-np.floor(0.5+t*freq))
        elif wave=='square': w=np.sign(np.sin(2*np.pi*freq*t))
        else: w=np.sin(2*np.pi*freq*t)
        env=np.ones(n2)
        att=max(1,int(SR*attack)); env[:att]=np.linspace(0,1,att)
        dec_e=min(att+int(SR*decay),n2)
        env[att:dec_e]=np.linspace(1,0.2,dec_e-att)
        env[dec_e:]=0.2
        rel=min(int(SR*0.03),n2); env[-rel:]*=np.linspace(1,0,rel)
        return w*env*vol

    def add(sig,t_sec,data):
        s=int(t_sec*SR); e=min(s+len(data),len(sig))
        if s<len(sig): sig[s:e]+=data[:e-s]

    # コード進行 C-Am-F-G (各1小節ずつループ)
    chord_sets = [
        [f('C4'),f('E4'),f('G4')],   # C
        [f('A3'),f('C4'),f('E4')],   # Am
        [f('F3'),f('A3'),f('C4')],   # F
        [f('G3'),f('B3'),f('D4')],   # G
    ]
    bass_freqs = [f('C3'),f('A2'),f('F2'),f('G2')]

    # コード（パッド音）
    tp=0.0; ci=0
    while tp<duration:
        ci=int(tp/bar)%4
        for nf in chord_sets[ci]:
            add(mix,tp,tone(nf,bar*0.95,vol=0.10,decay=0.8,wave='sine'))
        tp+=bar

    # ベース
    tp=0.0
    while tp<duration:
        ci=int(tp/bar)%4
        bf=bass_freqs[ci]
        add(mix,tp,tone(bf,beat*0.4,vol=0.45,decay=0.2,wave='sine'))
        add(mix,tp+beat*0.5,tone(bf,beat*0.3,vol=0.25,decay=0.15,wave='sine'))
        add(mix,tp+beat*2,tone(bf,beat*0.4,vol=0.40,decay=0.2,wave='sine'))
        add(mix,tp+beat*2.5,tone(bf,beat*0.3,vol=0.22,decay=0.15,wave='sine'))
        tp+=bar

    # シンセリード（明るいポップメロ）
    melody=[
        ('E5',1),('G5',1),('A5',2),('G5',1),('E5',1),('C5',2),
        ('D5',1),('F5',1),('G5',2),('A5',1),('G5',1),('E5',2),
        ('C5',1),('E5',1),('G5',2),('A5',1),('B5',1),('C6',2),
        ('B5',1),('A5',1),('G5',2),('E5',1),('D5',1),('C5',2),
    ]
    tp=0.0; mi=0
    while tp<duration:
        nn,db=melody[mi%len(melody)]
        dur_s=beat*db*0.5  # 8分音符基準
        nf=f(nn)
        # わずかにデチューン
        det=random.uniform(-1,1); nf_d=nf*(2**(det/1200))
        add(mix,tp,tone(nf_d,dur_s*0.8,vol=0.28,decay=0.25,wave='sine',attack=0.005))
        tp+=dur_s; mi+=1

    # アルペジオ（8分音符）
    arp_patterns=[
        [f('C4'),f('E4'),f('G4'),f('C5')],
        [f('A3'),f('C4'),f('E4'),f('A4')],
        [f('F3'),f('A3'),f('C4'),f('F4')],
        [f('G3'),f('B3'),f('D4'),f('G4')],
    ]
    tp=0.0
    while tp<duration:
        ci=int(tp/bar)%4
        pat=arp_patterns[ci]
        for j,nf in enumerate(pat*2):  # 8音/小節
            at=tp+j*(beat/2)
            if at<duration:
                add(mix,at,tone(nf,beat*0.35,vol=0.08,decay=0.15,wave='sine'))
        tp+=bar

    # キック（4つ打ち）
    tp=0.0
    while tp<duration:
        for off in [0,beat,beat*2,beat*3]:
            kt=tp+off
            if kt>=duration: break
            n2=int(SR*0.2)
            kf=60*np.exp(-np.linspace(0,0.2,n2)*30)
            k=np.sin(2*np.pi*np.cumsum(kf)/SR)*np.exp(-np.linspace(0,0.2,n2)*20)*0.65
            add(mix,kt,k)
        tp+=bar

    # オープンハイハット（8分音符）
    tp=0.0
    while tp<duration:
        for j in range(8):
            ht=tp+j*(beat/2)
            if ht>=duration: break
            n2=int(SR*0.06)
            hh=np.random.randn(n2)*np.exp(-np.linspace(0,15,n2))*(0.09 if j%2==0 else 0.05)
            add(mix,ht,hh)
        tp+=bar

    # スネア（2,4拍）
    tp=beat
    while tp<duration:
        n2=int(SR*0.12)
        sn=(np.random.randn(n2)*0.5+np.sin(2*np.pi*200*np.linspace(0,0.12,n2))*0.5)
        sn*=np.exp(-np.linspace(0,14,n2))*0.30
        add(mix,tp,sn); tp+=beat*2

    # クラップ（2,4拍 少し遅れ）
    tp=beat+0.01
    while tp<duration:
        n2=int(SR*0.05)
        cl=np.random.randn(n2)*np.exp(-np.linspace(0,20,n2))*0.12
        add(mix,tp,cl); tp+=beat*2

    # 正規化
    mx=np.max(np.abs(mix))
    if mx>0: mix=mix/mx*0.88
    fi=int(SR*0.8); fo=int(SR*1.5)
    mix[:fi]*=np.linspace(0,1,fi); mix[-fo:]*=np.linspace(1,0,fo)
    return np.clip(mix,-1,1)

def main():
    random.seed(7)
    print("縦画像収集...")
    all_v=get_vertical_images(PHOTO_DIR)
    print(f"縦画像: {len(all_v)}枚 → 全使用")
    selected=all_v  # 全24枚
    random.shuffle(selected)
    n=len(selected)

    photo_f=int(FPS*IMG_SEC)
    ann_f=int(FPS*2.5)
    total_f=ann_f+n*photo_f+(n-1)*FADE_FRAMES+FADE_FRAMES+ann_f
    total_sec=total_f/FPS
    print(f"総時間: {total_sec:.1f}秒, 写真{n}枚×{IMG_SEC}秒")

    print("BGM生成（BPM128 ポップダンス風）...")
    bgm=make_pop_bgm(total_sec+2)
    bgm_int=(bgm*32767).astype(np.int16)
    with wave.open(OUT_WAV,'w') as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes(bgm_int.tobytes())
    print(f"BGM完了: {len(bgm)/SR:.1f}秒")

    cmd=['ffmpeg','-y','-f','rawvideo','-vcodec','rawvideo',
         '-s',f'{W}x{H}','-pix_fmt','rgb24','-r',str(FPS),'-i','pipe:0',
         '-i',OUT_WAV,'-c:v','libx264','-preset','fast','-crf','22',
         '-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-shortest',OUT_MP4]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=open('/tmp/ffmpeg_v5.log','w'))

    fc=0
    def wf2(arr):
        nonlocal fc
        proc.stdin.write(arr.tobytes()); fc+=1
        if fc%(FPS*5)==0: print(f"  {fc}/{total_f} frames ({fc/FPS:.0f}s)")

    print("告知(オープン)...")
    ann=[make_announce_frame(ANNOUNCE_IMG,i,ann_f,True) for i in range(ann_f)]
    for f in ann: wf2(f)
    prev=ann[-1]

    print("写真フレーム...")
    for pi,path in enumerate(selected):
        zi=(pi%2==0)
        if pi>0:
            first=make_photo_frame(path,0,photo_f,pi,zi)
            for i in range(FADE_FRAMES):
                t=i/FADE_FRAMES; wf2((prev*(1-t)+first*t).astype(np.uint8))
        for fi in range(photo_f):
            wf2(make_photo_frame(path,fi,photo_f,pi,zi))
        prev=make_photo_frame(path,photo_f-1,photo_f,pi,zi)
        print(f"  [{pi+1}/{n}] {Path(path).name}")

    print("告知(クローズ)...")
    first_cl=make_announce_frame(ANNOUNCE_IMG,0,ann_f,False)
    for i in range(FADE_FRAMES):
        t=i/FADE_FRAMES; wf2((prev*(1-t)+first_cl*t).astype(np.uint8))
    for i in range(ann_f): wf2(make_announce_frame(ANNOUNCE_IMG,i,ann_f,False))

    proc.stdin.close(); proc.wait()
    sz=os.path.getsize(OUT_MP4)/1024/1024
    print(f"\n完了: {OUT_MP4}")
    print(f"サイズ: {sz:.1f}MB, {total_sec:.1f}秒, {W}x{H} (9:16)")

if __name__=='__main__':
    main()

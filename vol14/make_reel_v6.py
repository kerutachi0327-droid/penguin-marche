#!/usr/bin/env python3
"""
ペンギンマルシェ Instagram Reel v6
- 9:16 1080x1920, 30秒ぴったり
- 縦画像24枚 × 0.8秒
- BGMなし（無音）
"""
import os, random, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

W, H = 1080, 1920
FPS = 30
IMG_SEC = 0.8
FADE_FRAMES = 6
ANN_SEC = 3.0

FONT_PATH = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
PHOTO_DIR = b'/sessions/optimistic-awesome-mccarthy/mnt/\xe3\x81\xb8\xe3\x82\x9a\xe3\x82\x93\xe3\x81\xbe\xe3\x82\x8b14/'.decode('utf-8')
ANNOUNCE_IMG = '/sessions/optimistic-awesome-mccarthy/mnt/uploads/LINE_ALBUM_告知画像_260922_1.jpg'
OUT_MP4 = '/sessions/optimistic-awesome-mccarthy/mnt/outputs/penguin_reel_v6.mp4'

WHITE=(255,255,255); DARK=(30,20,40); YELLOW=(255,220,0)
HOT=(255,60,130); PINK=(255,150,200); PURPLE=(160,60,220); TEAL=(0,200,180)

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

def load_font(s): return ImageFont.truetype(FONT_PATH, s)

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

def fill_frame(path):
    img=Image.open(path).convert('RGB')
    iw,ih=img.size
    scale=max(W/iw,H/ih)
    nw,nh=int(iw*scale),int(ih*scale)
    img=img.resize((nw,nh),Image.BILINEAR)
    x0,y0=(nw-W)//2,(nh-H)//2
    return img.crop((x0,y0,x0+W,y0+H))

def make_photo_frame(path, fi, total_f, pop_idx, zoom_in=True):
    base = fill_frame(path)
    # Ken Burns
    t = fi / max(total_f-1, 1)
    scale = 1.0 + 0.03*(t if zoom_in else 1-t)
    nw,nh = int(W*scale), int(H*scale)
    z = base.resize((nw,nh), Image.BILINEAR)
    x0,y0 = (nw-W)//2, (nh-H)//2
    frame = z.crop((x0,y0,x0+W,y0+H))
    draw = ImageDraw.Draw(frame)

    # ポップ吹き出し
    pop_text,tc,bc = pop_texts[pop_idx % len(pop_texts)]
    font = load_font(68)
    lines = pop_text.split('\n')
    ld = []
    for ln in lines:
        bb = draw.textbbox((0,0),ln,font=font)
        ld.append((bb[2]-bb[0], bb[3]-bb[1]))
    tw = max(w for w,h in ld)
    th = sum(h for w,h in ld) + 8*(len(lines)-1)
    pad = 30; bw,bh = tw+pad*2, th+pad*2
    pos = ['bottom-right','top-left','bottom-left','top-right'][pop_idx%4]
    m = 50
    pm = {
        'bottom-right':(W-bw-m, H-bh-m-140),
        'top-left':    (m, m+80),
        'bottom-left': (m, H-bh-m-140),
        'top-right':   (W-bw-m, m+80),
    }
    bx,by = pm[pos]
    draw.rounded_rectangle([bx,by,bx+bw,by+bh], radius=22, fill=bc)
    cy = by+pad
    for ln,(lw,lh) in zip(lines,ld):
        draw.text((bx+pad+(tw-lw)//2, cy), ln, font=font, fill=tc)
        cy += lh+8

    # 下部バー
    font2 = load_font(36)
    draw.rectangle([0, H-84, W, H], fill=(20,10,30))
    msg = "ペンギンマルシェ｜第14回 振り返り"
    bb = draw.textbbox((0,0),msg,font=font2)
    draw.text(((W-(bb[2]-bb[0]))//2, H-66), msg, font=font2, fill=WHITE)
    return np.array(frame, dtype=np.uint8)

def make_announce_frame(path, fi, total_f, is_open=True):
    img = Image.open(path).convert('RGB')
    iw,ih = img.size
    scale = min(W/iw, H/ih)
    nw,nh = int(iw*scale), int(ih*scale)
    img = img.resize((nw,nh), Image.BILINEAR)
    frame = Image.new('RGB',(W,H),DARK)
    frame.paste(img, ((W-nw)//2,(H-nh)//2))
    draw = ImageDraw.Draw(frame)
    if not is_open:
        font = load_font(54)
        msg = "第15回 2026.11.1"
        bb = draw.textbbox((0,0),msg,font=font)
        draw.text(((W-(bb[2]-bb[0]))//2, H-210), msg, font=font, fill=YELLOW)
        font2 = load_font(42)
        sub = "ペンギンマルシェ"
        bb2 = draw.textbbox((0,0),sub,font=font2)
        draw.text(((W-(bb2[2]-bb2[0]))//2, H-145), sub, font=font2, fill=WHITE)
    else:
        font = load_font(46)
        msg = "第14回 開催の様子"
        bb = draw.textbbox((0,0),msg,font=font)
        draw.text(((W-(bb[2]-bb[0]))//2, H-185), msg, font=font, fill=WHITE)
    return np.array(frame, dtype=np.uint8)

def main():
    random.seed(7)
    all_v = get_vertical_images(PHOTO_DIR)
    print(f"縦画像: {len(all_v)}枚")
    selected = all_v[:]
    random.shuffle(selected)
    n = len(selected)

    photo_f = int(FPS * IMG_SEC)
    ann_f = int(FPS * ANN_SEC)
    total_f = ann_f + n*photo_f + (n-1)*FADE_FRAMES + FADE_FRAMES + ann_f
    print(f"総フレーム: {total_f} = {total_f/FPS:.1f}秒 (BGMなし)")

    # ffmpeg: 映像のみ（-an で音声なし）
    cmd = ['ffmpeg','-y',
           '-f','rawvideo','-vcodec','rawvideo',
           '-s',f'{W}x{H}','-pix_fmt','rgb24',
           '-r',str(FPS),'-i','pipe:0',
           '-c:v','libx264','-preset','fast','-crf','22',
           '-pix_fmt','yuv420p',
           '-an',  # 音声なし
           OUT_MP4]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stderr=open('/tmp/ffmpeg_v6.log','w'))
    fc = 0
    def wf(arr):
        nonlocal fc
        proc.stdin.write(arr.tobytes()); fc+=1
        if fc%(FPS*5)==0: print(f"  {fc}/{total_f} ({fc/FPS:.0f}s)")

    print("告知(オープン)...")
    ann = [make_announce_frame(ANNOUNCE_IMG,i,ann_f,True) for i in range(ann_f)]
    for f in ann: wf(f)
    prev = ann[-1]

    print("写真フレーム...")
    for pi,path in enumerate(selected):
        zi = (pi%2==0)
        if pi>0:
            first = make_photo_frame(path,0,photo_f,pi,zi)
            for i in range(FADE_FRAMES):
                t=i/FADE_FRAMES; wf((prev*(1-t)+first*t).astype(np.uint8))
        for fi in range(photo_f):
            wf(make_photo_frame(path,fi,photo_f,pi,zi))
        prev = make_photo_frame(path,photo_f-1,photo_f,pi,zi)
        print(f"  [{pi+1}/{n}] {Path(path).name}")

    print("告知(クローズ)...")
    first_cl = make_announce_frame(ANNOUNCE_IMG,0,ann_f,False)
    for i in range(FADE_FRAMES):
        t=i/FADE_FRAMES; wf((prev*(1-t)+first_cl*t).astype(np.uint8))
    for i in range(ann_f): wf(make_announce_frame(ANNOUNCE_IMG,i,ann_f,False))

    proc.stdin.close(); proc.wait()
    sz = os.path.getsize(OUT_MP4)/1024/1024
    print(f"\n完了: {OUT_MP4}")
    print(f"サイズ: {sz:.1f}MB, {total_f/FPS:.1f}秒, 無音, {W}x{H}")

if __name__=='__main__':
    main()

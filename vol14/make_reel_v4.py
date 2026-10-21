import os, sys, random, wave, subprocess, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

W, H = 1080, 1920
FPS = 30
IMG_SEC = 2.5
FADE_FRAMES = 8

FONT_PATH = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
PHOTO_DIR = b'/sessions/optimistic-awesome-mccarthy/mnt/\xe3\x81\xb8\xe3\x82\x9a\xe3\x82\x93\xe3\x81\xbe\xe3\x82\x8b14/'.decode('utf-8')
ANNOUNCE_IMG = '/sessions/optimistic-awesome-mccarthy/mnt/uploads/LINE_ALBUM_告知画像_260922_1.jpg'
OUT_MP4 = '/sessions/optimistic-awesome-mccarthy/mnt/outputs/penguin_reel_v4.mp4'
OUT_WAV = '/sessions/optimistic-awesome-mccarthy/mnt/outputs/bgm_v4.wav'

HOT    = (255, 60, 130)
PINK   = (255, 150, 200)
YELLOW = (255, 220, 0)
PURPLE = (160, 60, 220)
TEAL   = (0, 200, 180)
WHITE  = (255, 255, 255)
DARK   = (30, 20, 40)
SR = 44100

pop_texts = [
    ("★ 素敵な\nブース！",    HOT,    WHITE),
    ("♡ 笑顔が\nキラキラ！",  PINK,   DARK),
    ("♪ ありがとう♡",        TEAL,   WHITE),
    ("◆ 変身体験★",          PURPLE, YELLOW),
    ("★ かわいい！！",        HOT,    WHITE),
    ("◎ 素敵な出会い",        TEAL,   WHITE),
    ("◆ 夢の世界へ",          PURPLE, YELLOW),
    ("♡ エレガント♡",         PINK,   WHITE),
    ("♪ 美味しい瞬間",        (220,120,50), WHITE),
    ("★ 輝いてます！",        HOT,    WHITE),
    ("▶ 楽しい第14回",        TEAL,   WHITE),
    ("♡ みんなの笑顔♡",       PINK,   DARK),
]

def load_font(size):
    return ImageFont.truetype(FONT_PATH, size)

def get_vertical_images(folder):
    images = []
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        if not name.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue
        try:
            with Image.open(path) as img:
                w, h = img.size
                if h > w:
                    images.append(path)
        except:
            pass
    return images

def fill_frame(img_path):
    img = Image.open(img_path).convert('RGB')
    iw, ih = img.size
    scale = max(W / iw, H / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    img = img.resize((nw, nh), Image.BILINEAR)
    x0 = (nw - W) // 2
    y0 = (nh - H) // 2
    return img.crop((x0, y0, x0 + W, y0 + H))

def make_photo_frame(img_path, frame_idx, total_frames, pop_idx, zoom_in=True):
    base = fill_frame(img_path)
    # Ken Burns
    t = frame_idx / max(total_frames - 1, 1)
    scale = 1.0 + 0.04 * (t if zoom_in else 1-t)
    nw, nh = int(W * scale), int(H * scale)
    zoomed = base.resize((nw, nh), Image.BILINEAR)
    x0, y0 = (nw - W) // 2, (nh - H) // 2
    frame = zoomed.crop((x0, y0, x0 + W, y0 + H))
    
    draw = ImageDraw.Draw(frame)
    
    # ポップ吹き出し
    pop_text, tc, bc = pop_texts[pop_idx % len(pop_texts)]
    font = load_font(70)
    lines = pop_text.split('\n')
    line_data = []
    for line in lines:
        bb = draw.textbbox((0,0), line, font=font)
        line_data.append((bb[2]-bb[0], bb[3]-bb[1]))
    tw = max(w for w,h in line_data)
    th = sum(h for w,h in line_data) + 10*(len(lines)-1)
    pad = 32
    bw, bh = tw + pad*2, th + pad*2
    
    positions = ['bottom-right','top-left','bottom-left','top-right']
    pos = positions[pop_idx % 4]
    m = 56
    pos_map = {
        'bottom-right': (W-bw-m, H-bh-m-160),
        'top-left': (m, m+100),
        'bottom-left': (m, H-bh-m-160),
        'top-right': (W-bw-m, m+100),
    }
    bx, by = pos_map[pos]
    draw.rounded_rectangle([bx, by, bx+bw, by+bh], radius=24, fill=bc)
    cy = by + pad
    for i, (line, (lw, lh)) in enumerate(zip(lines, line_data)):
        lx = bx + pad + (tw - lw) // 2
        draw.text((lx, cy), line, font=font, fill=tc)
        cy += lh + 10
    
    # 下部バー
    font2 = load_font(38)
    draw.rectangle([0, H-90, W, H], fill=(20,10,30))
    msg = "ペンギンマルシェ｜第14回 振り返り"
    bb = draw.textbbox((0,0), msg, font=font2)
    draw.text(((W-(bb[2]-bb[0]))//2, H-68), msg, font=font2, fill=WHITE)
    
    return np.array(frame, dtype=np.uint8)

def make_announce_frame(img_path, frame_idx, total_frames, is_open=True):
    img = Image.open(img_path).convert('RGB')
    iw, ih = img.size
    scale = min(W/iw, H/ih)
    nw, nh = int(iw*scale), int(ih*scale)
    img = img.resize((nw, nh), Image.BILINEAR)
    frame = Image.new('RGB', (W, H), DARK)
    frame.paste(img, ((W-nw)//2, (H-nh)//2))
    
    draw = ImageDraw.Draw(frame)
    if not is_open:
        font = load_font(56)
        msg = "第15回 2026.11.1"
        bb = draw.textbbox((0,0), msg, font=font)
        draw.text(((W-(bb[2]-bb[0]))//2, H-220), msg, font=font, fill=YELLOW)
        font2 = load_font(44)
        sub = "ペンギンマルシェ"
        bb2 = draw.textbbox((0,0), sub, font=font2)
        draw.text(((W-(bb2[2]-bb2[0]))//2, H-150), sub, font=font2, fill=WHITE)
    return np.array(frame, dtype=np.uint8)

def make_bgm(duration):
    n = int(SR * duration)
    mix = np.zeros(n)
    BPM = 92
    beat = 60.0 / BPM
    bar = beat * 4
    
    note_map = {'C3':130.81,'F3':174.61,'G3':196,'A3':220,'C4':261.63,
                'D4':293.66,'E4':329.63,'F4':349.23,'G4':392,'A4':440,
                'C5':523.25,'D5':587.33,'E5':659.25,'G5':783.99,'A5':880}
    
    def tone(f, dur, vol=0.3, decay=0.5):
        n2 = int(SR*dur)
        t = np.linspace(0, dur, n2)
        w = np.sin(2*np.pi*f*t)
        env = np.exp(-t/decay)
        rel = int(SR*0.05); env[-rel:] *= np.linspace(1,0,rel)
        att = int(SR*0.02); env[:att] *= np.linspace(0,1,att)
        return w * env * vol
    
    def add(sig, t_sec, data):
        s = int(t_sec*SR); e = min(s+len(data), len(sig))
        if s < len(sig): sig[s:e] += data[:e-s]
    
    chords_notes = [
        [note_map['A3'], note_map['C4'], note_map['E4']],  # Am
        [note_map['F3'], note_map['A3'], note_map['C4']],  # F
        [note_map['C4'], note_map['E4'], note_map['G4']],  # C
        [note_map['G3'], note_map['C4'], note_map['E4']],  # G7
    ]
    bass_freqs = [note_map['A3']*0.5, note_map['F3']*0.5,
                  note_map['C3'], note_map['G3']*0.5]
    
    melody = [
        ('E5',0.5),('D5',0.5),('C5',1.0),('A4',0.5),('C5',0.5),('E5',1.0),
        ('G5',0.5),('E5',0.5),('C5',1.0),('D5',0.5),('C5',0.5),('A4',1.0),
    ]
    
    # コード + ベース
    tp = 0.0
    ci = 0
    while tp < duration:
        ci = int(tp/(bar*2)) % 4
        for f in chords_notes[ci]:
            add(mix, tp, tone(f, bar*1.8, vol=0.12, decay=1.2))
        add(mix, tp, tone(bass_freqs[ci], beat*0.5, vol=0.4, decay=0.3))
        if tp + beat*2 < duration:
            add(mix, tp+beat*2, tone(bass_freqs[ci]*1.0, beat*0.4, vol=0.25, decay=0.25))
        tp += bar*2
    
    # メロディ
    tp = 0.0; mi = 0
    while tp < duration:
        nn, db = melody[mi % len(melody)]
        f = note_map.get(nn, 440)
        dur_s = beat * db
        add(mix, tp, tone(f, dur_s*0.8, vol=0.22, decay=0.4))
        tp += dur_s; mi += 1
    
    # キック
    tp = 0.0
    while tp < duration:
        for off in [0, beat*2]:
            kt = tp + off
            if kt >= duration: break
            n2 = int(SR*0.15)
            kf = 80*np.exp(-np.linspace(0,0.15,n2)*20)
            k = np.sin(2*np.pi*np.cumsum(kf)/SR)*np.exp(-np.linspace(0,0.15,n2)*15)*0.5
            add(mix, kt, k)
        tp += bar
    
    # ハイハット
    tp = 0.0; hh_i = beat/2
    while tp < duration:
        n2 = int(SR*0.03)
        hh = np.random.randn(n2)*np.exp(-np.linspace(0,8,n2))*0.07
        add(mix, tp, hh); tp += hh_i
    
    # スネア
    tp = beat
    while tp < duration:
        n2 = int(SR*0.1)
        sn = np.random.randn(n2)*np.exp(-np.linspace(0,12,n2))*0.18
        add(mix, tp, sn); tp += bar/2
    
    # 正規化
    mx = np.max(np.abs(mix))
    if mx > 0: mix = mix/mx*0.82
    fi = int(SR*1.5); fo = int(SR*2)
    mix[:fi] *= np.linspace(0,1,fi)
    mix[-fo:] *= np.linspace(1,0,fo)
    return np.clip(mix, -1, 1)

def main():
    random.seed(42)
    print("縦画像収集...")
    all_v = get_vertical_images(PHOTO_DIR)
    print(f"縦画像: {len(all_v)}枚")
    n = min(12, len(all_v))
    selected = random.sample(all_v, n)
    print(f"選択: {n}枚 / 各{IMG_SEC}秒")
    
    photo_f = int(FPS * IMG_SEC)
    ann_f = int(FPS * 3)
    total_f = ann_f + n*photo_f + (n-1)*FADE_FRAMES + FADE_FRAMES + ann_f
    total_sec = total_f / FPS
    print(f"総時間: {total_sec:.1f}秒")
    
    print("BGM生成...")
    bgm = make_bgm(total_sec + 2)
    bgm_int = (bgm * 32767).astype(np.int16)
    with wave.open(OUT_WAV, 'w') as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes(bgm_int.tobytes())
    print(f"BGM: {OUT_WAV}")
    
    cmd = ['ffmpeg','-y','-f','rawvideo','-vcodec','rawvideo',
           '-s',f'{W}x{H}','-pix_fmt','rgb24','-r',str(FPS),'-i','pipe:0',
           '-i',OUT_WAV,'-c:v','libx264','-preset','fast','-crf','23',
           '-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-shortest',OUT_MP4]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=open('/tmp/ffmpeg_v4.log','w'))
    
    fc = 0
    def wf2(arr):
        nonlocal fc
        proc.stdin.write(arr.tobytes()); fc+=1
        if fc%60==0: print(f"  {fc}/{total_f} frames")
    
    print("告知(オープン)...")
    ann = [make_announce_frame(ANNOUNCE_IMG, i, ann_f, True) for i in range(ann_f)]
    for f in ann: wf2(f)
    prev = ann[-1]
    
    print("写真フレーム...")
    for pi, path in enumerate(selected):
        zi = (pi % 2 == 0)
        if pi > 0:
            first = make_photo_frame(path, 0, photo_f, pi, zi)
            for i in range(FADE_FRAMES):
                t = i/FADE_FRAMES
                wf2((prev*(1-t)+first*t).astype(np.uint8))
        for fi in range(photo_f):
            f = make_photo_frame(path, fi, photo_f, pi, zi)
            wf2(f)
        prev = make_photo_frame(path, photo_f-1, photo_f, pi, zi)
        print(f"  [{pi+1}/{n}] {Path(path).name}")
    
    print("告知(クローズ)...")
    first_cl = make_announce_frame(ANNOUNCE_IMG, 0, ann_f, False)
    for i in range(FADE_FRAMES):
        t = i/FADE_FRAMES
        wf2((prev*(1-t)+first_cl*t).astype(np.uint8))
    for i in range(ann_f):
        wf2(make_announce_frame(ANNOUNCE_IMG, i, ann_f, False))
    
    proc.stdin.close(); proc.wait()
    sz = os.path.getsize(OUT_MP4)/1024/1024
    print(f"\n完了: {OUT_MP4}")
    print(f"サイズ: {sz:.1f}MB, {total_sec:.1f}秒, {W}x{H}")

if __name__ == '__main__':
    main()

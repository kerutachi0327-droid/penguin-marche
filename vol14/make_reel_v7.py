#!/usr/bin/env python3
"""
ペンギンマルシェ Reel v7
- 画像を色特性でカテゴリ自動分類
- カテゴリ別テキスト自動生成
- 各カテゴリ30秒動画×3本
- BGMなし（インスタで選択）
"""
import os, json, numpy as np, subprocess
from PIL import Image, ImageDraw, ImageFont
from sklearn.cluster import KMeans
from pathlib import Path

W, H = 1080, 1920
FPS = 30
ANN_SEC = 3.0
FADE_FRAMES = 6
TARGET_SEC = 30.0

FONT_PATH = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
PHOTO_DIR = b'/sessions/optimistic-awesome-mccarthy/mnt/\xe3\x81\xb8\xe3\x82\x9a\xe3\x82\x93\xe3\x81\xbe\xe3\x82\x8b14/'.decode('utf-8')
ANNOUNCE_IMG = '/sessions/optimistic-awesome-mccarthy/mnt/uploads/LINE_ALBUM_告知画像_260922_1.jpg'
OUT_DIR = '/sessions/optimistic-awesome-mccarthy/mnt/outputs/'

WHITE=(255,255,255); DARK=(30,20,40); YELLOW=(255,220,0)
HOT=(255,60,130); PINK=(255,150,200); PURPLE=(160,60,220); TEAL=(0,200,180)
GREEN=(60,200,80); ORANGE=(255,140,0); CREAM=(255,245,220)

def load_font(s): return ImageFont.truetype(FONT_PATH, s)

# ─── STEP1: 画像収集 + 特徴量抽出 ────────────────────────────
def collect_and_cluster():
    vert = []
    for name in sorted(os.listdir(PHOTO_DIR)):
        if not name.lower().endswith(('.jpg','.jpeg','.png')): continue
        path = os.path.join(PHOTO_DIR, name)
        try:
            with Image.open(path) as img:
                w,h = img.size
                if h <= w: continue
                small = img.convert('HSV').resize((80,80))
                arr = np.array(small).astype(float)
                H2=arr[:,:,0]; S=arr[:,:,1]; V=arr[:,:,2]
                rgb = np.array(img.resize((80,80))).astype(float)
                h_hist = np.histogram(H2, bins=12, range=(0,255))[0].astype(float)
                h_hist /= h_hist.sum()
                feat = np.concatenate([h_hist, [S.mean()/255, V.mean()/255, S.std()/255]])
                vert.append({'path':path,'name':name,'feat':feat,
                             's':float(S.mean()),'v':float(V.mean()),
                             'h':float(H2.mean()),
                             'r':float(rgb[:,:,0].mean()),
                             'g':float(rgb[:,:,1].mean()),
                             'b':float(rgb[:,:,2].mean())})
        except: pass
    
    print(f'縦画像: {len(vert)}枚')
    X = np.stack([v['feat'] for v in vert])
    
    # K-means で3クラスタ（最小5枚確保）
    best_labels = None
    for seed in [42,7,13,99,1,55,23,88]:
        km = KMeans(n_clusters=3, random_state=seed, n_init=30)
        labels = km.fit_predict(X)
        sizes = [sum(labels==c) for c in range(3)]
        if min(sizes) >= 5:
            best_labels = labels
            print(f'クラスタサイズ: {sizes}')
            break
    
    if best_labels is None:
        # 強制バランス
        km = KMeans(n_clusters=3, random_state=42, n_init=30)
        best_labels = km.fit_predict(X)
        for ci in range(3):
            while sum(best_labels==ci) < 5:
                max_c = max(range(3), key=lambda x: sum(best_labels==x))
                idxs = [i for i,l in enumerate(best_labels) if l==max_c]
                dists = [np.linalg.norm(X[i]-km.cluster_centers_[max_c]) for i in idxs]
                best_labels[idxs[np.argmax(dists)]] = ci
    
    # クラスタ情報収集
    clusters = {}
    for c in range(3):
        idxs = [i for i,l in enumerate(best_labels) if l==c]
        r = np.mean([vert[i]['r'] for i in idxs])
        g = np.mean([vert[i]['g'] for i in idxs])
        b = np.mean([vert[i]['b'] for i in idxs])
        v_m = np.mean([vert[i]['v'] for i in idxs])
        s_m = np.mean([vert[i]['s'] for i in idxs])
        h_m = np.mean([vert[i]['h'] for i in idxs])
        paths = [vert[i]['path'] for i in idxs]
        clusters[c] = {'paths':paths,'r':r,'g':g,'b':b,'v':v_m,'s':s_m,'h':h_m,'n':len(idxs)}
    
    return clusters

# ─── STEP2: 色特性からカテゴリを自動命名 ──────────────────────
def auto_categorize(clusters):
    """RGB/HSV特性からカテゴリ名・テキスト・カラーを自動決定"""
    
    # 明度ランク付け (V値で判定)
    ranked = sorted(clusters.keys(), key=lambda c: clusters[c]['v'])
    dark_c, mid_c, bright_c = ranked[0], ranked[1], ranked[2]
    
    # 色相でウォーム/クール判定 (H: 0=赤, 85=緑, 170=青 in 0-255 scale)
    def is_warm(c):
        h = clusters[c]['h']
        r = clusters[c]['r']
        return r > clusters[c]['b'] or h < 50  # 赤/オレンジ系
    
    categorized = {}
    
    for c in range(3):
        cl = clusters[c]
        v = cl['v']; s = cl['s']; h = cl['h']
        r = cl['r']; g = cl['g']; b = cl['b']
        warm = r > b
        saturated = s > 70
        
        # 特性判定
        if c == dark_c:
            # 最も暗い = ウォームライト系 → にぎわい・人物
            if warm:
                name = "にぎわいシーン"
                subtitle = "笑顔あふれる会場の熱気"
                close_msg = "次回もお楽しみに！"
                colors = {
                    'pop_sets': [
                        ("★ 楽しいね！", HOT, WHITE),
                        ("♡ 素敵な出会い", ORANGE, DARK),
                        ("◆ にぎわう会場", PURPLE, YELLOW),
                        ("▶ みんなの笑顔", HOT, WHITE),
                        ("♪ 活気満点！", ORANGE, DARK),
                        ("◎ いい雰囲気♡", PURPLE, WHITE),
                        ("★ 盛り上がり中", HOT, YELLOW),
                        ("♡ ありがとう！", ORANGE, WHITE),
                    ],
                    'bar_bg': (60,20,10), 'bar_fg': CREAM
                }
            else:
                name = "会場の雰囲気"
                subtitle = "第14回 会場の様子"
                close_msg = "第15回もお待ちしています♡"
                colors = {
                    'pop_sets': [
                        ("★ 会場いい感じ", TEAL, WHITE),
                        ("♡ 素敵な空間", (100,180,255), DARK),
                        ("◆ マルシェの朝", TEAL, YELLOW),
                        ("▶ 準備万端！", (100,180,255), WHITE),
                        ("♪ 始まるよ！", TEAL, WHITE),
                        ("◎ ワクワク♡", (100,180,255), DARK),
                    ],
                    'bar_bg': (10,30,50), 'bar_fg': WHITE
                }
        elif c == bright_c:
            # 最も明るい = ナチュラル系 → 作品・ブース展示
            name = "ブース展示"
            subtitle = "こだわりの作品たち"
            close_msg = "出店者募集中！ 11/1(日)"
            colors = {
                'pop_sets': [
                    ("◆ 素敵な作品！", PURPLE, WHITE),
                    ("★ ハンドメイド♡", HOT, YELLOW),
                    ("♡ こだわりの1品", PINK, DARK),
                    ("◎ 丁寧な仕事", PURPLE, CREAM),
                    ("♪ 心を込めて", HOT, WHITE),
                    ("▶ 出会いの品々", PINK, DARK),
                    ("★ アート感♡", PURPLE, WHITE),
                    ("♡ 欲しくなる！", HOT, YELLOW),
                ],
                'bar_bg': (40,10,30), 'bar_fg': CREAM
            }
        else:
            # 中間 = 彩度で分ける
            if saturated or warm:
                name = "出店者&作品"
                subtitle = "素敵なお店が並ぶ会場"
                close_msg = "次回 11/1(日) 開催！"
                colors = {
                    'pop_sets': [
                        ("★ かわいい！！", HOT, WHITE),
                        ("♡ 輝く才能", ORANGE, DARK),
                        ("◆ アートな世界", PURPLE, YELLOW),
                        ("▶ センス抜群！", HOT, WHITE),
                        ("♪ 目が離せない", ORANGE, WHITE),
                        ("◎ 選ぶのが楽しい", PURPLE, CREAM),
                        ("★ 一期一会♡", HOT, YELLOW),
                        ("♡ また買いたい！", ORANGE, DARK),
                    ],
                    'bar_bg': (40,20,5), 'bar_fg': CREAM
                }
            else:
                name = "スマイル集"
                subtitle = "第14回 笑顔の瞬間"
                close_msg = "また会いましょう♡"
                colors = {
                    'pop_sets': [
                        ("★ 笑顔最高！", HOT, WHITE),
                        ("♡ キラキラ♡", PINK, DARK),
                        ("◆ 幸せオーラ", PURPLE, YELLOW),
                        ("▶ いい顔してる", HOT, WHITE),
                        ("♪ 楽しいね！", PINK, WHITE),
                        ("◎ 最高の笑顔", PURPLE, CREAM),
                        ("★ ありがとう♡", HOT, YELLOW),
                        ("♡ また来てね！", PINK, DARK),
                    ],
                    'bar_bg': (40,10,30), 'bar_fg': WHITE
                }
        
        categorized[c] = {
            'name': name,
            'subtitle': subtitle,
            'close_msg': close_msg,
            'paths': cl['paths'],
            'colors': colors,
            'n': cl['n']
        }
    
    return categorized

# ─── フレーム生成関数 ─────────────────────────────────────────
def fill_frame(path):
    img = Image.open(path).convert('RGB')
    iw,ih = img.size
    scale = max(W/iw, H/ih)
    nw,nh = int(iw*scale), int(ih*scale)
    img = img.resize((nw,nh), Image.BILINEAR)
    x0,y0 = (nw-W)//2, (nh-H)//2
    return img.crop((x0,y0,x0+W,y0+H))

def make_photo_frame(path, fi, total_f, pop_idx, cat_info, zoom_in=True):
    base = fill_frame(path)
    t = fi / max(total_f-1, 1)
    scale = 1.0 + 0.03*(t if zoom_in else 1-t)
    nw,nh = int(W*scale), int(H*scale)
    z = base.resize((nw,nh), Image.BILINEAR)
    x0,y0 = (nw-W)//2, (nh-H)//2
    frame = z.crop((x0,y0,x0+W,y0+H))
    draw = ImageDraw.Draw(frame)
    
    # カテゴリ別ポップ文字
    pop_sets = cat_info['colors']['pop_sets']
    pop_text, tc, bc = pop_sets[pop_idx % len(pop_sets)]
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
    pm = {'bottom-right':(W-bw-m,H-bh-m-140),
          'top-left':(m,m+80),
          'bottom-left':(m,H-bh-m-140),
          'top-right':(W-bw-m,m+80)}
    bx,by = pm[pos]
    draw.rounded_rectangle([bx,by,bx+bw,by+bh], radius=22, fill=bc)
    cy = by+pad
    for ln,(lw,lh) in zip(lines,ld):
        draw.text((bx+pad+(tw-lw)//2,cy), ln, font=font, fill=tc)
        cy += lh+8
    
    # カテゴリ別下部バー
    bar_bg = cat_info['colors']['bar_bg']
    bar_fg = cat_info['colors']['bar_fg']
    font2 = load_font(36)
    draw.rectangle([0,H-84,W,H], fill=bar_bg)
    msg = f"ペンギンマルシェ 第14回｜{cat_info['subtitle']}"
    bb = draw.textbbox((0,0),msg,font=font2)
    if bb[2]-bb[0] > W-40:
        msg = cat_info['subtitle']
    bb = draw.textbbox((0,0),msg,font=font2)
    draw.text(((W-(bb[2]-bb[0]))//2,H-66), msg, font=font2, fill=bar_fg)
    return np.array(frame, dtype=np.uint8)

def make_announce_frame(img_path, fi, total_f, is_open, cat_info):
    img = Image.open(img_path).convert('RGB')
    iw,ih = img.size
    scale = min(W/iw, H/ih)
    nw,nh = int(iw*scale), int(ih*scale)
    img = img.resize((nw,nh), Image.BILINEAR)
    frame = Image.new('RGB',(W,H),DARK)
    frame.paste(img, ((W-nw)//2,(H-nh)//2))
    draw = ImageDraw.Draw(frame)
    
    if is_open:
        font = load_font(52)
        msg = f"第14回 ｜ {cat_info['name']}"
        bb = draw.textbbox((0,0),msg,font=font)
        if bb[2]-bb[0] > W-60:
            font = load_font(42)
            bb = draw.textbbox((0,0),msg,font=font)
        draw.text(((W-(bb[2]-bb[0]))//2,H-210), msg, font=font, fill=WHITE)
        font2 = load_font(38)
        sub = cat_info['subtitle']
        bb2 = draw.textbbox((0,0),sub,font=font2)
        draw.text(((W-(bb2[2]-bb2[0]))//2,H-150), sub, font=font2, fill=YELLOW)
    else:
        font = load_font(50)
        msg = "第15回 2026.11.1(日)"
        bb = draw.textbbox((0,0),msg,font=font)
        draw.text(((W-(bb[2]-bb[0]))//2,H-220), msg, font=font, fill=YELLOW)
        font2 = load_font(40)
        sub = cat_info['close_msg']
        bb2 = draw.textbbox((0,0),sub,font=font2)
        draw.text(((W-(bb2[2]-bb2[0]))//2,H-155), sub, font=font2, fill=WHITE)
    return np.array(frame, dtype=np.uint8)

# ─── リール生成 ────────────────────────────────────────────────
def make_reel(cat_id, cat_info):
    paths = cat_info['paths']
    n = len(paths)
    ann_f = int(FPS * ANN_SEC)
    
    # 30秒になるよう1枚あたりの表示時間を自動計算
    fade_total = (n + 1) * FADE_FRAMES  # 写真間 + 告知→写真 + 写真→告知
    photo_total_f = int(FPS * TARGET_SEC) - ann_f * 2 - fade_total
    img_f = max(int(FPS * 0.8), photo_total_f // n)  # 最低0.8秒
    actual_total_f = ann_f + n * img_f + fade_total + ann_f
    actual_sec = actual_total_f / FPS
    
    out_path = os.path.join(OUT_DIR, f'penguin_reel_v7_{cat_id}_{cat_info["name"]}.mp4')
    print(f'\n[Reel {cat_id}] {cat_info["name"]}: {n}枚 × {img_f/FPS:.1f}s = {actual_sec:.1f}秒')
    print(f'  出力: {out_path}')
    
    cmd = ['ffmpeg','-y','-f','rawvideo','-vcodec','rawvideo',
           '-s',f'{W}x{H}','-pix_fmt','rgb24','-r',str(FPS),'-i','pipe:0',
           '-c:v','libx264','-preset','fast','-crf','22',
           '-pix_fmt','yuv420p','-an', out_path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stderr=open(f'/tmp/ffmpeg_v7_{cat_id}.log','w'))
    
    fc = 0
    def wf(arr):
        nonlocal fc
        proc.stdin.write(arr.tobytes()); fc+=1
    
    # 告知オープン
    ann_open = [make_announce_frame(ANNOUNCE_IMG,i,ann_f,True,cat_info) for i in range(ann_f)]
    for f in ann_open: wf(f)
    prev = ann_open[-1]
    
    # 写真
    for pi, path in enumerate(paths):
        zi = (pi % 2 == 0)
        first = make_photo_frame(path,0,img_f,pi,cat_info,zi)
        for i in range(FADE_FRAMES):
            t = i/FADE_FRAMES; wf((prev*(1-t)+first*t).astype(np.uint8))
        for fi in range(img_f):
            wf(make_photo_frame(path,fi,img_f,pi,cat_info,zi))
        prev = make_photo_frame(path,img_f-1,img_f,pi,cat_info,zi)
        print(f'  [{pi+1}/{n}] {Path(path).name}')
    
    # 告知クローズ
    first_cl = make_announce_frame(ANNOUNCE_IMG,0,ann_f,False,cat_info)
    for i in range(FADE_FRAMES):
        t=i/FADE_FRAMES; wf((prev*(1-t)+first_cl*t).astype(np.uint8))
    for i in range(ann_f): wf(make_announce_frame(ANNOUNCE_IMG,i,ann_f,False,cat_info))
    
    proc.stdin.close(); proc.wait()
    sz = os.path.getsize(out_path)/1024/1024
    print(f'  完了: {sz:.1f}MB, {actual_sec:.1f}秒')
    return out_path

# ─── メイン ───────────────────────────────────────────────────
def main():
    print('=== STEP1: 画像カテゴリ自動分類 ===')
    clusters = collect_and_cluster()
    
    print('\n=== STEP2: カテゴリ自動命名 ===')
    categorized = auto_categorize(clusters)
    for c, info in categorized.items():
        print(f'[{c}] {info["name"]} ({info["n"]}枚): {info["subtitle"]}')
        for p in info['paths']:
            print(f'   {Path(p).name}')
    
    print('\n=== STEP3: リール生成 (×3本) ===')
    out_paths = []
    for c, info in sorted(categorized.items()):
        p = make_reel(c, info)
        out_paths.append(p)
    
    print('\n=== 完了サマリー ===')
    for p in out_paths:
        sz = os.path.getsize(p)/1024/1024
        print(f'  {Path(p).name}: {sz:.1f}MB')

if __name__ == '__main__':
    main()

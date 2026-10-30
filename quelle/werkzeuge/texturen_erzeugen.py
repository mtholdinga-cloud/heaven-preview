import numpy as np
from scipy import ndimage
from PIL import Image, ImageFilter

def fbm(h, w, base=4, octaves=6, seed=0, persistence=0.5):
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
    for o in range(octaves):
        n = base * 2 ** o
        gh, gw = max(2, int(n * h / max(h, w)) + 2), max(2, int(n * w / max(h, w)) + 2)
        g = rng.standard_normal((gh, gw)).astype(np.float32)
        z = ndimage.zoom(g, (h / (gh - 1), w / (gw - 1)), order=3)[:h, :w]
        if z.shape != (h, w):
            z = np.pad(z, ((0, h - z.shape[0]), (0, w - z.shape[1])), mode='edge')
        out += amp * z; tot += amp; amp *= persistence
    out /= tot
    return (out - out.mean()) / (out.std() + 1e-6)

def warp(field, dx, dy):
    h, w = field.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    return ndimage.map_coordinates(field, [yy + dy, xx + dx], order=1, mode='reflect')

def ridged(n, sharp):
    return np.clip(1 - np.abs(n), 0, 1) ** sharp

def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)

def mix(a, b, t):
    return a * (1 - t[..., None]) + b * t[..., None]

def gold_layer_old(h, w, seed):
    """metallic gold colour field with crackle + sparkle"""
    n1 = fbm(h, w, 40, 4, seed + 11, 0.6)
    n2 = fbm(h, w, 8, 4, seed + 12)
    dark = np.array([110, 72, 22], np.float32); mid = np.array([196, 150, 72], np.float32)
    light = np.array([246, 220, 150], np.float32)
    t = smooth(-1.2, 1.4, n1 * 0.7 + n2 * 0.5)
    c = mix(dark, mid, t)
    c = mix(c, light, smooth(0.9, 2.2, n1 + 0.3 * n2))
    rng = np.random.default_rng(seed + 99)
    sp = (rng.random((h, w)) > 0.9965).astype(np.float32)
    sp = ndimage.gaussian_filter(sp, 1.0) * 8
    c = c + np.clip(sp, 0, 1)[..., None] * 90
    return np.clip(c, 0, 255)

def gold_layer(h, w, seed):
    hgt = fbm(h, w, 110, 3, seed + 11, 0.55) + 0.6 * fbm(h, w, 30, 3, seed + 13)
    gy, gx = np.gradient(hgt)
    lam = np.clip(0.55 + (-gx * 0.7 - gy * 0.9) * 2.2, 0, 1)
    dark = np.array([92, 58, 16], np.float32); mid = np.array([190, 142, 64], np.float32)
    light = np.array([250, 226, 160], np.float32)
    c = mix(dark, mid, smooth(0.0, 0.6, lam))
    c = mix(c, light, smooth(0.6, 0.95, lam))
    rng = np.random.default_rng(seed + 99)
    sp = ndimage.gaussian_filter((rng.random((h, w)) > 0.997).astype(np.float32), 0.9) * 9
    return np.clip(c + np.clip(sp, 0, 1)[..., None] * 80, 0, 255)

def flow_veins(h, w, seed, freq, angle, sharp, warpamp, keep=0.0):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32) / max(h, w)
    d = xx * np.cos(angle) + yy * np.sin(angle)
    n = fbm(h, w, 2, 5, seed, 0.55) * warpamp
    v = ridged(np.sin((d * freq + n) * np.pi), sharp)
    gate = smooth(keep - 0.3, keep + 0.5, fbm(h, w, 2, 3, seed + 1))
    v = v * gate * smooth(-0.5, 0.8, fbm(h, w, 25, 3, seed + 2) + 0.7)
    return v

def teal_layer(h, w, seed):
    n = fbm(h, w, 3, 6, seed)
    wx, wy = fbm(h, w, 3, 4, seed + 1) * 40, fbm(h, w, 3, 4, seed + 2) * 40
    n2 = warp(fbm(h, w, 6, 6, seed + 3), wx, wy)
    deep = np.array([9, 70, 72], np.float32); base = np.array([24, 150, 146], np.float32)
    pale = np.array([120, 214, 206], np.float32)
    c = mix(deep, base, smooth(-1.6, 0.8, n))
    c = mix(c, pale, smooth(0.6, 2.4, n2) * 0.8)
    # dark crackle network
    for s, sh, k in [(10, 18, 0.8), (22, 24, 0.55), (45, 30, 0.35)]:
        cr = ridged(warp(fbm(h, w, s, 3, seed + s), wx * .5, wy * .5), sh)
        c = mix(c, np.array([4, 38, 40], np.float32), cr * k)
    return c

def white_layer(h, w, seed):
    n = fbm(h, w, 3, 6, seed)
    c = mix(np.array([232, 236, 234], np.float32), np.array([250, 251, 250], np.float32), smooth(-1.5, 1.5, n))
    for i, (fq, ang, sh, k, col) in enumerate([(3, .7, 140, .5, [140, 152, 152]), (5, .9, 220, .4, [110, 124, 124]), (9, .5, 320, .3, [90, 120, 120]), (2, 2.3, 180, .35, [150, 160, 160])]):
        v = flow_veins(h, w, seed + 20 + i, fq, ang, sh, 1.6)
        c = mix(c, np.array(col, np.float32), v * k)
    return c

def gold_veins(h, w, seed, count_scale=3, sharp=26, width=1.0):
    wx, wy = fbm(h, w, 2, 4, seed + 7) * 90, fbm(h, w, 2, 4, seed + 8) * 90
    base = warp(fbm(h, w, count_scale, 4, seed + 30), wx, wy)
    v = ridged(base, sharp / width)
    rough = fbm(h, w, 60, 3, seed + 31)
    v = np.clip(v * 1.6 + rough * 0.25 * v, 0, 1)
    return smooth(0.35, 0.7, v)

def emboss_shadow(mask, img, strength=0.35, dx=3, dy=4):
    sh = ndimage.shift(ndimage.gaussian_filter(mask, 3), (dy, dx), order=1)
    return img * (1 - np.clip(sh - mask, 0, 1)[..., None] * strength)

def save(arr, path, q=82):
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(path, quality=q, optimize=True, progressive=True)

# ---------- 1) Weißer Marmor mit Türkis-Steinen und Goldrändern (wie Logo) ----------
def white_marble(h, w, seed, stones=True, stone_amount=0.0):
    c = white_layer(h, w, seed)
    gold = gold_layer(h, w, seed)
    if stones:
        wx, wy = fbm(h, w, 2, 4, seed + 40) * 120, fbm(h, w, 2, 4, seed + 41) * 120
        m = warp(fbm(h, w, 2, 5, seed + 42, 0.55), wx, wy)
        thr = 0.55 - stone_amount
        stone = smooth(thr, thr + 0.06, m)
        teal = teal_layer(h, w, seed + 50)
        c = emboss_shadow(stone, c, 0.25)
        c = mix(c, teal, stone)
        # Goldrand um die Steine, unregelmäßig breit, krakelig
        width = 0.05 + 0.09 * smooth(-1, 1.8, fbm(h, w, 5, 3, seed + 43))
        edge = np.exp(-((m - thr - 0.02) / width) ** 2)
        jag = fbm(h, w, 70, 3, seed + 44)
        edge = smooth(0.35, 0.55, edge + jag * 0.12)
    else:
        edge = np.zeros((h, w), np.float32)
    gv = smooth(0.3, 0.6, flow_veins(h, w, seed + 60, 2.2, 0.75, 22, 1.4, 0.2))
    gv2 = smooth(0.3, 0.6, flow_veins(h, w, seed + 61, 4, 0.55, 60, 1.8, 0.5)) * 0.9
    gmask = np.clip(np.maximum(edge, np.maximum(gv, gv2)), 0, 1)
    c = emboss_shadow(gmask, c, 0.3, 2, 3)
    c = mix(c, gold, gmask)
    return c

H, W = 1100, 1700
save(white_marble(H, W, 1, True, 0.0), 'tex_white_hero.jpg')       # viel Stein
save(white_marble(1200, 1600, 7, True, -0.25), 'tex_white_soft.jpg')  # weniger Stein, ruhiger
# ---------- 2) Türkis-Marmor (Platten, Schriftfüllung) ----------
t = teal_layer(1000, 1000, 21)
gv = gold_veins(1000, 1000, 21, 3, 40)
t = mix(emboss_shadow(gv, t, .35), gold_layer(1000, 1000, 21), gv)
save(t, 'tex_teal.jpg')
# ---------- 3) Schwarzer Marmor mit Glutadern (Seven / Hölle) ----------
h, w = 1100, 1700
n = fbm(h, w, 3, 6, 61)
c = mix(np.array([10, 6, 6], np.float32), np.array([34, 20, 18], np.float32), smooth(-1.5, 1.8, n))
wx, wy = fbm(h, w, 2, 4, 62) * 90, fbm(h, w, 2, 4, 63) * 90
for s, sh, k in [(5, 70, .35), (11, 110, .25)]:
    v = ridged(warp(fbm(h, w, s, 4, 64 + s), wx, wy), sh)
    c = mix(c, np.array([70, 52, 48], np.float32), v * k)
vein = np.maximum(gold_veins(h, w, 70, 2, 26), gold_veins(h, w, 71, 4, 50) * .8)
glow = ndimage.gaussian_filter(vein, 9)
heat = smooth(-1, 1.5, fbm(h, w, 30, 3, 72))
lava = mix(np.array([170, 30, 8], np.float32), np.array([255, 170, 70], np.float32), heat)
c = c + glow[..., None] * np.array([150, 40, 10], np.float32) * 0.9
c = mix(c, lava, vein)
save(c, 'tex_hell.jpg')
# ---------- 4) Wolken-Sprite ----------
s = 256
yy, xx = np.mgrid[0:s, 0:s] / s - 0.5
r = np.sqrt(xx ** 2 + yy ** 2)
n = fbm(s, s, 4, 6, 81) * .5 + fbm(s, s, 8, 4, 82) * .3
a = np.clip((0.5 - r) * 2.2 + n * 0.28, 0, 1) ** 1.6
a = ndimage.gaussian_filter(a, 1.5)
shade = np.clip(0.86 + n * 0.08 - yy * 0.25, 0, 1)
rgb = np.stack([shade * 255, shade * 252, shade * 250], -1)
Image.fromarray(np.dstack([rgb, a * 255]).astype(np.uint8), 'RGBA').save('cloud.png', optimize=True)
print('ok')

"""Aufbereitung dunkler Handy-Videos: Einzelbilder ausrichten, stapeln (Rauschen weg), Tonwerte & Farben im Heaven-Look."""
import cv2, numpy as np, subprocess, sys, os, json

def frames(path, t0, t1, n, width=2560):
    out = []
    for k in range(n):
        t = t0 + (t1 - t0) * k / max(1, n - 1)
        cmd = ['ffmpeg', '-v', 'error', '-ss', f'{t:.3f}', '-i', path, '-frames:v', '1', '-vf', f'scale={width}:-2', '-f', 'image2pipe', '-vcodec', 'png', '-']
        buf = subprocess.run(cmd, capture_output=True).stdout
        img = cv2.imdecode(np.frombuffer(buf, np.uint8), cv2.IMREAD_COLOR)
        if img is not None: out.append(img)
    return out

def sharpness(img):
    g = cv2.cvtColor(cv2.resize(img, None, fx=.5, fy=.5), cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(g, cv2.CV_64F).var()

def align_stack(imgs, keep=8):
    imgs = sorted(imgs, key=sharpness, reverse=True)
    ref = imgs[0]; rg = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)
    orb = cv2.ORB_create(6000); kr, dr = orb.detectAndCompute(rg, None)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    acc = [ref.astype(np.float32)]
    for im in imgs[1:keep]:
        g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY); k, d = orb.detectAndCompute(g, None)
        if d is None: continue
        m = sorted(bf.match(d, dr), key=lambda x: x.distance)[:800]
        if len(m) < 60: continue
        src = np.float32([k[x.queryIdx].pt for x in m]); dst = np.float32([kr[x.trainIdx].pt for x in m])
        H, inl = cv2.findHomography(src, dst, cv2.RANSAC, 3.0)
        if H is None or inl.sum() < 50: continue
        w = cv2.warpPerspective(im, H, (ref.shape[1], ref.shape[0]), borderMode=cv2.BORDER_REFLECT)
        # nur übernehmen, wenn die Ausrichtung wirklich passt
        if np.mean(np.abs(cv2.cvtColor(w, cv2.COLOR_BGR2GRAY).astype(np.float32) - rg)) > 18: continue
        acc.append(w.astype(np.float32))
    st = np.median(np.stack(acc), axis=0) if len(acc) >= 3 else np.mean(np.stack(acc), axis=0)
    return st.astype(np.uint8), len(acc)

def grade(img, exposure=1.0, shadows=0.35, sat=1.18, warm=0.04, strength_denoise=5):
    img = cv2.fastNlMeansDenoisingColored(img, None, strength_denoise, strength_denoise, 7, 21)
    f = img.astype(np.float32) / 255
    # Graubalance sanft
    means = f.reshape(-1, 3).mean(0); g = means.mean()
    f = f * (0.65 + 0.35 * (g / (means + 1e-6)))
    f = np.clip(f * exposure, 0, 1)
    # Schatten anheben (Kurve), Lichter schützen
    f = f + shadows * f * (1 - f) ** 2 * 2.2
    # lokaler Kontrast über CLAHE auf L
    lab = cv2.cvtColor((np.clip(f, 0, 1) * 255).astype(np.uint8), cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l = cv2.createCLAHE(clipLimit=1.6, tileGridSize=(8, 8)).apply(l)
    f = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR).astype(np.float32) / 255
    # Sättigung
    hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV); hsv[..., 1] = np.clip(hsv[..., 1] * sat, 0, 1); f = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    # Split-Toning: Schatten türkis, Lichter gold
    lum = f.mean(2, keepdims=True)
    teal = np.array([0.55, 0.45, 0.10], np.float32)  # BGR-Verschiebung Richtung Türkis
    gold = np.array([-0.35, 0.10, 0.45], np.float32)
    f = f + (1 - lum) ** 3 * teal * 0.09 + lum ** 2 * gold * warm
    # Schärfen
    blur = cv2.GaussianBlur(f, (0, 0), 1.6); f = f + (f - blur) * 0.55
    # Vignette
    h, w = f.shape[:2]; yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    f = f * (1 - 0.28 * np.clip(r - 0.55, 0, 1) ** 1.5)[..., None]
    return (np.clip(f, 0, 1) * 255).astype(np.uint8)

def crop(img, aspect, cx=.5, cy=.5, zoom=1.0):
    h, w = img.shape[:2]
    if w / h > aspect: ch = h / zoom; cw = ch * aspect
    else: cw = w / zoom; ch = cw / aspect
    x = int(np.clip(cx * w - cw / 2, 0, w - cw)); y = int(np.clip(cy * h - ch / 2, 0, h - ch))
    return img[y:y + int(ch), x:x + int(cw)]

if __name__ == '__main__':
    job = json.loads(sys.argv[1])
    fr = frames(job['src'], job['t0'], job['t1'], job.get('n', 10), job.get('width', 2560))
    st, used = align_stack(fr, job.get('keep', 8))
    if job.get('rotate'): st = cv2.rotate(st, {90: cv2.ROTATE_90_CLOCKWISE, -90: cv2.ROTATE_90_COUNTERCLOCKWISE}[job['rotate']])
    out = grade(st, job.get('exposure', 1.0), job.get('shadows', .35), job.get('sat', 1.18), job.get('warm', .04), job.get('dn', 5))
    if 'aspect' in job: out = crop(out, job['aspect'], job.get('cx', .5), job.get('cy', .5), job.get('zoom', 1))
    if 'outw' in job:
        h, w = out.shape[:2]; out = cv2.resize(out, (job['outw'], int(h * job['outw'] / w)), interpolation=cv2.INTER_AREA)
    cv2.imwrite(job['out'], out, [cv2.IMWRITE_JPEG_QUALITY, 84])
    print(job['out'], 'gestapelt:', used, 'Bild(er)', out.shape)

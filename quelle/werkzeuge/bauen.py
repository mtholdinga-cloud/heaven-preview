import os; os.makedirs('../../build',exist_ok=True)
import base64
s=open('../seite.html').read()
m={'__TEX_WHITE_HERO__':'tex_white_hero.jpg','__TEX_WHITE_SOFT__':'tex_white_soft.jpg','__TEX_TEAL__':'tex_teal.jpg','__TEX_GOLD__':'tex_gold.jpg','__CLOUD__':'cloud.png'}
imgs={'__IMG_TRESEN__':'tresen.jpg','__IMG_LOUNGE__':'lounge.jpg','__IMG_DRINK__':'drink.jpg','__IMG_SOFT__':'softdrinks.jpg','__IMG_SCHORLE__':'schorle.jpg'}
for k,f in imgs.items():
    s=s.replace(k,'data:image/jpeg;base64,'+base64.b64encode(open('../texturen/'+f if f.startswith(('tex_','cloud')) else '../fotos/'+f,'rb').read()).decode())
for k,f in m.items():
    mime='image/png' if f.endswith('png') else 'image/jpeg'
    s=s.replace(k,f'"data:{mime};base64,'+base64.b64encode(open('../texturen/'+f if f.startswith(('tex_','cloud')) else '../fotos/'+f,'rb').read()).decode()+'"')
F='../../node_modules/@fontsource/'
faces=[('Cinzel','cinzel',w,'normal') for w in (600,700,800)]+[('Cormorant Garamond','cormorant-garamond',w,'normal') for w in (500,600)]+[('Cormorant Garamond','cormorant-garamond',600,'italic')]+[('Jost','jost',w,'normal') for w in (400,500,600)]+[('Pinyon Script','pinyon-script',400,'normal')]
css=''
for fam,pk,w,st in faces:
    d=base64.b64encode(open(f'{F}{pk}/files/{pk}-latin-{w}-{st}.woff2','rb').read()).decode()
    css+=f"@font-face{{font-family:'{fam}';font-style:{st};font-weight:{w};font-display:swap;src:url(data:font/woff2;base64,{d}) format('woff2')}}\n"
s=s.replace('__FONTFACES__',css)
open('../../build/heaven-bar.html','w').write(s); print(len(s)//1024,'KB')

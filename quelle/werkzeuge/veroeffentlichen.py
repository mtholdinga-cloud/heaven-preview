# Baut deploy/index.html aus heaven-bar.html mit dem bestehenden NFC-Schlüssel
import hashlib,re,os
key=os.environ['NFC_KEY']
h=hashlib.sha256(key.encode()).hexdigest()
body=open('../../build/heaven-bar.html').read()
title=re.search(r'<title>.*?</title>',body).group(0)
body=body.replace(title,'',1).replace('<meta name="claude:viewport-fit-sides" content="cover">\n','',1)
gate='''<script>
/* Testzugang: Seite nur mit Schlüssel aus dem NFC-Chip (?k=...). Kein echter Passwortschutz. */
(function(){
  var H="%s", K="heaven-test-key";
  function sha(t){return crypto.subtle.digest("SHA-256",new TextEncoder().encode(t)).then(function(b){return Array.from(new Uint8Array(b)).map(function(x){return x.toString(16).padStart(2,"0")}).join("")})}
  var u=new URL(location.href), k=u.searchParams.get("k"), stored=null;
  try{stored=localStorage.getItem(K)}catch(e){}
  document.documentElement.style.visibility="hidden";
  sha(k||stored||"").then(function(x){
    if(x===H){
      try{localStorage.setItem(K,k||stored)}catch(e){}
      if(k){u.searchParams.delete("k");history.replaceState(null,"",u.pathname+u.search+u.hash)}
      document.documentElement.style.visibility="";
    }else{
      var deny=function(){document.body.innerHTML='<div style="min-height:100vh;display:grid;place-items:center;background:#052A2C;color:#F2D892;font-family:Georgia,serif;text-align:center;padding:24px"><div><p style="font-size:28px;letter-spacing:.1em;margin:0 0 12px">HEAVEN BAR</p><p style="color:#CFE3E0;font-size:18px;margin:0">Diese Testseite ist nur über den NFC-Chip erreichbar.</p></div></div>';document.documentElement.style.visibility="";};
      if(document.body)deny();else document.addEventListener("DOMContentLoaded",deny);
    }
  });
})();
</script>''' % h
html='''<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="robots" content="noindex,nofollow,noarchive">
<meta name="theme-color" content="#052A2C">
%s
<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0}img{max-width:100%%}[hidden]{display:none!important}</style>
%s
</head>
<body>
%s
</body>
</html>
''' % (title,gate,body)
open('../../index.html','w').write(html)
print('deploy ok',len(html)//1024,'KB')

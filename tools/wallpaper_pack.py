from pathlib import Path
from PIL import Image,ImageOps
import csv,hashlib,random,re,shutil

OUT=Path('output'); SIZE=(2560,1440)
ROOT=Path('sources')
repos={
 'ml4w':'https://github.com/mylinuxforwork/wallpaper',
 'sayimburak':'https://github.com/sayimburak/wallpapers',
 'usman':'https://github.com/usman-369/wallpapers',
 'michael':'https://github.com/michaelScopic/Wallpapers',
 'kitsunebishi':'https://github.com/kitsunebishi/Wallpapers',
 '0xl30':'https://github.com/0xl30/4k-wallpapers',
}
keys={
 'Nature':['nature','scenery','landscape','mountain','forest','ocean','beach','lake','river','sunset','snow'],
 'Cars':['car','cars','automotive','vehicle','mustang','porsche','ferrari','lamborghini'],
 'Movies_Games_Characters':['character','characters','movie','movies','game','gaming','anime','hero','cyberpunk'],
 'Space':['space','astronaut','galaxy','cosmic','nebula','planet','moon'],
}
quotas={'Nature':200,'Cars':90,'Movies_Games_Characters':90,'Space':50,'Other':70}

def cat(p):
 s=str(p).lower()
 for c,ws in keys.items():
  if any(w in s for w in ws): return c
 return 'Other'

def ok(im):
 w,h=im.size
 return w>=1600 and h>=900 and w/h>=1.25

def main():
 if OUT.exists(): shutil.rmtree(OUT)
 OUT.mkdir()
 candidates=[]
 for d in ROOT.iterdir():
  if not d.is_dir(): continue
  src=d.name
  for p in d.rglob('*'):
   if p.suffix.lower() not in {'.jpg','.jpeg','.png','.webp'}: continue
   low=str(p).lower()
   if any(x in low for x in ['thumb','preview','.git/']): continue
   try:
    with Image.open(p) as im:
     if ok(im): candidates.append((cat(p),src,p,im.size))
   except: pass
 random.Random(20260912).shuffle(candidates)
 selected=[]; used=set(); counts={k:0 for k in quotas}
 for c,src,p,sz in candidates:
  if counts[c]>=quotas[c]: continue
  try:
   with Image.open(p) as im:
    im=ImageOps.exif_transpose(im).convert('RGB')
    w=ImageOps.fit(im,SIZE,method=Image.Resampling.LANCZOS)
    digest=hashlib.sha1(w.resize((128,72)).tobytes()).hexdigest()
    if digest in used: continue
    used.add(digest); counts[c]+=1
    od=OUT/c; od.mkdir(exist_ok=True)
    name=f'{counts[c]:03d}_{src}_{re.sub(r"[^A-Za-z0-9._-]+","_",p.stem)[:70]}.jpg'
    dst=od/name
    w.save(dst,'JPEG',quality=88,optimize=True,progressive=True)
    selected.append([c,str(dst.relative_to(OUT)),src,repos[src],str(p.relative_to(ROOT/src)),sz[0],sz[1],2560,1440])
  except: pass
 if len(selected)<500:
  chosen={x[4] for x in selected}
  for c,src,p,sz in candidates:
   if len(selected)>=500: break
   rel=str(p.relative_to(ROOT/src))
   if rel in chosen: continue
   try:
    with Image.open(p) as im:
     im=ImageOps.exif_transpose(im).convert('RGB')
     w=ImageOps.fit(im,SIZE,method=Image.Resampling.LANCZOS)
     digest=hashlib.sha1(w.resize((128,72)).tobytes()).hexdigest()
     if digest in used: continue
     used.add(digest); counts[c]+=1
     od=OUT/c; od.mkdir(exist_ok=True)
     name=f'{counts[c]:03d}_{src}_{re.sub(r"[^A-Za-z0-9._-]+","_",p.stem)[:70]}.jpg'
     dst=od/name; w.save(dst,'JPEG',quality=88,optimize=True,progressive=True)
     selected.append([c,str(dst.relative_to(OUT)),src,repos[src],rel,sz[0],sz[1],2560,1440]); chosen.add(rel)
   except: pass
 if len(selected)!=500: raise SystemExit(f'need 500, got {len(selected)}; candidates={len(candidates)}')
 with open(OUT/'SOURCES.csv','w',newline='',encoding='utf-8-sig') as f:
  cw=csv.writer(f); cw.writerow(['category','file','source_repo','source_url','source_path','src_w','src_h','out_w','out_h']); cw.writerows(selected)
 (OUT/'README.txt').write_text('500 real wallpapers downloaded from public internet wallpaper repositories. All files are exactly 2560x1440 and were crop-to-filled without stretching. See SOURCES.csv for source repositories and paths. For personal desktop use; individual upstream image rights remain with their respective creators.\n',encoding='utf-8')
 print('OK',len(selected),counts)
if __name__=='__main__': main()

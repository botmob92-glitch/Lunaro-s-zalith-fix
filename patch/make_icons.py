#!/usr/bin/env python3
"""Generates the Lunaro Client moon icon (original artwork) into patch/res. Needs Pillow."""
import math, pathlib
from PIL import Image, ImageDraw
O = pathlib.Path(__file__).resolve().parent / "res"
for d in ("drawable", "values", *[f"mipmap-{x}" for x in ("mdpi","hdpi","xhdpi","xxhdpi","xxxhdpi")]):
    (O / d).mkdir(parents=True, exist_ok=True)
A=(50.0,56.0,27.0); B=(63.0,46.0,23.0)
(ax,ay,ar),(bx,by,br)=A,B
d=math.hypot(bx-ax,by-ay)
a=(ar*ar-br*br+d*d)/(2*d); h=math.sqrt(ar*ar-a*a)
mx,my=ax+a*(bx-ax)/d, ay+a*(by-ay)/d
P1=(mx+h*(by-ay)/d, my-h*(bx-ax)/d); P2=(mx-h*(by-ay)/d, my+h*(bx-ax)/d)
def ang(c,p): return math.atan2(p[1]-c[1],p[0]-c[0])
def arc(c,r,a0,a1,n,ccw):
    if not ccw:
        while a1<=a0: a1+=2*math.pi
    else:
        while a1>=a0: a1-=2*math.pi
    return [(c[0]+r*math.cos(a0+(a1-a0)*i/n), c[1]+r*math.sin(a0+(a1-a0)*i/n)) for i in range(n+1)]
def inside(p,c,r): return math.hypot(p[0]-c[0],p[1]-c[1])<r
for ccw in (False,True):
    pts=arc((ax,ay),ar,ang((ax,ay),P1),ang((ax,ay),P2),90,ccw)
    if not inside(pts[45],(bx,by),br): break
for ccw2 in (False,True):
    pts2=arc((bx,by),br,ang((bx,by),P2),ang((bx,by),P1),90,ccw2)
    if inside(pts2[45],(ax,ay),ar): break
poly=pts+pts2
def path(p): return "M"+" L".join(f"{x:.2f},{y:.2f}" for x,y in p)+"Z"
stars=[((78,30),3.2),((86,50),2.0),((70,18),1.8)]
def circ(c,r,n=18): return [(c[0]+r*math.cos(2*math.pi*i/n),c[1]+r*math.sin(2*math.pi*i/n)) for i in range(n)]
HEAD='<vector xmlns:android="http://schemas.android.com/apk/res/android"\n    android:width="108dp"\n    android:height="108dp"\n    android:viewportWidth="108"\n    android:viewportHeight="108">\n'
def vec(star_color):
    s=HEAD+f'    <path android:fillColor="#FFFFFF" android:pathData="{path(poly)}"/>\n'
    for c,r in stars: s+=f'    <path android:fillColor="{star_color}" android:pathData="{path(circ(c,r))}"/>\n'
    return s+'</vector>\n'
(O/"drawable/ic_launcher_foreground.xml").write_text(vec("#7FD7F2"))
(O/"drawable/ic_launcher_monochrome.xml").write_text(vec("#FFFFFF"))
(O/"values/ic_launcher_background.xml").write_text('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <color name="ic_launcher_background">#1B1240</color>\n</resources>\n')
def render(size,round_):
    S=size*4; im=Image.new("RGBA",(S,S),(0,0,0,0)); bg=Image.new("RGBA",(S,S)); px=bg.load()
    for y in range(S):
        for x in range(S):
            t=(x+y)/(2*S); px[x,y]=(int(0x2A+(0x0D-0x2A)*t),int(0x1A+(0x0B-0x1A)*t),int(0x6E+(0x1A-0x6E)*t),255)
    m=Image.new("L",(S,S),0); dm=ImageDraw.Draw(m)
    if round_: dm.ellipse((0,0,S-1,S-1),fill=255)
    else: dm.rounded_rectangle((0,0,S-1,S-1),radius=int(S*0.22),fill=255)
    im.paste(bg,(0,0),m); f=S/108.0; dr=ImageDraw.Draw(im)
    dr.polygon([(x*f,y*f) for x,y in poly],fill=(255,255,255,255))
    for c,r in stars: dr.ellipse(((c[0]-r)*f,(c[1]-r)*f,(c[0]+r)*f,(c[1]+r)*f),fill=(127,215,242,255))
    return im.resize((size,size),Image.LANCZOS)
for dens,sz in dict(mdpi=48,hdpi=72,xhdpi=96,xxhdpi=144,xxxhdpi=192).items():
    render(sz,False).save(O/f"mipmap-{dens}/ic_launcher.webp","WEBP",quality=95)
    render(sz,True).save(O/f"mipmap-{dens}/ic_launcher_round.webp","WEBP",quality=95)
print("icons generated in", O)

import sys,re,os
pat=re.compile(rb'(?:[\x81-\x84\x88-\x9f\xe0-\xea][\x40-\x7e\x80-\xfc]|[\x20-\x7e\x0a])+')
def lvl1(b2):  # SJIS bytes for one DB char
    v=(b2[0]<<8)|b2[1]
    return 0x889f<=v<=0x9872
def kana(c): o=ord(c); return 0x3041<=o<=0x30f6 or o==0x30fc
def okpunct(c): o=ord(c); return 0x3000<=o<=0x303f or 0xff01<=o<=0xff5e or c in '…―‐～・♪★☆○●◎◇◆□■△▲▽▼※→←↑↓×÷＋－'
def score(b):
    i=0; n=0; good=0; k=0
    while i<len(b):
        if b[i]>=0x81:
            ch=b[i:i+2]; c=ch.decode('cp932','replace'); n+=1
            if kana(c): good+=1;k+=1
            elif okpunct(c) or lvl1(ch): good+=1
            i+=2
        else: i+=1
    return n,good,k
def scan(data):
    out=[]
    for m in pat.finditer(data):
        b=m.group(); e=m.end()
        if e>=len(data) or data[e]!=0: continue   # require NUL terminator
        # trim leading ascii junk
        try:t=b.decode('cp932')
        except: continue
        n,g,k=score(b)
        if n<2 or g<n*0.95: continue
        if k==0 and n<2: continue
        if k==0 and not (m.start()==0 or data[m.start()-1]==0): continue
        asc=len(t)-n
        if asc>n*2+4: continue
        out.append((m.start(),t))
    return out
if __name__=='__main__':
    outdir=sys.argv[1]
    for path in sys.argv[2:]:
        data=open(path,'rb').read()
        s=scan(data); name=os.path.basename(path)
        with open(os.path.join(outdir,name+'.txt'),'w',encoding='utf-8') as f:
            for o,t in s: f.write(f"{o:08x}\t" + t.replace('\n','\\n').replace('\r','\\r') + "\n")
        print(f"{name:24s} strings={len(s):>7} jpchars={sum(sum(ord(c)>0x7f for c in t) for _,t in s):>8}")

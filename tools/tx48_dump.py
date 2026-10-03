import re,struct,sys,os
from PIL import Image
def decode(d,o):
    t,w,h,hs,ps,do,ds=struct.unpack_from('<7I',d,o+4)
    pal=d[o+hs:o+hs+ps]; n=ps//4
    cols=[(pal[i*4],pal[i*4+1],pal[i*4+2],min(255,pal[i*4+3]*2)) for i in range(n)]
    px=d[o+do:o+do+ds]
    im=Image.new('RGBA',(w,h))
    data=[]
    if t==1:
        for b in px[:w*h]: data.append(cols[b] if b<n else (0,0,0,0))
    else:
        for b in px[:w*h//2]:
            data.append(cols[b&15]); data.append(cols[b>>4])
    data+= [(0,0,0,0)]*(w*h-len(data))
    im.putdata(data[:w*h]); return im,(t,w,h),o+do+ds
def unswizzle(im,bpp):
    # PSP swizzle: 16-byte x 8 row blocks
    w,h=im.size; src=list(im.getdata()); dst=[None]*(w*h)
    bw=16*8//bpp  # pixels per block row
    i=0
    for by in range(0,h,8):
        for bx in range(0,w,bw):
            for y in range(8):
                for x in range(bw):
                    if by+y<h and bx+x<w and i<len(src): dst[(by+y)*w+bx+x]=src[i]
                    i+=1
    out=Image.new('RGBA',(w,h)); out.putdata([p or (0,0,0,0) for p in dst]); return out
if __name__=='__main__':
    fn,outdir=sys.argv[1],sys.argv[2]; sw=len(sys.argv)>3
    d=open(fn,'rb').read(); base=os.path.basename(fn)
    for k,m in enumerate(re.finditer(b'TX48',d)):
        try:
            im,(t,w,h),_=decode(d,m.start())
            if w*h<256: continue
            if sw: im=unswizzle(im,8 if t==1 else 4)
            bg=Image.new('RGBA',im.size,(40,40,60,255)); bg.alpha_composite(im)
            bg.convert('RGB').save(os.path.join(outdir,f'{base}_{k:04d}_{m.start():08x}.png'))
        except Exception as e: print('err',k,e)

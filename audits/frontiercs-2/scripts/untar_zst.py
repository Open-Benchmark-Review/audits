# usage: python3 -I untar_zst.py <archive.tar.zst> <outdir>   (safe extract: no abs paths / .. )
import sys,tarfile,zstandard,io,os
src,out=sys.argv[1],sys.argv[2]
os.makedirs(out,exist_ok=True)
with open(src,'rb') as f:
    r=zstandard.ZstdDecompressor().stream_reader(f)
    with tarfile.open(fileobj=r,mode='r|') as t:
        for m in t:
            if m.name.startswith('/') or '..' in m.name.split('/') or not (m.isfile() or m.isdir()): continue
            t.extract(m,out)
print('ok',out)

"""Send one local image to either decision HTTP route using Python's standard library."""
import argparse
import base64
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--image',required=True)
    p.add_argument('--request')
    p.add_argument('--base-url',default='http://127.0.0.1:8080')
    p.add_argument('--endpoint',choices=['decision','systemone'],default='decision')
    args=p.parse_args()
    path=Path(args.image)
    mime={'.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp'}.get(path.suffix.lower())
    if mime is None:p.error('Use PNG/JPEG/WebP')
    if path.stat().st_size>4*1024*1024:p.error('Image file exceeds 4 MiB')
    req=json.loads(Path(args.request).read_text()) if args.request else dict(
        model='NeoHorse-Jev-4B',state='Look at the supplied image.',questions={
            'color':dict(type='choice',instructions='What is the dominant color?',criteria={'red':'red','blue':'blue','green':'green'})})
    req.setdefault('model','NeoHorse-Jev-4B')
    req['image']='data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode()
    headers={'Content-Type':'application/json'}
    if os.environ.get('NEOHORSE_API_KEY'):headers['Authorization']='Bearer '+os.environ['NEOHORSE_API_KEY']
    call=Request(args.base_url.rstrip('/')+'/v1/'+args.endpoint,
                 data=json.dumps(req,ensure_ascii=False).encode(),headers=headers,method='POST')
    with urlopen(call,timeout=120) as response:
        print(json.dumps(json.load(response),ensure_ascii=False,indent=2))

if __name__=='__main__':main()

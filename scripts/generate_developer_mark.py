#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
src=ROOT/'public/assets/branding/wasm_splash.png'
out=ROOT/'public/assets/branding/wasm_developer_mark.png'
img=Image.open(src).convert('RGBA'); w,h=img.size
crop=img.crop((round(.28*w),round(.72*h),round(.72*w),round(.93*h)))
crop.save(out,optimize=True)
print(out)

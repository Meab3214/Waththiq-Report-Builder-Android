#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'src/App.tsx'
s=APP.read_text(encoding='utf-8')

colors="""[{id:'emerald' as ThemeColor,name:'الزمردي',bg:'bg-emerald-600'},{id:'teal' as ThemeColor,name:'البترولي',bg:'bg-teal-600'},{id:'navy' as ThemeColor,name:'الكحلي',bg:'bg-blue-800'},{id:'burgundy' as ThemeColor,name:'العنابي',bg:'bg-rose-800'},{id:'gold' as ThemeColor,name:'الذهبي',bg:'bg-amber-600'},{id:'forest' as ThemeColor,name:'الأخضر الغابي',bg:'bg-green-800'}]"""
fonts="""[{id:'Cairo' as ArabicFont,name:'Cairo'},{id:'Tajawal' as ArabicFont,name:'Tajawal'},{id:'Almarai' as ArabicFont,name:'Almarai'},{id:'IBM Plex Sans Arabic' as ArabicFont,name:'IBM Plex Sans Arabic'}]"""

if 'themeColorOptions.map' in s:
    s=s.replace('themeColorOptions.map', f'{colors}.map')
if 'fontOptions.map' in s:
    s=s.replace('fontOptions.map', f'{fonts}.map')

APP.write_text(s,encoding='utf-8')
print('mobile v5 type references fixed')

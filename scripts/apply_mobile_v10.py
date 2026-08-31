#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'src/App.tsx'
CSS=ROOT/'src/index.css'
MODAL=ROOT/'src/components/Editor/StepEditorModal.tsx'

# Final mobile appearance popup: centered card, compact controls, no bottom-sheet behavior.
s=APP.read_text(encoding='utf-8')
s=s.replace("import { ReportData, TemplateId } from './types';", "import { ReportData, TemplateId, ThemeColor, ArabicFont } from './types';")
a=s.find('      {appearanceModalOpen && (')
b=s.find('      <StepEditorModal ',a)
if a<0 or b<0:
    raise SystemExit('v10: appearance modal block not found')
block=s[a:b]
block=block.replace(
    'className="fixed inset-0 z-[12000] bg-slate-950/70 flex items-center justify-center p-4"',
    'className="wasm-appearance-overlay fixed inset-0 z-[12000] bg-slate-950/70 flex items-center justify-center p-3"'
)
block=block.replace(
    'className="w-full max-w-md max-h-[calc(100dvh-120px)] overflow-y-auto bg-white rounded-3xl shadow-2xl border border-slate-200 p-5"',
    'className="wasm-appearance-dialog w-full max-w-sm overflow-hidden bg-white rounded-3xl shadow-2xl border border-slate-200 p-4"'
)
block=block.replace('<div className="grid grid-cols-1 gap-2">','<div className="grid grid-cols-2 gap-2">',1)
block=block.replace('min-h-[52px] rounded-2xl border px-4 text-right flex items-center justify-between',
                    'min-h-[48px] rounded-2xl border px-3 py-2 text-right flex flex-col items-start justify-center')
s=s[:a]+block+s[b:]
APP.write_text(s,encoding='utf-8')

# Final step-navigation hooks. Make replacements tolerant of source variants.
m=MODAL.read_text(encoding='utf-8')
if 'wasm-step-overlay' not in m:
    m=m.replace('className="fixed inset-0 z-[90]', 'className="wasm-step-overlay fixed inset-0 z-[90]',1)
if 'wasm-step-dialog' not in m:
    m=re.sub(r'className="bg-white w-full max-w-3xl ', 'className="wasm-step-dialog bg-white w-full max-w-3xl ',m,count=1)
if 'wasm-step-tabs' not in m:
    m=m.replace('className="flex items-center gap-1.5 overflow-x-auto no-scrollbar"',
                'className="wasm-step-tabs flex items-center gap-1.5 overflow-x-auto no-scrollbar"',1)
if 'wasm-step-footer' not in m:
    m=re.sub(r'className="(p-(?:2\.5|3) sm:p-4 bg-slate-50 border-t border-slate-200[^"]*)"',
             r'className="wasm-step-footer \1"',m,count=1)
if 'wasm-step-footer' not in m:
    raise SystemExit('v10: could not attach step footer hook')
MODAL.write_text(m,encoding='utf-8')

c=CSS.read_text(encoding='utf-8')
c += r'''

/* WASM v10 final phone geometry: controls always clear Android navigation. */
@media (max-width:640px){
  .wasm-step-overlay{
    position:fixed!important;
    inset:0 0 88px 0!important;
    padding:0!important;
    align-items:stretch!important;
  }
  .wasm-step-dialog{
    width:100%!important;
    max-width:100%!important;
    height:100%!important;
    max-height:100%!important;
    margin:0!important;
    border-radius:0!important;
  }
  .wasm-step-footer{
    position:sticky!important;
    bottom:0!important;
    z-index:150!important;
    background:#f8fafc!important;
    padding:10px 12px 14px!important;
    box-shadow:0 -8px 24px rgba(15,23,42,.12)!important;
  }
  .wasm-step-footer>button:first-child{display:none!important}
  .wasm-step-footer>div{
    width:100%!important;
    min-width:0!important;
    display:grid!important;
    grid-template-columns:minmax(0,1fr) minmax(0,1.85fr)!important;
    gap:10px!important;
  }
  .wasm-step-footer>div>button{
    width:100%!important;
    min-width:0!important;
    min-height:52px!important;
    height:auto!important;
    margin:0!important;
    padding:10px 8px!important;
    font-size:12px!important;
    line-height:1.25!important;
    white-space:normal!important;
    justify-content:center!important;
  }
  .wasm-step-footer>div>button:only-child{grid-column:1/-1!important}
  .wasm-appearance-overlay{
    position:fixed!important;
    inset:0 0 88px 0!important;
    padding:10px!important;
    align-items:center!important;
    justify-content:center!important;
    overflow:hidden!important;
  }
  .wasm-appearance-dialog{
    width:min(100%,390px)!important;
    max-height:100%!important;
    overflow:hidden!important;
    margin:0 auto!important;
  }
  .wasm-appearance-dialog .grid.grid-cols-3{gap:8px!important}
  .wasm-appearance-dialog .grid.grid-cols-3 button{min-height:60px!important}
}
/* Exact A4 serialization independent from phone viewport/zoom. */
.wasm-export-wrapper,.wasm-export-wrapper .a4-sheet,.wasm-export-clone{
  box-sizing:border-box!important;
  width:794px!important;
  height:1123px!important;
  min-width:794px!important;
  min-height:1123px!important;
  max-width:794px!important;
  max-height:1123px!important;
  transform:none!important;
  transform-origin:top left!important;
  margin:0!important;
  overflow:hidden!important;
  background:#fff!important;
}
'''
CSS.write_text(c,encoding='utf-8')

# Build must fail if any of the requested fixes was not actually injected.
checks={
  APP:['wasm-appearance-dialog','حفظ وتطبيق على التقرير','renderExactA4DataUrl','wasm-report-appearance'],
  MODAL:['wasm-step-overlay','wasm-step-dialog','wasm-step-footer'],
  CSS:['inset:0 0 88px 0','Exact A4 serialization independent']
}
for path,needles in checks.items():
    text=path.read_text(encoding='utf-8')
    for needle in needles:
        if needle not in text:
            raise SystemExit(f'v10 verification failed: {needle} missing in {path.name}')
print('mobile v10: popup + A4 export hooks + Android navigation clearance verified')

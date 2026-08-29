#!/usr/bin/env python3
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'src/App.tsx'
s=APP.read_text(encoding='utf-8')
# Remove optional draft state if a source variant happened to receive it.
s=re.sub(r"\n\s*const \[appearanceDraftColor[^\n]+\n\s*const \[appearanceDraftFont[^\n]+",'',s)
s=s.replace('setAppearanceDraftColor(reportData.themeColor);setAppearanceDraftFont(reportData.fontFamily);setAppearanceModalOpen(true);','setAppearanceModalOpen(true);')
a=s.find('      {appearanceModalOpen && (')
b=s.find('      <StepEditorModal ',a)
if a<0 or b<0: raise SystemExit('appearance modal mount not found')
appearance=r'''      {appearanceModalOpen && (
        <div className="fixed inset-0 z-[12000] bg-slate-950/70 flex items-center justify-center p-4" onClick={()=>setAppearanceModalOpen(false)} dir="rtl">
          <section className="w-full max-w-md max-h-[calc(100dvh-120px)] overflow-y-auto bg-white rounded-3xl shadow-2xl border border-slate-200 p-5" onClick={e=>e.stopPropagation()}>
            <div className="flex items-start justify-between gap-3 mb-5">
              <div><h3 className="text-lg font-black text-emerald-950">اللون والخط</h3><p className="text-xs text-slate-500 mt-1">اختر المظهر ثم اضغط حفظ وتطبيق</p></div>
              <button type="button" onClick={()=>setAppearanceModalOpen(false)} className="w-10 h-10 rounded-full bg-slate-100 text-slate-600 font-black">×</button>
            </div>
            <div className="mb-5">
              <div className="text-sm font-black text-slate-800 mb-3">لون التقرير</div>
              <div className="grid grid-cols-3 gap-3">
                {([
                  {id:'emerald',name:'زمردي',bg:'bg-emerald-600'},
                  {id:'teal',name:'فيروزي',bg:'bg-teal-600'},
                  {id:'navy',name:'أزرق',bg:'bg-blue-700'},
                  {id:'burgundy',name:'عنابي',bg:'bg-rose-700'},
                  {id:'gold',name:'ذهبي',bg:'bg-amber-600'},
                  {id:'forest',name:'أخضر',bg:'bg-green-700'}
                ] as const).map(opt=><button key={opt.id} type="button" onClick={()=>setReportData({...reportData,themeColor:opt.id as any})} className={`min-h-[74px] rounded-2xl border-2 flex flex-col items-center justify-center gap-2 ${reportData.themeColor===opt.id?'border-amber-400 ring-2 ring-amber-200 bg-amber-50':'border-slate-200 bg-white'}`}><span className={`w-9 h-9 rounded-xl ${opt.bg} border border-black/5`}></span><span className="text-[11px] font-black text-slate-700">{opt.name}</span></button>)}
              </div>
            </div>
            <div className="mb-5">
              <div className="text-sm font-black text-slate-800 mb-3">الخط العربي</div>
              <div className="grid grid-cols-1 gap-2">
                {([{id:'Cairo',name:'Cairo'},{id:'Tajawal',name:'Tajawal'},{id:'Almarai',name:'Almarai'},{id:'IBM Plex Sans Arabic',name:'IBM Plex Sans Arabic'},{id:'Noto Kufi Arabic',name:'Noto Kufi Arabic'}] as const).map(opt=><button key={opt.id} type="button" onClick={()=>setReportData({...reportData,fontFamily:opt.id as any})} className={`min-h-[52px] rounded-2xl border px-4 text-right flex items-center justify-between ${reportData.fontFamily===opt.id?'bg-emerald-900 text-white border-emerald-950':'bg-slate-50 text-slate-800 border-slate-200'}`} style={{fontFamily:opt.id}}><span className="font-bold">نموذج الخط العربي</span><span className="text-xs opacity-80">{opt.name}</span></button>)}
              </div>
            </div>
            <button type="button" onClick={()=>{handleSaveLocal();setAppearanceModalOpen(false);setSaveToast('تم حفظ اللون والخط وتطبيقهما على التقرير');setTimeout(()=>setSaveToast(''),2600);}} className="w-full min-h-[54px] rounded-2xl bg-emerald-900 text-white text-sm font-black shadow-lg">حفظ وتطبيق على التقرير</button>
          </section>
        </div>
      )}

'''
s=s[:a]+appearance+s[b:]
APP.write_text(s,encoding='utf-8')
print('v8 appearance modal finalized without source-dependent draft types')

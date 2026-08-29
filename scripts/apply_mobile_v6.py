#!/usr/bin/env python3
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'src/App.tsx'; CSS=ROOT/'src/index.css'; AI=ROOT/'src/components/Editor/AIEducationalAssistant.tsx'
s=APP.read_text(encoding='utf-8')
# Make appearance choices visibly affect the entire report surface, including templates with hard-coded font classes.
needle='<ReportRenderer data={reportData} />'
wrapped="""<div className={`wasm-report-appearance wasm-theme-${reportData.themeColor}`} style={{fontFamily: reportData.fontFamily}}><ReportRenderer data={reportData} /></div>"""
s=s.replace(needle,wrapped)
# The appearance sheet gets an explicit save action. Choices are already held in reportData; Save persists them locally.
s=s.replace('onClick={()=>setAppearanceModalOpen(false)} className="h-9 px-4 rounded-xl bg-emerald-900 text-white text-xs font-black">تم</button>', 'onClick={()=>{handleSaveLocal();setAppearanceModalOpen(false);setSaveToast(\'تم حفظ اللون والخط وتطبيقهما على التقرير\');setTimeout(()=>setSaveToast(\'\'),2600);}} className="h-9 px-4 rounded-xl bg-emerald-900 text-white text-xs font-black">حفظ وتطبيق</button>')
# Use five professional Arabic fonts in the appearance dialog regardless of legacy option count.
old='{fontOptions.map(opt=><button key={opt.id} type="button" onClick={()=>setReportData({...reportData,fontFamily:opt.id})}'
new="{([{id:'Cairo',name:'Cairo'},{id:'Tajawal',name:'Tajawal'},{id:'Almarai',name:'Almarai'},{id:'IBM Plex Sans Arabic',name:'IBM Plex Sans Arabic'},{id:'Noto Kufi Arabic',name:'Noto Kufi Arabic'}] as const).map(opt=><button key={opt.id} type=\"button\" onClick={()=>setReportData({...reportData,fontFamily:opt.id as any})}"
s=s.replace(old,new)
APP.write_text(s,encoding='utf-8')
# AI: cloud only, no fake local content. Point Android native bridge to the production backend configured in native v6.
ai=AI.read_text(encoding='utf-8')
ai=ai.replace('المساعد الذكي غير متصل بالخدمة السحابية الآمنة في هذا الإصدار. لن يطلب التطبيق أي مفتاح من المستخدم ولن يستخدم محتوى محليًا مزيفًا.','تعذر الوصول إلى خدمة Gemini السحابية الآن. لا يستخدم وَسْم أي محتوى محلي مزيف.')
AI.write_text(ai,encoding='utf-8')
c=CSS.read_text(encoding='utf-8')
c += r'''
/* WASM v6: report appearance must override template-local typography. */
.wasm-report-appearance,.wasm-report-appearance *{font-family:inherit!important}
.wasm-theme-emerald{--wasm-accent:#059669}.wasm-theme-teal{--wasm-accent:#0d9488}.wasm-theme-navy{--wasm-accent:#1d4ed8}.wasm-theme-burgundy{--wasm-accent:#be123c}.wasm-theme-gold{--wasm-accent:#b7791f}.wasm-theme-forest{--wasm-accent:#15803d}
.wasm-report-appearance .text-emerald-900,.wasm-report-appearance .text-emerald-800,.wasm-report-appearance .text-emerald-700{color:var(--wasm-accent)!important}
.wasm-report-appearance .bg-emerald-900,.wasm-report-appearance .bg-emerald-800,.wasm-report-appearance .bg-emerald-700{background-color:var(--wasm-accent)!important}
.wasm-report-appearance .border-emerald-900,.wasm-report-appearance .border-emerald-800,.wasm-report-appearance .border-emerald-700{border-color:var(--wasm-accent)!important}
/* Native export mode: exact unscaled A4 CSS page, detached from preview zoom. */
html.wasm-native-export .a4-sheet{transform:none!important;width:794px!important;height:1123px!important;min-width:794px!important;min-height:1123px!important;max-width:794px!important;max-height:1123px!important;margin:0!important;position:fixed!important;left:0!important;top:0!important;z-index:2147483000!important;display:block!important;visibility:visible!important;opacity:1!important;background:#fff!important;overflow:hidden!important}
'''
CSS.write_text(c,encoding='utf-8')
print('mobile v6: saved appearance + 5 Arabic fonts + exact A4 export surface')

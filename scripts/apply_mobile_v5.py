#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'src/App.tsx'
MODAL=ROOT/'src/components/Editor/StepEditorModal.tsx'
AI=ROOT/'src/components/Editor/AIEducationalAssistant.tsx'
CSS=ROOT/'src/index.css'

s=APP.read_text(encoding='utf-8')

# Native report export is performed by Android PrintDocumentAdapter/PdfRenderer.
if 'exportReport(options:' not in s:
    s=s.replace('  finishFile(options: { id: string }): Promise<{ uri: string }>;\n', '  finishFile(options: { id: string }): Promise<{ uri: string }>;\n  exportReport(options: { fileName: string; format: \'pdf\' | \'png\' }): Promise<{ uri: string }>;\n', 1)

start=s.index('  const saveNativeDataUrl = async')
end=s.index('  const templates:',start)
exports=r'''  const waitForUi = (ms = 120) => new Promise<void>((resolve) => window.setTimeout(resolve, ms));

  const withNativeReportVisible = async <T,>(action: () => Promise<T>): Promise<T> => {
    const previousTab = mobileTab;
    if (previousTab !== 'preview') {
      setMobileTab('preview');
      await waitForUi(180);
      await new Promise<void>((resolve) => requestAnimationFrame(() => requestAnimationFrame(() => resolve())));
    }
    document.documentElement.classList.add('wasm-native-export');
    try {
      if (document.fonts?.ready) await document.fonts.ready;
      const sheet = reportRef.current?.querySelector('.a4-sheet') as HTMLElement | null;
      if (!sheet) throw new Error('لم يتم العثور على صفحة التقرير A4');
      const imgs = Array.from(sheet.querySelectorAll('img')) as HTMLImageElement[];
      await Promise.all(imgs.map((img) => img.complete ? Promise.resolve() : new Promise<void>((resolve) => {
        const done=()=>resolve(); img.addEventListener('load',done,{once:true}); img.addEventListener('error',done,{once:true});
      })));
      await waitForUi(80);
      return await action();
    } finally {
      document.documentElement.classList.remove('wasm-native-export');
      if (previousTab !== 'preview') setMobileTab(previousTab);
    }
  };

  const handleExportPDF = async () => {
    setExportDropdownOpen(false); setIsExporting(true); setSaveToast('جاري إنشاء PDF A4 بواسطة Android...');
    const safeTitle=(reportData.title||'تقرير_وَسْم').trim().replace(/[/\\?%*:|"<>]/g,'_').replace(/\s+/g,'_');
    try {
      if (isNativeAndroid) {
        await withNativeReportVisible(() => WasmNative.exportReport({ fileName:`تقرير_${safeTitle}.pdf`, format:'pdf' }));
        setSaveToast('تم حفظ PDF بنجاح في Downloads/WASM');
      } else {
        window.print();
        setSaveToast('تم فتح نافذة الطباعة؛ اختر حفظ كـ PDF.');
      }
    } catch (err:any) {
      console.error('Native PDF export failed',err);
      setSaveToast(`تعذر إنشاء PDF: ${err?.message||'خطأ Android غير معروف'}`);
    } finally { setIsExporting(false); setTimeout(()=>setSaveToast(''),5000); }
  };

  const handleExportImage = async () => {
    setExportDropdownOpen(false); setIsExporting(true); setSaveToast('جاري إنشاء PNG بواسطة Android...');
    const safeTitle=(reportData.title||'تقرير_وَسْم').trim().replace(/[/\\?%*:|"<>]/g,'_').replace(/\s+/g,'_');
    try {
      if (isNativeAndroid) {
        await withNativeReportVisible(() => WasmNative.exportReport({ fileName:`تقرير_${safeTitle}.png`, format:'png' }));
        setSaveToast('تم حفظ PNG بنجاح في Downloads/WASM');
      } else {
        throw new Error('تصدير PNG مخصص لتطبيق Android');
      }
    } catch (err:any) {
      console.error('Native PNG export failed',err);
      setSaveToast(`تعذر إنشاء PNG: ${err?.message||'خطأ Android غير معروف'}`);
    } finally { setIsExporting(false); setTimeout(()=>setSaveToast(''),5000); }
  };

'''
s=s[:start]+exports+s[end:]

# Replace the mobile command bar entirely: no horizontal overflow for primary actions.
h0=s.index('      {/* Android phone-first command bar:')
h1=s.index('      {/* Toast Notification */}',h0)
header=r'''      {/* Android phone-first command center: fixed two-column controls, no hidden primary buttons */}
      <header className="no-print sticky top-0 z-40 w-full bg-white border-b border-slate-200 shadow-sm" style={{paddingTop:'env(safe-area-inset-top)'}}>
        <div className="px-2 pt-2 grid grid-cols-2 gap-2">
          <button type="button" onClick={()=>openStepModal(0)} className="wasm-mobile-command bg-emerald-900 text-white"><PenTool className="w-4 h-4 text-amber-300"/><span>تحرير البيانات</span></button>
          <button type="button" onClick={()=>setMobileTab(mobileTab==='preview'?'editor':'preview')} className="wasm-mobile-command bg-slate-100 text-slate-800 border border-slate-200">{mobileTab==='preview'?<PenTool className="w-4 h-4 text-emerald-700"/>:<Eye className="w-4 h-4 text-emerald-700"/>}<span>{mobileTab==='preview'?'العودة للتحرير':'معاينة التقرير'}</span></button>
          <button type="button" onClick={(e)=>{e.preventDefault();e.stopPropagation();setAppearanceModalOpen(true);}} className="wasm-mobile-command bg-amber-50 text-emerald-950 border border-amber-200"><Palette className="w-4 h-4 text-amber-700"/><span>اللون والخط</span></button>
          <button type="button" onClick={()=>setExportDropdownOpen(v=>!v)} disabled={isExporting} className="wasm-mobile-command bg-emerald-800 text-white disabled:opacity-60"><Download className="w-4 h-4 text-amber-300"/><span>{isExporting?'جاري التصدير...':'تصدير وطباعة'}</span></button>
        </div>
        <div className="px-2 py-2 flex items-center gap-2">
          <label className="flex-1 min-w-0 rounded-xl bg-slate-50 border border-slate-200 px-2 py-1.5">
            <span className="block text-[8px] font-bold text-slate-400 mb-0.5">قالب التقرير</span>
            <select value={reportData.templateId} onChange={(e)=>setReportData({...reportData,templateId:e.target.value as TemplateId})} className="w-full bg-transparent outline-none text-[10px] font-black text-slate-800">
              {templates.map(t=><option key={t.id} value={t.id}>{t.label}</option>)}
            </select>
          </label>
          <button type="button" onClick={handleSaveLocal} className="h-[46px] px-3 rounded-xl bg-slate-100 border border-slate-200 text-slate-800 text-[10px] font-black flex items-center justify-center gap-1.5 shrink-0"><Save className="w-4 h-4 text-emerald-700"/>حفظ</button>
        </div>
        {exportDropdownOpen&&<div className="fixed inset-x-2 top-[calc(env(safe-area-inset-top)+112px)] bg-white rounded-2xl shadow-2xl border border-slate-200 p-2 z-[9998]" dir="rtl">
          <button type="button" onClick={()=>void handlePrint()} className="w-full p-3 text-right rounded-xl active:bg-emerald-50 flex items-center gap-3"><Printer className="w-5 h-5 text-emerald-800"/><span><b className="block text-xs">طباعة A4 فورية</b><small className="text-[10px] text-slate-500">نافذة الطباعة الأصلية في Android</small></span></button>
          <button type="button" onClick={()=>void handleExportPDF()} className="w-full p-3 text-right rounded-xl active:bg-emerald-50 flex items-center gap-3 border-t border-slate-100"><Download className="w-5 h-5 text-emerald-800"/><span><b className="block text-xs">حفظ PDF A4</b><small className="text-[10px] text-slate-500">محرك Android الأصلي — بدون تحويل CSS</small></span></button>
          <button type="button" onClick={()=>void handleExportImage()} className="w-full p-3 text-right rounded-xl active:bg-blue-50 flex items-center gap-3 border-t border-slate-100"><FileImage className="w-5 h-5 text-blue-700"/><span><b className="block text-xs">حفظ PNG عالية الدقة</b><small className="text-[10px] text-slate-500">تُنشأ من صفحة PDF الأصلية داخل Android</small></span></button>
          <button type="button" onClick={()=>setExportDropdownOpen(false)} className="w-full mt-1 py-2 rounded-xl bg-slate-100 text-xs font-bold text-slate-600">إغلاق</button>
        </div>}
      </header>

'''
s=s[:h0]+header+s[h1:]

# Replace appearance sheet with a guaranteed touchable Android sheet.
modal_mount=s.find('      <StepEditorModal ')
a=s.rfind('      {appearanceModalOpen && (',0,modal_mount)
if a>=0:
    s=s[:a]+s[modal_mount:]
    modal_mount=s.find('      <StepEditorModal ')
appearance=r'''      {appearanceModalOpen && (
        <div className="fixed inset-0 z-[10000] bg-slate-950/65 flex items-end justify-center" onClick={()=>setAppearanceModalOpen(false)} dir="rtl">
          <section className="w-full bg-white rounded-t-3xl shadow-2xl p-4" style={{paddingBottom:'max(18px,env(safe-area-inset-bottom))'}} onClick={e=>e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4"><div><h3 className="text-sm font-black text-emerald-950">اللون والخط</h3><p className="text-[10px] text-slate-500">يطبق التغيير مباشرة على التقرير</p></div><button type="button" onClick={()=>setAppearanceModalOpen(false)} className="h-9 px-4 rounded-xl bg-emerald-900 text-white text-xs font-black">تم</button></div>
            <div className="mb-4"><div className="text-xs font-black text-slate-800 mb-2">لون التقرير</div><div className="grid grid-cols-6 gap-2">{themeColorOptions.map(opt=><button key={opt.id} type="button" onClick={()=>setReportData({...reportData,themeColor:opt.id})} aria-label={opt.name} className={`h-11 rounded-xl ${opt.bg} border-2 ${reportData.themeColor===opt.id?'border-slate-950 ring-2 ring-amber-300':'border-white'}`}/>)}</div></div>
            <div><div className="text-xs font-black text-slate-800 mb-2">الخط العربي</div><div className="grid grid-cols-2 gap-2">{fontOptions.map(opt=><button key={opt.id} type="button" onClick={()=>setReportData({...reportData,fontFamily:opt.id})} className={`min-h-11 rounded-xl border px-2 py-2 text-[11px] font-bold ${reportData.fontFamily===opt.id?'bg-emerald-900 text-white border-emerald-950':'bg-slate-50 text-slate-700 border-slate-200'}`} style={{fontFamily:opt.id}}>{opt.name}</button>)}</div></div>
          </section>
        </div>
      )}

'''
pos=s.find('      <StepEditorModal ')
s=s[:pos]+appearance+s[pos:]
APP.write_text(s,encoding='utf-8')

# Modal: compact step selector and a footer that always fits a phone viewport.
m=MODAL.read_text(encoding='utf-8')
m=m.replace('className="flex items-center gap-1.5 overflow-x-auto pb-1 pt-1 no-scrollbar border-t border-emerald-800/60"','className="wasm-step-tabs grid grid-cols-5 gap-1 pt-2 border-t border-emerald-800/60"',1)
m=m.replace('py-1.5 px-2.5 sm:px-3 rounded-xl text-[11px]','py-1.5 px-1 rounded-xl text-[9px]',1)
# next label is intentionally short; current next step is already visible in header progress.
m=re.sub(r'<span>التالي: \{stepsConfig\[currentStep \+ 1\]\?\.title\}</span>','<span>الخطوة التالية</span>',m)
m=m.replace('<span>السابق</span>','<span>السابق</span>',1)
MODAL.write_text(m,encoding='utf-8')

# AI UX: no API keys, no raw HTTP/content-type errors. Backend must be a real secured API.
ai=AI.read_text(encoding='utf-8')
ai=ai.replace("setMsg(e?.message||'تعذر الاتصال بخدمة Gemini السحابية');","setMsg('المساعد الذكي غير متصل بالخدمة السحابية الآمنة في هذا الإصدار. لن يطلب التطبيق أي مفتاح من المستخدم ولن يستخدم محتوى محليًا مزيفًا.');")
ai=ai.replace("setMsg(`تعذر الاتصال بالمساعد الحقيقي: ${e?.message||'خطأ اتصال'}`);","setMsg('المساعد الذكي غير متصل بالخدمة السحابية الآمنة في هذا الإصدار. لن يطلب التطبيق أي مفتاح من المستخدم ولن يستخدم محتوى محليًا مزيفًا.');")
AI.write_text(ai,encoding='utf-8')

c=CSS.read_text(encoding='utf-8')
c += r'''

/* WASM Android phone-first v5 */
html,body,#root{width:100%;max-width:100%;overflow-x:hidden;-webkit-text-size-adjust:100%;text-size-adjust:100%;}
.wasm-mobile-command{height:46px;min-width:0;border-radius:14px;font-size:11px;font-weight:900;display:flex;align-items:center;justify-content:center;gap:7px;white-space:nowrap;overflow:hidden;}
.wasm-mobile-command span{overflow:hidden;text-overflow:ellipsis;}
@media (max-width:640px){
  .wasm-step-dialog{width:100vw!important;max-width:100vw!important;height:100dvh!important;max-height:100dvh!important;border-radius:0!important;}
  .wasm-step-dialog input,.wasm-step-dialog textarea,.wasm-step-dialog select{font-size:13px!important;line-height:1.55!important;}
  .wasm-step-tabs button{min-width:0!important;width:100%!important;justify-content:center!important;padding-inline:2px!important;}
  .wasm-step-tabs button>span:last-child{display:none!important;}
  .wasm-step-footer{position:relative!important;z-index:5!important;padding:8px 10px max(10px,env(safe-area-inset-bottom))!important;}
  .wasm-step-footer>div{width:100%!important;display:flex!important;gap:8px!important;}
  .wasm-step-footer>div>button{height:46px!important;min-width:0!important;margin:0!important;padding:8px 10px!important;font-size:11px!important;line-height:1.2!important;justify-content:center!important;}
  .wasm-step-footer>div>button:first-child:not(:only-child){flex:0 0 31%!important;}
  .wasm-step-footer>div>button:last-child{flex:1 1 auto!important;}
  .wasm-step-footer>div>button:only-child{width:100%!important;flex:1 1 100%!important;}
}
@media print{
  @page{size:A4 portrait;margin:0;}
  html,body{margin:0!important;padding:0!important;background:#fff!important;width:210mm!important;height:297mm!important;overflow:hidden!important;}
  body *{visibility:hidden!important;}
  .a4-sheet,.a4-sheet *{visibility:visible!important;}
  .a4-sheet{display:block!important;position:absolute!important;left:0!important;top:0!important;width:210mm!important;height:297mm!important;margin:0!important;transform:none!important;box-shadow:none!important;overflow:hidden!important;}
}
'''
CSS.write_text(c,encoding='utf-8')
print('mobile v5 applied: fixed phone controls, appearance sheet, native export calls, compact modal')

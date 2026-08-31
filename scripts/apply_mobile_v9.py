#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'src/App.tsx'
CSS=ROOT/'src/index.css'
MODAL=ROOT/'src/components/Editor/StepEditorModal.tsx'
TYPES=ROOT/'src/types.ts'

t=TYPES.read_text(encoding='utf-8')
t=t.replace("export type ArabicFont = 'Cairo' | 'Tajawal' | 'Almarai' | 'IBM Plex Sans Arabic';",
            "export type ArabicFont = 'Cairo' | 'Tajawal' | 'Almarai' | 'IBM Plex Sans Arabic' | 'Noto Kufi Arabic';")
TYPES.write_text(t,encoding='utf-8')

s=APP.read_text(encoding='utf-8')
start=s.find('  const saveNativeDataUrl = async')
end=s.find('  const templates:', start)
if start < 0 or end < 0:
    raise SystemExit('v9: export region not found')
exports=r'''  const saveNativeDataUrl = async (fileName: string, mimeType: string, dataUrl: string) => {
    const comma=dataUrl.indexOf(',');
    if(comma<0) throw new Error('بيانات الملف غير صالحة');
    const base64=dataUrl.slice(comma+1);
    const started=await WasmNative.startFile({fileName,mimeType});
    const chunkSize=49152;
    for(let i=0;i<base64.length;i+=chunkSize){
      await WasmNative.appendFileChunk({id:started.id,chunk:base64.slice(i,i+chunkSize)});
    }
    return WasmNative.finishFile({id:started.id});
  };

  const buildExactA4Clone = async (): Promise<{host:HTMLDivElement,wrapper:HTMLElement}> => {
    const sourceWrapper=reportRef.current?.querySelector('.wasm-report-appearance') as HTMLElement|null;
    if(!sourceWrapper) throw new Error('لم يتم العثور على معاينة التقرير');
    const host=document.createElement('div');
    host.setAttribute('aria-hidden','true');
    host.style.cssText='position:absolute;left:-10000px;top:0;width:794px;height:1123px;overflow:hidden;pointer-events:none;background:#fff;';
    const wrapper=sourceWrapper.cloneNode(true) as HTMLElement;
    wrapper.classList.add('wasm-export-wrapper');
    wrapper.style.setProperty('display','block','important');
    wrapper.style.setProperty('visibility','visible','important');
    wrapper.style.setProperty('opacity','1','important');
    wrapper.style.setProperty('transform','none','important');
    wrapper.style.setProperty('position','relative','important');
    wrapper.style.setProperty('left','0','important');
    wrapper.style.setProperty('top','0','important');
    wrapper.style.setProperty('width','794px','important');
    wrapper.style.setProperty('height','1123px','important');
    wrapper.style.setProperty('margin','0','important');
    wrapper.style.setProperty('overflow','hidden','important');
    wrapper.style.setProperty('font-family',reportData.fontFamily,'important');
    const page=wrapper.querySelector('.a4-sheet') as HTMLElement|null;
    if(!page) throw new Error('لم يتم العثور على صفحة A4');
    page.classList.add('wasm-export-clone');
    for(const [key,value] of Object.entries({display:'block',visibility:'visible',opacity:'1',transform:'none',position:'relative',left:'0',top:'0',width:'794px',height:'1123px','min-width':'794px','min-height':'1123px','max-width':'794px','max-height':'1123px',margin:'0',overflow:'hidden',background:'#fff'})){
      page.style.setProperty(key,value,'important');
    }
    host.appendChild(wrapper);
    document.body.appendChild(host);
    if(document.fonts?.ready) await document.fonts.ready;
    const imgs=Array.from(wrapper.querySelectorAll('img')) as HTMLImageElement[];
    await Promise.all(imgs.map(img=>img.complete?Promise.resolve():new Promise<void>(resolve=>{
      const done=()=>resolve(); img.addEventListener('load',done,{once:true}); img.addEventListener('error',done,{once:true});
    })));
    await new Promise<void>(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve())));
    return {host,wrapper};
  };

  const renderExactA4DataUrl = async (format:'png'|'jpeg'): Promise<string> => {
    const {host,wrapper}=await buildExactA4Clone();
    try{
      const baseOptions={width:794,height:1123,pixelRatio:2.0,backgroundColor:'#ffffff',cacheBust:true};
      const render=async(skipFonts:boolean)=>format==='png'
        ? toPng(wrapper,{...baseOptions,skipFonts})
        : toJpeg(wrapper,{...baseOptions,skipFonts,quality:.96});
      let dataUrl:string;
      try{ dataUrl=await render(false); }
      catch(first){ console.warn('A4 font embedding retry',first); dataUrl=await render(true); }
      if(!dataUrl||dataUrl.length<15000) throw new Error('تعذر إنشاء صفحة A4 كاملة');
      return dataUrl;
    }finally{host.remove();}
  };

  const handleExportPDF=async()=>{
    setExportDropdownOpen(false);setIsExporting(true);setSaveToast('جاري إنشاء PDF A4 كامل...');
    const safeTitle=(reportData.title||'تقرير_وَسْم').trim().replace(/[/\\?%*:|"<>]/g,'_').replace(/\s+/g,'_');
    try{
      const jpeg=await renderExactA4DataUrl('jpeg');
      const pdf=new jsPDF({orientation:'portrait',unit:'mm',format:'a4',compress:true});
      pdf.addImage(jpeg,'JPEG',0,0,210,297,undefined,'FAST');
      const fileName=`تقرير_${safeTitle}.pdf`;
      if(isNativeAndroid) await saveNativeDataUrl(fileName,'application/pdf',pdf.output('datauristring'));
      else pdf.save(fileName);
      setSaveToast('تم حفظ PDF A4 كاملاً في Downloads/WASM');
    }catch(err:any){console.error('PDF A4 export failed',err);setSaveToast(`تعذر PDF: ${err?.message||'خطأ غير معروف'}`);}
    finally{setIsExporting(false);setTimeout(()=>setSaveToast(''),5000);}
  };

  const handleExportImage=async()=>{
    setExportDropdownOpen(false);setIsExporting(true);setSaveToast('جاري إنشاء PNG A4 كاملة...');
    const safeTitle=(reportData.title||'تقرير_وَسْم').trim().replace(/[/\\?%*:|"<>]/g,'_').replace(/\s+/g,'_');
    try{
      const png=await renderExactA4DataUrl('png');
      const fileName=`تقرير_${safeTitle}.png`;
      if(isNativeAndroid) await saveNativeDataUrl(fileName,'image/png',png);
      else{const a=document.createElement('a');a.download=fileName;a.href=png;document.body.appendChild(a);a.click();a.remove();}
      setSaveToast('تم حفظ PNG A4 كاملة في Downloads/WASM');
    }catch(err:any){console.error('PNG A4 export failed',err);setSaveToast(`تعذر PNG: ${err?.message||'خطأ غير معروف'}`);}
    finally{setIsExporting(false);setTimeout(()=>setSaveToast(''),5000);}
  };

'''
s=s[:start]+exports+s[end:]
s=s.replace('className="fixed inset-0 z-[12000] bg-slate-950/70 flex items-center justify-center p-4" onClick={()=>setAppearanceModalOpen(false)}',
            'className="wasm-appearance-overlay fixed inset-0 z-[12000] bg-slate-950/70 flex items-center justify-center p-4" onClick={()=>setAppearanceModalOpen(false)}')
s=s.replace("fontFamily:opt.id as any", "fontFamily:opt.id as ArabicFont")
s=s.replace("themeColor:opt.id as any", "themeColor:opt.id as ThemeColor")
APP.write_text(s,encoding='utf-8')

m=MODAL.read_text(encoding='utf-8')
m=m.replace('className="fixed inset-0 z-[90] bg-slate-950/75 backdrop-blur-sm flex items-center justify-center p-2 sm:p-4"',
            'className="wasm-step-overlay fixed inset-0 z-[90] bg-slate-950/75 backdrop-blur-sm flex items-center justify-center p-2 sm:p-4"',1)
m=m.replace('className="bg-white w-full max-w-3xl h-[calc(100dvh-env(safe-area-inset-top)-env(safe-area-inset-bottom)-12px)] rounded-3xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col text-right"',
            'className="wasm-step-dialog bg-white w-full max-w-3xl h-[calc(100dvh-env(safe-area-inset-top)-env(safe-area-inset-bottom)-12px)] rounded-3xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col text-right"',1)
m=m.replace('className="flex items-center gap-1.5 overflow-x-auto no-scrollbar"',
            'className="wasm-step-tabs flex items-center gap-1.5 overflow-x-auto no-scrollbar"',1)
MODAL.write_text(m,encoding='utf-8')

c=CSS.read_text(encoding='utf-8')
font_import="@import url('https://fonts.googleapis.com/css2?family=Almarai:wght@400;700;800&family=Cairo:wght@400;600;700;800&family=IBM+Plex+Sans+Arabic:wght@400;600;700&family=Noto+Kufi+Arabic:wght@400;600;700;800&family=Tajawal:wght@400;500;700;800&display=swap');\n"
if 'family=Noto+Kufi+Arabic' not in c:
    p=c.find('\n')+1
    c=c[:p]+font_import+c[p:]

c += r'''

/* WASM v9: complete report theme engine. */
.wasm-theme-emerald{--wasm-deep:#064e3b;--wasm-main:#047857;--wasm-mid:#10b981;--wasm-light:#6ee7b7;--wasm-soft:#ecfdf5;--wasm-border:#a7f3d0}
.wasm-theme-teal{--wasm-deep:#134e4a;--wasm-main:#0f766e;--wasm-mid:#14b8a6;--wasm-light:#5eead4;--wasm-soft:#f0fdfa;--wasm-border:#99f6e4}
.wasm-theme-navy{--wasm-deep:#172554;--wasm-main:#1e40af;--wasm-mid:#2563eb;--wasm-light:#93c5fd;--wasm-soft:#eff6ff;--wasm-border:#bfdbfe}
.wasm-theme-burgundy{--wasm-deep:#4c0519;--wasm-main:#9f1239;--wasm-mid:#e11d48;--wasm-light:#fda4af;--wasm-soft:#fff1f2;--wasm-border:#fecdd3}
.wasm-theme-gold{--wasm-deep:#78350f;--wasm-main:#b45309;--wasm-mid:#d97706;--wasm-light:#fcd34d;--wasm-soft:#fffbeb;--wasm-border:#fde68a}
.wasm-theme-forest{--wasm-deep:#14532d;--wasm-main:#166534;--wasm-mid:#16a34a;--wasm-light:#86efac;--wasm-soft:#f0fdf4;--wasm-border:#bbf7d0}
.wasm-report-appearance,.wasm-report-appearance *{font-family:inherit!important}
.wasm-report-appearance :is(.text-emerald-950,.text-teal-950,.text-green-950){color:var(--wasm-deep)!important}
.wasm-report-appearance :is(.text-emerald-900,.text-emerald-800,.text-teal-900,.text-teal-800,.text-green-900,.text-green-800){color:var(--wasm-main)!important}
.wasm-report-appearance :is(.text-emerald-700,.text-emerald-600,.text-emerald-500,.text-teal-700,.text-teal-600,.text-teal-500,.text-green-700,.text-green-600,.text-green-500){color:var(--wasm-mid)!important}
.wasm-report-appearance :is(.bg-emerald-950,.bg-teal-950,.bg-green-950){background-color:var(--wasm-deep)!important}
.wasm-report-appearance :is(.bg-emerald-900,.bg-emerald-800,.bg-teal-900,.bg-teal-800,.bg-green-900,.bg-green-800){background-color:var(--wasm-main)!important}
.wasm-report-appearance :is(.bg-emerald-700,.bg-emerald-600,.bg-emerald-500,.bg-teal-700,.bg-teal-600,.bg-teal-500,.bg-green-700,.bg-green-600,.bg-green-500){background-color:var(--wasm-mid)!important}
.wasm-report-appearance :is(.bg-emerald-400,.bg-emerald-300,.bg-teal-400,.bg-teal-300,.bg-green-400,.bg-green-300){background-color:var(--wasm-light)!important}
.wasm-report-appearance :is(.bg-emerald-200,.bg-emerald-100,.bg-emerald-50,.bg-teal-200,.bg-teal-100,.bg-teal-50,.bg-green-200,.bg-green-100,.bg-green-50){background-color:var(--wasm-soft)!important}
.wasm-report-appearance :is(.border-emerald-950,.border-emerald-900,.border-emerald-800,.border-emerald-700,.border-teal-950,.border-teal-900,.border-teal-800,.border-teal-700,.border-green-950,.border-green-900,.border-green-800,.border-green-700){border-color:var(--wasm-main)!important}
.wasm-report-appearance :is(.border-emerald-600,.border-emerald-500,.border-emerald-400,.border-emerald-300,.border-emerald-200,.border-emerald-100,.border-teal-600,.border-teal-500,.border-teal-400,.border-teal-300,.border-teal-200,.border-teal-100,.border-green-600,.border-green-500,.border-green-400,.border-green-300,.border-green-200,.border-green-100){border-color:var(--wasm-border)!important}
.wasm-report-appearance [class*="from-emerald-"],.wasm-report-appearance [class*="from-teal-"],.wasm-report-appearance [class*="from-green-"]{--tw-gradient-from:var(--wasm-deep) var(--tw-gradient-from-position)!important}
.wasm-report-appearance [class*="via-emerald-"],.wasm-report-appearance [class*="via-teal-"],.wasm-report-appearance [class*="via-green-"]{--tw-gradient-via:var(--wasm-main) var(--tw-gradient-via-position)!important}
.wasm-report-appearance [class*="to-emerald-"],.wasm-report-appearance [class*="to-teal-"],.wasm-report-appearance [class*="to-green-"]{--tw-gradient-to:var(--wasm-main) var(--tw-gradient-to-position)!important}

/* WASM v9: exact export surface. */
.wasm-export-wrapper{box-sizing:border-box!important;width:794px!important;height:1123px!important;transform:none!important;margin:0!important;overflow:hidden!important;background:#fff!important}
.wasm-export-wrapper .a4-sheet,.wasm-export-clone{box-sizing:border-box!important;width:794px!important;height:1123px!important;min-width:794px!important;min-height:1123px!important;max-width:794px!important;max-height:1123px!important;transform:none!important;margin:0!important;overflow:hidden!important;background:#fff!important}

/* WASM v9: hard clearance from Android gesture/home navigation. */
@media (max-width:640px){
  .wasm-step-overlay{top:0!important;right:0!important;left:0!important;bottom:72px!important;padding:0!important;align-items:stretch!important}
  .wasm-step-dialog{width:100%!important;max-width:100%!important;height:100%!important;max-height:100%!important;margin:0!important;border-radius:0!important}
  .wasm-step-tabs{display:grid!important;grid-template-columns:repeat(5,minmax(0,1fr))!important;overflow:visible!important;gap:4px!important}
  .wasm-step-tabs button{width:100%!important;min-width:0!important;padding:6px 2px!important;justify-content:center!important}
  .wasm-step-tabs button>span:last-child{display:none!important}
  .wasm-step-footer{position:sticky!important;bottom:0!important;z-index:100!important;background:#f8fafc!important;padding:10px 12px 14px!important;box-shadow:0 -6px 20px rgba(15,23,42,.10)!important}
  .wasm-step-footer>button:first-child{display:none!important}
  .wasm-step-footer>div{width:100%!important;display:grid!important;grid-template-columns:minmax(0,1fr) minmax(0,1.8fr)!important;gap:10px!important}
  .wasm-step-footer>div>button{min-height:50px!important;height:auto!important;width:100%!important;min-width:0!important;padding:10px 8px!important;font-size:12px!important;white-space:normal!important;line-height:1.25!important;justify-content:center!important}
  .wasm-step-footer>div>button:only-child{grid-column:1/-1!important}
  .wasm-appearance-overlay{top:0!important;right:0!important;left:0!important;bottom:72px!important;padding:12px!important}
}
'''
CSS.write_text(c,encoding='utf-8')
print('mobile v9: centered appearance modal + full theme engine + exact A4 export + Android nav clearance')

#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'src/App.tsx'
CSS=ROOT/'src/index.css'
MODAL=ROOT/'src/components/Editor/StepEditorModal.tsx'

s=APP.read_text(encoding='utf-8')

# Ensure browser-native image renderer import exists. It serializes the DOM instead of
# asking Android to draw the phone viewport, so the full 794x1123 A4 surface is exported.
if "from 'html-to-image'" not in s:
    # insert after React/import block using the first import line as anchor
    m=re.search(r"^(import .*?;\n)",s,re.M)
    if not m:
        raise SystemExit('cannot locate import block')
    s=s[:m.end()]+"import { toPng, toJpeg } from 'html-to-image';\n"+s[m.end():]

# Make sure chunked native file methods are declared in the Capacitor plugin interface.
if 'startFile(options:' not in s:
    s=s.replace("  exportReport(options: { fileName: string; format: 'pdf' | 'png' }): Promise<{ uri: string }>;\n",
                "  exportReport(options: { fileName: string; format: 'pdf' | 'png' }): Promise<{ uri: string }>;\n  startFile(options: { fileName: string; mimeType: string }): Promise<{ id: string }>;\n  appendFileChunk(options: { id: string; chunk: string }): Promise<void>;\n  finishFile(options: { id: string }): Promise<{ uri: string }>;\n")

# Replace the native phone-viewport capture with a browser-rendered exact A4 clone.
start=s.find('  const waitForUi =')
if start < 0:
    start=s.find('  const saveNativeDataUrl = async')
end=s.find('  const templates:',start)
if start < 0 or end < 0:
    raise SystemExit('export function region not found')

exports=r'''  const saveNativeDataUrl = async (fileName: string, mimeType: string, dataUrl: string) => {
    const comma=dataUrl.indexOf(',');
    if(comma<0) throw new Error('بيانات الملف غير صالحة');
    const base64=dataUrl.slice(comma+1);
    const started=await WasmNative.startFile({fileName,mimeType});
    const chunkSize=131072;
    for(let i=0;i<base64.length;i+=chunkSize){
      await WasmNative.appendFileChunk({id:started.id,chunk:base64.slice(i,i+chunkSize)});
    }
    return WasmNative.finishFile({id:started.id});
  };

  const buildExactA4Clone = async (): Promise<{host:HTMLDivElement,clone:HTMLElement}> => {
    const source=reportRef.current?.querySelector('.a4-sheet') as HTMLElement|null;
    if(!source) throw new Error('لم يتم العثور على صفحة A4');
    const host=document.createElement('div');
    host.setAttribute('aria-hidden','true');
    host.style.cssText='position:fixed;left:0;top:0;width:794px;height:1123px;overflow:hidden;pointer-events:none;z-index:-2147483000;background:#fff;';
    const clone=source.cloneNode(true) as HTMLElement;
    clone.classList.add('wasm-export-clone');
    clone.style.setProperty('display','block','important');
    clone.style.setProperty('visibility','visible','important');
    clone.style.setProperty('opacity','1','important');
    clone.style.setProperty('transform','none','important');
    clone.style.setProperty('position','relative','important');
    clone.style.setProperty('left','0','important');
    clone.style.setProperty('top','0','important');
    clone.style.setProperty('width','794px','important');
    clone.style.setProperty('height','1123px','important');
    clone.style.setProperty('min-width','794px','important');
    clone.style.setProperty('min-height','1123px','important');
    clone.style.setProperty('max-width','794px','important');
    clone.style.setProperty('max-height','1123px','important');
    clone.style.setProperty('margin','0','important');
    clone.style.setProperty('overflow','hidden','important');
    host.appendChild(clone);
    document.body.appendChild(host);
    if(document.fonts?.ready) await document.fonts.ready;
    const imgs=Array.from(clone.querySelectorAll('img')) as HTMLImageElement[];
    await Promise.all(imgs.map(img=>img.complete?Promise.resolve():new Promise<void>(resolve=>{
      const done=()=>resolve(); img.addEventListener('load',done,{once:true}); img.addEventListener('error',done,{once:true});
    })));
    await new Promise<void>(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve())));
    return {host,clone};
  };

  const renderExactA4DataUrl = async (format:'png'|'jpeg'): Promise<string> => {
    const {host,clone}=await buildExactA4Clone();
    try{
      const options={width:794,height:1123,pixelRatio:2.5,backgroundColor:'#ffffff',cacheBust:true,skipFonts:false};
      const dataUrl=format==='png'?await toPng(clone,options):await toJpeg(clone,{...options,quality:.96});
      if(!dataUrl||dataUrl.length<15000) throw new Error('تعذر إنشاء صورة A4 كاملة');
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
      const png=await renderExactA4DataUrl('png'); const fileName=`تقرير_${safeTitle}.png`;
      if(isNativeAndroid) await saveNativeDataUrl(fileName,'image/png',png);
      else{const a=document.createElement('a');a.download=fileName;a.href=png;document.body.appendChild(a);a.click();a.remove();}
      setSaveToast('تم حفظ PNG كاملة في Downloads/WASM');
    }catch(err:any){console.error('PNG A4 export failed',err);setSaveToast(`تعذر PNG: ${err?.message||'خطأ غير معروف'}`);}
    finally{setIsExporting(false);setTimeout(()=>setSaveToast(''),5000);}
  };

'''
s=s[:start]+exports+s[end:]

# Draft state: appearance changes only commit when Save & Apply is pressed.
state_marker=re.search(r"(const \[appearanceModalOpen,setAppearanceModalOpen\]=useState\(false\);)",s)
if not state_marker:
    state_marker=re.search(r"(const \[appearanceModalOpen,\s*setAppearanceModalOpen\]\s*=\s*useState\(false\);)",s)
if state_marker and 'appearanceDraftColor' not in s:
    insert=state_marker.group(1)+"\n  const [appearanceDraftColor,setAppearanceDraftColor]=useState<ThemeColor>(reportData.themeColor);\n  const [appearanceDraftFont,setAppearanceDraftFont]=useState<ArabicFont>(reportData.fontFamily);"
    s=s[:state_marker.start()]+insert+s[state_marker.end():]

# Every appearance button opens the modal with current values copied into draft state.
s=s.replace('setAppearanceModalOpen(true);','setAppearanceDraftColor(reportData.themeColor);setAppearanceDraftFont(reportData.fontFamily);setAppearanceModalOpen(true);')

# Replace the entire previous bottom sheet with a centered modal. No horizontal scrolling.
a=s.find('      {appearanceModalOpen && (')
b=s.find('      <StepEditorModal ',a)
if a<0 or b<0:
    raise SystemExit('appearance modal mount not found')
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
                {themeColorOptions.map(opt=><button key={opt.id} type="button" onClick={()=>setAppearanceDraftColor(opt.id)} className={`min-h-[74px] rounded-2xl border-2 flex flex-col items-center justify-center gap-2 ${appearanceDraftColor===opt.id?'border-amber-400 ring-2 ring-amber-200 bg-amber-50':'border-slate-200 bg-white'}`}><span className={`w-9 h-9 rounded-xl ${opt.bg} border border-black/5`}></span><span className="text-[11px] font-black text-slate-700">{opt.name}</span></button>)}
              </div>
            </div>
            <div className="mb-5">
              <div className="text-sm font-black text-slate-800 mb-3">الخط العربي</div>
              <div className="grid grid-cols-1 gap-2">
                {([{id:'Cairo',name:'Cairo'},{id:'Tajawal',name:'Tajawal'},{id:'Almarai',name:'Almarai'},{id:'IBM Plex Sans Arabic',name:'IBM Plex Sans Arabic'},{id:'Noto Kufi Arabic',name:'Noto Kufi Arabic'}] as const).map(opt=><button key={opt.id} type="button" onClick={()=>setAppearanceDraftFont(opt.id as ArabicFont)} className={`min-h-[52px] rounded-2xl border px-4 text-right flex items-center justify-between ${appearanceDraftFont===opt.id?'bg-emerald-900 text-white border-emerald-950':'bg-slate-50 text-slate-800 border-slate-200'}`} style={{fontFamily:opt.id}}><span className="font-bold">نموذج الخط العربي</span><span className="text-xs opacity-80">{opt.name}</span></button>)}
              </div>
            </div>
            <button type="button" onClick={()=>{const next={...reportData,themeColor:appearanceDraftColor,fontFamily:appearanceDraftFont};setReportData(next);localStorage.setItem('waththiq_report_data',JSON.stringify(next));setAppearanceModalOpen(false);setSaveToast('تم حفظ اللون والخط وتطبيقهما على التقرير');setTimeout(()=>setSaveToast(''),2600);}} className="w-full min-h-[54px] rounded-2xl bg-emerald-900 text-white text-sm font-black shadow-lg">حفظ وتطبيق على التقرير</button>
          </section>
        </div>
      )}

'''
s=s[:a]+appearance+s[b:]
APP.write_text(s,encoding='utf-8')

# Keep step navigation physically above Android gesture/home navigation even if env(safe-area-inset-bottom)=0.
m=MODAL.read_text(encoding='utf-8')
MODAL.write_text(m,encoding='utf-8')

c=CSS.read_text(encoding='utf-8')
c += r'''

/* WASM v8 Android navigation safety: do not depend solely on safe-area inside WebView. */
@media (max-width:640px){
  .wasm-step-dialog{height:calc(100dvh - 64px)!important;max-height:calc(100dvh - 64px)!important;margin-bottom:64px!important;border-radius:0!important;}
  .wasm-step-footer{position:sticky!important;bottom:0!important;z-index:50!important;background:#f8fafc!important;padding:10px 12px 14px!important;box-shadow:0 -6px 20px rgba(15,23,42,.08)!important;}
  .wasm-step-footer>div{width:100%!important;display:grid!important;grid-template-columns:minmax(0,1fr) minmax(0,1.8fr)!important;gap:10px!important;}
  .wasm-step-footer button{min-height:48px!important;min-width:0!important;width:100%!important;font-size:12px!important;white-space:normal!important;line-height:1.25!important;justify-content:center!important;}
}
/* Export clone is always exact A4 and never inherits preview transforms. */
.wasm-export-clone{box-sizing:border-box!important;width:794px!important;height:1123px!important;transform:none!important;margin:0!important;overflow:hidden!important;background:#fff!important;}
'''
CSS.write_text(c,encoding='utf-8')
print('mobile v8: centered appearance modal + Android-safe step footer + exact browser A4 export')

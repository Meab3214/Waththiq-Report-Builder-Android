#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'src/App.tsx'
MODAL=ROOT/'src/components/Editor/StepEditorModal.tsx'
AI=ROOT/'src/components/Editor/AIEducationalAssistant.tsx'
RENDERER=ROOT/'src/components/ReportRenderer.tsx'
CSS=ROOT/'src/index.css'

# ---------- App: replace html2canvas export with html-to-image ----------
s=APP.read_text(encoding='utf-8')
if "from 'html-to-image'" not in s:
    marker="import html2canvas from 'html2canvas';"
    s=s.replace(marker, "import { toPng, toJpeg } from 'html-to-image';\n"+marker, 1)

start=s.index('  const saveNativeDataUrl = async')
end=s.index('  const templates:', start)
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

  const renderReportDataUrl = async (format:'png'|'jpeg'): Promise<string> => {
    const source=reportRef.current?.querySelector('.a4-sheet') as HTMLElement|null;
    if(!source) throw new Error('لم يتم العثور على صفحة التقرير A4');

    // Use a full-size clone rendered by the browser itself. This deliberately avoids
    // html2canvas's CSS color parser, which rejects modern oklch()/color() values on Android.
    const host=document.createElement('div');
    host.setAttribute('aria-hidden','true');
    host.style.cssText='position:fixed;left:0;top:0;width:794px;height:1123px;overflow:hidden;z-index:-2147483647;pointer-events:none;background:#fff;';
    const clone=source.cloneNode(true) as HTMLElement;
    clone.style.setProperty('display','block','important');
    clone.style.setProperty('visibility','visible','important');
    clone.style.setProperty('opacity','1','important');
    clone.style.setProperty('transform','none','important');
    clone.style.setProperty('width','794px','important');
    clone.style.setProperty('height','1123px','important');
    clone.style.setProperty('margin','0','important');
    host.appendChild(clone); document.body.appendChild(host);
    try{
      if(document.fonts?.ready) await document.fonts.ready;
      const imgs=Array.from(clone.querySelectorAll('img')) as HTMLImageElement[];
      await Promise.all(imgs.map(img=>img.complete?Promise.resolve():new Promise<void>(resolve=>{img.onload=()=>resolve();img.onerror=()=>resolve();})));
      await new Promise<void>(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve())));
      const common={pixelRatio:2,backgroundColor:'#ffffff',width:794,height:1123,cacheBust:true,skipFonts:false};
      const url=format==='png'?await toPng(clone,common):await toJpeg(clone,{...common,quality:0.95});
      if(!url || url.length<10000) throw new Error('المحرك أعاد ملفًا فارغًا');
      return url;
    } finally {host.remove();}
  };

  const handleExportPDF=async()=>{
    setExportDropdownOpen(false);setIsExporting(true);setSaveToast('جاري إنشاء PDF A4...');
    const safeTitle=(reportData.title||'تقرير_وَسْم').trim().replace(/[/\\?%*:|"<>]/g,'_').replace(/\s+/g,'_');
    try{
      const jpeg=await renderReportDataUrl('jpeg');
      const pdf=new jsPDF({orientation:'portrait',unit:'mm',format:'a4',compress:true});
      pdf.addImage(jpeg,'JPEG',0,0,210,297,undefined,'FAST');
      const fileName=`تقرير_${safeTitle}.pdf`;
      if(isNativeAndroid) await saveNativeDataUrl(fileName,'application/pdf',pdf.output('datauristring'));
      else pdf.save(fileName);
      setSaveToast(isNativeAndroid?'تم حفظ PDF في التنزيلات / WASM':'تم تنزيل PDF بنجاح');
    }catch(err:any){console.error('PDF export failed',err);setSaveToast(`تعذر PDF: ${err?.message||'خطأ غير معروف'}`);}
    finally{setIsExporting(false);setTimeout(()=>setSaveToast(''),5000);}
  };

  const handleExportImage=async()=>{
    setExportDropdownOpen(false);setIsExporting(true);setSaveToast('جاري إنشاء PNG عالية الدقة...');
    const safeTitle=(reportData.title||'تقرير_وَسْم').trim().replace(/[/\\?%*:|"<>]/g,'_').replace(/\s+/g,'_');
    try{
      const png=await renderReportDataUrl('png');const fileName=`تقرير_${safeTitle}.png`;
      if(isNativeAndroid) await saveNativeDataUrl(fileName,'image/png',png);
      else{const a=document.createElement('a');a.download=fileName;a.href=png;document.body.appendChild(a);a.click();a.remove();}
      setSaveToast(isNativeAndroid?'تم حفظ PNG في التنزيلات / WASM':'تم تنزيل PNG بنجاح');
    }catch(err:any){console.error('PNG export failed',err);setSaveToast(`تعذر PNG: ${err?.message||'خطأ غير معروف'}`);}
    finally{setIsExporting(false);setTimeout(()=>setSaveToast(''),5000);}
  };

'''
s=s[:start]+exports+s[end:]

# Make appearance sheet unquestionably above all WebView layers and touchable.
s=s.replace('z-[95] bg-slate-950/70', 'z-[9999] bg-slate-950/70', 1)
s=s.replace('onClick={() => setAppearanceModalOpen(true)} className="h-10', 'onClick={(e)=>{e.preventDefault();e.stopPropagation();setAppearanceModalOpen(true);}} className="h-10', 1)
APP.write_text(s,encoding='utf-8')

# ---------- Step modal: true phone viewport + bottom actions that cannot overflow ----------
m=MODAL.read_text(encoding='utf-8')
# Dialog full height on phones, rounded card only on wider screens.
m=re.sub(r'className="bg-white w-full max-w-2xl[^\"]*"',
         'className="wasm-step-dialog bg-white w-full sm:max-w-2xl h-[100dvh] sm:h-auto sm:max-h-[92dvh] sm:rounded-3xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col text-right font-[\'Cairo\',sans-serif]"',m,count=1)
# Footer gets a stable marker and mobile grid.
m=re.sub(r'className="p-3[^\"]*bg-slate-50 border-t border-slate-200[^\"]*"',
         'className="wasm-step-footer p-2.5 sm:p-4 bg-slate-50 border-t border-slate-200 shrink-0"',m,count=1)
# Wrap footer content behavior through CSS; make next/complete text shorter on mobile.
m=m.replace('الانتقال للخطوة التالية (', 'التالي: ', 1)
m=m.replace('إتمام وحفظ التقرير', 'حفظ وإتمام التقرير')
MODAL.write_text(m,encoding='utf-8')

# ---------- AI: no key UI, no canned fallback. Backend-only UX ----------
AI.write_text(r'''import React,{useState} from 'react';
import {Sparkles,Loader2,AlertCircle,CheckCircle2} from 'lucide-react';
import {Capacitor,registerPlugin} from '@capacitor/core';
import {ReportData} from '../../types';
interface Props{reportData:ReportData;onApplyContent:(generated:Partial<ReportData>)=>void;onApplySingleField?:(field:keyof ReportData,value:string)=>void;}
interface NativeAI{generateAi(options:{payload:string}):Promise<{response:string}>;}
const Native=registerPlugin<NativeAI>('WasmNative');
const android=Capacitor.isNativePlatform()&&Capacitor.getPlatform()==='android';
export const AIEducationalAssistant:React.FC<Props>=({reportData,onApplyContent})=>{
 const[topic,setTopic]=useState(reportData.title||'');const[loading,setLoading]=useState(false);const[msg,setMsg]=useState('');const[ok,setOk]=useState(false);
 const generate=async()=>{if(!topic.trim()){setOk(false);setMsg('اكتب موضوع البرنامج أو الفعالية أولاً.');return;}setLoading(true);setOk(false);setMsg('يتصل بالمساعد Gemini الحقيقي...');try{
  const payload={title:topic,category:reportData.categoryTag||'',targetAudience:reportData.targetAudience||'',reportType:reportData.reportType||'',existingContent:{generalGoal:reportData.generalGoal||'',detailedGoals:reportData.detailedGoals||'',executionMechanism:reportData.executionMechanism||'',resultsAndImpact:reportData.resultsAndImpact||'',recommendations:reportData.recommendations||''}};
  let json:any;if(android){const r=await Native.generateAi({payload:JSON.stringify(payload)});json=JSON.parse(r.response);}else{const r=await fetch('/api/ai/generate-content',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const text=await r.text();if(!r.ok||!text.trim().startsWith('{'))throw new Error('خدمة Gemini السحابية غير متاحة');json=JSON.parse(text);}
  if(!json?.success||!json?.data)throw new Error(json?.error||'لم يصل محتوى صالح من Gemini');onApplyContent(json.data);setOk(true);setMsg('تم التوليد الحقيقي وتطبيق المحتوى على التقرير.');
 }catch(e:any){console.error(e);setMsg(e?.message||'تعذر الاتصال بخدمة Gemini السحابية');}finally{setLoading(false);}};
 return <div className="rounded-2xl border border-emerald-200 bg-gradient-to-br from-emerald-50 to-white p-3.5"><div className="flex items-center gap-2 mb-2"><Sparkles className="w-4 h-4 text-amber-500"/><div><h3 className="text-xs font-black text-emerald-950">المساعد التعليمي الذكي</h3><p className="text-[9px] text-slate-500">توليد Gemini حقيقي — بدون عبارات محلية جاهزة</p></div></div><input value={topic} onChange={e=>setTopic(e.target.value)} placeholder="مثال: أسبوع الصحة المدرسية" className="w-full px-3 py-2.5 rounded-xl border border-slate-300 text-xs font-bold outline-none focus:border-emerald-700"/><button type="button" disabled={loading} onClick={generate} className="mt-2 w-full py-2.5 rounded-xl bg-emerald-800 text-white text-xs font-black flex items-center justify-center gap-2 disabled:opacity-60">{loading?<Loader2 className="w-4 h-4 animate-spin"/>:<Sparkles className="w-4 h-4 text-amber-300"/>}<span>{loading?'جاري التوليد...':'توليد المحتوى بالذكاء الاصطناعي'}</span></button>{msg&&<div className={`mt-2 rounded-xl p-2.5 text-[10px] font-bold flex gap-2 ${ok?'bg-emerald-50 text-emerald-800 border border-emerald-200':'bg-amber-50 text-amber-900 border border-amber-200'}`}>{ok?<CheckCircle2 className="w-4 h-4 shrink-0"/>:<AlertCircle className="w-4 h-4 shrink-0"/>}<span>{msg}</span></div>}</div>;
};
''',encoding='utf-8')

# ---------- Restore pre-v3 report designs (remove added frames/accents only) ----------
r=RENDERER.read_text(encoding='utf-8')
r=re.sub(r'\s*\$\{data\.templateId === \'template-2-health-wave\' \? \'template-accent-initiative\' : data\.templateId === \'template-3-watercolor-luxury\' \? \'template-accent-activity\' : data\.templateId === \'template-4-health-field\' \? \'template-accent-impact\' : data\.templateId === \'template-5-institutional\' \? \'template-accent-institutional\' : \'\'\}', '', r)
RENDERER.write_text(r,encoding='utf-8')

c=CSS.read_text(encoding='utf-8')
idx=c.find('/* Template role accents inspired by WASM identity; report remains brand-neutral. */')
if idx>=0:c=c[:idx].rstrip()+"\n"
c += r'''

/* Mobile dialog stability */
@media (max-width: 640px) {
  .wasm-step-dialog { width:100vw !important; max-width:100vw !important; height:100dvh !important; max-height:100dvh !important; border-radius:0 !important; }
  .wasm-step-footer { padding-bottom:max(10px, env(safe-area-inset-bottom)) !important; }
  .wasm-step-footer > button:first-child { display:none !important; }
  .wasm-step-footer > div { width:100% !important; min-width:0 !important; display:grid !important; grid-template-columns:minmax(0,.34fr) minmax(0,.66fr) !important; gap:8px !important; }
  .wasm-step-footer > div > button { min-width:0 !important; width:100% !important; padding:10px 8px !important; white-space:normal !important; line-height:1.25 !important; font-size:11px !important; justify-content:center !important; }
  .wasm-step-footer > div > button:only-child { grid-column:1/-1 !important; }
}
'''
CSS.write_text(c,encoding='utf-8')
print('mobile v4: responsive modal, browser-native export, restored templates, no user API-key UI')

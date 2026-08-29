#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'src/App.tsx'
AI=ROOT/'src/components/Editor/AIEducationalAssistant.tsx'
CSS=ROOT/'src/index.css'

s=APP.read_text(encoding='utf-8')

# Native interface: use chunked transfer for large PDF/PNG payloads.
s=s.replace("  generateAi(options: { payload: string }): Promise<{ response: string }>;\n}","  generateAi(options: { payload: string }): Promise<{ response: string }>;\n  startFile(options: { fileName: string; mimeType: string }): Promise<{ id: string }>;\n  appendFileChunk(options: { id: string; chunk: string }): Promise<void>;\n  finishFile(options: { id: string }): Promise<{ uri: string }>;\n}")

# Replace export implementation created by v2 with a robust visible-render clone + chunked native writer.
start=s.index('  const renderReportCanvas = async (): Promise<HTMLCanvasElement> => {')
end=s.index('  const templates:',start)
exports=r'''  const saveNativeDataUrl = async (fileName: string, mimeType: string, dataUrl: string) => {
    const comma = dataUrl.indexOf(',');
    if (comma < 0) throw new Error('Invalid export data');
    const base64 = dataUrl.slice(comma + 1);
    const started = await WasmNative.startFile({ fileName, mimeType });
    const chunkSize = 131072; // divisible by 4; keeps every Capacitor bridge call small.
    for (let i = 0; i < base64.length; i += chunkSize) {
      await WasmNative.appendFileChunk({ id: started.id, chunk: base64.slice(i, i + chunkSize) });
    }
    return WasmNative.finishFile({ id: started.id });
  };

  const renderReportCanvas = async (): Promise<HTMLCanvasElement> => {
    const source = reportRef.current?.querySelector('.a4-sheet') as HTMLElement | null;
    if (!source) throw new Error('لم يتم العثور على صفحة التقرير A4');

    // The preview can be display:none while editing. Clone it into a real, full-size render surface.
    // Keep it in the viewport and behind the app instead of far outside the viewport (which produced blank canvases on Android WebView).
    const host = document.createElement('div');
    host.setAttribute('aria-hidden','true');
    host.style.cssText='position:fixed;left:0;top:0;width:794px;height:1123px;overflow:visible;z-index:-2147483647;pointer-events:none;background:#fff;';
    const clone = source.cloneNode(true) as HTMLElement;
    clone.style.cssText += ';display:block!important;visibility:visible!important;opacity:1!important;transform:none!important;width:794px!important;height:1123px!important;margin:0!important;';
    host.appendChild(clone);
    document.body.appendChild(host);
    try {
      if (document.fonts?.ready) await document.fonts.ready;
      const images=Array.from(clone.querySelectorAll('img')) as HTMLImageElement[];
      await Promise.all(images.map(img => img.complete ? Promise.resolve() : new Promise<void>(resolve => { img.onload=()=>resolve(); img.onerror=()=>resolve(); })));
      await new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve())));
      const canvas=await html2canvas(clone,{scale:2,backgroundColor:'#ffffff',useCORS:true,allowTaint:false,logging:false,width:794,height:1123,windowWidth:794,windowHeight:1123,scrollX:0,scrollY:0});
      if(canvas.width < 1000 || canvas.height < 1500) throw new Error('فشل محرك الرسم في إنشاء الصفحة بالحجم المطلوب');
      return canvas;
    } finally { host.remove(); }
  };

  const handleExportPDF = async () => {
    setExportDropdownOpen(false); setIsExporting(true); setSaveToast('جاري إنشاء PDF A4...');
    const safeTitle=(reportData.title||'تقرير_وَسْم').trim().replace(/[/\\?%*:|"<>]/g,'_').replace(/\s+/g,'_');
    try {
      const canvas=await renderReportCanvas();
      const jpeg=canvas.toDataURL('image/jpeg',0.94);
      const pdf=new jsPDF({orientation:'portrait',unit:'mm',format:'a4',compress:true});
      pdf.addImage(jpeg,'JPEG',0,0,210,297,undefined,'FAST');
      const fileName=`تقرير_${safeTitle}.pdf`;
      if(isNativeAndroid) await saveNativeDataUrl(fileName,'application/pdf',pdf.output('datauristring'));
      else pdf.save(fileName);
      setSaveToast(isNativeAndroid?'تم حفظ PDF في التنزيلات / WASM':'تم تنزيل PDF بنجاح');
    } catch(err:any){ console.error('PDF export failed',err); setSaveToast(`تعذر PDF: ${err?.message||'خطأ غير معروف'}`); }
    finally{setIsExporting(false);setTimeout(()=>setSaveToast(''),4500);}
  };

  const handleExportImage = async () => {
    setExportDropdownOpen(false); setIsExporting(true); setSaveToast('جاري إنشاء PNG عالية الدقة...');
    const safeTitle=(reportData.title||'تقرير_وَسْم').trim().replace(/[/\\?%*:|"<>]/g,'_').replace(/\s+/g,'_');
    try {
      const canvas=await renderReportCanvas();
      const png=canvas.toDataURL('image/png'); const fileName=`تقرير_${safeTitle}.png`;
      if(isNativeAndroid) await saveNativeDataUrl(fileName,'image/png',png);
      else {const a=document.createElement('a');a.download=fileName;a.href=png;document.body.appendChild(a);a.click();a.remove();}
      setSaveToast(isNativeAndroid?'تم حفظ PNG في التنزيلات / WASM':'تم تنزيل PNG بنجاح');
    } catch(err:any){console.error('PNG export failed',err);setSaveToast(`تعذر PNG: ${err?.message||'خطأ غير معروف'}`);}
    finally{setIsExporting(false);setTimeout(()=>setSaveToast(''),4500);}
  };

'''
s=s[:start]+exports+s[end:]

# Functional template names instead of internal design names.
renames={
'الإنفوجرافيك الوزاري':'تقرير برنامج أو فعالية',
'المنظومة الرقمية':'تقرير مبادرة',
'الميثاق الفاخر':'تقرير توثيق نشاط',
'لوحة قياس الأثر':'تقرير قياس الأثر',
'المسار الإجرائي':'تقرير إنجاز مؤسسي',
}
for a,b in renames.items(): s=s.replace(a,b)

# Replace mobile header: no horizontally-hidden primary controls. Two compact 3-column rows.
h0=s.index('      {/* Mobile-only top navigation */}')
h1=s.index('      {/* Toast Notification */}',h0)
header=r'''      {/* Android phone-first command bar: every primary action stays inside the viewport */}
      <header className="no-print sticky top-0 z-40 bg-white/98 backdrop-blur border-b border-slate-200 shadow-sm" style={{paddingTop:'env(safe-area-inset-top)'}}>
        <div className="px-2 pt-2 pb-1 grid grid-cols-3 gap-1.5">
          <button type="button" onClick={()=>openStepModal(0)} className="h-10 min-w-0 rounded-xl bg-emerald-900 text-white text-[10px] font-black flex items-center justify-center gap-1"><PenTool className="w-3.5 h-3.5 text-amber-300 shrink-0"/><span className="truncate">تحرير البيانات</span></button>
          <button type="button" onClick={()=>setMobileTab(mobileTab==='editor'?'preview':'editor')} className="h-10 min-w-0 rounded-xl bg-slate-100 border border-slate-200 text-slate-800 text-[10px] font-black flex items-center justify-center gap-1">{mobileTab==='editor'?<Eye className="w-3.5 h-3.5 text-emerald-700 shrink-0"/>:<PenTool className="w-3.5 h-3.5 text-emerald-700 shrink-0"/>}<span className="truncate">{mobileTab==='editor'?'معاينة التقرير':'عودة للتحرير'}</span></button>
          <button type="button" onClick={()=>setAppearanceModalOpen(true)} className="h-10 min-w-0 rounded-xl bg-amber-50 border border-amber-200 text-emerald-950 text-[10px] font-black flex items-center justify-center gap-1"><Palette className="w-3.5 h-3.5 shrink-0"/><span className="truncate">اللون والخط</span></button>
        </div>
        <div className="px-2 pb-2 grid grid-cols-3 gap-1.5">
          <div className="relative min-w-0" ref={exportDropdownRef}>
            <button type="button" onClick={()=>setExportDropdownOpen(v=>!v)} disabled={isExporting} className="w-full h-10 min-w-0 rounded-xl bg-emerald-800 text-white text-[10px] font-black flex items-center justify-center gap-1 disabled:opacity-60"><Download className="w-3.5 h-3.5 text-amber-300 shrink-0"/><span className="truncate">تصدير وطباعة</span></button>
            {exportDropdownOpen&&<div className="fixed inset-x-2 top-[calc(env(safe-area-inset-top)+92px)] bg-white rounded-2xl shadow-2xl border border-slate-200 p-2 z-[90]">
              <button type="button" onClick={()=>void handlePrint()} className="w-full p-3 text-right rounded-xl active:bg-emerald-50 flex items-center gap-3"><Printer className="w-5 h-5 text-emerald-800"/><span><b className="block text-xs">طباعة A4 فورية</b><small className="text-[10px] text-slate-500">نافذة طباعة Android الرسمية</small></span></button>
              <button type="button" onClick={()=>void handleExportPDF()} className="w-full p-3 text-right rounded-xl active:bg-emerald-50 flex items-center gap-3 border-t"><Download className="w-5 h-5 text-emerald-800"/><span><b className="block text-xs">حفظ PDF</b><small className="text-[10px] text-slate-500">A4 جاهز للطباعة في Downloads/WASM</small></span></button>
              <button type="button" onClick={()=>void handleExportImage()} className="w-full p-3 text-right rounded-xl active:bg-blue-50 flex items-center gap-3 border-t"><FileImage className="w-5 h-5 text-blue-700"/><span><b className="block text-xs">حفظ PNG</b><small className="text-[10px] text-slate-500">صورة التقرير كاملة عالية الدقة</small></span></button>
            </div>}
          </div>
          <button type="button" onClick={handleSaveLocal} className="h-10 min-w-0 rounded-xl bg-slate-100 border border-slate-200 text-slate-800 text-[10px] font-black flex items-center justify-center gap-1"><Save className="w-3.5 h-3.5 text-emerald-700 shrink-0"/><span className="truncate">حفظ التقرير</span></button>
          <button type="button" onClick={()=>setMobileTab('preview')} className="h-10 min-w-0 rounded-xl bg-[#08211e] text-[#f4ead8] text-[10px] font-black flex items-center justify-center gap-1"><FileText className="w-3.5 h-3.5 text-[#d6a34a] shrink-0"/><span className="truncate">عرض A4</span></button>
        </div>
        <div className="px-2 pb-2 overflow-x-auto no-scrollbar"><div className="flex gap-1.5 min-w-max">{templates.map(tpl=><button type="button" key={tpl.id} onClick={()=>setReportData({...reportData,templateId:tpl.id})} className={`px-2.5 py-1.5 rounded-lg text-[9px] font-bold whitespace-nowrap ${reportData.templateId===tpl.id?'bg-emerald-900 text-white':'bg-slate-100 border border-slate-200 text-slate-600'}`}>{tpl.number}. {tpl.label}</button>)}</div></div>
      </header>

'''
s=s[:h0]+header+s[h1:]
APP.write_text(s,encoding='utf-8')

# Replace AI component with real Gemini only; supports on-device key setup and never falls back to canned local content.
AI.write_text(r'''import React,{useEffect,useState} from 'react';
import {Sparkles,Loader2,KeyRound,CheckCircle2,AlertCircle} from 'lucide-react';
import {Capacitor,registerPlugin} from '@capacitor/core';
import {ReportData} from '../../types';
interface Props{reportData:ReportData;onApplyContent:(generated:Partial<ReportData>)=>void;onApplySingleField?:(field:keyof ReportData,value:string)=>void;}
interface NativeAI{generateAi(options:{payload:string}):Promise<{response:string}>;hasGeminiKey():Promise<{configured:boolean}>;setGeminiKey(options:{key:string}):Promise<void>;}
const Native=registerPlugin<NativeAI>('WasmNative');
const android=Capacitor.isNativePlatform()&&Capacitor.getPlatform()==='android';
export const AIEducationalAssistant:React.FC<Props>=({reportData,onApplyContent})=>{
 const[topic,setTopic]=useState(reportData.title||''); const[loading,setLoading]=useState(false); const[msg,setMsg]=useState(''); const[configured,setConfigured]=useState(false); const[key,setKey]=useState('');
 useEffect(()=>{if(android) Native.hasGeminiKey().then(r=>setConfigured(r.configured)).catch(()=>setConfigured(false));},[]);
 const saveKey=async()=>{if(!key.trim()){setMsg('أدخل مفتاح Gemini API.');return;}try{await Native.setGeminiKey({key:key.trim()});setConfigured(true);setKey('');setMsg('تم حفظ مفتاح Gemini داخل مساحة التطبيق الخاصة.');}catch(e:any){setMsg(e?.message||'تعذر حفظ المفتاح');}};
 const generate=async()=>{if(!topic.trim()){setMsg('اكتب موضوع البرنامج أو الفعالية أولاً.');return;}if(android&&!configured){setMsg('يلزم إعداد مفتاح Gemini API مرة واحدة لتوليد حقيقي مباشر.');return;}setLoading(true);setMsg('يتصل الآن بـ Gemini مباشرة...');try{
  const body={title:topic,category:reportData.categoryTag||'',targetAudience:reportData.targetAudience||'',reportType:reportData.reportType||'',existingContent:{generalGoal:reportData.generalGoal||'',detailedGoals:reportData.detailedGoals||'',executionMechanism:reportData.executionMechanism||'',resultsAndImpact:reportData.resultsAndImpact||'',recommendations:reportData.recommendations||''}};
  let json:any;if(android){const r=await Native.generateAi({payload:JSON.stringify(body)});json=JSON.parse(r.response);}else{const r=await fetch('/api/ai/generate-content',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const ct=r.headers.get('content-type')||'';if(!r.ok||!ct.includes('application/json'))throw new Error(`الخادم أعاد ${r.status} بدلاً من JSON`);json=await r.json();}
  if(!json?.success||!json?.data)throw new Error(json?.error||'لم يصل محتوى صالح من Gemini');onApplyContent(json.data);setMsg('تم التوليد الحقيقي بواسطة Gemini وتطبيق المحتوى.');
 }catch(e:any){console.error(e);setMsg(`تعذر Gemini: ${e?.message||'خطأ اتصال'}`);}finally{setLoading(false);}};
 return <div className="rounded-2xl border border-emerald-200 bg-gradient-to-br from-emerald-50 to-white p-3.5 space-y-2.5">
  <div className="flex items-start gap-2"><Sparkles className="w-4 h-4 text-amber-500 mt-0.5"/><div><h3 className="text-xs font-black text-emerald-950">المساعد التعليمي الذكي — Gemini مباشر</h3><p className="text-[9px] text-slate-500">لا توجد عبارات محلية جاهزة أو توليد وهمي.</p></div></div>
  {android&&!configured&&<div className="rounded-xl bg-amber-50 border border-amber-200 p-2.5"><div className="flex items-center gap-1.5 text-[10px] font-black text-amber-900 mb-2"><KeyRound className="w-3.5 h-3.5"/>إعداد Gemini مرة واحدة</div><div className="flex gap-1.5"><input type="password" value={key} onChange={e=>setKey(e.target.value)} placeholder="Gemini API Key" className="min-w-0 flex-1 px-2.5 py-2 rounded-lg border border-amber-200 bg-white text-[10px] outline-none"/><button type="button" onClick={()=>void saveKey()} className="px-3 rounded-lg bg-amber-400 text-emerald-950 text-[10px] font-black">حفظ</button></div></div>}
  {configured&&<div className="flex items-center gap-1 text-[9px] font-bold text-emerald-700"><CheckCircle2 className="w-3 h-3"/>Gemini الحقيقي جاهز</div>}
  <input value={topic} onChange={e=>setTopic(e.target.value)} placeholder="مثال: أسبوع الصحة المدرسية" className="w-full px-3 py-2.5 rounded-xl border border-slate-200 bg-white text-xs outline-none focus:border-emerald-600"/>
  <button type="button" onClick={()=>void generate()} disabled={loading} className="w-full py-2.5 rounded-xl bg-emerald-800 text-white text-xs font-black disabled:opacity-50 flex items-center justify-center gap-2">{loading?<Loader2 className="w-4 h-4 animate-spin"/>:<Sparkles className="w-4 h-4 text-amber-300"/>}توليد ذكي مباشر</button>
  {msg&&<div className={`text-[9px] font-bold flex items-start gap-1 ${msg.includes('تعذر')||msg.includes('يلزم')?'text-rose-700':'text-emerald-700'}`}>{msg.includes('تعذر')?<AlertCircle className="w-3 h-3 mt-0.5 shrink-0"/>:null}<span>{msg}</span></div>}
 </div>;
};
''',encoding='utf-8')

# Splash-inspired decorative treatment for selected report templates; strip app/developer branding from report components.
templates_dir=ROOT/'src/components/templates'
if templates_dir.exists():
    candidates=[]
    for p in templates_dir.glob('*.tsx'):
        txt=p.read_text(encoding='utf-8')
        for literal in ['Bandar Arishi','< DEVELOPER />','&lt; DEVELOPER /&gt;','إنجازك في تقرير يليق بأثره']:
            txt=txt.replace(literal,'')
        # Never brand generated reports with the app identity.
        txt=txt.replace('>وَسْم<','><')
        if re.search(r'(Template2|Template3|HealthWave|WatercolorLuxury|Institutional)',p.name,re.I):
            txt=txt.replace('a4-sheet','a4-sheet wasm-inspired-report',1)
        p.write_text(txt,encoding='utf-8')

css=CSS.read_text(encoding='utf-8')
if 'WASM_REPORT_DECOR_V3' not in css:
    css += r'''
/* WASM_REPORT_DECOR_V3: abstract identity-inspired decoration only; no app name or developer credit inside reports. */
.a4-sheet.wasm-inspired-report{position:relative;overflow:hidden}
.a4-sheet.wasm-inspired-report::before{content:"";position:absolute;z-index:0;right:-110px;top:-145px;width:390px;height:255px;border-radius:48% 52% 60% 40%;background:linear-gradient(145deg,rgba(8,33,30,.96),rgba(12,73,64,.88));transform:rotate(-9deg);pointer-events:none}
.a4-sheet.wasm-inspired-report::after{content:"";position:absolute;z-index:0;left:-145px;bottom:-165px;width:430px;height:275px;border-radius:55% 45% 42% 58%;background:linear-gradient(145deg,rgba(8,33,30,.96),rgba(23,105,90,.86));border-top:2px solid rgba(214,163,74,.75);transform:rotate(8deg);pointer-events:none}
.a4-sheet.wasm-inspired-report>*{position:relative;z-index:1}
'''
CSS.write_text(css,encoding='utf-8')
print('mobile v3 root fixes applied')

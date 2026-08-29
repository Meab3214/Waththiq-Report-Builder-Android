#!/usr/bin/env python3
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'src/App.tsx'; AI=ROOT/'src/components/Editor/AIEducationalAssistant.tsx'; CSS=ROOT/'src/index.css'
s=APP.read_text(encoding='utf-8')
s=s.replace("import { toPng, toJpeg } from 'html-to-image';\n","")
s=s.replace("  print(options: { jobName: string }): Promise<void>;\n}","  print(options: { jobName: string }): Promise<void>;\n  generateAi(options: { payload: string }): Promise<{ response: string }>;\n}")
start=s.index('  // Export as PDF (A4 high resolution')
end=s.index('  const templates:', start)
new_export=r'''  const renderReportCanvas = async (): Promise<HTMLCanvasElement> => {
    const source = reportRef.current?.querySelector('.a4-sheet') as HTMLElement | null;
    if (!source) throw new Error('A4 sheet not found');
    const host = document.createElement('div');
    host.setAttribute('aria-hidden', 'true');
    host.style.cssText = 'position:fixed;left:-12000px;top:0;width:794px;height:1123px;background:#fff;overflow:hidden;z-index:-9999;pointer-events:none;';
    const clone = source.cloneNode(true) as HTMLElement;
    clone.style.transform = 'none'; clone.style.margin = '0'; clone.style.width = '794px'; clone.style.height = '1123px';
    host.appendChild(clone); document.body.appendChild(host);
    try {
      if (document.fonts?.ready) await document.fonts.ready;
      const imgs = Array.from(clone.querySelectorAll('img')) as HTMLImageElement[];
      await Promise.all(imgs.map((img) => img.complete ? Promise.resolve() : new Promise<void>((resolve) => { img.onload=()=>resolve(); img.onerror=()=>resolve(); })));
      await new Promise<void>((resolve) => requestAnimationFrame(() => requestAnimationFrame(() => resolve())));
      const canvas = await html2canvas(clone, { scale: 2.2, backgroundColor:'#ffffff', useCORS:true, allowTaint:false, logging:false, width:794, height:1123, windowWidth:794, windowHeight:1123, scrollX:0, scrollY:0 });
      if (!canvas.width || !canvas.height) throw new Error('Empty export canvas');
      return canvas;
    } finally { host.remove(); }
  };

  const handleExportPDF = async () => {
    if (!reportRef.current) return;
    setExportDropdownOpen(false); setIsExporting(true); setSaveToast('جاري إنشاء ملف PDF...');
    const safeTitle=(reportData.title||'تقرير_وَسْم').trim().replace(/[/\\?%*:|"<>]/g,'_').replace(/\s+/g,'_');
    try {
      const canvas=await renderReportCanvas();
      const imgData=canvas.toDataURL('image/jpeg',0.96);
      const pdf=new jsPDF({orientation:'portrait',unit:'mm',format:'a4',compress:true});
      pdf.addImage(imgData,'JPEG',0,0,210,297,undefined,'FAST');
      const fileName=`تقرير_${safeTitle}.pdf`;
      if(isNativeAndroid){ const uri=pdf.output('datauristring'); await WasmNative.saveBase64({fileName,mimeType:'application/pdf',base64Data:uri.substring(uri.indexOf(',')+1)}); }
      else pdf.save(fileName);
      setSaveToast('تم حفظ PDF في مجلد Downloads/WASM.');
    } catch(err){ console.error(err); setSaveToast('تعذر تصدير PDF.'); }
    finally{ setIsExporting(false); setTimeout(()=>setSaveToast(''),3200); }
  };

  const handleExportImage = async () => {
    if (!reportRef.current) return;
    setExportDropdownOpen(false); setIsExporting(true); setSaveToast('جاري إنشاء صورة PNG...');
    const safeTitle=(reportData.title||'تقرير_وَسْم').trim().replace(/[/\\?%*:|"<>]/g,'_').replace(/\s+/g,'_');
    try {
      const canvas=await renderReportCanvas(); const dataUrl=canvas.toDataURL('image/png'); const fileName=`تقرير_${safeTitle}.png`;
      if(isNativeAndroid) await WasmNative.saveBase64({fileName,mimeType:'image/png',base64Data:dataUrl.substring(dataUrl.indexOf(',')+1)});
      else { const a=document.createElement('a'); a.download=fileName; a.href=dataUrl; a.click(); }
      setSaveToast('تم حفظ PNG في مجلد Downloads/WASM.');
    } catch(err){ console.error(err); setSaveToast('تعذر تصدير PNG.'); }
    finally{ setIsExporting(false); setTimeout(()=>setSaveToast(''),3200); }
  };

'''
s=s[:start]+new_export+s[end:]
h0=s.index('      {/* Top Main Navbar */}')
h1=s.index('      {/* Toast Notification */}',h0)
header=r'''      {/* Mobile-only top navigation */}
      <header className="no-print sticky top-0 z-40 bg-white/98 backdrop-blur border-b border-slate-200 shadow-sm" style={{paddingTop:'env(safe-area-inset-top)'}}>
        <div className="h-11 px-3 flex items-center justify-between gap-2">
          <button type="button" onClick={() => openStepModal(0)} className="h-9 px-3 rounded-xl bg-emerald-900 text-white text-[11px] font-black flex items-center gap-1.5"><PenTool className="w-4 h-4 text-amber-300"/>البيانات</button>
          <h1 className="font-black text-[#08211e] text-[15px] tracking-wide">وَسْم</h1>
          <button type="button" onClick={() => setMobileTab(mobileTab==='editor'?'preview':'editor')} className="h-9 px-3 rounded-xl bg-slate-100 text-slate-800 text-[11px] font-black flex items-center gap-1.5">{mobileTab==='editor'?<Eye className="w-4 h-4 text-emerald-700"/>:<PenTool className="w-4 h-4 text-emerald-700"/>}{mobileTab==='editor'?'المعاينة':'التحرير'}</button>
        </div>
        <div className="px-2 pb-2 overflow-x-auto no-scrollbar">
          <div className="flex items-center gap-1.5 min-w-max">
            <div className="relative" ref={exportDropdownRef}>
              <button type="button" onClick={()=>setExportDropdownOpen(v=>!v)} disabled={isExporting} className="h-9 px-3 rounded-xl bg-emerald-800 text-white text-[10px] font-black flex items-center gap-1.5"><Download className="w-3.5 h-3.5 text-amber-300"/>تصدير وطباعة<ChevronDown className="w-3 h-3"/></button>
              {exportDropdownOpen && <div className="fixed right-2 top-[calc(env(safe-area-inset-top)+88px)] w-[calc(100vw-16px)] max-w-sm bg-white rounded-2xl shadow-2xl border border-slate-200 p-2 z-[80]">
                <button onClick={()=>void handlePrint()} className="w-full p-3 text-right rounded-xl hover:bg-emerald-50 flex gap-2"><Printer className="w-5 h-5 text-emerald-800"/><span><b className="block text-xs">طباعة A4 فورية</b><small className="text-[10px] text-slate-500">فتح طباعة Android</small></span></button>
                <button onClick={()=>void handleExportPDF()} className="w-full p-3 text-right rounded-xl hover:bg-emerald-50 flex gap-2 border-t"><Download className="w-5 h-5 text-emerald-800"/><span><b className="block text-xs">تصدير PDF</b><small className="text-[10px] text-slate-500">حفظ في Downloads/WASM</small></span></button>
                <button onClick={()=>void handleExportImage()} className="w-full p-3 text-right rounded-xl hover:bg-blue-50 flex gap-2 border-t"><FileImage className="w-5 h-5 text-blue-700"/><span><b className="block text-xs">تصدير PNG</b><small className="text-[10px] text-slate-500">صورة عالية الدقة</small></span></button>
              </div>}
            </div>
            <button type="button" onClick={()=>setAppearanceModalOpen(true)} className="h-9 px-3 rounded-xl bg-amber-50 border border-amber-200 text-emerald-950 text-[10px] font-black flex items-center gap-1.5"><Palette className="w-3.5 h-3.5"/>اللون والخط</button>
            <button type="button" onClick={handleSaveLocal} className="h-9 px-3 rounded-xl bg-slate-100 text-slate-800 text-[10px] font-black flex items-center gap-1.5"><Save className="w-3.5 h-3.5 text-emerald-700"/>حفظ</button>
            <button type="button" onClick={handleReset} className="h-9 px-3 rounded-xl bg-slate-100 text-slate-800 text-[10px] font-black flex items-center gap-1.5"><RotateCcw className="w-3.5 h-3.5"/>تفريغ</button>
          </div>
        </div>
        <div className="px-2 pb-2 overflow-x-auto no-scrollbar"><div className="flex items-center gap-1 min-w-max">{templates.map(tpl=><button key={tpl.id} onClick={()=>setReportData({...reportData,templateId:tpl.id})} className={`px-2.5 py-1.5 rounded-lg text-[9px] font-bold whitespace-nowrap ${reportData.templateId===tpl.id?'bg-emerald-900 text-white':'bg-slate-100 text-slate-600'}`}>{tpl.number}. {tpl.label}</button>)}</div></div>
      </header>

'''
s=s[:h0]+header+s[h1:]
s=s.replace('className="flex-1 w-full max-w-[100vw] mx-auto p-2 grid grid-cols-1 gap-2 pb-28 overflow-x-hidden"','className="flex-1 w-full max-w-[100vw] mx-auto p-2 grid grid-cols-1 gap-2 pb-3 overflow-x-hidden"')
s=s.replace("className={`no-print lg:col-span-5 ${mobileTab === 'editor' ? 'block' : 'hidden lg:block'} h-auto`}","className={`no-print ${mobileTab === 'editor' ? 'block' : 'hidden'} h-auto`}")
s=s.replace("mobileTab === 'preview' ? 'flex' : 'hidden lg:flex'","mobileTab === 'preview' ? 'flex' : 'hidden'")
old=re.compile(r'''<div\n\s+ref=\{reportRef\}\n\s+className="origin-top transition-transform duration-150"\n\s+style=\{\{\n\s+transform: `scale\(\$\{zoomLevel\}\)`,\n\s+transformOrigin: 'top center',\n\s+marginBottom: `\$\{\(1123 \* zoomLevel\) - 1123\}px`,\n\s+\}\}\n\s+>\n\s+<ReportRenderer data=\{reportData\} />\n\s+</div>''')
rep='''<div style={{ width: `${794 * zoomLevel}px`, height: `${1123 * zoomLevel}px`, position: 'relative', flex: '0 0 auto' }}><div ref={reportRef} style={{ width:'794px', height:'1123px', transform:`scale(${zoomLevel})`, transformOrigin:'top left', position:'absolute', top:0, left:0 }}><ReportRenderer data={reportData} /></div></div>'''
s,n=old.subn(rep,s,1)
if n!=1: raise SystemExit('preview wrapper marker not found')
fb=s.find('      {/* Floating Mobile Bottom Quick Action Bar */}')
if fb>=0:
    fm=s.find('      <StepEditorModal',fb)
    s=s[:fb]+s[fm:]
footer_start=s.find('      <footer className="no-print')
if footer_start>=0:
    footer_end=s.find('      </footer>',footer_start)+len('      </footer>')
    footer='''      <footer className="no-print bg-[#08211e] px-4 py-4 mt-2 flex flex-col items-center justify-center text-center gap-2" dir="rtl"><img src="/icons/icon-512.png" alt="وَسْم" className="w-14 h-14 rounded-2xl shadow-md"/><div><div className="text-[11px] font-black text-[#f4ead8]">إنجازك في تقرير</div><div className="text-[11px] font-black text-[#d6a34a]">يليق بأثره</div></div><img src="/assets/branding/wasm_developer_mark.png" alt="BA Developer Bandar Arishi" className="w-[150px] max-w-[45vw] h-auto object-contain mt-1"/></footer>'''
    s=s[:footer_start]+footer+s[footer_end:]
APP.write_text(s,encoding='utf-8')
AI.write_text(r'''import React,{useState} from 'react';
import {Sparkles,Loader2,CheckCircle2,AlertCircle} from 'lucide-react';
import {Capacitor,registerPlugin} from '@capacitor/core';
import {ReportData} from '../../types';
interface Props{reportData:ReportData;onApplyContent:(generated:Partial<ReportData>)=>void;onApplySingleField?:(field:keyof ReportData,value:string)=>void;}
interface NativeAI{generateAi(options:{payload:string}):Promise<{response:string}>}
const WasmNative=registerPlugin<NativeAI>('WasmNative');
const isAndroid=Capacitor.isNativePlatform()&&Capacitor.getPlatform()==='android';
export const AIEducationalAssistant:React.FC<Props>=({reportData,onApplyContent})=>{const[topic,setTopic]=useState(reportData.title||'');const[loading,setLoading]=useState(false);const[msg,setMsg]=useState('');
const generate=async()=>{if(!topic.trim()){setMsg('اكتب موضوع البرنامج أو الفعالية أولاً.');return;}setLoading(true);setMsg('اتصال مباشر بالمساعد الذكي...');try{const body={title:topic,category:reportData.categoryTag||'',mode:'all',customPrompt:'صياغة تربوية أصلية ومخصصة للموضوع الحالي',targetAudience:reportData.targetAudience||'',existingContent:{generalGoal:reportData.generalGoal,detailedGoals:reportData.detailedGoals,executionMechanism:reportData.executionMechanism,resultsAndImpact:reportData.resultsAndImpact}};let json:any;if(isAndroid){const r=await WasmNative.generateAi({payload:JSON.stringify(body)});json=JSON.parse(r.response);}else{const r=await fetch('/api/ai/generate-content',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});if(!r.ok)throw new Error(`HTTP ${r.status}`);json=await r.json();}if(!json?.success||!json?.data||json?.isFallback)throw new Error('لم يصل رد Gemini الحقيقي من الخادم');onApplyContent(json.data);setMsg('تم التوليد مباشرة بواسطة Gemini وتطبيق المحتوى على التقرير.');}catch(e:any){console.error(e);setMsg(`تعذر الاتصال بالمساعد الحقيقي: ${e?.message||'خطأ اتصال'}`);}finally{setLoading(false);}};
return <div className="rounded-2xl border border-emerald-200 bg-gradient-to-br from-emerald-50 to-white p-3.5"><div className="flex items-center gap-2 mb-2"><Sparkles className="w-4 h-4 text-amber-500"/><div><h3 className="text-xs font-black text-emerald-950">المساعد التعليمي الذكي — Gemini مباشر</h3><p className="text-[9px] text-slate-500">توليد حقيقي عبر خادم الذكاء الاصطناعي، بدون عبارات محلية جاهزة.</p></div></div><div className="flex gap-2"><input value={topic} onChange={e=>setTopic(e.target.value)} placeholder="مثال: برنامج تعزيز الصحة المدرسية" className="flex-1 min-w-0 px-3 py-2.5 rounded-xl border border-slate-300 text-xs outline-none focus:border-emerald-700"/><button type="button" onClick={generate} disabled={loading} className="px-3.5 rounded-xl bg-emerald-800 text-white text-[10px] font-black disabled:opacity-60 flex items-center gap-1.5">{loading?<Loader2 className="w-4 h-4 animate-spin"/>:<Sparkles className="w-4 h-4 text-amber-300"/>}توليد</button></div>{msg&&<div className={`mt-2 text-[10px] font-bold flex items-center gap-1.5 ${msg.startsWith('تعذر')?'text-rose-700':'text-emerald-800'}`}>{msg.startsWith('تعذر')?<AlertCircle className="w-3.5 h-3.5"/>:<CheckCircle2 className="w-3.5 h-3.5"/>}{msg}</div>}</div>;
};
''',encoding='utf-8')
css=CSS.read_text(encoding='utf-8')
css+='''\nhtml,body,#root{width:100%;max-width:100%;min-height:100%;overflow-x:hidden} body{overscroll-behavior-x:none} button,input,select,textarea{max-width:100%} @media(max-width:600px){.a4-sheet{box-shadow:0 2px 10px rgba(15,23,42,.12)!important}}\n'''
CSS.write_text(css,encoding='utf-8')
print('WASM mobile v2 fixes applied')

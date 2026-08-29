#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'src/App.tsx'
MODAL = ROOT / 'src/components/Editor/StepEditorModal.tsx'
AI = ROOT / 'src/components/Editor/AIEducationalAssistant.tsx'
CSS = ROOT / 'src/index.css'


def replace_between(text: str, start: str, end: str, replacement: str) -> str:
    a = text.find(start)
    if a < 0:
        raise SystemExit(f'missing start marker: {start}')
    b = text.find(end, a)
    if b < 0:
        raise SystemExit(f'missing end marker: {end}')
    return text[:a] + replacement + text[b:]

# ---------- App.tsx ----------
s = APP.read_text(encoding='utf-8')
if "from '@capacitor/core'" not in s:
    s = s.replace("import React, { useState, useRef, useEffect } from 'react';", "import React, { useState, useRef, useEffect } from 'react';\nimport { Capacitor, registerPlugin } from '@capacitor/core';")

s = s.replace('  ChevronDown,\n}', '  ChevronDown,\n  Palette,\n  Type,\n}', 1)

native_decl = '''\ninterface WasmNativePlugin {\n  saveBase64(options: { fileName: string; mimeType: string; base64Data: string }): Promise<{ uri: string }>;\n  print(options: { jobName: string }): Promise<void>;\n}\n\nconst WasmNative = registerPlugin<WasmNativePlugin>('WasmNative');\nconst isNativeAndroid = Capacitor.isNativePlatform() && Capacitor.getPlatform() === 'android';\n'''
if 'interface WasmNativePlugin' not in s:
    s = s.replace("import confetti from 'canvas-confetti';\n", "import confetti from 'canvas-confetti';\n" + native_decl)

state_marker = "  const [exportDropdownOpen, setExportDropdownOpen] = useState<boolean>(false);\n"
if 'appearanceModalOpen' not in s:
    s = s.replace(state_marker, state_marker + "  const [appearanceModalOpen, setAppearanceModalOpen] = useState<boolean>(false);\n", 1)

old_zoom = '''  // Auto-adjust zoom on initial load for mobile screens\n  useEffect(() => {\n    if (window.innerWidth < 640) {\n      setZoomLevel(0.44);\n    } else if (window.innerWidth < 1024) {\n      setZoomLevel(0.65);\n    } else {\n      setZoomLevel(0.85);\n    }\n  }, []);\n'''
new_zoom = '''  // Mobile-first A4 fit. 794px is the report's CSS A4 width.\n  useEffect(() => {\n    const fit = () => {\n      const available = Math.max(300, window.innerWidth - 20);\n      setZoomLevel(Math.min(0.92, Math.max(0.36, available / 794)));\n    };\n    fit();\n    window.addEventListener('resize', fit);\n    return () => window.removeEventListener('resize', fit);\n  }, []);\n'''
if old_zoom in s:
    s = s.replace(old_zoom, new_zoom, 1)

start = '  // Direct Print (Works in all browsers & iframes)\n'
end = '  // Export as PDF (A4 high resolution with dual-engine fallback)\n'
print_fn = '''  // Native Android printing with browser fallback.\n  const handlePrint = async () => {\n    setExportDropdownOpen(false);\n    setSaveToast('جاري فتح طباعة A4...');\n    try {\n      if (isNativeAndroid) {\n        await WasmNative.print({ jobName: reportData.title || 'تقرير وَسْم' });\n      } else {\n        window.print();\n      }\n      setSaveToast('تم فتح نافذة الطباعة A4.');\n    } catch (error) {\n      console.error('Print failed:', error);\n      try { window.print(); } catch (_) {}\n      setSaveToast('تعذر فتح الطباعة. حاول مرة أخرى.');\n    } finally {\n      setTimeout(() => setSaveToast(''), 2500);\n    }\n  };\n\n'''
s = replace_between(s, start, end, print_fn + end)

old_pdf_save = "      pdf.save(`تقرير_${safeTitle}.pdf`);"
new_pdf_save = '''      const pdfFileName = `تقرير_${safeTitle}.pdf`;\n      if (isNativeAndroid) {\n        const dataUri = pdf.output('datauristring');\n        const base64Data = dataUri.substring(dataUri.indexOf(',') + 1);\n        await WasmNative.saveBase64({ fileName: pdfFileName, mimeType: 'application/pdf', base64Data });\n      } else {\n        pdf.save(pdfFileName);\n      }'''
if old_pdf_save not in s:
    raise SystemExit('missing pdf.save marker')
s = s.replace(old_pdf_save, new_pdf_save, 1)

old_png = '''      const link = document.createElement('a');\n      link.download = `تقرير_${safeTitle}.png`;\n      link.href = dataUrl;\n      document.body.appendChild(link);\n      link.click();\n      document.body.removeChild(link);'''
new_png = '''      const imageFileName = `تقرير_${safeTitle}.png`;\n      if (isNativeAndroid) {\n        const base64Data = dataUrl.substring(dataUrl.indexOf(',') + 1);\n        await WasmNative.saveBase64({ fileName: imageFileName, mimeType: 'image/png', base64Data });\n      } else {\n        const link = document.createElement('a');\n        link.download = imageFileName;\n        link.href = dataUrl;\n        document.body.appendChild(link);\n        link.click();\n        document.body.removeChild(link);\n      }'''
if old_png not in s:
    raise SystemExit('missing PNG download marker')
s = s.replace(old_png, new_png, 1)

s = s.replace('className="min-h-screen bg-slate-100 flex flex-col', 'className="min-h-[100dvh] w-full max-w-[100vw] overflow-x-hidden bg-slate-100 flex flex-col', 1)
s = s.replace('className="max-w-7xl mx-auto px-3 sm:px-4 py-2 flex items-center justify-between gap-2"', 'className="w-full px-2.5 py-2 flex items-center justify-between gap-2"', 1)
s = s.replace('className="wasm-brand-icon w-9 h-9 sm:w-10 sm:h-10 rounded-xl shadow-sm shrink-0"', 'className="wasm-brand-icon w-8 h-8 rounded-lg shadow-sm shrink-0"', 1)
s = s.replace('className="min-w-0 hidden xs:block"', 'className="min-w-0 block"', 1)
s = s.replace('className="text-sm sm:text-base font-black text-[#08211e] leading-none"', 'className="text-[13px] font-black text-[#08211e] leading-none"', 1)
s = s.replace('text-[8.5px] sm:text-[9.5px]', 'text-[7.5px] sm:text-[8.5px]', 1)

needle = '''            <button onClick={() => openStepModal(0)} title="فتح نموذج إدخال البيانات"'''
if needle in s and 'title="تغيير اللون والخط"' not in s:
    insert = '''            <button type="button" onClick={() => setAppearanceModalOpen(true)} title="تغيير اللون والخط" className="p-2 rounded-xl bg-white border border-slate-200 text-emerald-900 min-h-[38px] min-w-[38px] flex items-center justify-center shadow-sm"><Palette className="w-4 h-4" /></button>\n'''
    pos = s.index(needle)
    s = s[:pos] + insert + s[pos:]

s = s.replace('className="flex-1 max-w-7xl w-full mx-auto p-2 sm:p-4 grid grid-cols-1 lg:grid-cols-12 gap-4 pb-20 lg:pb-4"', 'className="flex-1 w-full max-w-[100vw] mx-auto p-2 grid grid-cols-1 gap-2 pb-28 overflow-x-hidden"', 1)
s = s.replace("h-auto lg:h-[calc(100vh-105px)]", "h-auto", 1)
s = s.replace("flex-col h-[calc(100vh-145px)] lg:h-[calc(100vh-105px)]", "flex-col min-h-[calc(100dvh-180px)]", 1)
s = s.replace('className="flex-1 overflow-auto p-2 sm:p-4 flex items-start justify-center"', 'className="flex-1 overflow-hidden p-1.5 flex items-start justify-center w-full max-w-full"', 1)
s = s.replace("if (window.innerWidth < 640) setZoomLevel(0.44);\n                  else if (window.innerWidth < 1024) setZoomLevel(0.65);\n                  else setZoomLevel(0.85);", "setZoomLevel(Math.min(0.92, Math.max(0.36, (window.innerWidth - 20) / 794)));", 1)

footer_start = '      {/* Global Web App Developer Footer'
footer_end = '      {/* Floating Mobile Bottom Quick Action Bar */}'
if footer_start in s and footer_end in s:
    developer_footer = '''      <footer className="no-print w-full px-3 py-2.5 mb-16 bg-white border-t border-slate-200 flex items-center justify-between gap-3 text-[10px]" dir="ltr">\n        <div className="flex items-center gap-2 min-w-0">\n          <div className="leading-none text-[#08211e] font-black text-lg tracking-[-0.08em]">BA</div>\n          <div className="min-w-0">\n            <div className="font-mono text-[8px] text-[#d6a34a] tracking-wider">&lt; DEVELOPER /&gt;</div>\n            <div className="font-bold text-[#08211e] text-[10px] truncate">Bandar Arishi</div>\n          </div>\n        </div>\n        <div className="text-right" dir="rtl">\n          <div className="font-black text-[#08211e]">وَسْم</div>\n          <div className="text-[8px] font-bold"><span className="text-[#8b7a65]">إنجازك في تقرير </span><span className="text-[#d6a34a]">يليق بأثره</span></div>\n        </div>\n      </footer>\n\n'''
    s = replace_between(s, footer_start, footer_end, developer_footer + footer_end)

appearance = '''      {appearanceModalOpen && (\n        <div className="fixed inset-0 z-[95] bg-slate-950/70 flex items-end justify-center" onClick={() => setAppearanceModalOpen(false)} dir="rtl">\n          <div className="w-full max-w-md bg-white rounded-t-3xl p-4 pb-[max(16px,env(safe-area-inset-bottom))] shadow-2xl" onClick={(e) => e.stopPropagation()}>\n            <div className="flex items-center justify-between mb-4"><div><h3 className="font-black text-emerald-950">مظهر التقرير</h3><p className="text-[10px] text-slate-500">تغيير اللون والخط مباشرة</p></div><button onClick={() => setAppearanceModalOpen(false)} className="px-3 py-2 rounded-xl bg-slate-100 text-xs font-bold">تم</button></div>\n            <div className="mb-4"><div className="flex items-center gap-1.5 text-xs font-black mb-2"><Palette className="w-4 h-4"/>اللون</div><div className="grid grid-cols-6 gap-2">{[\n              ['emerald','#059669'],['teal','#0d9488'],['navy','#1e3a8a'],['burgundy','#9f1239'],['gold','#d97706'],['forest','#166534']\n            ].map(([id,color]) => <button key={id} type="button" onClick={() => setReportData({...reportData, themeColor:id as any})} className={`h-10 rounded-xl border-2 ${reportData.themeColor===id?'border-slate-950 scale-105':'border-white'}`} style={{backgroundColor:color}} aria-label={id}/> )}</div></div>\n            <div><div className="flex items-center gap-1.5 text-xs font-black mb-2"><Type className="w-4 h-4"/>الخط</div><div className="grid grid-cols-2 gap-2">{['Cairo','Tajawal','Almarai','IBM Plex Sans Arabic'].map((font) => <button key={font} type="button" onClick={() => setReportData({...reportData,fontFamily:font as any})} className={`py-2.5 px-3 rounded-xl border text-xs font-bold ${reportData.fontFamily===font?'bg-emerald-800 text-white border-emerald-900':'bg-slate-50 border-slate-200 text-slate-700'}`} style={{fontFamily:font}}>{font}</button>)}</div></div>\n          </div>\n        </div>\n      )}\n\n'''
mount_marker = '      <StepEditorModal '
if mount_marker in s and 'appearanceModalOpen &&' not in s[s.find(mount_marker)-5000:s.find(mount_marker)]:
    pos = s.find(mount_marker)
    s = s[:pos] + appearance + s[pos:]

APP.write_text(s, encoding='utf-8')

m = MODAL.read_text(encoding='utf-8')
m = m.replace("else { onComplete?.(); onClose(); }", "else { localStorage.setItem('waththiq_report_data', JSON.stringify(data)); onComplete?.(); window.setTimeout(onClose, 80); }")
m = m.replace('h-[min(92dvh,860px)]', 'h-[calc(100dvh-env(safe-area-inset-top)-env(safe-area-inset-bottom)-12px)]')
m = m.replace('className="p-3 sm:p-4 bg-slate-50 border-t border-slate-200 flex items-center justify-between gap-2 shrink-0"', 'className="p-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between gap-2 shrink-0" style={{ paddingBottom: \'max(12px, env(safe-area-inset-bottom))\' }}')
m = m.replace('px-4 sm:px-5 py-2.5', 'px-3.5 py-3')
m = m.replace('<span>إتمام جميع الخطوات وإغلاق القائمة</span>', '<span>إتمام وحفظ التقرير</span>')
MODAL.write_text(m, encoding='utf-8')

AI.write_text(r'''import React, { useMemo, useState } from 'react';
import { Sparkles, Wand2, CheckCircle2, Loader2, WifiOff } from 'lucide-react';
import { ReportData } from '../../types';

interface Props {
  reportData: ReportData;
  onApplyContent: (generated: Partial<ReportData>) => void;
  onApplySingleField?: (field: keyof ReportData, value: string) => void;
}

const PRESETS = ['برنامج تعليمي', 'مبادرة مدرسية', 'فعالية توعوية', 'الصحة المدرسية', 'المهارات الرقمية', 'الانضباط المدرسي'];

function localDraft(topic: string, data: ReportData): Partial<ReportData> {
  const subject = topic.trim() || data.title || 'البرنامج التعليمي';
  const audience = data.targetAudience || 'الفئة المستهدفة';
  return {
    title: data.title || `تقرير توثيق ${subject}`,
    subtitle: data.subtitle || `توثيق التنفيذ وقياس الأثر المتحقق لـ ${subject}`,
    categoryTag: data.categoryTag || 'برنامج تربوي وتعليمي',
    generalGoal: `تنفيذ ${subject} بصورة منظمة تسهم في رفع مستوى الوعي والمشاركة وتحقيق أثر تربوي قابل للقياس لدى ${audience}.`,
    detailedGoals: `رفع مستوى الوعي والمعرفة المرتبطة بموضوع ${subject}\nتعزيز المشاركة الفاعلة والتطبيق العملي لدى ${audience}\nقياس أثر التنفيذ ومتابعة مؤشرات التحسن\nتوثيق المخرجات والشواهد بصورة مهنية`,
    executionMechanism: `التخطيط المسبق وتحديد الفئة المستهدفة والاحتياج\nتهيئة المواد والأدوات وتوزيع الأدوار والمسؤوليات\nتنفيذ الأنشطة والتطبيقات وفق الخطة الزمنية\nتوثيق التنفيذ وجمع المؤشرات والشواهد\nتحليل النتائج وصياغة التوصيات ومقترحات التحسين`,
    resultsAndImpact: `تحقق مشاركة إيجابية من الفئة المستهدفة\nارتفاع مستوى الوعي والتفاعل مع موضوع البرنامج\nتوثيق المخرجات والشواهد بصورة منظمة\nتوفير مؤشرات قابلة للاستفادة منها في تحسين البرامج القادمة`,
    recommendations: `استمرار متابعة الأثر بعد انتهاء التنفيذ\nتطوير الأنشطة وفق التغذية الراجعة ونتائج القياس\nتوسيع نطاق الاستفادة من الممارسات الناجحة`,
  };
}

export const AIEducationalAssistant: React.FC<Props> = ({ reportData, onApplyContent }) => {
  const [topic, setTopic] = useState(reportData.title || '');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const apiBase = useMemo(() => (import.meta.env.VITE_AI_API_BASE_URL || '').replace(/\/$/, ''), []);

  const generate = async () => {
    setLoading(true); setMessage('');
    try {
      if (apiBase) {
        const response = await fetch(`${apiBase}/api/ai/generate-content`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ topic: topic || reportData.title, reportData }),
        });
        if (response.ok) {
          const payload = await response.json();
          const generated = payload.generated || payload.content || payload;
          onApplyContent(generated);
          setMessage('تم إنشاء المحتوى الذكي وتطبيقه على التقرير.');
          return;
        }
      }
      onApplyContent(localDraft(topic, reportData));
      setMessage('تم إنشاء مسودة ذكية محلياً داخل التطبيق بدون الحاجة للخادم.');
    } catch (error) {
      console.warn('Remote AI unavailable, using local smart draft.', error);
      onApplyContent(localDraft(topic, reportData));
      setMessage('تعذر الاتصال بالخدمة الخارجية؛ تم إنشاء مسودة ذكية محلياً.');
    } finally { setLoading(false); }
  };

  return <div className="rounded-2xl border border-amber-200 bg-gradient-to-br from-amber-50 to-emerald-50 p-3.5 space-y-3">
    <div className="flex items-center gap-2"><span className="w-9 h-9 rounded-xl bg-emerald-900 text-amber-300 flex items-center justify-center"><Sparkles className="w-4 h-4"/></span><div><div className="text-xs font-black text-emerald-950">المساعد التعليمي الذكي</div><div className="text-[10px] text-slate-500">يعمل محلياً، ويستخدم الخدمة السحابية تلقائياً عند توفرها</div></div></div>
    <input value={topic} onChange={(e)=>setTopic(e.target.value)} placeholder="اكتب موضوع البرنامج أو المبادرة" className="w-full px-3 py-2.5 rounded-xl border border-slate-300 bg-white text-xs font-semibold outline-none focus:border-emerald-700" />
    <div className="flex gap-1.5 overflow-x-auto no-scrollbar">{PRESETS.map(p=><button key={p} type="button" onClick={()=>setTopic(p)} className="shrink-0 px-2.5 py-1.5 rounded-lg bg-white border border-slate-200 text-[10px] font-bold text-slate-700">{p}</button>)}</div>
    <button type="button" onClick={generate} disabled={loading} className="w-full py-2.5 rounded-xl bg-emerald-800 text-white text-xs font-black flex items-center justify-center gap-2 disabled:opacity-60">{loading?<Loader2 className="w-4 h-4 animate-spin"/>:<Wand2 className="w-4 h-4 text-amber-300"/>}<span>{loading?'جاري إنشاء المحتوى...':'إنشاء محتوى التقرير الآن'}</span></button>
    {message && <div className="text-[10px] font-bold text-emerald-800 flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5"/>{message}</div>}
    {!apiBase && <div className="text-[9px] text-slate-500 flex items-center gap-1"><WifiOff className="w-3 h-3"/>الوضع المحلي مفعل لضمان عمل المساعد داخل APK.</div>}
  </div>;
};
''', encoding='utf-8')

css = CSS.read_text(encoding='utf-8')
if '/* Android mobile-first hardening */' not in css:
    css += r'''

/* Android mobile-first hardening */
html, body, #root { width: 100%; max-width: 100%; overflow-x: hidden; }
body { overscroll-behavior-x: none; -webkit-text-size-adjust: 100%; }
button, input, select, textarea { touch-action: manipulation; }
@media (max-width: 600px) {
  .a4-sheet { flex: none; }
  header { max-width: 100vw; }
}
'''
    CSS.write_text(css, encoding='utf-8')

print('Android mobile-first fixes applied: modal completion, native export/print, AI fallback, appearance, branding footer, responsive layout.')

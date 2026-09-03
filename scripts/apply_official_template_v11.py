#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'src/App.tsx'
CSS = ROOT / 'src/index.css'
TYPES = ROOT / 'src/types.ts'
PRESETS = ROOT / 'src/data/presets.ts'
TEMPLATE = ROOT / 'src/components/templates/Template5InstitutionalMilestone.tsx'
EDITORS = [
    ROOT / 'src/components/Editor/ReportEditorForm.tsx',
    ROOT / 'src/components/Editor/StepEditorModal.tsx',
]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f'v11: expected block not found: {label}')
    return text.replace(old, new, 1)


# -----------------------------------------------------------------------------
# Types: preserve existing fields and add two independent official-template fields.
# -----------------------------------------------------------------------------
t = TYPES.read_text(encoding='utf-8')
if 'optionalLogoUrl?: string;' not in t:
    t = t.replace(
        '  customLogoUrl?: string; // الشعار المرفوع\n',
        '  customLogoUrl?: string; // شعار وزارة التعليم المرفوع\n'
        '  optionalLogoUrl?: string; // شعار اختياري للتقرير / البرنامج / المبادرة\n'
    )
if 'supporterName?: string;' not in t:
    t = t.replace(
        "  executorName: string; // 'الاسم'\n",
        "  executorName: string; // 'الاسم'\n  supporterName?: string; // مساند/ة التقرير\n"
    )
TYPES.write_text(t, encoding='utf-8')

# Defaults are backward compatible because both additions are optional, but make new reports explicit.
p = PRESETS.read_text(encoding='utf-8')
if "optionalLogoUrl: ''," not in p:
    p = p.replace("  customLogoUrl: '',\n", "  customLogoUrl: '',\n  optionalLogoUrl: '',\n", 1)
    # sample block as well
    second = p.find("  customLogoUrl: '',", p.find("export const SAMPLE_REPORT_DATA"))
    if second >= 0 and "optionalLogoUrl" not in p[second:second+120]:
        end = second + len("  customLogoUrl: '',")
        p = p[:end] + "\n  optionalLogoUrl: ''," + p[end:]
if "supporterName: ''," not in p:
    p = p.replace("  executorName: '',\n", "  executorName: '',\n  supporterName: '',\n", 1)
    second = p.find("  executorName:", p.find("export const SAMPLE_REPORT_DATA"))
    if second >= 0:
        line_end = p.find('\n', second)
        if 'supporterName' not in p[line_end:line_end+100]:
            p = p[:line_end+1] + "  supporterName: '',\n" + p[line_end+1:]
PRESETS.write_text(p, encoding='utf-8')

# -----------------------------------------------------------------------------
# Editors: separate ministry logo from optional report logo; cap official evidence at 4.
# -----------------------------------------------------------------------------
logo_ui = r'''            {/* Independent logos: ministry + optional report logo */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="bg-emerald-50/60 border border-emerald-200/80 rounded-xl p-3 space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <SaudiMinistryLogo customLogoUrl={data.customLogoUrl} className="h-10" color="#007A5E" showText={false} />
                    <div className="min-w-0">
                      <div className="text-xs font-black text-emerald-950">شعار وزارة التعليم</div>
                      <div className="text-[10px] font-semibold text-slate-500 truncate">
                        {data.customLogoUrl ? 'تم إرفاق الشعار الرسمي' : 'يمكن إرفاق شعار الوزارة بدقة عالية'}
                      </div>
                    </div>
                  </div>
                  {data.customLogoUrl && (
                    <button type="button" onClick={() => updateField('customLogoUrl', '')} className="p-1.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-700" title="حذف شعار وزارة التعليم">
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
                <label className="w-full py-2 px-3 rounded-lg bg-white border border-emerald-300 text-emerald-950 hover:bg-emerald-50 text-[11px] font-bold flex items-center justify-center gap-2 cursor-pointer">
                  <Upload className="w-3.5 h-3.5 text-emerald-700" />
                  <span>{data.customLogoUrl ? 'تغيير شعار وزارة التعليم' : 'إرفاق شعار وزارة التعليم'}</span>
                  <input type="file" accept="image/png,image/jpeg,image/webp,image/svg+xml" onChange={handleLogoUpload} className="hidden" />
                </label>
              </div>

              <div className="bg-teal-50/60 border border-teal-200/80 rounded-xl p-3 space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    {data.optionalLogoUrl ? (
                      <img src={data.optionalLogoUrl} alt="الشعار الاختياري للتقرير" className="h-10 w-20 object-contain shrink-0" />
                    ) : (
                      <div className="h-10 w-14 rounded-lg border border-dashed border-teal-300 flex items-center justify-center text-teal-600 shrink-0"><Sparkles className="w-4 h-4" /></div>
                    )}
                    <div className="min-w-0">
                      <div className="text-xs font-black text-teal-950">شعار اختياري للتقرير</div>
                      <div className="text-[10px] font-semibold text-slate-500 truncate">برنامج / مبادرة / فعالية / جهة مشاركة</div>
                    </div>
                  </div>
                  {data.optionalLogoUrl && (
                    <button type="button" onClick={() => updateField('optionalLogoUrl', '')} className="p-1.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-700" title="حذف الشعار الاختياري">
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
                <label className="w-full py-2 px-3 rounded-lg bg-white border border-teal-300 text-teal-950 hover:bg-teal-50 text-[11px] font-bold flex items-center justify-center gap-2 cursor-pointer">
                  <Upload className="w-3.5 h-3.5 text-teal-700" />
                  <span>{data.optionalLogoUrl ? 'تغيير الشعار الاختياري' : 'إرفاق شعار اختياري'}</span>
                  <input type="file" accept="image/png,image/jpeg,image/webp,image/svg+xml" onChange={handleOptionalLogoUpload} className="hidden" />
                </label>
              </div>
            </div>

'''

for path in EDITORS:
    s = path.read_text(encoding='utf-8')

    # New independent upload handler.
    if 'handleOptionalLogoUpload' not in s:
        marker = '  // Multiple Photos Upload (1 to 15)\n'
        if marker not in s:
            marker = '  // Multiple Photos Upload'
        idx = s.find(marker)
        if idx < 0:
            raise SystemExit(f'v11: photo upload marker not found in {path.name}')
        optional_handler = r'''  const handleOptionalLogoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => updateField('optionalLogoUrl', event.target?.result as string);
    reader.readAsDataURL(file);
    e.target.value = '';
  };

  const maxPhotos = data.templateId === 'template-5-institutional' ? 4 : 15;

'''
        s = s[:idx] + optional_handler + s[idx:]
    elif "const maxPhotos = data.templateId" not in s:
        pos = s.find('  // Multiple Photos Upload')
        s = s[:pos] + "  const maxPhotos = data.templateId === 'template-5-institutional' ? 4 : 15;\n\n" + s[pos:]

    s = s.replace(
        'const remainingSlots = Math.max(0, 15 - (data.photos || []).length);',
        'const remainingSlots = Math.max(0, maxPhotos - (data.photos || []).length);'
    )
    s = s.replace(
        'caption: `شاهد ${newPhotos.length + 1}`,',
        "caption: data.templateId === 'template-5-institutional' ? '' : `شاهد ${newPhotos.length + 1}` ,"
    )

    # Replace the combined logo card with two independent controls.
    a = s.find('            {/* Ministry Info Box */}')
    b = s.find('            {/* Directorate Selection */}', a)
    if a >= 0 and b > a:
        s = s[:a] + logo_ui + s[b:]
    elif 'Independent logos: ministry + optional report logo' not in s:
        raise SystemExit(f'v11: ministry logo UI block not found in {path.name}')

    # Neutral supporter field for the official template only.
    if "updateField('supporterName'" not in s:
        manager_marker = '''                <div>\n                  <label className="text-[11px] font-bold text-slate-700 block mb-1">\n                    اسم مدير/ة المدرسة (الاعتماد)'''
        supporter = r'''                {data.templateId === 'template-5-institutional' && (
                  <div>
                    <label className="text-[11px] font-bold text-slate-700 block mb-1">اسم مساند/ة التقرير</label>
                    <input
                      type="text"
                      value={data.supporterName ?? ''}
                      onChange={(e) => updateField('supporterName', e.target.value)}
                      placeholder="يظهر في القالب الرسمي فقط عند إدخال الاسم"
                      className="w-full px-3 py-2 rounded-xl border border-slate-300 focus:border-emerald-700 outline-none text-xs font-semibold"
                    />
                  </div>
                )}

                {data.templateId === 'template-5-institutional' && (
                  <div>
                    <label className="text-[11px] font-bold text-slate-700 block mb-1">اسم معد/ة التقرير</label>
                    <input
                      type="text"
                      value={data.signatures?.preparedByName ?? ''}
                      onChange={(e) => updateField('signatures', { ...data.signatures, preparedByName: e.target.value })}
                      placeholder="يظهر في قسم التوقيعات عند إدخاله"
                      className="w-full px-3 py-2 rounded-xl border border-slate-300 focus:border-emerald-700 outline-none text-xs font-semibold"
                    />
                  </div>
                )}

'''
        if manager_marker in s:
            s = s.replace(manager_marker, supporter + manager_marker, 1)
        else:
            raise SystemExit(f'v11: manager field marker not found in {path.name}')

    # Make upload limit visible and accurate.
    s = s.replace('رفع الشواهد المصورة (حتى 15 صورة)', 'رفع الشواهد المصورة (حتى {maxPhotos} صور)')
    s = s.replace('Upload Area for up to 15 Photos', 'Upload Area with template-aware limit')
    s = s.replace('يتم تنظيم وترقيم الصور تلقائياً داخل شبكة التقرير المطبوع حسب مقاس الصفحة.', 'يتم تنظيم الصور تلقائياً داخل شبكة التقرير حسب مساحة صفحة A4.')

    path.write_text(s, encoding='utf-8')

# -----------------------------------------------------------------------------
# Official template: copy the reviewed source patch.
# -----------------------------------------------------------------------------
PATCH_DIR = ROOT / 'patches/v11'
TEMPLATE.write_text((PATCH_DIR / 'Template5InstitutionalMilestone.tsx').read_text(encoding='utf-8'), encoding='utf-8')

# -----------------------------------------------------------------------------
# App: label official template, keep preview as source of truth, official export via html2canvas.
# -----------------------------------------------------------------------------
a = APP.read_text(encoding='utf-8')
a = a.replace("{ id: 'template-5-institutional', label: 'تقرير إنجاز مؤسسي', number: 5 },", "{ id: 'template-5-institutional', label: 'القالب الرسمي', number: 5 },")
a = a.replace('<div ref={reportRef} style={{ width:\'794px\', height:\'1123px\', transform:`scale(${zoomLevel})`', '<div ref={reportRef} className="wasm-screen-report" style={{ width:\'794px\', height:\'1123px\', transform:`scale(${zoomLevel})`')

# Print: wait for the actual preview resources before handing the WebView to Android PrintManager.
print_start = a.find('  // Native Android printing with browser fallback.')
print_end = a.find('  const saveNativeDataUrl', print_start)
if print_start >= 0 and print_end > print_start:
    print_fn = r'''  const waitForReportResources = async (root?: HTMLElement | null) => {
    if (document.fonts?.ready) await document.fonts.ready;
    try {
      if (document.fonts?.load) await document.fonts.load(`700 16px "${reportData.fontFamily}"`, 'وزارة التعليم الهدف العام الأهداف التفصيلية');
    } catch (_) {}
    if (root) {
      const images = Array.from(root.querySelectorAll('img')) as HTMLImageElement[];
      await Promise.all(images.map(async (img) => {
        if (!img.complete || img.naturalWidth <= 0) {
          await new Promise<void>((resolve) => {
            const done = () => resolve();
            img.addEventListener('load', done, { once: true });
            img.addEventListener('error', done, { once: true });
          });
        }
        try { if (img.decode) await img.decode(); } catch (_) {}
      }));
    }
    await new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve())));
  };

  // Native Android A4 printing with a prepared, stable report DOM.
  const handlePrint = async () => {
    setExportDropdownOpen(false);
    setIsExporting(true);
    setSaveToast('جارٍ تجهيز طباعة A4...');
    try {
      await waitForReportResources(reportRef.current);
      if (isNativeAndroid) {
        await WasmNative.print({ jobName: reportData.title || 'تقرير وَسْم' });
      } else {
        window.print();
      }
      setSaveToast('تم فتح معاينة الطباعة A4.');
    } catch (error) {
      console.error('Print A4 failed:', error);
      try { window.print(); }
      catch (_) { setSaveToast('تعذر تجهيز التقرير للطباعة. يرجى المحاولة مرة أخرى.'); }
    } finally {
      setIsExporting(false);
      setTimeout(() => setSaveToast(''), 3500);
    }
  };

'''
    a = a[:print_start] + print_fn + a[print_end:]
else:
    raise SystemExit('v11: print function region not found')

# Replace export pipeline after all v8/v9/v10 patches. Non-official templates retain html-to-image behavior.
exp_start = a.find('  const buildExactA4Clone')
exp_end = a.find('  const templates:', exp_start)
if exp_start < 0 or exp_end < 0:
    raise SystemExit('v11: export region not found')
exports = r'''  const buildExactA4Clone = async (): Promise<{host:HTMLDivElement,wrapper:HTMLElement,page:HTMLElement}> => {
    await waitForReportResources(reportRef.current);
    const sourceWrapper = reportRef.current?.querySelector('.wasm-report-appearance') as HTMLElement | null;
    const sourcePage = sourceWrapper?.querySelector('.a4-sheet') as HTMLElement | null;
    if (!sourceWrapper || !sourcePage) throw new Error('لم يتم العثور على معاينة التقرير A4');

    const host = document.createElement('div');
    host.setAttribute('aria-hidden', 'true');
    host.className = 'wasm-export-host';
    host.style.cssText = 'position:fixed;left:0;top:0;width:794px;height:1123px;pointer-events:none;z-index:-2147483000;background:#fff;overflow:hidden;';

    const wrapper = sourceWrapper.cloneNode(true) as HTMLElement;
    wrapper.classList.add('wasm-export-wrapper');
    wrapper.style.setProperty('display', 'block', 'important');
    wrapper.style.setProperty('visibility', 'visible', 'important');
    wrapper.style.setProperty('opacity', '1', 'important');
    wrapper.style.setProperty('transform', 'none', 'important');
    wrapper.style.setProperty('position', 'relative', 'important');
    wrapper.style.setProperty('width', '794px', 'important');
    wrapper.style.setProperty('height', '1123px', 'important');
    wrapper.style.setProperty('margin', '0', 'important');
    wrapper.style.setProperty('font-family', reportData.fontFamily, 'important');

    const page = wrapper.querySelector('.a4-sheet') as HTMLElement | null;
    if (!page) throw new Error('لم يتم العثور على صفحة A4 داخل التقرير');
    page.classList.add('wasm-export-clone');
    page.style.setProperty('display', 'block', 'important');
    page.style.setProperty('visibility', 'visible', 'important');
    page.style.setProperty('opacity', '1', 'important');
    page.style.setProperty('transform', 'none', 'important');
    page.style.setProperty('position', 'relative', 'important');
    page.style.setProperty('left', '0', 'important');
    page.style.setProperty('top', '0', 'important');
    page.style.setProperty('width', '794px', 'important');
    page.style.setProperty('height', '1123px', 'important');
    page.style.setProperty('min-width', '794px', 'important');
    page.style.setProperty('min-height', '1123px', 'important');
    page.style.setProperty('max-width', '794px', 'important');
    page.style.setProperty('max-height', '1123px', 'important');
    page.style.setProperty('margin', '0', 'important');

    const remoteImages = Array.from(wrapper.querySelectorAll('img')) as HTMLImageElement[];
    remoteImages.forEach(img => {
      const src = img.getAttribute('src') || '';
      if (/^https?:\/\//i.test(src)) img.crossOrigin = 'anonymous';
    });

    host.appendChild(wrapper);
    document.body.appendChild(host);
    await waitForReportResources(wrapper);
    return { host, wrapper, page };
  };

  const renderLegacyA4DataUrl = async (format:'png'|'jpeg'): Promise<string> => {
    const { host, wrapper } = await buildExactA4Clone();
    try {
      const baseOptions = { width:794, height:1123, pixelRatio:2.0, backgroundColor:'#ffffff', cacheBust:true };
      const render = async (skipFonts:boolean) => format === 'png'
        ? toPng(wrapper, { ...baseOptions, skipFonts })
        : toJpeg(wrapper, { ...baseOptions, skipFonts, quality:.96 });
      let dataUrl:string;
      try { dataUrl = await render(false); }
      catch (first) { console.warn('Legacy font embedding retry', first); dataUrl = await render(true); }
      if (!dataUrl || dataUrl.length < 15000) throw new Error('تعذر إنشاء صفحة A4 كاملة');
      return dataUrl;
    } finally { host.remove(); }
  };

  const renderOfficialA4DataUrl = async (format:'png'|'jpeg'): Promise<string> => {
    const { host, page } = await buildExactA4Clone();
    try {
      const content = page.querySelector('[data-official-content]') as HTMLElement | null;
      if (content && content.scrollHeight > content.clientHeight + 2) {
        throw new Error('محتوى القالب الرسمي يتجاوز المساحة الآمنة لصفحة A4');
      }
      const canvas = await html2canvas(page, {
        backgroundColor: '#ffffff',
        scale: 2,
        useCORS: true,
        allowTaint: false,
        logging: false,
        width: 794,
        height: 1123,
        windowWidth: 794,
        windowHeight: 1123,
        scrollX: 0,
        scrollY: 0,
      });
      if (!canvas.width || !canvas.height) throw new Error('تعذر رسم صفحة A4');
      const dataUrl = format === 'png' ? canvas.toDataURL('image/png') : canvas.toDataURL('image/jpeg', .97);
      if (!dataUrl || dataUrl.length < 18000) throw new Error('ناتج التصدير فارغ أو غير مكتمل');
      return dataUrl;
    } finally { host.remove(); }
  };

  const renderExactA4DataUrl = async (format:'png'|'jpeg'): Promise<string> => {
    return reportData.templateId === 'template-5-institutional'
      ? renderOfficialA4DataUrl(format)
      : renderLegacyA4DataUrl(format);
  };

  const handleExportPDF = async () => {
    setExportDropdownOpen(false); setIsExporting(true); setSaveToast('جارٍ إنشاء PDF A4...');
    const safeTitle=(reportData.title||'تقرير_وَسْم').trim().replace(/[/\\?%*:|"<>]/g,'_').replace(/\s+/g,'_');
    try {
      const official = reportData.templateId === 'template-5-institutional';
      const image = await renderExactA4DataUrl(official ? 'png' : 'jpeg');
      const pdf = new jsPDF({ orientation:'portrait', unit:'mm', format:'a4', compress:true });
      pdf.addImage(image, official ? 'PNG' : 'JPEG', 0, 0, 210, 297, undefined, official ? 'NONE' : 'FAST');
      const fileName=`تقرير_${safeTitle}.pdf`;
      if (isNativeAndroid) await saveNativeDataUrl(fileName, 'application/pdf', pdf.output('datauristring'));
      else pdf.save(fileName);
      setSaveToast('تم حفظ PDF A4 بنجاح.');
    } catch (err:any) {
      console.error('PDF A4 export failed', err);
      setSaveToast(`تعذر PDF: ${err?.message || 'خطأ غير معروف'}`);
    } finally { setIsExporting(false); setTimeout(()=>setSaveToast(''),5000); }
  };

  const handleExportImage = async () => {
    setExportDropdownOpen(false); setIsExporting(true); setSaveToast('جارٍ إنشاء PNG A4...');
    const safeTitle=(reportData.title||'تقرير_وَسْم').trim().replace(/[/\\?%*:|"<>]/g,'_').replace(/\s+/g,'_');
    try {
      const png = await renderExactA4DataUrl('png');
      const fileName=`تقرير_${safeTitle}.png`;
      if (isNativeAndroid) await saveNativeDataUrl(fileName,'image/png',png);
      else { const link=document.createElement('a'); link.download=fileName; link.href=png; document.body.appendChild(link); link.click(); link.remove(); }
      setSaveToast('تم حفظ PNG A4 بنجاح.');
    } catch (err:any) {
      console.error('PNG A4 export failed', err);
      setSaveToast(`تعذر PNG: ${err?.message || 'خطأ غير معروف'}`);
    } finally { setIsExporting(false); setTimeout(()=>setSaveToast(''),5000); }
  };

'''
a = a[:exp_start] + exports + a[exp_end:]
APP.write_text(a, encoding='utf-8')

# -----------------------------------------------------------------------------
# CSS: append the reviewed official-template CSS patch after all previous mobile patches.
# -----------------------------------------------------------------------------
c = CSS.read_text(encoding='utf-8')
marker = '/* WASM v11 official template */'
if marker not in c:
    css_patch = (PATCH_DIR / 'official-template.css').read_text(encoding='utf-8')
    c += '\n\n' + css_patch.rstrip() + '\n'
CSS.write_text(c, encoding='utf-8')

# Verification hooks used by workflow.
checks = {
    TYPES: ['optionalLogoUrl?: string;', 'supporterName?: string;'],
    TEMPLATE: ['official-template-page', 'الشواهد والتوثيق الميداني', 'معد/ة التقرير', 'مدير/ة المدرسة'],
    APP: ['renderOfficialA4DataUrl', 'html2canvas(page', "label: 'القالب الرسمي'"],
    CSS: ['WASM v11 official template', '.official-evidence-4', '.wasm-screen-report'],
}
for path, needles in checks.items():
    text = path.read_text(encoding='utf-8')
    for needle in needles:
        if needle not in text:
            raise SystemExit(f'v11 verification failed: {needle} missing in {path}')
print('v11: official template + independent logos + 4-photo evidence + preview/export/print parity applied')

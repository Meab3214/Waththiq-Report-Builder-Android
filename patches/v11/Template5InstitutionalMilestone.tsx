import React, { useLayoutEffect, useMemo, useRef, useState } from 'react';
import { ReportData } from '../../types';
import { SaudiMinistryLogo } from '../common/SaudiMinistryLogo';
import {
  BookOpen,
  CalendarDays,
  Camera,
  CheckCircle2,
  ClipboardCheck,
  FileCheck2,
  Lightbulb,
  MapPin,
  Sparkles,
  Target,
  UserCheck,
  Users,
  Clock3,
} from 'lucide-react';

interface TemplateProps { data: ReportData; }

const hasValue = (value: unknown): boolean => {
  if (typeof value === 'number') return Number.isFinite(value);
  if (typeof value === 'string') return value.trim().length > 0;
  return Boolean(value);
};

const splitLines = (value?: string) => (value || '').split('\n').map(v => v.trim()).filter(Boolean);

export const Template5InstitutionalMilestone: React.FC<TemplateProps> = ({ data }) => {
  const contentRef = useRef<HTMLDivElement>(null);
  const [fitLevel, setFitLevel] = useState(0);

  const goals = splitLines(data.detailedGoals);
  const results = splitLines(data.resultsAndImpact);
  const mechanism = splitLines(data.executionMechanism);
  const recommendations = splitLines(data.recommendations);
  const photos = (data.photos || []).filter(photo => Boolean(photo?.url)).slice(0, 4);

  const executorName = (data.executorName || '').trim();
  const supporterName = (data.supporterName || '').trim();
  const preparedByName = (data.signatures?.preparedByName || '').trim();
  const approverName = (data.approverName || data.signatures?.approvedByName || '').trim();

  const metadata = [
    { label: 'فترة التنفيذ', value: data.executionDate, icon: CalendarDays },
    { label: 'مدة البرنامج', value: data.duration, icon: Clock3 },
    { label: 'الفئة المستهدفة', value: data.targetAudience, icon: Users },
    { label: 'عدد المستفيدين/ات', value: data.beneficiariesCount, icon: Users },
    { label: 'مكان التنفيذ', value: data.location, icon: MapPin },
    { label: 'منفذ/ة', value: executorName, icon: UserCheck },
    { label: 'مساند/ة', value: supporterName, icon: Users },
  ].filter(item => hasValue(item.value));

  const metrics = [
    { label: 'المستهدف', value: data.targetMetric },
    { label: 'المتحقق', value: data.achievedMetric },
    { label: 'نسبة الرضا', value: hasValue(data.satisfactionRate) ? `${data.satisfactionRate}%` : '' },
    { label: 'نسبة الحضور', value: hasValue(data.attendanceRate) ? `${data.attendanceRate}%` : '' },
    { label: 'عدد الأنشطة', value: data.activitiesCount },
  ].filter(item => hasValue(item.value));

  const fitSignature = useMemo(() => [
    data.title, data.subtitle, data.categoryTag, data.generalGoal, data.detailedGoals,
    data.resultsAndImpact, data.executionMechanism, data.recommendations, data.notes,
    data.directorate, data.schoolName, data.department, data.academicYear, data.semester,
    executorName, supporterName, preparedByName, approverName, photos.length, metadata.length,
  ].map(v => String(v || '').length).join('|'), [
    data.title, data.subtitle, data.categoryTag, data.generalGoal, data.detailedGoals,
    data.resultsAndImpact, data.executionMechanism, data.recommendations, data.notes,
    data.directorate, data.schoolName, data.department, data.academicYear, data.semester,
    executorName, supporterName, approverName, photos.length, metadata.length, metrics.length,
  ]);

  useLayoutEffect(() => {
    let cancelled = false;
    let level = 0;
    setFitLevel(0);
    const measure = () => {
      if (cancelled) return;
      const node = contentRef.current;
      if (!node) return;
      if (node.scrollHeight > node.clientHeight + 1 && level < 3) {
        level += 1;
        setFitLevel(level);
        requestAnimationFrame(() => requestAnimationFrame(measure));
      }
    };
    requestAnimationFrame(() => requestAnimationFrame(measure));
    return () => { cancelled = true; };
  }, [fitSignature]);

  const hasSignatures = Boolean(preparedByName || approverName);
  const hasRecommendations = recommendations.length > 0 || hasValue(data.notes);
  const title = (data.title || '').trim();

  return (
    <div
      className={`a4-sheet official-template-page official-fit-${fitLevel} bg-white text-slate-800 relative mx-auto overflow-hidden`}
      style={{
        width: '210mm',
        height: '297mm',
        padding: 'var(--official-page-padding)',
        fontFamily: data.fontFamily ? `'${data.fontFamily}', sans-serif` : "'Cairo', sans-serif",
      }}
      dir="rtl"
    >
      <div ref={contentRef} data-official-content className="official-content h-full flex flex-col">
        <header className="official-top-frame relative overflow-hidden">
          <div className="official-frame-icons" aria-hidden="true">
            <span><BookOpen className="w-3.5 h-3.5" /></span>
            <span><Lightbulb className="w-3.5 h-3.5" /></span>
            <span><FileCheck2 className="w-3.5 h-3.5" /></span>
          </div>

          <div className="relative z-10 flex items-center justify-between gap-4">
            <div className="flex items-center gap-2.5 min-w-0">
              {data.showLogo !== false && (
                <SaudiMinistryLogo
                  customLogoUrl={data.customLogoUrl}
                  className="official-ministry-logo h-12 shrink-0"
                  color="#0B6658"
                  showText={false}
                />
              )}
              <div className="min-w-0 leading-normal">
                <div className="official-ministry-title font-black text-[#0B5147]">وزارة التعليم</div>
                {hasValue(data.directorate) && <div className="official-header-sub font-bold text-slate-700">{data.directorate}</div>}
                {hasValue(data.schoolName) && <div className="official-header-sub font-semibold text-slate-600">{data.schoolName}</div>}
                {hasValue(data.department) && <div className="official-header-tiny font-semibold text-slate-500">{data.department}</div>}
              </div>
            </div>

            {data.optionalLogoUrl && (
              <div className="official-optional-logo-wrap shrink-0 flex items-center justify-center">
                <img src={data.optionalLogoUrl} alt="الشعار الاختياري للتقرير" className="official-optional-logo object-contain" />
              </div>
            )}
          </div>
        </header>

        <main className="official-main flex flex-col">
          {(hasValue(data.reportType) || title || hasValue(data.subtitle) || hasValue(data.categoryTag)) && (
            <section className="official-title-block flex items-end justify-between gap-4">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  {hasValue(data.reportType) && <span className="official-report-type">{data.reportType}</span>}
                  {hasValue(data.categoryTag) && <span className="official-category-tag">{data.categoryTag}</span>}
                </div>
                {title && <h1 className="official-title font-black text-[#103D37]">{title}</h1>}
                {hasValue(data.subtitle) && <p className="official-subtitle font-semibold text-slate-600">{data.subtitle}</p>}
              </div>
              {(hasValue(data.academicYear) || hasValue(data.semester)) && (
                <div className="official-term text-left shrink-0">
                  {hasValue(data.academicYear) && <div className="font-black text-[#0B6658]">{data.academicYear}</div>}
                  {hasValue(data.semester) && <div className="font-semibold text-slate-500">{data.semester}</div>}
                </div>
              )}
            </section>
          )}

          {metadata.length > 0 && (
            <section className="official-info-grid" style={{ gridTemplateColumns: `repeat(${Math.min(4, metadata.length)}, minmax(0, 1fr))` }}>
              {metadata.map(({ label, value, icon: Icon }, idx) => (
                <div key={`${label}-${idx}`} className="official-info-item">
                  <div className="official-info-label flex items-center gap-1"><Icon className="w-3 h-3" /><span>{label}</span></div>
                  <div className="official-info-value">{String(value)}</div>
                </div>
              ))}
            </section>
          )}

          {hasValue(data.generalGoal) && (
            <section className="official-section official-goal">
              <div className="official-section-head"><Target className="w-3.5 h-3.5" /><span>الهدف العام</span><i /></div>
              <p className="official-body-text">{data.generalGoal}</p>
            </section>
          )}

          {(goals.length > 0 || results.length > 0) && (
            <div className={`official-dual-grid ${goals.length > 0 && results.length > 0 ? 'grid-cols-2' : 'grid-cols-1'}`}>
              {goals.length > 0 && (
                <section className="official-section">
                  <div className="official-section-head"><Sparkles className="w-3.5 h-3.5" /><span>الأهداف التفصيلية</span><i /></div>
                  <div className="official-list">
                    {goals.map((goal, idx) => <div key={idx} className="official-list-row"><b>{idx + 1}</b><span>{goal}</span></div>)}
                  </div>
                </section>
              )}
              {results.length > 0 && (
                <section className="official-section">
                  <div className="official-section-head"><CheckCircle2 className="w-3.5 h-3.5" /><span>النتائج والأثر الملموس</span><i /></div>
                  <div className="official-list">
                    {results.map((item, idx) => <div key={idx} className="official-check-row"><CheckCircle2 className="w-3 h-3" /><span>{item}</span></div>)}
                  </div>
                </section>
              )}
            </div>
          )}

          {(mechanism.length > 0 || hasRecommendations) && (
            <div className={`official-dual-grid ${mechanism.length > 0 && hasRecommendations ? 'grid-cols-2' : 'grid-cols-1'}`}>
              {mechanism.length > 0 && (
                <section className="official-section">
                  <div className="official-section-head"><ClipboardCheck className="w-3.5 h-3.5" /><span>آلية وأساليب التنفيذ</span><i /></div>
                  <div className="official-list">
                    {mechanism.map((item, idx) => <div key={idx} className="official-check-row"><span className="official-dot" /><span>{item}</span></div>)}
                  </div>
                </section>
              )}
              {hasRecommendations && (
                <section className="official-section official-note-section">
                  <div className="official-section-head"><Lightbulb className="w-3.5 h-3.5" /><span>التوصيات والملاحظات</span><i /></div>
                  <div className="official-list">
                    {recommendations.map((item, idx) => <div key={idx} className="official-check-row"><span className="official-dot" /><span>{item}</span></div>)}
                    {hasValue(data.notes) && <div className="official-body-text">{data.notes}</div>}
                  </div>
                </section>
              )}
            </div>
          )}

          {data.showKpi && metrics.length > 0 && (
            <section className="official-metrics" style={{ gridTemplateColumns: `repeat(${Math.min(5, metrics.length)}, minmax(0, 1fr))` }}>
              {metrics.map((item, idx) => <div key={idx}><span>{item.label}</span><b>{String(item.value)}</b></div>)}
            </section>
          )}

          {data.showPhotos !== false && photos.length > 0 && (
            <section className="official-evidence-section">
              <div className="official-section-head official-evidence-head"><Camera className="w-3.5 h-3.5" /><span>الشواهد والتوثيق الميداني</span><i /></div>
              <div className={`official-evidence-grid official-evidence-${photos.length}`}>
                {photos.map((photo, idx) => (
                  <div key={photo.id || idx} className="official-evidence-frame">
                    <img src={photo.url} alt="" referrerPolicy="no-referrer" className="official-evidence-image" />
                  </div>
                ))}
              </div>
            </section>
          )}

          {data.showSignatures !== false && hasSignatures && (
            <section className="official-signatures official-signatures-2">
              {preparedByName && <div><span>معد/ة التقرير</span><b>{preparedByName}</b><em>التوقيع: __________________</em></div>}
              {approverName && <div><span>مدير/ة المدرسة</span><b>{approverName}</b><em>التوقيع: __________________</em></div>}
            </section>
          )}
        </main>

        {data.showFooter !== false && <div className="official-footer-line" aria-hidden="true"><span /><i /></div>}
      </div>
    </div>
  );
};

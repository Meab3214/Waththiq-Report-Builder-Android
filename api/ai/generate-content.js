const MODEL = process.env.GEMINI_MODEL || 'gemini-2.5-flash';

function json(res, status, body) {
  res.statusCode = status;
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Access-Control-Allow-Methods', 'POST,OPTIONS');
  res.end(JSON.stringify(body));
}

function extractJson(text) {
  const cleaned = String(text || '').replace(/^```json\s*/i, '').replace(/^```\s*/i, '').replace(/```\s*$/i, '').trim();
  const start = cleaned.indexOf('{');
  const end = cleaned.lastIndexOf('}');
  if (start < 0 || end < start) throw new Error('Gemini did not return JSON');
  return JSON.parse(cleaned.slice(start, end + 1));
}

export default async function handler(req, res) {
  if (req.method === 'OPTIONS') return json(res, 204, {});
  if (req.method !== 'POST') return json(res, 405, { success: false, error: 'Method not allowed' });

  const apiKey = process.env.GEMINI_API_KEY || process.env.GOOGLE_GENERATIVE_AI_API_KEY;
  if (!apiKey) return json(res, 503, { success: false, error: 'AI service is not configured' });

  try {
    const body = typeof req.body === 'string' ? JSON.parse(req.body || '{}') : (req.body || {});
    const title = String(body.title || '').trim();
    if (!title) return json(res, 400, { success: false, error: 'title is required' });

    const prompt = `أنت مساعد تربوي سعودي محترف متخصص في كتابة تقارير البرامج والمبادرات والفعاليات المدرسية.\n\nاكتب محتوى أصلياً ومخصصاً للموضوع التالي، ولا تستخدم عبارات عامة محفوظة.\nالعنوان: ${title}\nنوع التقرير: ${body.reportType || ''}\nالتصنيف: ${body.category || ''}\nالفئة المستهدفة: ${body.targetAudience || ''}\n\nأعد JSON فقط، بدون Markdown، بالمفاتيح التالية حرفياً:\n{\n  "generalGoal": "هدف عام مهني ومحدد",\n  "detailedGoals": "4 أهداف تفصيلية، كل هدف في سطر مستقل",\n  "executionMechanism": "4 خطوات تنفيذ عملية، كل خطوة في سطر مستقل",\n  "resultsAndImpact": "3 إلى 4 نتائج وأثر متوقع/متحقق بصياغة قابلة للتوثيق، كل نتيجة في سطر",\n  "recommendations": "3 توصيات تطويرية، كل توصية في سطر"\n}\n\nالتزم باللغة العربية الرسمية، وتجنب اختلاق أرقام أو نسب غير مقدمة من المستخدم.`;

    const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(MODEL)}:generateContent?key=${encodeURIComponent(apiKey)}`;
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ role: 'user', parts: [{ text: prompt }] }],
        generationConfig: { temperature: 0.55, responseMimeType: 'application/json' }
      })
    });

    const raw = await response.text();
    if (!response.ok) {
      console.error('Gemini HTTP', response.status, raw.slice(0, 500));
      return json(res, 502, { success: false, error: `Gemini HTTP ${response.status}` });
    }

    const gemini = JSON.parse(raw);
    const text = gemini?.candidates?.[0]?.content?.parts?.map((p) => p.text || '').join('') || '';
    const data = extractJson(text);
    return json(res, 200, { success: true, data, model: MODEL, isFallback: false });
  } catch (error) {
    console.error(error);
    return json(res, 500, { success: false, error: 'AI generation failed' });
  }
}

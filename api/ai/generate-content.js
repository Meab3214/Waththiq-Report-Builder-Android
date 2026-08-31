function send(res,status,body){
  res.statusCode=status;
  res.setHeader('Content-Type','application/json; charset=utf-8');
  res.setHeader('Cache-Control','no-store');
  res.setHeader('Access-Control-Allow-Origin','*');
  res.setHeader('Access-Control-Allow-Headers','Content-Type, X-WASM-Client');
  res.setHeader('Access-Control-Allow-Methods','POST,OPTIONS');
  res.end(JSON.stringify(body));
}

function extractJson(text){
  const cleaned=String(text||'').replace(/^```json\s*/i,'').replace(/^```\s*/i,'').replace(/\s*```$/i,'').trim();
  const a=cleaned.indexOf('{'), b=cleaned.lastIndexOf('}');
  if(a<0||b<a) throw new Error('No JSON object in model output');
  return JSON.parse(cleaned.slice(a,b+1));
}

function promptFor(body){
  const title=String(body.title||body.topic||'').trim();
  return {
    title,
    prompt:`أنت مساعد تربوي سعودي محترف متخصص في صياغة تقارير البرامج والمبادرات والفعاليات المدرسية.
أنشئ محتوى عربياً أصلياً ومخصصاً، دون اختلاق أرقام أو نسب لم يقدمها المستخدم.
العنوان: ${title}
نوع التقرير: ${body.reportType||''}
التصنيف: ${body.category||''}
الفئة المستهدفة: ${body.targetAudience||''}

أعد JSON فقط وبدون Markdown بالمفاتيح التالية حرفياً:
{
  "generalGoal":"هدف عام مهني ومحدد",
  "detailedGoals":"4 أهداف تفصيلية، كل هدف في سطر مستقل",
  "executionMechanism":"4 خطوات تنفيذ عملية، كل خطوة في سطر مستقل",
  "resultsAndImpact":"3 إلى 4 نتائج وأثر بصياغة قابلة للتوثيق، كل نتيجة في سطر مستقل",
  "recommendations":"3 توصيات تطويرية، كل توصية في سطر مستقل"
}`
  };
}

async function viaGeminiKey(prompt){
  const key=process.env.GEMINI_API_KEY||process.env.GOOGLE_GENERATIVE_AI_API_KEY;
  if(!key) throw new Error('GEMINI_KEY_NOT_CONFIGURED');
  const model=process.env.GEMINI_MODEL||'gemini-2.5-flash';
  const url=`https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent?key=${encodeURIComponent(key)}`;
  const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
    contents:[{role:'user',parts:[{text:prompt}]}],
    generationConfig:{temperature:0.5,responseMimeType:'application/json'}
  })});
  const raw=await r.text();
  if(!r.ok) throw new Error(`GEMINI_HTTP_${r.status}: ${raw.slice(0,240)}`);
  const parsed=JSON.parse(raw);
  const text=parsed?.candidates?.[0]?.content?.parts?.map(p=>p.text||'').join('')||'';
  return {data:extractJson(text),provider:'gemini-direct',model};
}

async function viaVercelGateway(prompt){
  const token=process.env.AI_GATEWAY_API_KEY||process.env.VERCEL_OIDC_TOKEN;
  if(!token) throw new Error('AI_GATEWAY_NOT_CONFIGURED');
  const model='google/gemini-2.5-flash';
  const r=await fetch('https://ai-gateway.vercel.sh/v1/chat/completions',{
    method:'POST',
    headers:{Authorization:`Bearer ${token}`,'Content-Type':'application/json'},
    body:JSON.stringify({model,messages:[{role:'user',content:prompt}],temperature:0.5})
  });
  const raw=await r.text();
  if(!r.ok) throw new Error(`AI_GATEWAY_HTTP_${r.status}: ${raw.slice(0,240)}`);
  const parsed=JSON.parse(raw);
  const text=parsed?.choices?.[0]?.message?.content||'';
  return {data:extractJson(text),provider:'vercel-ai-gateway',model};
}

export default async function handler(req,res){
  if(req.method==='OPTIONS') return send(res,204,{});
  if(req.method!=='POST') return send(res,405,{success:false,error:'Method not allowed'});
  try{
    const body=typeof req.body==='string'?JSON.parse(req.body||'{}'):(req.body||{});
    const {title,prompt}=promptFor(body);
    if(!title) return send(res,400,{success:false,error:'title is required'});

    const errors=[];
    // Prefer the server-side Gemini credential when configured, then Vercel AI Gateway/OIDC.
    for(const provider of [viaGeminiKey,viaVercelGateway]){
      try{
        const out=await provider(prompt);
        return send(res,200,{success:true,data:out.data,model:out.model,provider:out.provider,isFallback:false});
      }catch(error){
        errors.push(String(error?.message||error));
      }
    }
    console.error('WASM AI providers unavailable',errors);
    return send(res,503,{success:false,error:'خدمة Gemini غير مهيأة على الخادم',code:'AI_BACKEND_NOT_CONFIGURED'});
  }catch(error){
    console.error('WASM AI generation error',error);
    return send(res,500,{success:false,error:'تعذر توليد المحتوى بواسطة Gemini'});
  }
}

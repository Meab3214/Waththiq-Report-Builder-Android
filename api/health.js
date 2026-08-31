export default function handler(req,res){
  res.statusCode=200;
  res.setHeader('Content-Type','application/json; charset=utf-8');
  res.setHeader('Cache-Control','no-store');
  res.end(JSON.stringify({
    ok:true,
    service:'wasm-ai',
    version:'v12',
    geminiConfigured:Boolean(process.env.GEMINI_API_KEY||process.env.GOOGLE_GENERATIVE_AI_API_KEY),
    gatewayConfigured:Boolean(process.env.AI_GATEWAY_API_KEY||process.env.VERCEL_OIDC_TOKEN)
  }));
}

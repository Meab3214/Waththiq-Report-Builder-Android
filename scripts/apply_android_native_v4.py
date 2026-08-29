#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'android/app/src/main/java/com/waththiq/reports/WasmNativePlugin.java'
s=p.read_text(encoding='utf-8')
start=s.index('    @PluginMethod\n    public void generateAi(PluginCall call) {')
end=s.rfind('\n}')
method=r'''    @PluginMethod
    public void generateAi(PluginCall call) {
        final String payload=call.getString("payload","{}");
        new Thread(()->{
            String[] endpoints=new String[]{
                "https://ais-pre-naruvl7phpn7dhi46ynsxx-6197440816.europe-west1.run.app/api/ai/generate-content"
            };
            Exception last=null;
            for(String endpoint:endpoints){
                HttpURLConnection c=null;
                try{
                    URL url=new URL(endpoint);
                    c=(HttpURLConnection)url.openConnection();
                    c.setRequestMethod("POST");
                    c.setConnectTimeout(15000);
                    c.setReadTimeout(60000);
                    c.setDoOutput(true);
                    c.setRequestProperty("Content-Type","application/json; charset=UTF-8");
                    c.setRequestProperty("Accept","application/json");
                    c.setRequestProperty("X-Requested-With","XMLHttpRequest");
                    byte[] bytes=payload.getBytes(StandardCharsets.UTF_8);
                    try(OutputStream out=c.getOutputStream()){out.write(bytes);out.flush();}
                    int code=c.getResponseCode();
                    BufferedReader reader=new BufferedReader(new InputStreamReader(code>=200&&code<300?c.getInputStream():c.getErrorStream(),StandardCharsets.UTF_8));
                    StringBuilder body=new StringBuilder();String line;while((line=reader.readLine())!=null)body.append(line);reader.close();
                    String text=body.toString().trim();
                    String contentType=c.getContentType()==null?"":c.getContentType().toLowerCase();
                    if(code>=200&&code<300&&contentType.contains("json")&&text.startsWith("{")){
                        JSObject result=new JSObject();result.put("response",text);call.resolve(result);return;
                    }
                    last=new IllegalStateException("AI backend returned HTTP "+code+" / "+contentType);
                }catch(Exception e){last=e;}finally{if(c!=null)c.disconnect();}
            }
            call.reject("خدمة Gemini السحابية غير متاحة حالياً"+(last!=null?": "+last.getMessage():""));
        }).start();
    }
'''
s=s[:start]+method+s[end:]
p.write_text(s,encoding='utf-8')
print('native v4: backend-only Gemini bridge; no API key requested from end users')

#!/usr/bin/env python3
from pathlib import Path
import os,re

ROOT=Path(__file__).resolve().parents[1]
plugin=ROOT/'android/app/src/main/java/com/waththiq/reports/WasmNativePlugin.java'
s=plugin.read_text(encoding='utf-8')
start=s.find('    @PluginMethod\n    public void generateAi(PluginCall call) {')
if start<0:
    raise SystemExit('v9: generateAi method not found')
end=s.rfind('\n}')
method=r'''    @PluginMethod
    public void generateAi(PluginCall call) {
        final String payload=call.getString("payload","{}");
        new Thread(()->{
            String[] endpoints=new String[]{
                "https://wasm-ai-sdk-v10.vercel.app/api/ai/generate-content",
                "https://wasm-ai-public-v9.vercel.app/api/ai/generate-content",
                "https://wasm-ai-prod.vercel.app/api/ai/generate-content"
            };
            String lastError="";
            for(String endpoint:endpoints){
                HttpURLConnection c=null;
                try{
                    URL url=new URL(endpoint);
                    c=(HttpURLConnection)url.openConnection();
                    c.setRequestMethod("POST");
                    c.setConnectTimeout(15000);
                    c.setReadTimeout(70000);
                    c.setDoOutput(true);
                    c.setRequestProperty("Content-Type","application/json; charset=UTF-8");
                    c.setRequestProperty("Accept","application/json");
                    c.setRequestProperty("X-WASM-Client","android");
                    byte[] bytes=payload.getBytes(StandardCharsets.UTF_8);
                    try(OutputStream out=c.getOutputStream()){out.write(bytes);out.flush();}
                    int code=c.getResponseCode();
                    java.io.InputStream stream=(code>=200&&code<300)?c.getInputStream():c.getErrorStream();
                    if(stream==null){lastError="HTTP "+code;continue;}
                    BufferedReader reader=new BufferedReader(new InputStreamReader(stream,StandardCharsets.UTF_8));
                    StringBuilder body=new StringBuilder();String line;while((line=reader.readLine())!=null)body.append(line);reader.close();
                    String text=body.toString().trim();
                    String contentType=c.getContentType()==null?"":c.getContentType().toLowerCase();
                    if(code>=200&&code<300&&contentType.contains("json")&&text.startsWith("{")){
                        JSONObject parsed=new JSONObject(text);
                        if(parsed.optBoolean("success",false)&&parsed.optJSONObject("data")!=null){
                            JSObject result=new JSObject();result.put("response",text);call.resolve(result);return;
                        }
                        lastError=parsed.optString("error","Invalid AI response");
                    }else{
                        lastError="HTTP "+code+" / "+contentType;
                    }
                }catch(Exception e){lastError=e.getMessage()==null?e.getClass().getSimpleName():e.getMessage();}
                finally{if(c!=null)c.disconnect();}
            }
            call.reject("تعذر الاتصال بخدمة Gemini الحقيقية"+(lastError.isEmpty()?"":": "+lastError));
        }).start();
    }
'''
s=s[:start]+method+s[end:]
plugin.write_text(s,encoding='utf-8')

gradle=ROOT/'android/app/build.gradle'
g=gradle.read_text(encoding='utf-8')
run_number=int(os.getenv('GITHUB_RUN_NUMBER','1'))
version_code=2000000+run_number
g=re.sub(r'versionCode\s+\d+',f'versionCode {version_code}',g,count=1)
g=re.sub(r'versionName\s+"[^"]+"',f'versionName "1.9.{run_number}"',g,count=1)
gradle.write_text(g,encoding='utf-8')

main=ROOT/'android/app/src/main/java/com/waththiq/reports/MainActivity.java'
if main.exists():
    m=main.read_text(encoding='utf-8')
    if 'import androidx.core.view.WindowCompat;' not in m:
        m=m.replace('import androidx.core.view.WindowInsetsCompat;','import androidx.core.view.WindowInsetsCompat;\nimport androidx.core.view.WindowCompat;')
    if 'WindowCompat.setDecorFitsSystemWindows' not in m:
        m=m.replace('super.onCreate(savedInstanceState);','super.onCreate(savedInstanceState);\n        WindowCompat.setDecorFitsSystemWindows(getWindow(), true);',1)
    main.write_text(m,encoding='utf-8')

print(f'native v9: secure cloud Gemini failover + Android nav fit + versionCode={version_code}')

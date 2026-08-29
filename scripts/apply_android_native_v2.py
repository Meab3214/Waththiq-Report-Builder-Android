#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'android/app/src/main/java/com/waththiq/reports/WasmNativePlugin.java'
s=p.read_text(encoding='utf-8')
if 'generateAi(PluginCall call)' in s:
    print('already patched')
    raise SystemExit
s=s.replace('import java.io.OutputStream;','import java.io.OutputStream;\nimport java.io.BufferedReader;\nimport java.io.InputStreamReader;\nimport java.net.HttpURLConnection;\nimport java.net.URL;\nimport java.nio.charset.StandardCharsets;')
insert=r'''
    @PluginMethod
    public void generateAi(PluginCall call) {
        final String payload = call.getString("payload", "{}");
        new Thread(() -> {
            HttpURLConnection connection = null;
            try {
                URL url = new URL("https://ais-pre-naruvl7phpn7dhi46ynsxx-6197440816.europe-west1.run.app/api/ai/generate-content");
                connection = (HttpURLConnection) url.openConnection();
                connection.setRequestMethod("POST");
                connection.setConnectTimeout(15000);
                connection.setReadTimeout(45000);
                connection.setDoOutput(true);
                connection.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
                connection.setRequestProperty("Accept", "application/json");
                byte[] bytes = payload.getBytes(StandardCharsets.UTF_8);
                try (OutputStream out = connection.getOutputStream()) { out.write(bytes); out.flush(); }
                int code = connection.getResponseCode();
                BufferedReader reader = new BufferedReader(new InputStreamReader(code >= 200 && code < 300 ? connection.getInputStream() : connection.getErrorStream(), StandardCharsets.UTF_8));
                StringBuilder body = new StringBuilder(); String line;
                while ((line = reader.readLine()) != null) body.append(line);
                reader.close();
                if (code < 200 || code >= 300) { call.reject("AI backend HTTP " + code + ": " + body); return; }
                JSObject result = new JSObject(); result.put("response", body.toString()); call.resolve(result);
            } catch (Exception e) {
                call.reject("AI backend connection failed: " + e.getMessage(), e);
            } finally { if (connection != null) connection.disconnect(); }
        }).start();
    }

'''
pos=s.rfind('\n}')
s=s[:pos]+insert+s[pos:]
p.write_text(s,encoding='utf-8')
print('native AI bridge added')

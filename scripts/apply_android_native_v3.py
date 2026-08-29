#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'android/app/src/main/java/com/waththiq/reports/WasmNativePlugin.java'

plugin=r'''package com.waththiq.reports;

import android.content.ContentResolver;
import android.content.ContentValues;
import android.content.Context;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.provider.MediaStore;
import android.print.PrintAttributes;
import android.print.PrintDocumentAdapter;
import android.print.PrintManager;
import android.util.Base64;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@CapacitorPlugin(name = "WasmNative")
public class WasmNativePlugin extends Plugin {
    private static class PendingFile {
        String fileName;
        String mimeType;
        StringBuilder base64 = new StringBuilder();
    }
    private final Map<String, PendingFile> pendingFiles = new ConcurrentHashMap<>();

    private Uri writeBytes(String fileName, String mimeType, byte[] bytes) throws Exception {
        Uri savedUri;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            ContentResolver resolver = getContext().getContentResolver();
            ContentValues values = new ContentValues();
            values.put(MediaStore.Downloads.DISPLAY_NAME, fileName);
            values.put(MediaStore.Downloads.MIME_TYPE, mimeType);
            values.put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS + "/WASM");
            values.put(MediaStore.Downloads.IS_PENDING, 1);
            savedUri = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
            if (savedUri == null) throw new IllegalStateException("Could not create Downloads item");
            try (OutputStream out = resolver.openOutputStream(savedUri)) {
                if (out == null) throw new IllegalStateException("Could not open output stream");
                out.write(bytes); out.flush();
            }
            values.clear(); values.put(MediaStore.Downloads.IS_PENDING, 0);
            resolver.update(savedUri, values, null, null);
        } else {
            File dir = new File(getContext().getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS), "WASM");
            if (!dir.exists() && !dir.mkdirs()) throw new IllegalStateException("Could not create download folder");
            File file = new File(dir, fileName);
            try (FileOutputStream out = new FileOutputStream(file)) { out.write(bytes); out.flush(); }
            savedUri = Uri.fromFile(file);
        }
        return savedUri;
    }

    @PluginMethod
    public void saveBase64(PluginCall call) {
        String fileName=call.getString("fileName"); String mime=call.getString("mimeType","application/octet-stream"); String data=call.getString("base64Data");
        if(fileName==null||data==null){call.reject("Missing fileName or base64Data");return;}
        try{Uri uri=writeBytes(fileName,mime,Base64.decode(data,Base64.DEFAULT));JSObject r=new JSObject();r.put("uri",uri.toString());call.resolve(r);}catch(Exception e){call.reject("Failed to save file: "+e.getMessage(),e);}
    }

    @PluginMethod
    public void startFile(PluginCall call) {
        String fileName=call.getString("fileName"); String mime=call.getString("mimeType","application/octet-stream");
        if(fileName==null){call.reject("Missing fileName");return;}
        String id=UUID.randomUUID().toString(); PendingFile f=new PendingFile();f.fileName=fileName;f.mimeType=mime;pendingFiles.put(id,f);
        JSObject r=new JSObject();r.put("id",id);call.resolve(r);
    }

    @PluginMethod
    public void appendFileChunk(PluginCall call) {
        String id=call.getString("id"); String chunk=call.getString("chunk"); PendingFile f=id==null?null:pendingFiles.get(id);
        if(f==null||chunk==null){call.reject("Invalid export session");return;}
        f.base64.append(chunk); call.resolve();
    }

    @PluginMethod
    public void finishFile(PluginCall call) {
        String id=call.getString("id"); PendingFile f=id==null?null:pendingFiles.remove(id);
        if(f==null){call.reject("Invalid export session");return;}
        try{byte[] bytes=Base64.decode(f.base64.toString(),Base64.DEFAULT);if(bytes.length<512)throw new IllegalStateException("Generated file is empty");Uri uri=writeBytes(f.fileName,f.mimeType,bytes);JSObject r=new JSObject();r.put("uri",uri.toString());call.resolve(r);}catch(Exception e){call.reject("Failed to finish file: "+e.getMessage(),e);}
    }

    @PluginMethod
    public void print(PluginCall call) {
        final String jobName=call.getString("jobName","WASM Report");
        getActivity().runOnUiThread(()->{try{PrintManager pm=(PrintManager)getActivity().getSystemService(Context.PRINT_SERVICE);PrintDocumentAdapter adapter=getBridge().getWebView().createPrintDocumentAdapter(jobName);PrintAttributes attrs=new PrintAttributes.Builder().setMediaSize(PrintAttributes.MediaSize.ISO_A4).setMinMargins(PrintAttributes.Margins.NO_MARGINS).setColorMode(PrintAttributes.COLOR_MODE_COLOR).build();pm.print(jobName,adapter,attrs);call.resolve();}catch(Exception e){call.reject("Failed to open Android print dialog: "+e.getMessage(),e);}});
    }

    private SharedPreferences prefs(){return getContext().getSharedPreferences("wasm_secure_settings",Context.MODE_PRIVATE);}

    @PluginMethod
    public void setGeminiKey(PluginCall call){String key=call.getString("key","").trim();if(key.length()<20){call.reject("Gemini API key is invalid");return;}prefs().edit().putString("gemini_api_key",key).apply();call.resolve();}

    @PluginMethod
    public void hasGeminiKey(PluginCall call){JSObject r=new JSObject();r.put("configured",!prefs().getString("gemini_api_key","").trim().isEmpty());call.resolve(r);}

    @PluginMethod
    public void generateAi(PluginCall call) {
        final String payload=call.getString("payload","{}"); final String apiKey=prefs().getString("gemini_api_key","").trim();
        if(apiKey.isEmpty()){call.reject("Gemini API key is not configured");return;}
        new Thread(()->{HttpURLConnection c=null;try{
            JSONObject input=new JSONObject(payload);
            String title=input.optString("title","برنامج تعليمي");String category=input.optString("category","");String audience=input.optString("targetAudience","");String reportType=input.optString("reportType","");
            String prompt="أنت مساعد متخصص في كتابة تقارير التوثيق التعليمية السعودية. اكتب محتوى عربي مهني أصلي ومحدد للموضوع، ولا تستخدم عبارات عامة مكررة. الموضوع: "+title+". نوع التقرير: "+reportType+". المجال: "+category+". الفئة المستهدفة: "+audience+". أعد JSON فقط بالمفاتيح التالية: generalGoal نص موجز، detailedGoals نص متعدد الأسطر يتضمن 4 أهداف، executionMechanism نص متعدد الأسطر يتضمن 4 خطوات عملية، resultsAndImpact نص متعدد الأسطر يتضمن نتائج قابلة للقياس، recommendations نص متعدد الأسطر يتضمن 3 توصيات. لا تستخدم Markdown ولا أي نص خارج JSON.";
            JSONObject request=new JSONObject();
            org.json.JSONArray contents=new org.json.JSONArray();JSONObject item=new JSONObject();org.json.JSONArray parts=new org.json.JSONArray();JSONObject part=new JSONObject();part.put("text",prompt);parts.put(part);item.put("parts",parts);contents.put(item);request.put("contents",contents);
            JSONObject generation=new JSONObject();generation.put("temperature",0.7);generation.put("responseMimeType","application/json");request.put("generationConfig",generation);
            URL url=new URL("https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key="+apiKey);
            c=(HttpURLConnection)url.openConnection();c.setRequestMethod("POST");c.setConnectTimeout(15000);c.setReadTimeout(60000);c.setDoOutput(true);c.setRequestProperty("Content-Type","application/json; charset=UTF-8");c.setRequestProperty("Accept","application/json");
            byte[] bytes=request.toString().getBytes(StandardCharsets.UTF_8);try(OutputStream out=c.getOutputStream()){out.write(bytes);out.flush();}
            int code=c.getResponseCode();BufferedReader reader=new BufferedReader(new InputStreamReader(code>=200&&code<300?c.getInputStream():c.getErrorStream(),StandardCharsets.UTF_8));StringBuilder body=new StringBuilder();String line;while((line=reader.readLine())!=null)body.append(line);reader.close();
            if(code<200||code>=300){call.reject("Gemini HTTP "+code+": "+body);return;}
            JSONObject raw=new JSONObject(body.toString());String text=raw.getJSONArray("candidates").getJSONObject(0).getJSONObject("content").getJSONArray("parts").getJSONObject(0).getString("text").trim();
            if(text.startsWith("```")){text=text.replaceFirst("^```(?:json)?\\s*","").replaceFirst("\\s*```$","");}
            JSONObject data=new JSONObject(text);JSONObject wrapped=new JSONObject();wrapped.put("success",true);wrapped.put("data",data);JSObject result=new JSObject();result.put("response",wrapped.toString());call.resolve(result);
        }catch(Exception e){call.reject("Gemini direct connection failed: "+e.getMessage(),e);}finally{if(c!=null)c.disconnect();}}).start();
    }
}
'''
p.write_text(plugin,encoding='utf-8')
print('native v3: chunked export + direct Gemini configured')

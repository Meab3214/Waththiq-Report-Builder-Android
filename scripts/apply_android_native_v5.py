#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'android/app/src/main/java/com/waththiq/reports/WasmNativePlugin.java'
s=p.read_text(encoding='utf-8')

imports='''import android.graphics.Bitmap;\nimport android.graphics.Canvas;\nimport android.graphics.Color;\nimport android.graphics.pdf.PdfDocument;\nimport java.io.ByteArrayOutputStream;\nimport org.json.JSONObject;\nimport org.json.JSONTokener;\n'''
marker='import android.content.ContentResolver;\n'
if 'import android.graphics.pdf.PdfDocument;' not in s:
    s=s.replace(marker,marker+imports,1)

pos=s.index('    @PluginMethod\n    public void print(PluginCall call) {')
method=r'''    @PluginMethod
    public void exportReport(PluginCall call) {
        final String fileName=call.getString("fileName");
        final String format=call.getString("format","pdf").toLowerCase();
        if(fileName==null || !(format.equals("pdf")||format.equals("png"))){call.reject("Invalid export request");return;}

        getActivity().runOnUiThread(()->{
            try {
                final android.webkit.WebView webView=getBridge().getWebView();
                final String js="(()=>{const e=document.querySelector('.a4-sheet');if(!e)return '';const r=e.getBoundingClientRect();return JSON.stringify({x:r.left,y:r.top,w:r.width,h:r.height});})()";
                webView.evaluateJavascript(js,(value)->{
                    try {
                        Object parsed=new JSONTokener(value).nextValue();
                        String json=String.valueOf(parsed);
                        if(json==null || json.length()<3) throw new IllegalStateException("A4 report page not found");
                        JSONObject rect=new JSONObject(json);
                        final float x=(float)rect.getDouble("x");
                        final float y=(float)rect.getDouble("y");
                        final float w=(float)rect.getDouble("w");
                        final float h=(float)rect.getDouble("h");
                        if(w<100 || h<100) throw new IllegalStateException("Invalid A4 report dimensions");

                        if(format.equals("png")) {
                            final int targetW=1654;
                            final int targetH=2339;
                            Bitmap bitmap=Bitmap.createBitmap(targetW,targetH,Bitmap.Config.ARGB_8888);
                            Canvas canvas=new Canvas(bitmap);
                            canvas.drawColor(Color.WHITE);
                            float scale=Math.min(targetW/w,targetH/h);
                            canvas.scale(scale,scale);
                            canvas.translate(-x,-y);
                            webView.draw(canvas);
                            ByteArrayOutputStream out=new ByteArrayOutputStream();
                            if(!bitmap.compress(Bitmap.CompressFormat.PNG,100,out)) throw new IllegalStateException("PNG encoding failed");
                            bitmap.recycle();
                            byte[] bytes=out.toByteArray();
                            if(bytes.length<1024) throw new IllegalStateException("Generated PNG is empty");
                            Uri uri=writeBytes(fileName,"image/png",bytes);
                            JSObject result=new JSObject(); result.put("uri",uri.toString()); result.put("bytes",bytes.length); call.resolve(result);
                            return;
                        }

                        PdfDocument pdf=new PdfDocument();
                        try {
                            final int pageW=595;
                            final int pageH=842;
                            PdfDocument.PageInfo info=new PdfDocument.PageInfo.Builder(pageW,pageH,1).create();
                            PdfDocument.Page page=pdf.startPage(info);
                            Canvas canvas=page.getCanvas();
                            canvas.drawColor(Color.WHITE);
                            float scale=Math.min(pageW/w,pageH/h);
                            canvas.scale(scale,scale);
                            canvas.translate(-x,-y);
                            webView.draw(canvas);
                            pdf.finishPage(page);
                            ByteArrayOutputStream out=new ByteArrayOutputStream();
                            pdf.writeTo(out);
                            byte[] bytes=out.toByteArray();
                            if(bytes.length<1024) throw new IllegalStateException("Generated PDF is empty");
                            Uri uri=writeBytes(fileName,"application/pdf",bytes);
                            JSObject result=new JSObject(); result.put("uri",uri.toString()); result.put("bytes",bytes.length); call.resolve(result);
                        } finally { pdf.close(); }
                    } catch(Exception e) {
                        call.reject("Android report export failed: "+e.getMessage(),e);
                    }
                });
            } catch(Exception e) {
                call.reject("Could not start Android export: "+e.getMessage(),e);
            }
        });
    }

'''
s=s[:pos]+method+s[pos:]
p.write_text(s,encoding='utf-8')

# Enable whole-document drawing before Capacitor creates the WebView.
main=ROOT/'android/app/src/main/java/com/waththiq/reports/MainActivity.java'
if main.exists():
    m=main.read_text(encoding='utf-8')
    if 'enableSlowWholeDocumentDraw' not in m:
        if 'import android.webkit.WebView;' not in m:
            m=m.replace('package com.waththiq.reports;\n','package com.waththiq.reports;\n\nimport android.webkit.WebView;\n',1)
        m=m.replace('super.onCreate(savedInstanceState);','WebView.enableSlowWholeDocumentDraw();\n        super.onCreate(savedInstanceState);',1)
        main.write_text(m,encoding='utf-8')

print('native v5: direct WebView A4 rendering to PdfDocument/PNG')

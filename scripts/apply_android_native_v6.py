#!/usr/bin/env python3
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'android/app/src/main/java/com/waththiq/reports/WasmNativePlugin.java'
s=p.read_text(encoding='utf-8')
# Stable cloud-only AI endpoint. No key is embedded in the APK.
s=re.sub(r'https://[^\"\']+/api/ai/generate-content','https://wasm-ai-service-bandrbk6-3214.vercel.app/api/ai/generate-content',s)
# Replace exportReport with scroll-aware exact A4 capture. CSS export mode pins .a4-sheet to viewport origin.
start=s.index('    @PluginMethod\n    public void exportReport(PluginCall call) {')
end=s.index('    @PluginMethod\n    public void print(PluginCall call) {',start)
method=r'''    @PluginMethod
    public void exportReport(PluginCall call) {
        final String fileName=call.getString("fileName");
        final String format=call.getString("format","pdf").toLowerCase();
        if(fileName==null || !(format.equals("pdf")||format.equals("png"))){call.reject("Invalid export request");return;}
        getActivity().runOnUiThread(()->{
            try {
                final android.webkit.WebView webView=getBridge().getWebView();
                final String js="(()=>{const e=document.querySelector('.a4-sheet');if(!e)return '';const r=e.getBoundingClientRect();return JSON.stringify({x:r.left+window.scrollX,y:r.top+window.scrollY,w:r.width,h:r.height,sx:window.scrollX,sy:window.scrollY,dpr:window.devicePixelRatio||1});})()";
                webView.evaluateJavascript(js,(value)->{
                    try {
                        Object parsed=new JSONTokener(value).nextValue(); String json=String.valueOf(parsed);
                        if(json==null||json.length()<3)throw new IllegalStateException("A4 report page not found");
                        JSONObject rect=new JSONObject(json); float x=(float)rect.getDouble("x"),y=(float)rect.getDouble("y"),w=(float)rect.getDouble("w"),h=(float)rect.getDouble("h");
                        if(w<700||h<1000)throw new IllegalStateException("A4 export surface is not full size");
                        final int targetW=1654,targetH=2339;
                        Bitmap bitmap=Bitmap.createBitmap(targetW,targetH,Bitmap.Config.ARGB_8888); Canvas bc=new Canvas(bitmap); bc.drawColor(Color.WHITE);
                        float scale=Math.min(targetW/w,targetH/h); bc.scale(scale,scale); bc.translate(-x,-y); webView.draw(bc);
                        if(format.equals("png")){
                            ByteArrayOutputStream out=new ByteArrayOutputStream(); if(!bitmap.compress(Bitmap.CompressFormat.PNG,100,out))throw new IllegalStateException("PNG encoding failed"); byte[] bytes=out.toByteArray(); bitmap.recycle(); if(bytes.length<4096)throw new IllegalStateException("Generated PNG is empty"); Uri uri=writeBytes(fileName,"image/png",bytes); JSObject result=new JSObject();result.put("uri",uri.toString());result.put("bytes",bytes.length);call.resolve(result);return;
                        }
                        PdfDocument pdf=new PdfDocument(); try{PdfDocument.PageInfo info=new PdfDocument.PageInfo.Builder(595,842,1).create();PdfDocument.Page page=pdf.startPage(info);Canvas pc=page.getCanvas();pc.drawColor(Color.WHITE);pc.drawBitmap(bitmap,null,new android.graphics.Rect(0,0,595,842),null);pdf.finishPage(page);ByteArrayOutputStream out=new ByteArrayOutputStream();pdf.writeTo(out);byte[] bytes=out.toByteArray();if(bytes.length<4096)throw new IllegalStateException("Generated PDF is empty");Uri uri=writeBytes(fileName,"application/pdf",bytes);JSObject result=new JSObject();result.put("uri",uri.toString());result.put("bytes",bytes.length);call.resolve(result);}finally{bitmap.recycle();pdf.close();}
                    }catch(Exception e){call.reject("Android A4 export failed: "+e.getMessage(),e);}
                });
            }catch(Exception e){call.reject("Could not start Android export: "+e.getMessage(),e);}
        });
    }

'''
s=s[:start]+method+s[end:]
p.write_text(s,encoding='utf-8')
print('native v6: exact A4 bitmap->PDF/PNG + cloud AI endpoint')

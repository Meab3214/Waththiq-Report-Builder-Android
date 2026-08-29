#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'android/app/src/main/java/com/waththiq/reports/WasmNativePlugin.java'
s=p.read_text(encoding='utf-8')

imports='''import android.graphics.Bitmap;\nimport android.graphics.Color;\nimport android.graphics.pdf.PdfRenderer;\nimport android.os.Bundle;\nimport android.os.CancellationSignal;\nimport android.os.ParcelFileDescriptor;\nimport android.print.PageRange;\nimport android.print.PrintDocumentInfo;\nimport java.io.ByteArrayOutputStream;\nimport java.io.FileInputStream;\n'''
marker='import android.content.ContentResolver;\n'
if 'import android.graphics.pdf.PdfRenderer;' not in s:
    s=s.replace(marker,marker+imports,1)

# Add helpers and exportReport before print().
pos=s.index('    @PluginMethod\n    public void print(PluginCall call) {')
method=r'''    private byte[] readFileBytes(File file) throws Exception {
        try(FileInputStream in=new FileInputStream(file); ByteArrayOutputStream out=new ByteArrayOutputStream()) {
            byte[] buf=new byte[65536]; int n;
            while((n=in.read(buf))>0) out.write(buf,0,n);
            return out.toByteArray();
        }
    }

    private byte[] renderPdfFirstPageToPng(File pdfFile) throws Exception {
        try(ParcelFileDescriptor fd=ParcelFileDescriptor.open(pdfFile,ParcelFileDescriptor.MODE_READ_ONLY);
            PdfRenderer renderer=new PdfRenderer(fd)) {
            if(renderer.getPageCount()<1) throw new IllegalStateException("PDF has no pages");
            PdfRenderer.Page page=renderer.openPage(0);
            try {
                final int width=1654; // ~200 DPI A4
                final int height=2339;
                Bitmap bitmap=Bitmap.createBitmap(width,height,Bitmap.Config.ARGB_8888);
                bitmap.eraseColor(Color.WHITE);
                page.render(bitmap,null,null,PdfRenderer.Page.RENDER_MODE_FOR_PRINT);
                ByteArrayOutputStream out=new ByteArrayOutputStream();
                if(!bitmap.compress(Bitmap.CompressFormat.PNG,100,out)) throw new IllegalStateException("PNG encoding failed");
                bitmap.recycle();
                return out.toByteArray();
            } finally { page.close(); }
        }
    }

    @PluginMethod
    public void exportReport(PluginCall call) {
        final String fileName=call.getString("fileName");
        final String format=call.getString("format","pdf").toLowerCase();
        if(fileName==null || !(format.equals("pdf")||format.equals("png"))){call.reject("Invalid export request");return;}

        getActivity().runOnUiThread(()->{
            try {
                final File tempPdf=new File(getContext().getCacheDir(),"wasm-report-"+UUID.randomUUID()+".pdf");
                final ParcelFileDescriptor destination=ParcelFileDescriptor.open(tempPdf,
                    ParcelFileDescriptor.MODE_CREATE|ParcelFileDescriptor.MODE_TRUNCATE|ParcelFileDescriptor.MODE_READ_WRITE);
                final PrintAttributes attrs=new PrintAttributes.Builder()
                    .setMediaSize(PrintAttributes.MediaSize.ISO_A4)
                    .setResolution(new PrintAttributes.Resolution("wasm_a4","WASM A4",300,300))
                    .setMinMargins(PrintAttributes.Margins.NO_MARGINS)
                    .setColorMode(PrintAttributes.COLOR_MODE_COLOR)
                    .build();
                final PrintDocumentAdapter adapter=getBridge().getWebView().createPrintDocumentAdapter("WASM Report");
                adapter.onStart();
                adapter.onLayout(attrs,attrs,new CancellationSignal(),new PrintDocumentAdapter.LayoutResultCallback(){
                    @Override public void onLayoutFinished(PrintDocumentInfo info, boolean changed){
                        adapter.onWrite(new PageRange[]{PageRange.ALL_PAGES},destination,new CancellationSignal(),new PrintDocumentAdapter.WriteResultCallback(){
                            @Override public void onWriteFinished(PageRange[] pages){
                                try{destination.close();}catch(Exception ignored){}
                                adapter.onFinish();
                                new Thread(()->{
                                    try{
                                        byte[] bytes;
                                        String mime;
                                        if(format.equals("png")) { bytes=renderPdfFirstPageToPng(tempPdf); mime="image/png"; }
                                        else { bytes=readFileBytes(tempPdf); mime="application/pdf"; }
                                        if(bytes.length<1024) throw new IllegalStateException("Generated report is empty");
                                        Uri uri=writeBytes(fileName,mime,bytes);
                                        tempPdf.delete();
                                        JSObject result=new JSObject(); result.put("uri",uri.toString()); result.put("bytes",bytes.length); call.resolve(result);
                                    }catch(Exception e){tempPdf.delete();call.reject("Android report export failed: "+e.getMessage(),e);}
                                }).start();
                            }
                            @Override public void onWriteFailed(CharSequence error){try{destination.close();}catch(Exception ignored){}adapter.onFinish();tempPdf.delete();call.reject("Android PDF writer failed: "+error);}
                            @Override public void onWriteCancelled(){try{destination.close();}catch(Exception ignored){}adapter.onFinish();tempPdf.delete();call.reject("Report export cancelled");}
                        });
                    }
                    @Override public void onLayoutFailed(CharSequence error){try{destination.close();}catch(Exception ignored){}adapter.onFinish();tempPdf.delete();call.reject("Android print layout failed: "+error);}
                    @Override public void onLayoutCancelled(){try{destination.close();}catch(Exception ignored){}adapter.onFinish();tempPdf.delete();call.reject("Report layout cancelled");}
                },new Bundle());
            }catch(Exception e){call.reject("Could not start Android export: "+e.getMessage(),e);}
        });
    }

'''
s=s[:pos]+method+s[pos:]
p.write_text(s,encoding='utf-8')
print('native v5: PrintDocumentAdapter PDF + PdfRenderer PNG export')

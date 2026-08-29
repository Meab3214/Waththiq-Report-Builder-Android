#!/usr/bin/env python3
from pathlib import Path
import os, re

ROOT = Path(__file__).resolve().parents[1]
ANDROID = ROOT / 'android'
APP = ANDROID / 'app'
PKG = APP / 'src/main/java/com/waththiq/reports'
PKG.mkdir(parents=True, exist_ok=True)

plugin = r'''package com.waththiq.reports;

import android.content.ContentResolver;
import android.content.ContentValues;
import android.content.Context;
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

import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStream;

@CapacitorPlugin(name = "WasmNative")
public class WasmNativePlugin extends Plugin {
    @PluginMethod
    public void saveBase64(PluginCall call) {
        String fileName = call.getString("fileName");
        String mimeType = call.getString("mimeType", "application/octet-stream");
        String base64Data = call.getString("base64Data");
        if (fileName == null || base64Data == null) {
            call.reject("Missing fileName or base64Data");
            return;
        }
        try {
            byte[] bytes = Base64.decode(base64Data, Base64.DEFAULT);
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
                    out.write(bytes);
                    out.flush();
                }
                values.clear();
                values.put(MediaStore.Downloads.IS_PENDING, 0);
                resolver.update(savedUri, values, null, null);
            } else {
                File dir = new File(getContext().getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS), "WASM");
                if (!dir.exists() && !dir.mkdirs()) throw new IllegalStateException("Could not create download folder");
                File file = new File(dir, fileName);
                try (FileOutputStream out = new FileOutputStream(file)) { out.write(bytes); out.flush(); }
                savedUri = Uri.fromFile(file);
            }
            JSObject result = new JSObject();
            result.put("uri", savedUri.toString());
            call.resolve(result);
        } catch (Exception e) {
            call.reject("Failed to save file: " + e.getMessage(), e);
        }
    }

    @PluginMethod
    public void print(PluginCall call) {
        final String jobName = call.getString("jobName", "WASM Report");
        getActivity().runOnUiThread(() -> {
            try {
                PrintManager printManager = (PrintManager) getActivity().getSystemService(Context.PRINT_SERVICE);
                PrintDocumentAdapter adapter = getBridge().getWebView().createPrintDocumentAdapter(jobName);
                PrintAttributes attributes = new PrintAttributes.Builder()
                    .setMediaSize(PrintAttributes.MediaSize.ISO_A4)
                    .setMinMargins(PrintAttributes.Margins.NO_MARGINS)
                    .setColorMode(PrintAttributes.COLOR_MODE_COLOR)
                    .build();
                printManager.print(jobName, adapter, attributes);
                call.resolve();
            } catch (Exception e) {
                call.reject("Failed to open Android print dialog: " + e.getMessage(), e);
            }
        });
    }
}
'''
(PKG / 'WasmNativePlugin.java').write_text(plugin, encoding='utf-8')

main = r'''package com.waththiq.reports;

import android.graphics.Color;
import android.os.Bundle;
import android.view.View;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(WasmNativePlugin.class);
        super.onCreate(savedInstanceState);
        View webView = getBridge().getWebView();
        webView.setBackgroundColor(Color.rgb(8, 33, 30));
        ViewCompat.setOnApplyWindowInsetsListener(webView, (view, windowInsets) -> {
            Insets systemBars = windowInsets.getInsets(WindowInsetsCompat.Type.systemBars());
            view.setPadding(systemBars.left, view.getPaddingTop(), systemBars.right, systemBars.bottom);
            return windowInsets;
        });
        ViewCompat.requestApplyInsets(webView);
    }
}
'''
(PKG / 'MainActivity.java').write_text(main, encoding='utf-8')

gradle = APP / 'build.gradle'
s = gradle.read_text(encoding='utf-8')
run_number = int(os.getenv('GITHUB_RUN_NUMBER', '100'))
version_code = 1000 + run_number
s = re.sub(r'versionCode\s+\d+', f'versionCode {version_code}', s, count=1)
s = re.sub(r'versionName\s+"[^"]+"', f'versionName "1.1.{run_number}"', s, count=1)
if 'signingConfigs {' not in s:
    s = s.replace('    buildTypes {', '''    signingConfigs {\n        release {\n            storeFile file("../../wasm-release.jks")\n            storePassword "WasmRelease2026!"\n            keyAlias "wasmrelease"\n            keyPassword "WasmRelease2026!"\n        }\n    }\n    buildTypes {''', 1)
    s = s.replace('        release {\n            minifyEnabled false', '        release {\n            signingConfig signingConfigs.release\n            minifyEnabled false', 1)
gradle.write_text(s, encoding='utf-8')

print(f'Native Android bridge + stable signing configured. versionCode={version_code}')

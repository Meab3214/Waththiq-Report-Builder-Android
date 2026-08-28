#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def replace_required(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"Expected branding source block not found in {path}")
    path.write_text(text.replace(old, new), encoding="utf-8")

# App header: replace the old visual identity only. Storage keys are intentionally untouched.
app = ROOT / "src/App.tsx"
replace_required(
    app,
    '''          {/* Brand & Platform Emblem */}
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-xl bg-emerald-800 text-white flex items-center justify-center font-black text-sm sm:text-base shadow-xs shrink-0">
              وثق
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <h1 className="text-xs sm:text-sm font-black text-emerald-950 truncate max-w-[140px] sm:max-w-none">
                  منصة وثّق للتقارير
                </h1>
                <span className="hidden sm:inline-block bg-emerald-100 text-emerald-900 text-[9px] font-bold px-2 py-0.5 rounded-full">
                  الهوية المعتمدة
                </span>
              </div>
              <p className="text-[9px] sm:text-[10px] text-slate-500 font-medium hidden md:block">
                توثيق الأنشطة والبرامج والفعاليات التعليمية
              </p>
            </div>
          </div>
''',
    '''          {/* WASM Official Brand */}
          <div className="flex items-center gap-2.5 min-w-0">
            <img
              src="/icons/icon-512.png"
              alt="وَسْم"
              className="wasm-brand-icon w-9 h-9 sm:w-10 sm:h-10 rounded-xl shadow-sm shrink-0"
            />
            <div className="min-w-0">
              <div className="flex items-center gap-1.5">
                <h1 className="text-sm sm:text-base font-black text-[#08211e] leading-none">
                  وَسْم
                </h1>
                <span className="hidden sm:inline-block bg-[#08211e]/8 text-[#0b302c] text-[9px] font-bold px-2 py-0.5 rounded-full border border-[#d6a34a]/20">
                  الهوية الرسمية
                </span>
              </div>
              <p className="wasm-tagline-chip mt-1 inline-flex items-center gap-1.5 rounded-lg px-2 py-0.5 text-[8.5px] sm:text-[9.5px] font-bold whitespace-nowrap" aria-label="إنجازك في تقرير يليق بأثره">
                <span className="wasm-tagline-cream">إنجازك في تقرير</span>
                <span className="wasm-tagline-gold">يليق بأثره</span>
              </p>
            </div>
          </div>
'''
)
replace_required(
    app,
    '''          <div className="w-5 h-5 rounded-md bg-emerald-800 text-amber-300 flex items-center justify-center font-bold text-[10px]">
            <Sparkles className="w-3 h-3 text-amber-400" />
          </div>
          <div className="flex items-center gap-2 font-medium">
            <span className="text-slate-700 font-bold">منصة وثّق للتقارير المدرسية</span>
''',
    '''          <img
            src="/icons/icon-512.png"
            alt=""
            className="wasm-brand-icon w-5 h-5 rounded-md shadow-2xs"
          />
          <div className="flex items-center gap-2 font-medium">
            <span className="text-slate-700 font-bold">وَسْم — إنجازك في تقرير يليق بأثره</span>
'''
)

editor = ROOT / "src/components/Editor/ReportEditorForm.tsx"
replace_required(
    editor,
    '''          <div className="w-5 h-5 rounded-md bg-emerald-900 text-amber-400 flex items-center justify-center font-bold text-[9px] shadow-2xs">
            <Sparkles className="w-3 h-3 text-amber-400" />
          </div>
          <div className="flex items-center gap-1.5 text-[10.5px] font-semibold text-slate-700">
            <span className="text-slate-500">منصة وثّق</span>
''',
    '''          <img
            src="/icons/icon-512.png"
            alt=""
            className="wasm-brand-icon w-5 h-5 rounded-md shadow-2xs"
          />
          <div className="flex items-center gap-1.5 text-[10.5px] font-semibold text-slate-700">
            <span className="text-slate-600 font-black">وَسْم</span>
'''
)

# Splash component mounts above the already-initializing app, so initialization continues under it.
splash = ROOT / "src/components/branding/WasmSplash.tsx"
splash.parent.mkdir(parents=True, exist_ok=True)
splash.write_text('''import { useEffect, useState } from 'react';

const SPLASH_VISIBLE_MS = 1600;
const SPLASH_FADE_MS = 300;

export default function WasmSplash() {
  const [fading, setFading] = useState(false);
  const [mounted, setMounted] = useState(true);

  useEffect(() => {
    const fadeTimer = window.setTimeout(() => setFading(true), SPLASH_VISIBLE_MS);
    const unmountTimer = window.setTimeout(
      () => setMounted(false),
      SPLASH_VISIBLE_MS + SPLASH_FADE_MS
    );

    return () => {
      window.clearTimeout(fadeTimer);
      window.clearTimeout(unmountTimer);
    };
  }, []);

  if (!mounted) return null;

  return (
    <div
      className={`wasm-splash-screen ${fading ? 'wasm-splash-screen--fade' : ''}`}
      role="presentation"
      aria-hidden="true"
    >
      <img
        src="/assets/branding/wasm_splash.png"
        alt=""
        className="wasm-splash-image"
        draggable={false}
      />
    </div>
  );
}
''', encoding="utf-8")

main = ROOT / "src/main.tsx"
main_text = main.read_text(encoding="utf-8")
if "WasmSplash" not in main_text:
    main_text = main_text.replace("import App from './App.tsx';", "import App from './App.tsx';\nimport WasmSplash from './components/branding/WasmSplash.tsx';")
    main_text = main_text.replace("    <App />", "    <App />\n    <WasmSplash />")
    main.write_text(main_text, encoding="utf-8")

css = ROOT / "src/index.css"
css_text = css.read_text(encoding="utf-8")
if "/* WASM official identity */" not in css_text:
    css_text += '''

/* WASM official identity */
:root {
  --wasm-brand-dark: #08211e;
  --wasm-brand-deep: #041513;
  --wasm-brand-gold: #d6a34a;
  --wasm-brand-cream: #f2e5d4;
}
html, body, #root { min-height: 100%; }
html, body { background: var(--wasm-brand-dark); }
.wasm-splash-screen {
  position: fixed;
  inset: 0;
  z-index: 99999;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
  background: var(--wasm-brand-dark);
  opacity: 1;
  visibility: visible;
  transition: opacity 300ms ease, visibility 300ms ease;
  padding:
    env(safe-area-inset-top, 0px)
    env(safe-area-inset-right, 0px)
    env(safe-area-inset-bottom, 0px)
    env(safe-area-inset-left, 0px);
}
.wasm-splash-screen--fade { opacity: 0; visibility: hidden; pointer-events: none; }
.wasm-splash-image {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: center;
  user-select: none;
  -webkit-user-drag: none;
}
.wasm-brand-icon { object-fit: contain; object-position: center; }
.wasm-tagline-chip { background: var(--wasm-brand-dark); border: 1px solid rgba(214, 163, 74, 0.28); }
.wasm-tagline-cream { color: var(--wasm-brand-cream); }
.wasm-tagline-gold { color: var(--wasm-brand-gold); }
@media (prefers-reduced-motion: reduce) {
  .wasm-splash-screen { transition-duration: 0ms; }
}
'''
    css.write_text(css_text, encoding="utf-8")

(ROOT / "index.html").write_text('''<!doctype html>
<html lang="ar" dir="rtl">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover" />
    <title>وَسْم — إنجازك في تقرير يليق بأثره</title>
    <meta name="description" content="إنجازك في تقرير يليق بأثره" />
    <link rel="manifest" href="/manifest.json" />
    <link rel="icon" href="/favicon.ico" sizes="any" />
    <link rel="icon" type="image/png" sizes="16x16" href="/icons/icon-16.png" />
    <link rel="icon" type="image/png" sizes="32x32" href="/icons/icon-32.png" />
    <link rel="icon" type="image/png" sizes="48x48" href="/icons/icon-48.png" />
    <link rel="apple-touch-icon" sizes="180x180" href="/icons/icon-180.png" />
    <meta name="theme-color" content="#08211e" />
    <style>html,body,#root{margin:0;min-height:100%;background:#08211e}</style>
    <meta name="mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
    <meta name="apple-mobile-web-app-title" content="وَسْم" />
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Almarai:wght@300;400;700;800&family=Cairo:wght@300;400;600;700;800;900&family=IBM+Plex+Sans+Arabic:wght@300;400;500;600;700&family=Tajawal:wght@300;400;500;700;800;900&display=swap" rel="stylesheet" crossorigin="anonymous">
  </head>
  <body class="bg-slate-50 text-slate-900 antialiased font-['Cairo',sans-serif]">
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
    <script>
      if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
          navigator.serviceWorker.register('/sw.js').catch(() => {});
        });
      }
    </script>
  </body>
</html>
''', encoding="utf-8")

(ROOT / "public/manifest.json").write_text('''{
  "short_name": "وَسْم",
  "name": "وَسْم",
  "description": "إنجازك في تقرير يليق بأثره",
  "icons": [
    {"src": "/icons/icon-192.png", "type": "image/png", "sizes": "192x192", "purpose": "any"},
    {"src": "/icons/icon-256.png", "type": "image/png", "sizes": "256x256", "purpose": "any"},
    {"src": "/icons/icon-384.png", "type": "image/png", "sizes": "384x384", "purpose": "any"},
    {"src": "/icons/icon-512.png", "type": "image/png", "sizes": "512x512", "purpose": "any"},
    {"src": "/icons/icon-maskable-512.png", "type": "image/png", "sizes": "512x512", "purpose": "maskable"}
  ],
  "start_url": "/",
  "scope": "/",
  "background_color": "#08211e",
  "theme_color": "#08211e",
  "display": "standalone",
  "orientation": "portrait",
  "lang": "ar",
  "dir": "rtl"
}
''', encoding="utf-8")

(ROOT / "public/sw.js").write_text('''// WASM Service Worker for PWA Offline Capability
const CACHE_NAME = 'wasm-brand-v2';
const ASSETS_TO_CACHE = [
  '/', '/index.html', '/manifest.json', '/favicon.ico',
  '/assets/branding/wasm_app_icon.png', '/assets/branding/wasm_splash.png',
  '/icons/icon-192.png', '/icons/icon-512.png', '/icons/icon-maskable-512.png'
];
self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS_TO_CACHE)));
  self.skipWaiting();
});
self.addEventListener('activate', (event) => {
  event.waitUntil(caches.keys().then((names) => Promise.all(names.map((name) => name !== CACHE_NAME ? caches.delete(name) : undefined))));
  self.clients.claim();
});
self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  event.respondWith(caches.match(event.request).then((cached) => cached || fetch(event.request).then((response) => {
    if (!response || response.status !== 200 || response.type !== 'basic') return response;
    const clone = response.clone();
    caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
    return response;
  }).catch(() => caches.match('/'))));
});
''', encoding="utf-8")

old_icon = ROOT / "public/icon.svg"
if old_icon.exists():
    old_icon.unlink()

(ROOT / "metadata.json").write_text('''{
  "name": "وَسْم",
  "description": "إنجازك في تقرير يليق بأثره",
  "requestFramePermissions": [],
  "majorCapabilities": ["MAJOR_CAPABILITY_SERVER_SIDE_GEMINI_API"]
}
''', encoding="utf-8")

(ROOT / "capacitor.config.ts").write_text('''import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.waththiq.reports',
  appName: 'وَسْم',
  webDir: 'dist'
};

export default config;
''', encoding="utf-8")

server = ROOT / "server.ts"
if server.exists():
    server.write_text(
        server.read_text(encoding="utf-8").replace(
            "Waththiq Report Platform running on",
            "WASM Report Platform running on",
        ),
        encoding="utf-8",
    )

print("WASM source branding applied without changing storage/database/API logic.")

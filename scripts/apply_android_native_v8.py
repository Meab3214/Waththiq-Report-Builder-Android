#!/usr/bin/env python3
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'android/app/src/main/java/com/waththiq/reports/WasmNativePlugin.java'
s=p.read_text(encoding='utf-8')
s=re.sub(r'https://[^\"\']+/api/ai/generate-content','https://wasm-ai-prod-bandrbk6-3214.vercel.app/api/ai/generate-content',s)
p.write_text(s,encoding='utf-8')
print('native v8: production Gemini backend endpoint applied')

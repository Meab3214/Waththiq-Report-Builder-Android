#!/usr/bin/env python3
from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parents[1]

parser = argparse.ArgumentParser()
parser.add_argument('--source', action='store_true')
parser.add_argument('--android', action='store_true')
args = parser.parse_args()

if args.source:
    ai = ROOT / 'src/components/Editor/AIEducationalAssistant.tsx'
    text = ai.read_text(encoding='utf-8')
    old = "const apiBase = useMemo(() => (import.meta.env.VITE_AI_API_BASE_URL || '').replace(/\\\/$/, ''), []);"
    new = "const apiBase = useMemo(() => ((((import.meta as any).env?.VITE_AI_API_BASE_URL || '') as string).replace(/\\\/$/, '')), []);"
    if old not in text:
        # tolerate the regex as written by the source generator
        old = "const apiBase = useMemo(() => (import.meta.env.VITE_AI_API_BASE_URL || '').replace(/\/$/, ''), []);"
        new = "const apiBase = useMemo(() => ((((import.meta as any).env?.VITE_AI_API_BASE_URL || '') as string).replace(/\/$/, '')), []);"
    if old not in text:
        raise SystemExit('Could not find VITE_AI_API_BASE_URL expression to patch')
    ai.write_text(text.replace(old, new, 1), encoding='utf-8')
    print('Source TypeScript compatibility patch applied.')

if args.android:
    gradle = ROOT / 'android/app/build.gradle'
    text = gradle.read_text(encoding='utf-8')
    old = 'storeFile file("../../wasm-release.jks")'
    new = 'storeFile file("../wasm-release.jks")'
    if old not in text and new not in text:
        raise SystemExit('Could not find WASM signing storeFile setting')
    gradle.write_text(text.replace(old, new), encoding='utf-8')
    print('Android stable signing path patched.')

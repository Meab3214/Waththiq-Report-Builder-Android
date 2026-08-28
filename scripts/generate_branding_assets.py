#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BRAND_DIR = ROOT / "public" / "assets" / "branding"
ICON_SOURCE = BRAND_DIR / "wasm_app_icon.png"
SPLASH_SOURCE = BRAND_DIR / "wasm_splash.png"
ICONS_DIR = ROOT / "public" / "icons"

EXPECTED_ICON_SHA256 = "e31d2d96c7465771fd02853455fdf626768ea9e5b7ae32331c93e15da11222ef"
EXPECTED_SPLASH_SHA256 = "58b1ccc43e4b6594862e78266b09e0bac928a6b2eeac1ccb7121f7b34de68598"
BRAND_DARK = (8, 33, 30, 255)

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def validate_sources() -> None:
    if sha256(ICON_SOURCE) != EXPECTED_ICON_SHA256:
        raise SystemExit("wasm_app_icon.png does not match the approved official source")
    if sha256(SPLASH_SOURCE) != EXPECTED_SPLASH_SHA256:
        raise SystemExit("wasm_splash.png does not match the approved official source")

def transparent_corner_background(src: Image.Image) -> Image.Image:
    """Remove only the neutral-black area connected to the outer corners.

    The approved icon artwork itself remains unchanged; this derived alpha mask
    prevents its rectangular JPEG corner background from showing inside Android
    adaptive/squircle/circular masks.
    """
    rgba = src.convert("RGBA")
    px = rgba.load()
    width, height = rgba.size
    seen: set[tuple[int, int]] = set()
    stack = [(0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)]

    def is_outer_black(x: int, y: int) -> bool:
        r, g, b, _ = px[x, y]
        return max(r, g, b) <= 24 and (max(r, g, b) - min(r, g, b)) <= 9

    while stack:
        x, y = stack.pop()
        if (x, y) in seen or not (0 <= x < width and 0 <= y < height):
            continue
        if not is_outer_black(x, y):
            continue
        seen.add((x, y))
        r, g, b, _ = px[x, y]
        px[x, y] = (r, g, b, 0)
        stack.extend(((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)))
    return rgba

def resize_square(src: Image.Image, size: int, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    src.resize((size, size), Image.Resampling.LANCZOS).save(dst, "PNG", optimize=True)

def generate_web() -> None:
    validate_sources()
    ICONS_DIR.mkdir(parents=True, exist_ok=True)
    icon = transparent_corner_background(Image.open(ICON_SOURCE))
    for size in (16, 32, 48, 180, 192, 256, 384, 512):
        resize_square(icon, size, ICONS_DIR / f"icon-{size}.png")
    icon.resize((48, 48), Image.Resampling.LANCZOS).save(
        ROOT / "public" / "favicon.ico",
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48)],
    )
    canvas = Image.new("RGBA", (512, 512), BRAND_DARK)
    inner = int(512 * 0.72)
    scaled = icon.resize((inner, inner), Image.Resampling.LANCZOS)
    canvas.alpha_composite(scaled, ((512 - inner) // 2, (512 - inner) // 2))
    canvas.save(ICONS_DIR / "icon-maskable-512.png", "PNG", optimize=True)

def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def generate_android(android_dir: Path) -> None:
    validate_sources()
    app_main = android_dir / "app" / "src" / "main"
    res = app_main / "res"
    icon = Image.open(ICON_SOURCE).convert("RGBA")
    legacy_sizes = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
    foreground_sizes = {"mdpi": 108, "hdpi": 162, "xhdpi": 216, "xxhdpi": 324, "xxxhdpi": 432}

    for density, size in legacy_sizes.items():
        folder = res / f"mipmap-{density}"
        resize_square(icon, size, folder / "ic_launcher.png")
        round_canvas = Image.new("RGBA", (size, size), BRAND_DARK)
        inner = int(size * 0.82)
        scaled = icon.resize((inner, inner), Image.Resampling.LANCZOS)
        round_canvas.alpha_composite(scaled, ((size - inner) // 2, (size - inner) // 2))
        round_canvas.save(folder / "ic_launcher_round.png", "PNG", optimize=True)

    for density, size in foreground_sizes.items():
        folder = res / f"mipmap-{density}"
        foreground = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        inner = int(size * 0.66)
        scaled = icon.resize((inner, inner), Image.Resampling.LANCZOS)
        foreground.alpha_composite(scaled, ((size - inner) // 2, (size - inner) // 2))
        foreground.save(folder / "ic_launcher_foreground.png", "PNG", optimize=True)

    adaptive = """<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/wasm_brand_dark"/>
    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>
</adaptive-icon>
"""
    write_text(res / "mipmap-anydpi-v26" / "ic_launcher.xml", adaptive)
    write_text(res / "mipmap-anydpi-v26" / "ic_launcher_round.xml", adaptive)
    write_text(res / "values" / "wasm_branding.xml", """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="wasm_brand_dark">#08211E</color>
    <color name="wasm_brand_gold">#D6A34A</color>
    <color name="wasm_brand_cream">#F2E5D4</color>
</resources>
""")
    write_text(res / "values" / "ic_launcher_background.xml", """<?xml version="1.0" encoding="utf-8"?>
<resources><color name="ic_launcher_background">#08211E</color></resources>
""")
    write_text(res / "values" / "strings.xml", """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">وَسْم</string>
    <string name="title_activity_main">وَسْم</string>
    <string name="package_name">com.waththiq.reports</string>
    <string name="custom_url_scheme">com.waththiq.reports</string>
</resources>
""")
    write_text(res / "values" / "styles.xml", """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="AppTheme" parent="Theme.AppCompat.Light.DarkActionBar">
        <item name="colorPrimary">@color/colorPrimary</item>
        <item name="colorPrimaryDark">@color/colorPrimaryDark</item>
        <item name="colorAccent">@color/colorAccent</item>
        <item name="android:navigationBarColor">@color/wasm_brand_dark</item>
        <item name="android:statusBarColor">@color/wasm_brand_dark</item>
    </style>
    <style name="AppTheme.NoActionBar" parent="Theme.AppCompat.DayNight.NoActionBar">
        <item name="windowActionBar">false</item>
        <item name="windowNoTitle">true</item>
        <item name="android:background">@color/wasm_brand_dark</item>
        <item name="android:windowBackground">@color/wasm_brand_dark</item>
        <item name="android:navigationBarColor">@color/wasm_brand_dark</item>
        <item name="android:statusBarColor">@color/wasm_brand_dark</item>
    </style>
    <style name="AppTheme.NoActionBarLaunch" parent="Theme.SplashScreen">
        <item name="windowSplashScreenBackground">@color/wasm_brand_dark</item>
        <item name="windowSplashScreenAnimatedIcon">@mipmap/ic_launcher_foreground</item>
        <item name="postSplashScreenTheme">@style/AppTheme.NoActionBar</item>
    </style>
</resources>
""")
    write_text(res / "values-v31" / "styles.xml", """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="AppTheme.NoActionBarLaunch" parent="Theme.SplashScreen">
        <item name="android:windowSplashScreenBackground">@color/wasm_brand_dark</item>
        <item name="android:windowSplashScreenAnimatedIcon">@mipmap/ic_launcher_foreground</item>
        <item name="android:windowSplashScreenIconBackgroundColor">@color/wasm_brand_dark</item>
        <item name="postSplashScreenTheme">@style/AppTheme.NoActionBar</item>
    </style>
</resources>
""")
    write_text(app_main / "AndroidManifest.xml", """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application android:allowBackup="true" android:icon="@mipmap/ic_launcher" android:label="@string/app_name" android:roundIcon="@mipmap/ic_launcher_round" android:supportsRtl="true" android:theme="@style/AppTheme">
        <activity android:configChanges="orientation|keyboardHidden|keyboard|screenSize|locale|smallestScreenSize|screenLayout|uiMode|navigation|density" android:name=".MainActivity" android:label="@string/title_activity_main" android:theme="@style/AppTheme.NoActionBarLaunch" android:launchMode="singleTask" android:exported="true">
            <intent-filter><action android:name="android.intent.action.MAIN" /><category android:name="android.intent.category.LAUNCHER" /></intent-filter>
        </activity>
        <provider android:name="androidx.core.content.FileProvider" android:authorities="${applicationId}.fileprovider" android:exported="false" android:grantUriPermissions="true">
            <meta-data android:name="android.support.FILE_PROVIDER_PATHS" android:resource="@xml/file_paths" />
        </provider>
    </application>
    <uses-permission android:name="android.permission.INTERNET" />
</manifest>
""")
    java = app_main / "java" / "com" / "waththiq" / "reports" / "MainActivity.java"
    write_text(java, """package com.waththiq.reports;

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
        super.onCreate(savedInstanceState);
        View webView = getBridge().getWebView();
        webView.setBackgroundColor(Color.rgb(8, 33, 30));
        ViewCompat.setOnApplyWindowInsetsListener(webView, (view, windowInsets) -> {
            Insets systemBars = windowInsets.getInsets(WindowInsetsCompat.Type.systemBars());
            view.setPadding(view.getPaddingLeft(), view.getPaddingTop(), view.getPaddingRight(), systemBars.bottom);
            return windowInsets;
        });
        ViewCompat.requestApplyInsets(webView);
    }
}
""")

    # Android 12+ splash compatibility. Capacitor does not add this dependency
    # unless the splash plugin is installed, so add only the AndroidX primitive
    # required by the official launch theme.
    app_gradle = android_dir / "app" / "build.gradle"
    gradle_text = app_gradle.read_text(encoding="utf-8")
    splash_dependency = "implementation 'androidx.core:core-splashscreen:1.0.1'"
    if splash_dependency not in gradle_text:
        gradle_text = gradle_text.replace(
            "dependencies {",
            "dependencies {\n    " + splash_dependency,
            1,
        )
        app_gradle.write_text(gradle_text, encoding="utf-8")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--android-dir", type=Path, default=None)
    args = parser.parse_args()
    generate_web()
    if args.android_dir is not None:
        generate_android(args.android_dir.resolve())

if __name__ == "__main__":
    main()

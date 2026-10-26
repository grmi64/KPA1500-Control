#!/bin/bash
set -eu
cd "$(dirname "$0")/.."
APP="$PWD/dist/KPA1500 Control.app"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources" /tmp/kpa1500-swift-cache
swiftc -module-cache-path /tmp/kpa1500-swift-cache -O Sources/App.swift Sources/WindowPlacement.swift -framework Cocoa -framework WebKit -o "$APP/Contents/MacOS/KPA1500Control"
BUILD_PYTHON="${AMP_BUILD_PYTHON:-/tmp/powermaster-build-env/bin/python}"
PYINSTALLER_CONFIG_DIR=/tmp/kpa1500-pyinstaller "$BUILD_PYTHON" -m PyInstaller --noconfirm --onedir --name amp-engine --distpath /tmp/kpa1500-frozen --workpath /tmp/kpa1500-freeze-work --specpath /tmp/kpa1500-freeze-spec --add-data "$PWD/Sources/index.html:." --add-data "$PWD/Sources/app.js:." --add-data "$PWD/Sources/app.css:." --add-data "$PWD/Sources/kpa_meter_colors.js:." Sources/server.py
ditto /tmp/kpa1500-frozen/amp-engine "$APP/Contents/Resources/amp-engine"
cp Assets/AppIcon.icns "$APP/Contents/Resources/AppIcon.icns"
/usr/bin/python3 - "$APP" <<'PY'
import plistlib,sys
from pathlib import Path
p=Path(sys.argv[1])/'Contents/Info.plist'
p.write_bytes(plistlib.dumps(dict(CFBundleIdentifier='com.grmi64.KPA1500Control',CFBundleName='KPA1500 Control',CFBundleDisplayName='KPA1500 Control',CFBundleExecutable='KPA1500Control',CFBundlePackageType='APPL',CFBundleShortVersionString='0.1.9',CFBundleVersion='10',CFBundleIconFile='AppIcon.icns',LSMinimumSystemVersion='12.0',NSHighResolutionCapable=True,NSPrincipalClass='NSApplication')))
PY
codesign --force --deep --sign - "$APP"
echo "$APP"

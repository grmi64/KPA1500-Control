# KPA1500 Control application icon

AppIcon-source.png is the shared high-resolution transparent artwork. AppIcon.icns is the macOS application icon referenced by CFBundleIconFile. AppIcon.ico contains transparent PNG-backed entries at 16, 24, 32, 48, 64, 128 and 256 pixels for Windows packaging. Both Windows build identities now embed this ICO. Project-owned artwork is covered by the root MIT LICENSE; no image content was changed in this step.

Run `python3 scripts/build_icons.py` on macOS to regenerate both containers with sips and iconutil. The Mac app build copies the prebuilt ICNS; it does not require image-generation tools or Pillow.

Design: dark graphite instrument, mint semicircular power gauge, amber needle and RF waveform. A future PowerMaster II icon should retain the family materials but use a distinct horizontal meter silhouette and blue accents. PowerMaster artwork is deferred.

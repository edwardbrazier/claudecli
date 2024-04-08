# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['claudecli\\__main__.py'],
    pathex=['C:\\Users\\Edward\\Programming\\claudecli\\venv\\Lib\\site-packages'],
    binaries=[],
    datas=[],
    hiddenimports=[
        "black",
        "certifi",
        "charset-normalizer",
        "click",
        "idna",
        "markdown-it-py",
        "mdurl",
        "mypy-extensions",
        "packaging",
        "pathspec",
        "platformdirs",
        "prompt-toolkit",
        "pygments",
        "pyyaml",
        "requests",
        "rich",
        "tomli",
        "typing_extensions",
        "urllib3",
        "wcwidth",
        "xdg-base-dirs",
        "pyperclip",
        "pysocks",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='__main__',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='__main__',
    options=[('onefile', '')]
)

"""
build.py — Memeface 릴리즈 빌드 오케스트레이터

사용법
------
  python build.py                # 일반 빌드
  python build.py --clean        # 캐시·산출물 정리 후 빌드
  python build.py --sign         # 빌드 + 자체 서명
  python build.py --clean --sign # 풀 파이프라인
  python build.py --no-build --sign  # 이미 빌드된 EXE만 서명

산출물
------
  dist/Memeface/Memeface.exe
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT     = Path(__file__).parent.resolve()
DIST     = ROOT / 'dist'
BUILD    = ROOT / 'build'
SPEC     = ROOT / 'memeface.spec'

ICON_PNG = ROOT / 'meme' / 'default.png'
ICON_ICO = ROOT / 'build_icon.ico'
VERSION  = ROOT / 'version_info.txt'

EXE_NAME = 'Memeface.exe'
EXE_PATH = DIST / 'Memeface' / EXE_NAME


# ─── 사전 준비물 생성 ─────────────────────────────────────────────────────────

def make_icon() -> None:
    """default.png → build_icon.ico (256x256 까지 다중 사이즈)"""
    if ICON_ICO.exists():
        return
    if not ICON_PNG.exists():
        print(f'[Build] 경고: 아이콘 원본 없음 → 아이콘 미설정')
        return
    try:
        from PIL import Image
    except ImportError:
        print('[Build] Pillow 미설치 → 아이콘 변환 건너뜀')
        return
    img = Image.open(ICON_PNG).convert('RGBA')
    img.save(
        ICON_ICO,
        format='ICO',
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print(f'[Build] 아이콘 생성: {ICON_ICO}')


def make_version_info() -> None:
    """Windows EXE 메타데이터 (속성 → 자세히 탭에 표시)"""
    if VERSION.exists():
        return
    content = '''# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0),
  ),
  kids=[
    StringFileInfo([
      StringTable('040904B0', [
        StringStruct('CompanyName', 'Memeface'),
        StringStruct('FileDescription', 'Memeface - Webcam Meme Overlay'),
        StringStruct('FileVersion', '1.0.0.0'),
        StringStruct('InternalName', 'Memeface'),
        StringStruct('LegalCopyright', 'Copyright (c) 2026 Memeface'),
        StringStruct('OriginalFilename', 'Memeface.exe'),
        StringStruct('ProductName', 'Memeface'),
        StringStruct('ProductVersion', '1.0.0.0'),
      ])
    ]),
    VarFileInfo([VarStruct('Translation', [0x0409, 1200])])
  ]
)
'''
    VERSION.write_text(content, encoding='utf-8')
    print(f'[Build] 버전 정보 생성: {VERSION}')


# ─── 동작 ────────────────────────────────────────────────────────────────────

def clean() -> None:
    """이전 빌드 산출물 정리"""
    for p in (DIST, BUILD):
        if p.exists():
            shutil.rmtree(p, ignore_errors=True)
            print(f'[Clean] 삭제: {p}')
    for f in (ICON_ICO, VERSION):
        if f.exists():
            f.unlink()
            print(f'[Clean] 삭제: {f}')


def build() -> None:
    """PyInstaller 호출"""
    make_icon()
    make_version_info()

    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print('[Build] PyInstaller 미설치 → pip install pyinstaller 실행')
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', 'pyinstaller'],
            check=True,
        )

    # Windows 파일 잠금 회피: distpath/workpath 를 매번 unique 하게
    import time as _time
    stamp = _time.strftime('%H%M%S')
    work = ROOT / f'build_{stamp}'
    out  = ROOT / f'dist_{stamp}'

    cmd = [
        sys.executable, '-m', 'PyInstaller', '--noconfirm',
        '--workpath', str(work),
        '--distpath', str(out),
        str(SPEC),
    ]
    print(f'[Build] 실행: {" ".join(cmd)}')
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        print('[Build] FAIL - PyInstaller exit code != 0')
        sys.exit(1)

    # 산출물을 dist/Memeface 로 이동
    final_dir = DIST / 'Memeface'
    DIST.mkdir(exist_ok=True)
    if final_dir.exists():
        try:
            shutil.rmtree(final_dir)
        except Exception as e:
            print(f'[Build] 기존 dist 삭제 실패: {e}')
            # 백업 이름으로 옮기고 진행
            backup = DIST / f'Memeface_old_{stamp}'
            try:
                final_dir.rename(backup)
                print(f'[Build] 백업: {backup}')
            except Exception:
                print(f'[Build] 백업도 실패 - 산출물은 {out}/Memeface 에 그대로 둠')
                EXE_PATH_OUT = out / 'Memeface' / EXE_NAME
                if EXE_PATH_OUT.exists():
                    size_mb = EXE_PATH_OUT.stat().st_size / 1024 / 1024
                    print(f'[Build] OK 완료: {EXE_PATH_OUT} ({size_mb:.1f} MB)')
                # 작업 폴더 정리
                shutil.rmtree(work, ignore_errors=True)
                return
    shutil.move(str(out / 'Memeface'), str(final_dir))
    shutil.rmtree(out, ignore_errors=True)
    shutil.rmtree(work, ignore_errors=True)

    if not EXE_PATH.exists():
        print(f'[Build] FAIL - 산출물 없음: {EXE_PATH}')
        sys.exit(1)

    size_mb = EXE_PATH.stat().st_size / 1024 / 1024
    print(f'[Build] OK 완료: {EXE_PATH} ({size_mb:.1f} MB)')


def package() -> None:
    """dist/Memeface/ 폴더를 Memeface-1.0.0.zip 으로 압축"""
    if not (DIST / 'Memeface').exists():
        print(f'[Pkg] 빌드 폴더 없음: {DIST / "Memeface"}')
        sys.exit(1)
    zip_path = DIST / 'Memeface-1.0.0.zip'
    if zip_path.exists():
        zip_path.unlink()
    print(f'[Pkg] 압축 생성: {zip_path}')
    # shutil.make_archive 는 .zip 확장자 자동 부착
    shutil.make_archive(
        base_name=str(zip_path.with_suffix('')),
        format='zip',
        root_dir=str(DIST),
        base_dir='Memeface',
    )
    size_mb = zip_path.stat().st_size / 1024 / 1024
    print(f'[Pkg] OK 완료: {zip_path} ({size_mb:.1f} MB)')


def sign() -> None:
    """sign.ps1 PowerShell 스크립트 호출"""
    if not EXE_PATH.exists():
        print(f'[Sign] EXE 없음: {EXE_PATH}')
        sys.exit(1)
    ps1 = ROOT / 'sign.ps1'
    if not ps1.exists():
        print(f'[Sign] sign.ps1 없음: {ps1}')
        sys.exit(1)
    # pwsh.exe (PowerShell 7): UTF-8 BOM 없는 ps1도 올바르게 읽음
    # powershell.exe (5.x): CP949로 읽어 한글이 깨져 파싱 오류 발생
    cmd = [
        'pwsh.exe',
        '-NoProfile', '-ExecutionPolicy', 'Bypass',
        '-File', str(ps1),
        '-ExePath', str(EXE_PATH),
    ]
    print(f'[Sign] 실행: {" ".join(cmd)}')
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        print('[Sign] 실패')
        sys.exit(1)
    print('[Sign] OK 완료')


# ─── 진입점 ───────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(description='Memeface 릴리즈 빌드')
    p.add_argument('--clean',    action='store_true', help='빌드 폴더 정리')
    p.add_argument('--sign',     action='store_true', help='빌드 후 코드 서명')
    p.add_argument('--package',  action='store_true', help='빌드 후 배포 ZIP 생성')
    p.add_argument('--no-build', action='store_true', help='빌드 건너뛰기 (서명/패키징만)')
    args = p.parse_args()

    if args.clean:
        clean()
    if not args.no_build:
        build()
    if args.sign:
        sign()
    if args.package:
        package()


if __name__ == '__main__':
    main()

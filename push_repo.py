import os
import shutil
import stat
import subprocess
import sys

REPO_DIR = r"C:\Working\SkyTemple"
REMOTE_URL = "https://github.com/Dev-Corgi/Explorers-of-Alpha-.git"
SIZE_LIMIT = 95 * 1024 * 1024  # GitHub 한도 100MB보다 약간 낮게

IGNORE_LINES = [
    "*.nds",
    "PatchTesting/",
    "tools/melonds_compatibility_*/",
]


def run(cmd, check=True):
    print(f"\n> {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=REPO_DIR, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip())
    if check and result.returncode != 0:
        sys.exit(f"실패: {' '.join(cmd)}")
    return result


def remove_readonly(func, path, _):
    os.chmod(path, stat.S_IWRITE)
    func(path)


def main():
    os.chdir(REPO_DIR)

    # 1. 기존 .git 삭제
    git_dir = os.path.join(REPO_DIR, ".git")
    if os.path.exists(git_dir):
        print("기존 .git 삭제 중...")
        shutil.rmtree(git_dir, onerror=remove_readonly)

    # 2. .gitignore 먼저 작성 (기존 내용 유지, 중복 제외)
    gi_path = os.path.join(REPO_DIR, ".gitignore")
    existing = []
    if os.path.exists(gi_path):
        with open(gi_path, encoding="utf-8") as f:
            existing = f.read().splitlines()
    with open(gi_path, "a", encoding="utf-8") as f:
        if existing and existing[-1] != "":
            f.write("\n")
        for line in IGNORE_LINES:
            if line not in existing:
                f.write(line + "\n")

    # 3. 새 저장소 초기화 및 add
    run(["git", "init", "-b", "main"])
    run(["git", "add", "."])

    # 4. 스테이징된 파일 중 큰 파일 검사
    staged = run(["git", "ls-files"]).stdout.splitlines()
    big = []
    for p in staged:
        fp = os.path.join(REPO_DIR, p)
        if os.path.isfile(fp) and os.path.getsize(fp) > SIZE_LIMIT:
            big.append((p, os.path.getsize(fp) / 1024 / 1024))
    if big:
        print("\n⚠ 95MB 넘는 파일이 있어 중단합니다. .gitignore에 추가하세요:")
        for p, mb in big:
            print(f"  {p} ({mb:.1f} MB)")
        sys.exit(1)

    # 5. 커밋
    run(["git", "commit", "-m", "Initial commit"])

    # 6. 원격 연결 후 푸시
    run(["git", "remote", "add", "origin", REMOTE_URL])
    run(["git", "push", "-u", "origin", "main", "--force"])

    print("\n완료!")


if __name__ == "__main__":
    main()
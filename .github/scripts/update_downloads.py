import os
import re
import urllib.request
import json

USERNAME = "RyuuMeow"
README = "README.md"

TOKEN = os.environ.get("GITHUB_TOKEN")

headers = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2026-03-10",
}

if TOKEN:
    headers["Authorization"] = f"Bearer {TOKEN}"


def get_json(url):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        return json.load(response)


def get_all_pages(url):
    page = 1
    result = []

    while True:
        separator = "&" if "?" in url else "?"
        data = get_json(f"{url}{separator}per_page=100&page={page}")

        if not data:
            break

        result.extend(data)

        if len(data) < 100:
            break

        page += 1

    return result


# 取得帳號下所有公開 repositories
repos = get_all_pages(
    f"https://api.github.com/users/{USERNAME}/repos?type=owner"
)

total_downloads = 0
repo_stats = []

for repo in repos:
    # 可選：跳過 fork
    if repo["fork"]:
        continue

    repo_name = repo["name"]

    releases = get_all_pages(
        f"https://api.github.com/repos/{USERNAME}/{repo_name}/releases"
    )

    repo_downloads = 0

    for release in releases:
        for asset in release.get("assets", []):
            repo_downloads += asset.get("download_count", 0)

    if repo_downloads > 0:
        repo_stats.append((repo_name, repo_downloads))

    total_downloads += repo_downloads


print("\nRelease download stats:")
for name, count in sorted(
    repo_stats,
    key=lambda x: x[1],
    reverse=True
):
    print(f"{name}: {count:,}")

print(f"\nTOTAL: {total_downloads:,}")


# Badge 顯示格式，例如 12,345
display_count = f"{total_downloads:,}"

badge = (
    '<img '
    'src="https://img.shields.io/badge/DOWNLOADS-'
    f'{display_count.replace(",", "%2C")}-'
    'FFB454?style=flat-square&logo=github&labelColor=161B22" '
    'alt="Total release downloads">'
)

with open(README, "r", encoding="utf-8") as f:
    content = f.read()

pattern = (
    r"<!-- TOTAL_RELEASE_DOWNLOADS:START -->"
    r".*?"
    r"<!-- TOTAL_RELEASE_DOWNLOADS:END -->"
)

replacement = (
    "<!-- TOTAL_RELEASE_DOWNLOADS:START -->\n"
    f"{badge}\n"
    "<!-- TOTAL_RELEASE_DOWNLOADS:END -->"
)

new_content, count = re.subn(
    pattern,
    replacement,
    content,
    flags=re.DOTALL,
)

if count == 0:
    raise RuntimeError(
        "TOTAL_RELEASE_DOWNLOADS markers not found in README.md"
    )

with open(README, "w", encoding="utf-8") as f:
    f.write(new_content)

import requests
import base64
import re

BASE_URL = "https://api.github.com"


def get_default_branch(owner, repo, token):
    url = f"{BASE_URL}/repos/{owner}/{repo}"
    headers = {"Authorization": f"token {token}"}
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json().get("default_branch", "main")


def get_branch_sha(owner, repo, branch, token):
    url = f"{BASE_URL}/repos/{owner}/{repo}/branches/{branch}"
    headers = {"Authorization": f"token {token}"}
    r = requests.get(url, headers=headers, timeout=10)
    if r.status_code == 404 and branch == "main":
        # Retry with master if main not found
        return get_branch_sha(owner, repo, "master", token)
    r.raise_for_status()
    return r.json()["commit"]["sha"]


def get_repo_files(owner, repo, branch, token):
    sha = get_branch_sha(owner, repo, branch, token)
    url = f"{BASE_URL}/repos/{owner}/{repo}/git/trees/{sha}?recursive=1"
    headers = {"Authorization": f"token {token}"}
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    data = r.json()
    return [item for item in data.get("tree", []) if item["type"] == "blob"]


def fetch_file_content(owner, repo, path, branch, token):
    url = f"{BASE_URL}/repos/{owner}/{repo}/contents/{path}?ref={branch}"
    headers = {"Authorization": f"token {token}"}
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    data = r.json()
    if data.get("encoding") == "base64":
        return base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
    return data.get("content", "")


def analyze_repo(owner, repo, token, branch="main"):
    branch = get_default_branch(owner, repo, token)
    files = get_repo_files(owner, repo, branch, token)

    readme_text = ""
    readme_summary = ""
    for f in files:
        if f["path"].lower().startswith("readme"):
            readme_text = fetch_file_content(owner, repo, f["path"], branch, token)
            # Simple summary (first 300 chars)
            readme_summary = readme_text[:300] + ("..." if len(readme_text) > 300 else "")
            break

    file_list = [f["path"] for f in files]
    return {
        "repo": f"{owner}/{repo}",
        "branch": branch,
        "file_count": len(files),
        "files": file_list[:20],
        "readme_summary": readme_summary,
        "readme_text": readme_text,
    }

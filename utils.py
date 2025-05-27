import requests
import re
from transformers import pipeline

# Initialize models
summarizer = pipeline("summarization", model="facebook/bart-large-cnn", device=-1)
qa_pipeline = pipeline("question-answering", model="deepset/roberta-base-squad2", device=-1)

def get_default_branch(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}"
    r = requests.get(url)
    if r.status_code == 200:
        return r.json().get("default_branch", "main")
    return "main"

def summarize_text(text):
    if len(text) < 50:
        return text
    chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]
    summary = ""
    for chunk in chunks:
        summary += summarizer(chunk, max_length=150, min_length=30, do_sample=False)[0]['summary_text'] + "\n"
    return summary.strip()

def get_repo_files(owner, repo, branch):
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    res = requests.get(url)
    if res.status_code != 200:
        return []
    tree = res.json().get("tree", [])
    allowed_exts = [".py", ".txt", ".html", ".md", "requirements.txt"]
    return [f for f in tree if f["type"] == "blob" and any(f["path"].endswith(ext) for ext in allowed_exts)]

def fetch_file_content(owner, repo, path, branch):
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
    res = requests.get(url)
    return res.text if res.status_code == 200 else None

def clean_python_code(content):
    docstrings = re.findall(r'"""(.*?)"""', content, re.DOTALL)
    comments = re.findall(r'#.*', content)
    defs = re.findall(r'(def .*?:|class .*?:)', content)
    return "\n".join(docstrings + comments + defs)

def find_root_readme(files):
    root_readmes = [f for f in files if f['path'].lower() in ['readme.md', 'readme', 'readme.txt']]
    if root_readmes:
        return root_readmes[0]
    readmes = [f for f in files if 'readme' in f['path'].lower()]
    return readmes[0] if readmes else None

def answer_question(question, summary_context):
    if len(summary_context) < 50:
        return "⚠️ Not enough context to answer."
    try:
        result = qa_pipeline(question=question, context=summary_context)
        return result.get("answer", "No answer found.")
    except Exception as e:
        return f"⚠️ Error while answering: {str(e)}"

def analyze_repo(owner, repo):
    branch = get_default_branch(owner, repo)
    files = get_repo_files(owner, repo, branch)
    if not files:
        return {"summary": "❌ No files found or unable to fetch repository files.", "context": ""}

    all_text = ""
    readme_summary = None
    file_types_used = set()
    function_class_list = []

    readme_file = find_root_readme(files)
    if readme_file:
        content = fetch_file_content(owner, repo, readme_file['path'], branch)
        if content:
            readme_summary = summarize_text(content)

    for f in files:
        path = f['path']
        if readme_file and path == readme_file['path']:
            continue

        content = fetch_file_content(owner, repo, path, branch)
        if not content:
            continue

        if path.endswith(".py"):
            file_types_used.add(".py")
            defs_classes = re.findall(r'(def\s+\w+\s*\(.*?\)\s*:|class\s+\w+\s*(\(.*?\))?\s*:)', content)
            function_class_list.extend([f"{path}: {item[0].strip()}" for item in defs_classes])
            cleaned = clean_python_code(content)
            if cleaned:
                all_text += f"\n# Summary of {path}\n" + cleaned

        elif path.endswith("requirements.txt"):
            file_types_used.add("requirements.txt")
            all_text += f"\n# Dependencies from {path}:\n" + content

        elif path.endswith(".html"):
            file_types_used.add(".html")
            all_text += f"\n# HTML structure from {path}:\n" + content

        elif path.endswith(".md"):
            file_types_used.add(".md")
            all_text += f"\n# Markdown file {path}:\n" + content

        elif path.endswith(".txt"):
            file_types_used.add(".txt")
            all_text += f"\n# Text file {path}:\n" + content

    summary_parts = []

    if readme_summary:
        summary_parts.append(f"### 📘 README Summary:\n{readme_summary}")

    if all_text.strip():
        code_summary = summarize_text(all_text)
        summary_parts.append(f"### 🧾 Code & Files Summary:\n{code_summary}")

    file_list = ", ".join(sorted(file_types_used)) if file_types_used else "No identifiable file types."
    summary_parts.append(f"### 📂 File Types Used:\n{file_list}")

    if function_class_list:
        formatted_fc = "\n".join(f"- {line}" for line in function_class_list)
        summary_parts.append(f"### 🧠 Key Functions & Classes Found:\n{formatted_fc}")

    full_summary = "\n\n".join(summary_parts)

    return {
        "summary": full_summary,
        "context": full_summary  # Used for Q&A
    }

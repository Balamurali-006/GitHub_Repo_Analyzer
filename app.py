import streamlit as st
import os
import requests
import base64
from transformers import pipeline
import openai
from dotenv import load_dotenv

# ----------------- LOAD ENV -----------------
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")

if not GITHUB_TOKEN:
    st.error("❌ GITHUB_TOKEN not found. Check your .env file.")
if not OPENROUTER_KEY:
    st.error("❌ OPENROUTER_KEY not found. Check your .env file.")

# OpenRouter client
client = openai.OpenAI(api_key=OPENROUTER_KEY, base_url="https://openrouter.ai/api/v1")

# ----------------- CONFIG -----------------
GITHUB_API = "https://api.github.com"
DEFAULT_BRANCH = "main"

# ----------------- HELPERS -----------------
def sanitize_repo_input(repo_input):
    repo_input = repo_input.strip()
    if repo_input.endswith(".git"):
        repo_input = repo_input[:-4]
    return repo_input

def fetch_branch_sha(repo, branch=DEFAULT_BRANCH):
    url = f"{GITHUB_API}/repos/{repo}/branches/{branch}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 404 and branch == "main":
        return fetch_branch_sha(repo, "master")
    r.raise_for_status()
    return r.json()["commit"]["commit"]["tree"]["sha"]

def fetch_github_tree(repo, branch=DEFAULT_BRANCH):
    sha = fetch_branch_sha(repo, branch)
    url = f"{GITHUB_API}/repos/{repo}/git/trees/{sha}?recursive=1"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json()

def fetch_file_content(repo, path, branch=DEFAULT_BRANCH):
    url = f"{GITHUB_API}/repos/{repo}/contents/{path}?ref={branch}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    data = r.json()
    if data.get("encoding") == "base64":
        return base64.b64decode(data["content"]).decode("utf-8")
    return data.get("content")

def summarize_text(text):
    if not text or len(text.strip()) < 20:
        return text
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    summary = summarizer(text, max_length=300, min_length=40, do_sample=False)
    return summary[0]['summary_text']

def generate_fallback_summary(repo, branch, files):
    combined_texts = []
    for f in files:
        if f.split('.')[-1].lower() in ["png", "jpg", "jpeg", "gif", "exe", "dll", "zip"]:
            continue
        try:
            content = fetch_file_content(repo, f, branch)
            if content and len(content) < 50000:
                combined_texts.append(f"### {f}\n{content[:5000]}")
        except Exception:
            continue
    if not combined_texts:
        return "No meaningful content found to analyze."
    combined = "\n\n".join(combined_texts)
    return summarize_text(combined)

def ask_question(summary, question):
    messages = [
        {"role": "system", "content": "You are CodeMentorGPT, a helpful coding mentor."},
        {"role": "user", "content": f"Use ONLY the following summary to answer questions:\n\n{summary}"},
        {"role": "user", "content": f"Question: {question}"}
    ]
    response = client.chat.completions.create(
        model="mistralai/mixtral-8x7b-instruct",
        messages=messages,
        temperature=0.7
    )
    return response.choices[0].message.content

# ----------------- STREAMLIT UI -----------------
st.title("🔍 GitHub Repository Analyzer & Q&A")
st.write("Analyze a repository, summarize the README, or fallback to all files.")

if "readme_summary" not in st.session_state:
    st.session_state.readme_summary = ""
if "qa_history" not in st.session_state:
    st.session_state.qa_history = []

# Clear history
if st.button("🧹 Clear History"):
    st.session_state.qa_history = []
    st.session_state.readme_summary = ""
    st.success("History cleared!")

repo_input = st.text_input("Repository (owner/repo)", placeholder="e.g., torvalds/linux")
branch_input = st.text_input(f"Branch (default: {DEFAULT_BRANCH})", placeholder=DEFAULT_BRANCH)

if st.button("Analyze Repository") and repo_input:
    repo = sanitize_repo_input(repo_input)
    branch = branch_input.strip() or DEFAULT_BRANCH
    try:
        st.session_state.qa_history = []
        st.session_state.readme_summary = ""

        tree_data = fetch_github_tree(repo, branch)
        files = [f['path'] for f in tree_data.get('tree', [])]

        st.subheader("📁 Repository Structure")
        st.write(f"Branch: {branch}")
        st.write(f"Total files: {len(files)}")
        for f in files[:50]:
            st.write(f" - {f}")
        if len(files) > 50:
            st.write(f"...and {len(files)-50} more files")

        readme_path = next((f for f in files if f.lower().startswith("readme")), None)

        if readme_path:
            readme_content = fetch_file_content(repo, readme_path, branch)
            if readme_content:
                readme_summary = summarize_text(readme_content)
                st.session_state.readme_summary = readme_summary
                st.subheader("📘 README Summary")
                st.write(readme_summary)
                with st.expander("📄 View Full README"):
                    st.text(readme_content)
            else:
                st.warning("⚠️ Could not fetch README content.")
        else:
            st.warning("⚠️ README.md not found. Summarizing repository files instead...")
            fallback_summary = generate_fallback_summary(repo, branch, files)
            st.session_state.readme_summary = fallback_summary
            st.subheader("📜 Repository Summary (Fallback)")
            st.write(fallback_summary)

    except requests.exceptions.HTTPError as e:
        st.error(f"⚠️ GitHub API error: {e}")
    except Exception as e:
        st.error(f"⚠️ Unexpected error: {e}")

if st.session_state.readme_summary:
    st.subheader("❓ Ask Questions")
    question_input = st.text_input("Your Question", key="question_input")
    if st.button("Get Answer"):
        if question_input:
            try:
                answer = ask_question(st.session_state.readme_summary, question_input)
                st.session_state.qa_history.append({"q": question_input, "a": answer})
            except Exception as e:
                st.error(f"⚠️ Error fetching answer: {e}")
        else:
            st.warning("Enter a question to get an answer.")

    for qa in st.session_state.qa_history:
        st.markdown(f"**Q:** {qa['q']}")
        st.markdown(f"**A:** {qa['a']}")
        st.write("---")

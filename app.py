import streamlit as st
from utils import analyze_repo, answer_question

st.set_page_config(page_title="GitHub Repo Analyzer", layout="centered")

st.title("🧠 GitHub Repo Analyzer")
st.markdown("Enter a **GitHub repo link** and get a short NLP-based project summary. You can also **ask questions** about the repo!")

# Store repo context for Q&A
if "repo_context" not in st.session_state:
    st.session_state.repo_context = ""

repo_url = st.text_input("🔗 GitHub Repository URL", placeholder="e.g. https://github.com/owner/repo")

if st.button("Summarize Repository"):
    if repo_url:
        try:
            parts = repo_url.strip().split("/")
            owner = parts[-2]
            repo = parts[-1]
            with st.spinner("🔍 Analyzing repository..."):
                result = analyze_repo(owner, repo)
                summary = result.get("summary", "⚠️ No summary generated.")
                st.session_state.repo_context = result.get("context", "")
            st.success("✅ Summary generated!")
            st.markdown("### 📌 Project Summary")
            st.write(summary)
        except Exception as e:
            st.error(f"❌ Error: {e}")
    else:
        st.warning("⚠️ Please enter a valid GitHub repo URL.")

st.divider()

st.subheader("💬 Ask a Question about the Repository")
question = st.text_input("Type your question", placeholder="e.g. What ML model is used?")

if st.button("Get Answer"):
    if not question:
        st.warning("⚠️ Please type a question.")
    elif not st.session_state.repo_context:
        st.warning("❗ Analyze a repository first before asking questions.")
    else:
        with st.spinner("🧠 Thinking..."):
            answer = answer_question(question, st.session_state.repo_context)
        st.success("✅ Answer ready!")
        st.markdown(f"**Q:** {question}")
        st.markdown(f"**A:** {answer}")

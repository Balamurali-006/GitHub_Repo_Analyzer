# 🔎 GitHub Repo Analyzer (NLP-Based)

A simple **Streamlit** web app that summarizes any **public GitHub repository** using **Hugging Face Transformers**. Ideal for quickly understanding unfamiliar repositories without reading every file.

---

## ✨ Features
- 📂 Extracts key files like **README.md**, `requirements.txt`, and code snippets.  
- 🧠 Summarizes content using Hugging Face’s **`distilbart-cnn-12-6`** model.  
- ⚡ Works **without any API key** – completely free and open-source.  

---

## 🚀 How to Run
1. **Clone the Repository**  
   ```bash
   git clone https://github.com/<your-username>/GitHub_Repo_Analyzer.git
   cd GitHub_Repo_Analyzer
**2. Install Dependencies**
    ```bash
    pip install -r requirements.txt
**3. Launch the App**
    ```bash
    streamlit run app.py
**4. Open in Browser**
    http://localhost:8501
**Example Input**
    https://github.com/owner/repo

***🛠 Tech Stack***

Streamlit
 – Interactive UI framework

Transformers
 – NLP summarization

Requests
 – GitHub API interactions


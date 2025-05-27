
# GitHub Repo Analyzer (NLP-Based)

A simple Streamlit web app that summarizes the content of any public GitHub repository using Hugging Face Transformers.

## 💡 Features
- Extracts code, README, and requirements.txt
- Summarizes using `distilbart-cnn-12-6` from Hugging Face
- No API key required

## 🚀 Run the App
```bash
pip install -r requirements.txt
streamlit run app.py
```

## 📥 Example Input
```
https://github.com/owner/repo
```


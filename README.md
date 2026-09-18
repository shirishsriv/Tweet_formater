# X Post Formatter

Streamlit app that splits a draft into X-ready posts.

- Free accounts: 280 weighted characters per post
- X Premium: optional 25,000-character long post
- Thread numbering: `(1/n)` or `1/n`
- Split on words, sentences, or paragraphs
- URLs count as 23 characters

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Push this folder to a public GitHub repo (files at repo root: `app.py`, `requirements.txt`).
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **Create app** → select the repo, branch `main`, main file `app.py`.
4. Deploy. Your public URL will look like:
   `https://<app-name>.streamlit.app`

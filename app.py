import re
import streamlit as st

# --- X-style weighted length (approx official twitter-text rules) ---
URL_RE = re.compile(r"https?://[^\s]+", re.IGNORECASE)
# Most emoji / symbols outside BMP count as 2 weighted units
HEAVY_RE = re.compile(
    r"[\U0001F300-\U0001FAFF\U00002700-\U000027BF\U00002600-\U000026FF]"
)


def weighted_len(text: str) -> int:
    """Approximate X weighted character count. URLs count as 23."""
    if not text:
        return 0
    urls = URL_RE.findall(text)
    stripped = URL_RE.sub("\x00", text)
    weight = 0
    for ch in stripped:
        if ch == "\x00":
            continue
        weight += 2 if HEAVY_RE.match(ch) else 1
    weight += 23 * len(urls)
    return weight


def split_units(text: str, mode: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if mode == "Paragraphs":
        parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        return parts or [text]
    if mode == "Sentences":
        parts = re.split(r"(?<=[.!?])\s+", text)
        return [p.strip() for p in parts if p.strip()]
    return text.split()


def pack_units(units: list[str], joiner: str, limit: int) -> list[str]:
    tweets, current = [], ""
    for unit in units:
        # If a single unit is itself over the limit, hard-wrap it
        if weighted_len(unit) > limit:
            if current:
                tweets.append(current)
                current = ""
            tweets.extend(hard_wrap(unit, limit))
            continue
        trial = unit if not current else current + joiner + unit
        if weighted_len(trial) <= limit:
            current = trial
        else:
            if current:
                tweets.append(current)
            current = unit
    if current:
        tweets.append(current)
    return tweets


def hard_wrap(text: str, limit: int) -> list[str]:
    chunks, buf = [], ""
    for ch in text:
        trial = buf + ch
        if weighted_len(trial) <= limit:
            buf = trial
        else:
            if buf:
                chunks.append(buf)
            buf = ch
    if buf:
        chunks.append(buf)
    return chunks or [text]


def number_tweets(tweets: list[str], style: str, limit: int) -> list[str]:
    n = len(tweets)
    if n <= 1 or style == "None":
        return tweets

    numbered = []
    for i, t in enumerate(tweets, 1):
        suffix = f" ({i}/{n})" if style == "(1/n)" else f" {i}/{n}"
        # shrink body so suffix still fits
        body = t
        while weighted_len(body + suffix) > limit and body:
            body = body.rsplit(" ", 1)[0] if " " in body else body[:-1]
        numbered.append(body.rstrip() + suffix)
    return numbered


SAMPLE = """A 6-line Pandas pattern I use more than I admit.

df = df[df.select_dtypes("number").apply(lambda s: s.isfinite()).all(axis=1)]

Clean numeric rows. No NaN, no inf. Ready for the model."""


st.set_page_config(
    page_title="X Post Formatter",
    page_icon="𝕏",
    layout="wide",
)

st.markdown(
    """
    <style>
      .block-container {max-width: 1100px; padding-top: 1.4rem;}
      .tweet-card {
        background: #0f1419;
        color: #e7e9ea;
        border: 1px solid #2f3336;
        border-radius: 16px;
        padding: 16px 18px;
        font-family: "Chirp", "Helvetica Neue", Helvetica, Arial, sans-serif;
        font-size: 17px;
        line-height: 1.45;
        white-space: pre-wrap;
        word-break: break-word;
      }
      .meta {color: #71767b; font-size: 13px; margin-top: 8px;}
      .ok {color: #00ba7c;}
      .warn {color: #ffd400;}
      .bad {color: #f4212e;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("X Post Formatter")
st.caption("Split a draft into 280-character posts or keep one Premium long post. Copy and paste onto X.")

col_in, col_opt = st.columns([1.6, 1])

with col_in:
    draft = st.text_area(
        "Draft",
        value=SAMPLE,
        height=280,
        placeholder="Paste the post you want to format…",
    )

with col_opt:
    account = st.radio(
        "Account type",
        ["Free (280)", "Premium long post (25,000)", "Premium but thread at 280"],
        index=0,
    )
    split_mode = st.selectbox("Split on", ["Words", "Sentences", "Paragraphs"])
    numbering = st.selectbox("Thread numbers", ["(1/n)", "1/n", "None"])
    st.caption("Links count as 23 characters. Most emoji count as 2.")

if account.startswith("Premium long"):
    limit = 25000
    force_thread = False
else:
    limit = 280
    force_thread = True

raw_len = weighted_len(draft)
reserve = 8 if numbering != "None" and (force_thread or raw_len > limit) else 0
pack_limit = max(20, limit - reserve)

joiner = " " if split_mode == "Words" else " "
units = split_units(draft, split_mode)

if not force_thread and raw_len <= 25000:
    tweets = [draft.strip()] if draft.strip() else []
else:
    tweets = pack_units(units, joiner, pack_limit)
    tweets = number_tweets(tweets, numbering, limit)

st.divider()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Weighted chars (draft)", raw_len)
m2.metric("Posts", len(tweets))
m3.metric("Limit / post", limit)
over = raw_len > 280
m4.metric("Timeline hook", "Needs hook" if over else "Fits in feed")

if not tweets:
    st.info("Write something in the draft box.")
    st.stop()

st.subheader("Ready to post")

all_text = "\n\n---\n\n".join(tweets)
st.download_button(
    "Download thread as .txt",
    data=all_text,
    file_name="x_thread.txt",
    mime="text/plain",
)

for i, tweet in enumerate(tweets, 1):
    w = weighted_len(tweet)
    if w <= limit:
        klass, label = "ok", "within limit"
    elif w <= limit + 5:
        klass, label = "warn", "close to limit"
    else:
        klass, label = "bad", "over limit"

    left, right = st.columns([4, 1])
    with left:
        st.markdown(
            f'<div class="tweet-card">{tweet}</div>'
            f'<div class="meta"><span class="{klass}">{w} / {limit}</span> · {label} · post {i}</div>',
            unsafe_allow_html=True,
        )
    with right:
        st.code(tweet, language=None)
        if w > 280:
            hook = tweet[:270].rsplit(" ", 1)[0] + "…"
            st.caption(f"Feed preview (~280): {hook}")

if len(tweets) == 1 and weighted_len(tweets[0]) > 280:
    st.info(
        "Premium long posts still truncate in the timeline at ~280 characters. "
        "Make the first line a hook."
    )

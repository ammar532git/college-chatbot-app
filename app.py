import streamlit as st
from utils import create_college_bot
from PIL import Image
import base64
import io
import re
import os
import bcrypt
import difflib


hashed_password = b'$2b$12$VBsMkg3onMsj93qe9TSOCe3EcUq1.qGT0/CJ6Ywb11eCJnVtFT5wO'  

# ==== Session State ====
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "selected_question" not in st.session_state:
    st.session_state.selected_question = None
if "history" not in st.session_state:
    st.session_state.history = []

# ==== Page Config ====
st.set_page_config(page_title="College Doubt-Solver", page_icon="🎓", layout="centered")

# ==== CSS Styling ====
st.markdown("""
    <style>
    section[data-testid="stSidebar"] {
        width: 220px !important;
    }

    .moving-banner {
        position: fixed;
        top: 15px;
        right: -400px;
        color: white;
        padding: 10px 20px;
        font-size: 16px;
        font-weight: 600;
        z-index: 9999;
        white-space: nowrap;
        animation: slideBanner 18s linear infinite;
    }
    @keyframes slideBanner {
        0% { right: -400px; }
        100% { right: 100%; }
    }

    @media only screen and (max-width: 768px) {
        h1 {
            font-size: 20px !important;
        }
        .moving-banner {
            font-size: 14px;
            padding: 8px 16px;
        }
        .css-1v0mbdj, .css-10trblm, .stTextInput>div>div>input {
            font-size: 16px !important;
        }
        img {
            max-height: 60px !important;
        }
        .stButton button {
            font-size: 14px !important;
        }
    }
    </style>
    <div class="moving-banner">
        University is accredited with <b>"A" Grade</b> by NAAC.
    </div>
""", unsafe_allow_html=True)

# ==== Load Bot ====
retriever, faq_questions, qa_dict = create_college_bot(return_questions=True)
all_keywords = list(set(word.lower() for q in faq_questions for word in q.split()))

# ==== Logo ====
logo_path = "data/logo.png"
logo_image = Image.open(logo_path)
buffered = io.BytesIO()
logo_image.save(buffered, format="PNG")
logo_base64 = base64.b64encode(buffered.getvalue()).decode()

st.markdown(f"""
<div style='display: flex; align-items: center;'>
    <img src='data:image/png;base64,{logo_base64}' style='height:80px; margin-right: 20px;'>
    <h1 style='color:white; font-size:26px; font-weight:bold;'>Prof. Rajendra Singh (Rajju Bhaiya) University, Prayagraj.</h1>
</div>
""", unsafe_allow_html=True)

st.title("🎓 Ask Your College Doubts")

# ==== Welcome Text ====
st.markdown("""
<p style='color: #FFD700; font-size: 16px; font-weight: bold; margin-top: -10px;'>
    Welcome! Type a keyword (like <b>exam</b>, <b>dean</b>, <b>hostel</b>) to find matching questions.
</p>
""", unsafe_allow_html=True)

st.markdown("---")

# ==== Sidebar ====
with st.sidebar:
    st.markdown("## ⚙️ Options")
    if st.button("🧹 Reset Chat"):
        st.session_state.selected_question = None
        st.session_state.history = []

    with st.expander("🔐 Admin Login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username == "admin" and bcrypt.checkpw(password.encode(), hashed_password):
                st.success("✅ Login successful.")
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("❌ Invalid credentials")

# ==== Admin Viewer ====
if st.session_state.admin_logged_in:
    st.markdown("## 📋 Reported Feedbacks")

    if st.button("❌ Close Report Viewer"):
        st.session_state.admin_logged_in = False
        st.rerun()

    if os.path.exists("reported_answers.txt"):
        with open("reported_answers.txt", "r", encoding="utf-8") as f:
            content = f.read()
        st.text_area("Reported Feedback", content, height=300)
        with open("reported_answers.txt", "rb") as f:
            st.download_button("📅 Download Reports", f, file_name="reported_answers.txt")
    else:
        st.info("No reports submitted yet.")

# ==== Input and Suggestions ====
user_input = st.text_input("🔍 Start typing a keyword...")
suggestions = difflib.get_close_matches(user_input.lower(), all_keywords, n=5, cutoff=0.3) if user_input else []
selected_keyword = st.selectbox("💡 Suggested Keywords", suggestions) if suggestions else user_input

# ==== Show Matches ====
if selected_keyword and not st.session_state.selected_question:
    matches = [q for q in faq_questions if selected_keyword.lower() in q.lower()]
    if matches:
        st.markdown("### 💡 Matching Questions:")
        for i, q in enumerate(matches):
            col1, col2 = st.columns([0.85, 0.15])
            with col1:
                st.markdown(f"**{q}**")
            with col2:
                if st.button("Ask", key=f"ask_{i}"):
                    st.session_state.selected_question = q
                    st.rerun()
    else:
        st.warning("❌ No matching questions found.")

# ==== Show Answer ====
if st.session_state.selected_question:
    q = st.session_state.selected_question
    st.markdown(f"**You asked:** {q}")
    with st.spinner("🤖 Thinking..."):
        if q in qa_dict:
            answer = qa_dict[q]
        else:
            docs = retriever.get_relevant_documents(q)
            answer = docs[0].page_content.strip() if docs else "❌ No answer found."

    formatted = "\n".join(f"- {a.strip()}" for a in answer.split(";") if a.strip())
    st.session_state.history.append((q, formatted))
    st.session_state.selected_question = None
    st.rerun()

# ==== History and Reporting ====
if st.session_state.history:
    st.markdown("### 💬 Previous Questions & Answers")
    for idx, (q, a) in enumerate(st.session_state.history):
        with st.expander(q):
            st.markdown(f"**Answer:**\n\n{a}")
            with st.expander("🚩 Report this answer"):
                with st.form(f"report_form_{idx}"):
                    name = st.text_input("Your Name", key=f"name_{idx}")
                    email = st.text_input("Your Email", key=f"email_{idx}")
                    reason = st.text_area("Reason", key=f"reason_{idx}")
                    submitted = st.form_submit_button("Submit Report")
                    if submitted:
                        if name and re.match(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) and reason:
                            with open("reported_answers.txt", "a", encoding="utf-8") as f:
                                f.write(f"Name: {name}\nEmail: {email}\nQuestion: {q}\nAnswer: {a}\nReason: {reason}\n---\n")
                            st.success("✅ Report submitted.")
                        else:
                            st.error("❗ All fields are required and email must be valid.")

# ==== Footer ====
st.markdown("---")
st.markdown("<center><small>🤖 College FAQ Bot • Built by Ammar • Powered by Streamlit</small></center>", unsafe_allow_html=True)

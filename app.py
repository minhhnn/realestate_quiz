import streamlit as st
import json
import random
import time

# ================== CONFIG ==================
JSON_PATH = "questions.json"
NUM_SETS = 3
TIME_LIMIT_MINUTES = 20
PASS_THRESHOLD_PERCENT = 70
# ============================================

def load_questions(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def split_into_sets(questions, n_sets):
    random.shuffle(questions)
    return [questions[i::n_sets] for i in range(n_sets)]

# CALLBACK: Saves selection to a dictionary that won't be deleted
def record_answer(q_idx, widget_key):
    st.session_state.permanent_answers[q_idx] = st.session_state[widget_key]

# ================= STREAMLIT =================
st.set_page_config(page_title="Quiz App", layout="centered")
st.title("📘 Quiz Pháp Luật Bất Động Sản")

try:
    all_questions = load_questions(JSON_PATH)
except FileNotFoundError:
    st.error("Không tìm thấy file questions.json!")
    st.stop()

# ============== SESSION STATE ================
if "question_sets" not in st.session_state:
    st.session_state.question_sets = split_into_sets(all_questions, NUM_SETS)
if "selected_set" not in st.session_state:
    st.session_state.selected_set = 0
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()
if "review_mode" not in st.session_state:
    st.session_state.review_mode = False
# The "Safe" storage for user answers
if "permanent_answers" not in st.session_state:
    st.session_state.permanent_answers = {}

# ================= SET PICKER =================
set_choice = st.selectbox(
    "Chọn bộ câu hỏi:",
    options=[f"Bộ {i+1}" for i in range(NUM_SETS)],
    index=st.session_state.selected_set,
    disabled=st.session_state.submitted
)

st.session_state.selected_set = int(set_choice.split()[-1]) - 1
current_questions = st.session_state.question_sets[st.session_state.selected_set]

# ================= TIMER =====================
if not st.session_state.submitted:
    elapsed = time.time() - st.session_state.start_time
    remaining = max(0, TIME_LIMIT_MINUTES * 60 - elapsed)
    mins, secs = divmod(int(remaining), 60)
    st.info(f"⏱️ Thời gian còn lại: **{mins:02d}:{secs:02d}**")

# ================= QUESTIONS =================
for i, q in enumerate(current_questions):
    st.markdown(f"### Câu {i+1}: {q['question']}")
    
    widget_key = f"q_widget_{st.session_state.selected_set}_{i}"
    correct_answer = q["correct_answer"]
    user_choice = st.session_state.permanent_answers.get(i)

    # ---------- BEFORE SUBMIT (ACTIVE QUIZ) ----------
    if not st.session_state.submitted:
        st.radio(
            "Chọn đáp án:",
            q["options"],
            index=None,
            key=widget_key,
            on_change=record_answer,
            args=(i, widget_key),
            label_visibility="collapsed"
        )

    # ---------- AFTER SUBMIT (REVIEW MODE) ----------
    else:
        # We loop through ALL options so they are all visible
        for opt in q["options"]:
            if opt == correct_answer:
                # Logic: Correct answer is always GREEN
                st.success(f"✅ **{opt}** (Đáp án đúng)")
            elif opt == user_choice and user_choice != correct_answer:
                # Logic: If user picked this and it's wrong, it's RED
                st.error(f"❌ **{opt}** (Lựa chọn của bạn)")
            else:
                # Logic: All other choices stay visible as neutral items
                st.write(f"▫️ {opt}")
    
    st.divider()

# ================= SUBMIT / RESULTS ====================
if not st.session_state.submitted:
    if st.button("📊 Nộp bài", use_container_width=True):
        st.session_state.submitted = True
        st.rerun()

else:
    # Calculation
    correct_count = sum(1 for i, q in enumerate(current_questions) 
                        if st.session_state.permanent_answers.get(i) == q["correct_answer"])
    score_pct = round((correct_count / len(current_questions)) * 100, 1)
    
    st.subheader("📈 KẾT QUẢ")
    st.write(f"Số câu đúng: **{correct_count}/{len(current_questions)}** — Điểm: **{score_pct}%**")

    if score_pct >= PASS_THRESHOLD_PERCENT:
        st.success("🎉 **KẾT QUẢ: ĐẠT**")
    else:
        st.error("❌ **KẾT QUẢ: KHÔNG ĐẠT**")

    # This toggle automatically refreshes the question loop above
    st.session_state.review_mode = st.toggle("🔍 Bật Review Mode (Hiện tất cả đáp án)", value=True)

    if st.button("🔄 Làm bài thi mới", type="primary", use_container_width=True):
        # Clear all state to allow a fresh start
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
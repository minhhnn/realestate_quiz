import streamlit as st
import json
import random
import time

# ================== CONFIG & DATA ==================
def load_questions(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Không tìm thấy file {path}")
        return []

def split_into_sets(questions, n_sets):
    random.shuffle(questions)
    n_sets = max(1, n_sets)
    return [questions[i::n_sets] for i in range(n_sets)]

# CALLBACK: Saves the selection to a permanent dict immediately
def save_answer(q_idx, widget_key):
    st.session_state.permanent_answers[q_idx] = st.session_state[widget_key]

# ================= STREAMLIT SETUP =================
st.set_page_config(page_title="Quiz App", layout="centered")

# --- SIDEBAR: UI CUSTOMIZATION ---
st.sidebar.header("⚙️ Cấu hình bài thi")
ui_num_sets = st.sidebar.number_input("Số lượng bộ đề", min_value=1, max_value=100, value=3)
ui_time_limit = st.sidebar.slider("Thời gian làm bài (phút)", min_value=1, max_value=120, value=20)
ui_pass_threshold = st.sidebar.slider("Điểm đạt (%)", min_value=0, max_value=100, value=70)

if st.sidebar.button("🔄 Áp dụng & Làm mới bài thi"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

st.title("📘 Quiz Pháp Luật Bất Động Sản")

# ============== SESSION STATE ================
if "raw_questions" not in st.session_state:
    st.session_state.raw_questions = load_questions("questions.json")

if "question_sets" not in st.session_state:
    st.session_state.question_sets = split_into_sets(st.session_state.raw_questions, ui_num_sets)

if "selected_set" not in st.session_state:
    st.session_state.selected_set = 0

if "submitted" not in st.session_state:
    st.session_state.submitted = False

if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()

if "review_mode" not in st.session_state:
    st.session_state.review_mode = False

# This survives even when radio widgets are gone
if "permanent_answers" not in st.session_state:
    st.session_state.permanent_answers = {}

# ================= SET PICKER =================
current_set_idx = min(st.session_state.selected_set, len(st.session_state.question_sets) - 1)
set_choice = st.selectbox(
    "Chọn bộ câu hỏi:",
    options=[f"Bộ {i+1}" for i in range(len(st.session_state.question_sets))],
    index=current_set_idx,
    disabled=st.session_state.submitted
)
st.session_state.selected_set = int(set_choice.split()[-1]) - 1
selected_questions = st.session_state.question_sets[st.session_state.selected_set]

# ================= TIMER =====================
elapsed = time.time() - st.session_state.start_time
remaining = max(0, ui_time_limit * 60 - elapsed)
mins, secs = divmod(int(remaining), 60)

if not st.session_state.submitted:
    st.info(f"⏱️ Thời gian còn lại: **{mins:02d}:{secs:02d}** (Cần đạt: {ui_pass_threshold}%)")
    if remaining <= 0:
        st.warning("⏰ Hết giờ! Vui lòng nộp bài.")

# ================= QUESTIONS =================
for i, q in enumerate(selected_questions):
    st.markdown(f"**Câu {i+1}: {q['question']}**")
    
    widget_key = f"q_{st.session_state.selected_set}_{i}"
    correct_answer = q["correct_answer"]
    user_choice = st.session_state.permanent_answers.get(i)

    # --- BEFORE SUBMIT ---
    if not st.session_state.submitted:
        st.radio(
            "Chọn đáp án:", 
            options=q["options"], 
            index=None, 
            key=widget_key, 
            on_change=save_answer, 
            args=(i, widget_key),
            label_visibility="collapsed"
        )

    # --- REVIEW MODE (LOGIC) ---
    else:
        # Loop through ALL options to keep them visible
        for opt in q["options"]:
            if opt == correct_answer:
                # Correct answer always green
                st.success(f"✅ {opt}")
            elif opt == user_choice and user_choice != correct_answer:
                # User's wrong selection in red
                st.error(f"❌ {opt}")
            else:
                # All other neutral choices
                st.write(f"▫️ {opt}")

    st.divider()

# ================= SUBMIT / RESULTS ====================
if not st.session_state.submitted:
    if st.button("📊 Nộp bài", use_container_width=True):
        st.session_state.submitted = True
        st.rerun()

if st.session_state.submitted:
    score = sum(1 for i, q in enumerate(selected_questions) 
                if st.session_state.permanent_answers.get(i) == q["correct_answer"])
    
    percent = round(score / len(selected_questions) * 100, 2)
    passed = percent >= ui_pass_threshold

    st.subheader("📈 KẾT QUẢ BÀI THI")
    col1, col2 = st.columns(2)
    col1.metric("Số câu đúng", f"{score}/{len(selected_questions)}")
    col2.metric("Tỉ lệ", f"{percent}%")

    if passed:
        st.success(f"🎉 **KẾT QUẢ: ĐẠT** (Vượt ngưỡng {ui_pass_threshold}%)")
    else:
        st.error(f"❌ **KẾT QUẢ: KHÔNG ĐẠT** (Cần {ui_pass_threshold}%)")

    # This toggle triggers the review loop above
    st.session_state.review_mode = st.toggle("🔍 Bật Review Mode", value=True)
    
    if st.button("🔄 Làm bài mới", type="primary", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
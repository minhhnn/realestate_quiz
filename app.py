import streamlit as st
import json
import random
import time

# ================== CONFIG & UI SETTINGS ==================
def load_questions(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def split_into_sets(questions, n_sets):
    random.shuffle(questions)
    # Ensure we don't try to create more sets than questions
    n_sets = min(n_sets, len(questions))
    return [questions[i::n_sets] for i in range(n_sets)]

st.set_page_config(page_title="Quiz App", layout="centered")

# --- SIDEBAR CUSTOMIZATION ---
st.sidebar.header("⚙️ Cấu hình bài thi")

ui_num_sets = st.sidebar.number_input("Số lượng bộ đề", min_value=1, max_value=10, value=3)
ui_time_limit = st.sidebar.slider("Thời gian làm bài (phút)", min_value=1, max_value=120, value=20)
ui_pass_threshold = st.sidebar.slider("Điểm đạt (%)", min_value=0, max_value=100, value=70)

if st.sidebar.button("🔄 Làm mới & Áp dụng cài đặt"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# ================= STREAMLIT MAIN =================
st.title("📘 Quiz Pháp Luật Bất Động Sản")

try:
    questions = load_questions("questions.json")
except FileNotFoundError:
    st.error("Không tìm thấy file questions.json")
    st.stop()

# ============== SESSION STATE ================
if "question_sets" not in st.session_state:
    st.session_state.question_sets = split_into_sets(questions, ui_num_sets)

if "selected_set" not in st.session_state:
    st.session_state.selected_set = 0

if "submitted" not in st.session_state:
    st.session_state.submitted = False

if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()

if "review_mode" not in st.session_state:
    st.session_state.review_mode = False

# ================= SET PICKER =================
# Ensure index is within range if NUM_SETS was decreased
current_set_index = min(st.session_state.selected_set, len(st.session_state.question_sets) - 1)

set_choice = st.selectbox(
    "Chọn bộ câu hỏi:",
    options=[f"Bộ {i+1}" for i in range(len(st.session_state.question_sets))],
    index=current_set_index,
    disabled=st.session_state.submitted
)

st.session_state.selected_set = int(set_choice.split()[-1]) - 1
selected_questions = st.session_state.question_sets[st.session_state.selected_set]
total_questions = len(selected_questions)

# ================= TIMER =====================
elapsed = time.time() - st.session_state.start_time
remaining = max(0, ui_time_limit * 60 - elapsed)

minutes = int(remaining // 60)
seconds = int(remaining % 60)

if not st.session_state.submitted:
    st.info(f"⏱️ Thời gian còn lại: **{minutes:02d}:{seconds:02d}** (Yêu cầu đạt: {ui_pass_threshold}%)")

if remaining <= 0 and not st.session_state.submitted:
    st.warning("⏰ Hết giờ! Bài thi đã được nộp tự động.")
    st.session_state.submitted = True

# ================= QUESTIONS =================
for i, q in enumerate(selected_questions):
    st.markdown(f"**Câu {i+1}: {q['question']}**")

    key = f"q_{st.session_state.selected_set}_{i}"
    user_answer = st.session_state.get(key)
    correct_answer = q["correct_answer"]

    if not st.session_state.submitted:
        st.radio("Chọn đáp án:", options=q["options"], index=None, key=key, label_visibility="collapsed")
    else:
        if st.session_state.review_mode:
            for opt in q["options"]:
                if user_answer == correct_answer and opt == correct_answer:
                    st.success(f"✅ {opt}")
                elif user_answer and user_answer != correct_answer:
                    if opt == user_answer:
                        st.error(f"❌ {opt}")
                    elif opt == correct_answer:
                        st.success(f"✅ {opt}")
                    else:
                        st.write(f"▫️ {opt}")
                elif user_answer is None and opt == correct_answer:
                    st.success(f"✅ {opt}")
                else:
                    st.write(f"▫️ {opt}")
        else:
            if user_answer:
                st.info(f"📝 Bạn đã chọn: {user_answer}")
            else:
                st.info("📝 Bạn không chọn đáp án")
    st.divider()

# ================= SUBMIT / RESULTS ====================
if not st.session_state.submitted:
    if st.button("📊 Nộp bài", use_container_width=True):
        st.session_state.submitted = True
        st.rerun()

if st.session_state.submitted:
    score = sum(1 for i, q in enumerate(selected_questions) 
                if st.session_state.get(f"q_{st.session_state.selected_set}_{i}") == q["correct_answer"])
    
    percent = round(score / total_questions * 100, 2)
    passed = percent >= ui_pass_threshold

    st.subheader("📈 KẾT QUẢ BÀI THI")
    col1, col2 = st.columns(2)
    col1.metric("Đúng", f"{score}/{total_questions}")
    col2.metric("Điểm số", f"{percent}%")

    if passed:
        st.success(f"🎉 **KẾT QUẢ: ĐẠT** (Vượt ngưỡng {ui_pass_threshold}%)")
    else:
        st.error(f"❌ **KẾT QUẢ: KHÔNG ĐẠT** (Yêu cầu tối thiểu {ui_pass_threshold}%)")

    st.session_state.review_mode = st.toggle("🔍 Bật Review Mode", value=st.session_state.review_mode)
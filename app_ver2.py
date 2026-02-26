import streamlit as st
import json
import os
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
#import pyttsx3
import base64

# =====================
# CONFIG
# =====================
TOPIC_FOLDER = "Topics"
USER_FOLDER = "Users"
INIT_INTERVAL_HOURS = 4
INIT_EASE = 2.5

# =====================
# PAGE CONFIG
# =====================
st.set_page_config(
    page_title="English Vocab Learning",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================
# CUSTOM CSS
# =====================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem;
    }
    .word-card {
        background-color: #f0f2f6;
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stat-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem;
    }
    .success-msg {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
        padding: 0.5rem 1rem;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return data

img_main = get_base64_image("static/background.jpg")      # ảnh nền chính
img_side = get_base64_image("static/sidebar.jpg")         # ảnh nền sidebar

st.markdown(f"""
<style>
/* Nền chính + overlay mờ */
.stApp {{
    background-image: url("data:image/jpg;base64,{img_main}");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}}
.stApp::before {{
    content: "";
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background: rgba(0, 0, 0, 0.55);  /* tăng số này → tối hơn, giảm → sáng hơn */
    z-index: 0;
}}

/* Sidebar + overlay mờ */
[data-testid="stSidebar"] {{
    background-image: url("data:image/jpg;base64,{img_side}");
    background-size: cover;
    background-position: center;
}}
[data-testid="stSidebar"]::before {{
    content: "";
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background: rgba(0, 0, 0, 0.6);  /* tăng số này → tối hơn */
    z-index: 0;
}}

/* Màu chữ toàn bộ */
html, body, [class*="css"], p, h1, h2, h3, label, span {{
    color: #ffffff !important;   /* đổi màu chữ ở đây */
}}


</style>
""", unsafe_allow_html=True)



# =====================
# UTILS
# =====================
def hours(h):
    return timedelta(hours=h)

def read_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =====================
# USER FUNCTIONS
# =====================
def create_user(user_name):
    return {
        "username": user_name,
        "words": {},           # Từ đã học xong ít nhất 1 lần → vào SRS
        "pending_words": {},   # Từ mới thêm, chưa học lần nào
        "stats": {
            "total_words": 0,
            "words_mastered": 0,
            "total_reviews": 0,
            "streak_days": 0,
            "last_study": None
        },
        "knew_words": {}
    }

def login_user(username, password):
    users = read_json("Users/total_users.json")
    if username in users and users[username] == password:
        user_file = os.path.join(USER_FOLDER, f"{username}.json")
        user_data = read_json(user_file)
        # Đảm bảo field pending_words tồn tại cho user cũ
        if "pending_words" not in user_data:
            user_data["pending_words"] = {}
            save_json(user_file, user_data)
        return True, user_data
    return False, None

def register_user(username, password):
    users = read_json("Users/total_users.json")
    if username in users:
        return False, "Tài khoản đã tồn tại"
    
    users[username] = password
    save_json("Users/total_users.json", users)
    
    user_data = create_user(username)
    user_file = os.path.join(USER_FOLDER, f"{username}.json")
    save_json(user_file, user_data)
    
    return True, "Đăng ký thành công!"

def reload_user_data(username):
    """Load data từ file json"""
    user_file = os.path.join(USER_FOLDER, f"{username}.json")
    user_data = read_json(user_file)
    st.session_state.user_data = user_data
    return user_data

# =====================
# WORD FUNCTIONS
# =====================
def add_word_to_pending(word_id, vocab, user_data, username):
    """
    Thêm từ vào hàng chờ (pending_words).
    Chưa tính stats, chưa có SRS interval.
    Chỉ khi học xong mới chuyển sang words chính thức.
    """
    if word_id not in user_data["words"] and word_id not in user_data["pending_words"]:
        user_data["pending_words"][word_id] = {
            "word": vocab[word_id]["word"],
            "pos": vocab[word_id].get("pos", ""),
            "meaning": vocab[word_id].get("meaning", ""),
            "example": vocab[word_id].get("example", ""),
            "example_meaning": vocab[word_id].get("example_meaning", ""),
        }
        user_file = os.path.join(USER_FOLDER, f"{username}.json")
        save_json(user_file, user_data)

def promote_pending_to_words(word_id, user_data, username):
    """
    Sau khi học xong 1 từ pending → chuyển sang words (SRS) và tính stats.
    """
    if word_id not in user_data["pending_words"]:
        return
    if word_id in user_data["words"]:
        # Đã tồn tại rồi, chỉ xoá pending
        del user_data["pending_words"][word_id]
        user_file = os.path.join(USER_FOLDER, f"{username}.json")
        save_json(user_file, user_data)
        return

    pending = user_data["pending_words"][word_id]
    current_time = datetime.now()
    next_time = current_time + hours(INIT_INTERVAL_HOURS)

    user_data["words"][word_id] = {
        "word": pending["word"],
        "pos": pending.get("pos", ""),
        "meaning": pending.get("meaning", ""),
        "example": pending.get("example", ""),
        "example_meaning": pending.get("example_meaning", ""),
        "interval_hours": INIT_INTERVAL_HOURS,
        "ease_factor": INIT_EASE,
        "next_review": next_time.isoformat(),
        "review_count": 0
    }

    # Xoá khỏi pending
    del user_data["pending_words"][word_id]

    # Cập nhật stats
    user_data["stats"]["total_words"] += 1

    user_file = os.path.join(USER_FOLDER, f"{username}.json")
    save_json(user_file, user_data)

def get_due_words(user_data):
    due = []
    words = user_data.get("words", {})
    
    for word_id, state in words.items():
        next_review = datetime.fromisoformat(state["next_review"])
        if next_review <= datetime.now():
            due.append((word_id, next_review))
    
    due.sort(key=lambda x: x[1])
    return [w[0] for w in due]

def update_srs(word_id, remembered, user_data, username):
    state = user_data["words"][word_id]
    
    interval = state["interval_hours"]
    ease = state["ease_factor"]
    
    if remembered:
        interval *= ease
        ease += 0.1
    else:
        interval = max(2, interval / 2)
        ease = max(1.3, ease - 0.2)
    
    state["interval_hours"] = interval
    state["ease_factor"] = ease
    state["next_review"] = (datetime.now() + hours(interval)).isoformat()
    state["review_count"] += 1
    
    user_data["stats"]["total_reviews"] += 1
    if remembered and state["review_count"] >= 5:
        user_data["stats"]["words_mastered"] = sum(
            1 for w in user_data["words"].values() if w["review_count"] >= 5
        )
    
    user_file = os.path.join(USER_FOLDER, f"{username}.json")
    save_json(user_file, user_data)

def add_knew_word_to_user(word_id, vocab, user_data, username):
    if word_id not in user_data["knew_words"]:
        user_data["knew_words"][word_id] = {
            "word": vocab[word_id]["word"],
            "pos": vocab[word_id].get("pos", ""),
            "meaning": vocab[word_id].get("meaning", ""),
            "example": vocab[word_id].get("example", ""),
            "example_meaning": vocab[word_id].get("example_meaning", "")
        }
        # Nếu từ này đang trong pending thì xoá luôn
        if word_id in user_data.get("pending_words", {}):
            del user_data["pending_words"][word_id]

        user_file = os.path.join(USER_FOLDER, f"{username}.json")
        save_json(user_file, user_data)

#def play_sound(text):
#    engine = pyttsx3.init()
#    engine.setProperty('rate', 120)
#    engine.say(text)
#    engine.runAndWait()

from gtts import gTTS
import io

def play_sound(text):
    tts = gTTS(text=text, lang='en')
    audio_bytes = io.BytesIO()
    tts.write_to_fp(audio_bytes)
    audio_bytes.seek(0)
    st.audio(audio_bytes, format="audio/mp3")

# =====================
# PAGES
# =====================

def login_page():
    st.markdown('<p class="main-header">📚 English Vocabulary Learning</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["🔐 Đăng Nhập", "📝 Đăng Ký"])
        
        with tab1:
            st.subheader("Đăng Nhập")
            username = st.text_input("Tài khoản", key="login_username")
            password = st.text_input("Mật khẩu", type="password", key="login_password")
            
            if st.button("Đăng Nhập", key="login_btn"):
                if username and password:
                    success, user_data = login_user(username, password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.user_data = user_data
                        st.success("Đăng nhập thành công!")
                        st.rerun()
                    else:
                        st.error("Tài khoản hoặc mật khẩu không đúng!")
                else:
                    st.warning("Vui lòng nhập đầy đủ thông tin!")
        
        with tab2:
            st.subheader("Đăng Ký Tài Khoản Mới")
            new_username = st.text_input("Tài khoản mới", key="reg_username")
            new_password = st.text_input("Mật khẩu", type="password", key="reg_password")
            confirm_password = st.text_input("Xác nhận mật khẩu", type="password", key="reg_confirm")
            
            if st.button("Đăng Ký", key="register_btn"):
                if new_username and new_password and confirm_password:
                    if new_password != confirm_password:
                        st.error("Mật khẩu xác nhận không khớp!")
                    else:
                        success, message = register_user(new_username, new_password)
                        if success:
                            st.success(message)
                            st.info("Vui lòng chuyển sang tab Đăng Nhập!")
                        else:
                            st.error(message)
                else:
                    st.warning("Vui lòng nhập đầy đủ thông tin!")

def dashboard_page():
    st.markdown(f'<p class="main-header">👋 Xin chào, {st.session_state.username}!</p>', unsafe_allow_html=True)
    
    user_data = st.session_state.user_data
    stats = user_data.get("stats", {})
    pending_count = len(user_data.get("pending_words", {}))
    
    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stat-box">
            <h2>{stats.get('total_words', 0)}</h2>
            <p>Từ đã học</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-box">
            <h2>{pending_count}</h2>
            <p>Từ chờ học</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        due_count = len(get_due_words(user_data))
        st.markdown(f"""
        <div class="stat-box">
            <h2>{due_count}</h2>
            <p>Từ cần ôn</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="stat-box">
            <h2>{stats.get('total_reviews', 0)}</h2>
            <p>Lượt ôn tập</p>
        </div>
        """, unsafe_allow_html=True)

    if pending_count > 0:
        st.warning(f"📌 Bạn còn **{pending_count}** từ chưa học. Vào **🎓 Học từ vựng** để học nhé!")
    
    st.markdown("---")
    
    # Progress Chart
    if user_data.get("words"):
        st.subheader("📊 Tiến Độ Học Tập")
        
        review_counts = [w["review_count"] for w in user_data["words"].values()]
        df = pd.DataFrame({
            'Số lần ôn': review_counts
        })
        
        fig = px.histogram(df, x='Số lần ôn', nbins=10,
                          title='Phân bố số lần ôn tập',
                          labels={'Số lần ôn': 'Số lần ôn tập ', 'count': 'Số từ'})
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='white'
        )
        st.plotly_chart(fig, use_container_width=True)

def add_words_page():
    st.title("➕ Thêm Từ Mới")
    
    if not os.path.exists(TOPIC_FOLDER):
        os.makedirs(TOPIC_FOLDER)
    
    files = [f for f in os.listdir(TOPIC_FOLDER) if f.endswith('.json')]
    
    if not files:
        st.warning("⚠️ Chưa có topic nào. Vui lòng thêm file JSON vào thư mục Topics/")
        st.info("📝 Format file JSON:\n```json\n{\n  \"word_1\": {\n    \"word\": \"hello\",\n    \"pos\": \"(n)\",\n    \"meaning\": \"xin chào\",\n    \"example\": \"Hello, how are you?\",\n    \"example_meaning\": \"Xin chào, bạn khỏe không?\"\n  }\n}\n```")
        return
    
    selected_topic = st.selectbox(
        "📚 Chọn Topic", 
        files, 
        on_change=lambda: st.session_state.update({"show_words": False})
    )

    if "show_words" not in st.session_state:
        st.session_state.show_words = False

    if st.button("🔍 Xem từ vựng trong topic này"):
        st.session_state.show_words = True

    if st.session_state.show_words:
        topic_path = os.path.join(TOPIC_FOLDER, selected_topic)
        topic_data = read_json(topic_path)
        
        user_data = st.session_state.user_data
        
        new_words = {}
        for word_id, info in topic_data.items():
            if (word_id not in user_data["words"]
                    and word_id not in user_data.get("knew_words", {})
                    and word_id not in user_data.get("pending_words", {})):
                new_words[word_id] = info

        # Từ đang chờ học (đã thêm nhưng chưa học)
        pending_in_topic = {
            wid: info for wid, info in topic_data.items()
            if wid in user_data.get("pending_words", {})
        }

        if pending_in_topic:
            st.info(f"⏳ Có **{len(pending_in_topic)}** từ bạn đã thêm nhưng chưa học xong. Vào **🎓 Học từ vựng** để hoàn thành!")

        if not new_words:
            st.success("🎉 Bạn đã thêm hết từ vựng trong topic này!")
        else:
            st.info(f"📝 Có {len(new_words)} từ mới chưa thêm trong topic này")
            
            for i, (word_id, info) in enumerate(new_words.items()):
                with st.expander(f"**{info['word']}** {info['pos']}", expanded=False):
                    
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"Nghĩa: {info['meaning']}")
                    with col2:
                        if st.button("🔊", key=f"sound_word_{word_id}"):
                            play_sound(info['word'])
                    
                    example = info.get('example', '')
                    example_meaning = info.get('example_meaning', '')
                    
                    if example:
                        col3, col4 = st.columns([4, 1])
                        with col3:
                            st.write(f"**Ví dụ:** {example}")
                        with col4:
                            if st.button("🔊", key=f"sound_example_{word_id}"):
                                play_sound(example)
                    
                    if example_meaning:
                        st.write(f"**Nghĩa ví dụ:** {example_meaning}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Đã biết", key=f"know_{i}"):
                            add_knew_word_to_user(word_id, topic_data, user_data, st.session_state.username)
                            st.session_state.user_data = read_json(
                                os.path.join(USER_FOLDER, f"{st.session_state.username}.json")
                            )
                            st.success(f"Đã thêm '{info['word']}' vào danh sách từ đã biết!")
                            st.rerun()
                    with col2:
                        if st.button("➕ Thêm vào học", key=f"add_{i}"):
                            add_word_to_pending(word_id, topic_data, user_data, st.session_state.username)
                            st.session_state.user_data = read_json(
                                os.path.join(USER_FOLDER, f"{st.session_state.username}.json")
                            )
                            st.success(f"Đã thêm '{info['word']}' vào hàng chờ! Vào 🎓 Học từ vựng để học.")
                            st.rerun()

def learn_words_page():
    import random
    st.title("🎓 Học từ vựng mới")

    user_data = st.session_state.user_data
    pending_words = user_data.get("pending_words", {})

    if not pending_words:
        learned_count = len(user_data.get("words", {}))
        if learned_count > 0:
            st.success("🎉 Không có từ mới nào chờ học! Bạn đã học hết rồi.")
            st.info("💡 Hãy thêm từ mới ở mục **➕ Thêm từ mới**.")
        else:
            st.warning("Bạn chưa thêm từ nào vào danh sách học. Hãy vào '➕ Thêm từ mới' trước!")
        return

    word_list = list(pending_words.items())  # [(word_id, word_data), ...]
    st.info(f"📚 Bạn có **{len(word_list)}** từ mới cần học")

    # --- Khởi tạo session state ---
    if "learn_index" not in st.session_state:
        st.session_state.learn_index = 0
        st.session_state.learn_mode = None
        st.session_state.learn_answered = False
        st.session_state.learn_correct = None
        st.session_state.learn_choices = []
        st.session_state.learn_fill_input = ""

    # Nếu học xong tất cả
    if st.session_state.learn_index >= len(word_list):
        st.success("🎊 Bạn đã hoàn thành toàn bộ từ mới trong phiên này!")
        st.balloons()
        if st.button("🔄 Học lại từ đầu"):
            for k in ["learn_index", "learn_mode", "learn_answered", "learn_correct", "learn_choices", "learn_fill_input"]:
                st.session_state.pop(k, None)
            st.rerun()
        return

    word_id, word_data = word_list[st.session_state.learn_index]

    # --- Progress ---
    progress = (st.session_state.learn_index + 1) / len(word_list)
    st.progress(progress)
    st.write(f"Từ {st.session_state.learn_index + 1}/{len(word_list)}")

    # --- Chọn chế độ ngẫu nhiên nếu chưa có ---
    if st.session_state.learn_mode is None:
        # Nếu chưa có đủ từ khác để làm trắc nghiệm thì dùng fill
        if len(word_list) >= 4:
            st.session_state.learn_mode = random.choice(["mc", "fill"])
        else:
            st.session_state.learn_mode = "fill"

        if st.session_state.learn_mode == "mc":
            other_words = [w for wid, w in word_list if wid != word_id]
            wrong_choices = random.sample(other_words, min(3, len(other_words)))
            choices = [(word_data["meaning"], True)] + [(w["meaning"], False) for w in wrong_choices]
            random.shuffle(choices)
            st.session_state.learn_choices = choices

    mode = st.session_state.learn_mode

    # ==================
    # DẠNG 1: Trắc nghiệm (MC)
    # ==================
    if mode == "mc":
        st.markdown(f"""
        <div class="word-card">
            <h2 style="text-align:center; color:#1f77b4;">"{word_data['word']}" <span style="color:#888; font-size:1rem;">{word_data.get('pos','')}</span></h2>
            <p style="text-align:center; color:#555;">Chọn nghĩa đúng của từ trên:</p>
        </div>
        """, unsafe_allow_html=True)

        for i, (choice_text, is_correct) in enumerate(st.session_state.learn_choices):
            if not st.session_state.learn_answered:
                if st.button(choice_text, key=f"mc_{i}"):
                    st.session_state.learn_answered = True
                    st.session_state.learn_correct = is_correct
                    st.rerun()
            else:
                if is_correct:
                    st.success(f"✅ {choice_text}")
                else:
                    st.button(choice_text, key=f"mc_dis_{i}", disabled=True)

    # ==================
    # DẠNG 2: Điền vào chỗ trống
    # ==================
    elif mode == "fill":
        word = word_data["word"]

        def mask_word(w):
            if len(w) <= 2:
                return w[0] + "_" * (len(w) - 1)
            masked = list("_" * len(w))
            masked[0] = w[0]
            masked[-1] = w[-1]
            for i in range(2, len(w) - 1, 3):
                masked[i] = w[i]
            return "".join(masked)

        hint = mask_word(word)

        st.markdown(f"""
        <div class="word-card">
            <p style="text-align:center; color:#555; font-size:1.1rem;">Nghĩa: <b>{word_data['meaning']}</b></p>
            <p style="text-align:center; color:#555;">Ví dụ: <i>{word_data.get('example','')}</i></p>
            <h2 style="text-align:center; letter-spacing:6px; color:#1f77b4;">{hint}</h2>
            <p style="text-align:center; color:#aaa;">({len(word)} chữ cái)</p>
        </div>
        """, unsafe_allow_html=True)

        if not st.session_state.learn_answered:
            user_input = st.text_input("Nhập từ tiếng Anh:", key=f"fill_{st.session_state.learn_index}")
            if st.button("✔️ Kiểm tra"):
                st.session_state.learn_answered = True
                st.session_state.learn_correct = user_input.strip().lower() == word.lower()
                st.session_state.learn_fill_input = user_input.strip()
                st.rerun()

    # ==================
    # Hiện kết quả & nút tiếp
    # ==================
    if st.session_state.learn_answered:
        if st.session_state.learn_correct:
            st.success("🎉 Chính xác!")
        else:
            if mode == "fill":
                st.error(f"❌ Sai rồi! Đáp án đúng là: **{word_data['word']}**")
            else:
                st.error(f"❌ Sai rồi! Nghĩa đúng là: **{word_data['meaning']}**")

        st.markdown(f"**Ví dụ:** {word_data.get('example','')}")
        st.markdown(f"*{word_data.get('example_meaning','')}*")

        if st.button("➡️ Từ tiếp theo"):
            # ✅ Chỉ ở đây mới promote từ pending → words (SRS) và tính stats
            promote_pending_to_words(word_id, user_data, st.session_state.username)
            st.session_state.user_data = read_json(
                os.path.join(USER_FOLDER, f"{st.session_state.username}.json")
            )

            st.session_state.learn_index += 1
            st.session_state.learn_mode = None
            st.session_state.learn_answered = False
            st.session_state.learn_correct = None
            st.session_state.learn_choices = []
            st.session_state.learn_fill_input = ""
            st.rerun()

def review_page():
    st.title("📝 Ôn Tập Từ Vựng")
    
    user_data = st.session_state.user_data
    due_words = get_due_words(user_data)
    len_due = len(due_words)
    
    if not due_words:
        st.success("🎉 Tuyệt vời! Bạn chưa có từ nào cần ôn tập.")
        st.info("💡 Hãy quay lại sau hoặc thêm từ mới để học!")
        # Tạo bảng đẹp từ words
        display_data = []
        for word_id, w in user_data["words"].items():
            next_review = datetime.fromisoformat(w["next_review"])
            display_data.append({
                "Từ": w["word"],
                "Nghĩa": w["meaning"],
                "Ví dụ": w.get("example", ""),
                "Nghĩa ví dụ": w.get("example_meaning", ""),
                "Ôn tiếp theo": next_review.strftime("%d/%m/%Y %H:%M")
            })

        df_display = pd.DataFrame(display_data)
        rows_html = ""
        for row in display_data:
            rows_html += (
                "<tr style='border-bottom: 1px solid rgba(255,255,255,0.1);'>"
                f"<td style='padding:10px;'>{row['Từ']}</td>"
                f"<td style='padding:10px;'>{row['Nghĩa']}</td>"
                f"<td style='padding:10px;'>{row['Ví dụ']}</td>"
                f"<td style='padding:10px;'>{row['Nghĩa ví dụ']}</td>"
                f"<td style='padding:10px;'>{row['Ôn tiếp theo']}</td>"
                "</tr>"
            )

        table_html = (
            "<table style='width:100%; border-collapse:collapse; background:transparent; color:white;'>"
            "<thead><tr style='border-bottom: 1px solid rgba(255,255,255,0.3);'>"
            "<th style='padding:10px; text-align:left;'>Từ</th>"
            "<th style='padding:10px; text-align:left;'>Nghĩa</th>"
            "<th style='padding:10px; text-align:left;'>Ví dụ</th>"
            "<th style='padding:10px; text-align:left;'>Nghĩa ví dụ</th>"
            "<th style='padding:10px; text-align:left;'>Ôn tiếp theo</th>"
            "</tr></thead>"
            f"<tbody>{rows_html}</tbody></table>"
        )
        st.markdown(table_html, unsafe_allow_html=True)
        return
    
    st.info(f"📚 Bạn có **{len_due}** từ cần ôn tập")
    
    if "review_index" not in st.session_state:
        st.session_state.review_index = 0
        st.session_state.show_answer = False
    
    if st.session_state.review_index >= len(due_words):
        st.success("🎊 Chúc mừng! Bạn đã hoàn thành phiên ôn tập!")
        if st.button("🔄 Bắt đầu lại"):
            st.session_state.review_index = 0
            st.session_state.show_answer = False
            st.rerun()
        return
    
    word_id = due_words[st.session_state.review_index]
    word_data = user_data["words"][word_id]
    
    progress = (st.session_state.review_index + 1) / len(due_words)
    st.progress(progress)
    st.write(f"Từ {st.session_state.review_index + 1}/{len(due_words)}")
    
    st.markdown(f"""
    <div class="word-card">
        <h1 style="color: #1f77b4; text-align: center;">{word_data['word']}</h1>
        <p style="text-align: center; color: #666;">Số lần ôn: {word_data['review_count']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.show_answer:
        if st.button("👁️ Xem đáp án", use_container_width=True):
            st.session_state.show_answer = True
            st.rerun()
    else:
        st.markdown(f"""
        <div class="word-card">
            <h3>📖 Nghĩa:</h3>
            <p style="font-size: 1.2rem;">{word_data['meaning']}</p>
            <h3>💬 Ví dụ:</h3>
            <p style="font-style: italic;">{word_data['example']}</p>
            <p>{word_data['example_meaning']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### Bạn có nhớ từ này không?")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Nhớ rồi", use_container_width=True, type="primary"):
                update_srs(word_id, True, user_data, st.session_state.username)
                st.session_state.user_data = read_json(
                    os.path.join(USER_FOLDER, f"{st.session_state.username}.json")
                )
                st.session_state.review_index += 1
                st.session_state.show_answer = False
                st.rerun()
        
        with col2:
            if st.button("❌ Chưa nhớ", use_container_width=True):
                update_srs(word_id, False, user_data, st.session_state.username)
                st.session_state.user_data = read_json(
                    os.path.join(USER_FOLDER, f"{st.session_state.username}.json")
                )
                st.session_state.review_index += 1
                st.session_state.show_answer = False
                st.rerun()

# =====================
# MAIN APP
# =====================
def main():
    os.makedirs(TOPIC_FOLDER, exist_ok=True)
    os.makedirs(USER_FOLDER, exist_ok=True)
    
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    
    if not st.session_state.logged_in:
        login_page()
    else:
        with st.sidebar:
            st.title("📚 Menu")
            st.markdown(f"**User:** {st.session_state.username}")
            st.markdown("---")
            
            page = st.radio(
                "Chọn chức năng:",
                ["🏠 Trang chủ", "➕ Thêm từ mới", "🎓 Học từ vựng", "📝 Ôn tập", "📊 Thống kê"],
                label_visibility="collapsed"
            )
            
            st.markdown("---")
            if st.button("🚪 Đăng xuất"):
                st.session_state.logged_in = False
                st.session_state.username = None
                st.session_state.user_data = None
                for k in ["review_index", "show_answer", "learn_index", "learn_mode",
                          "learn_answered", "learn_correct", "learn_choices", "learn_fill_input"]:
                    st.session_state.pop(k, None)
                st.rerun()
        
        if page == "🏠 Trang chủ":
            dashboard_page()
        elif page == "➕ Thêm từ mới":
            add_words_page()
        elif page == "🎓 Học từ vựng":
            learn_words_page()
        elif page == "📝 Ôn tập":
            review_page()
        elif page == "📊 Thống kê":
            dashboard_page()
        
        import time
        placeholder = st.empty()
        with placeholder.container():
            st.sidebar.write("---")
            countdown_placeholder = st.sidebar.empty()
            
        REFRESH_INTERVAL = 3

        for remaining in range(REFRESH_INTERVAL, 0, -1):
            countdown_placeholder.caption(f"🔄 Cập nhật sau: {remaining}s")
            time.sleep(1)
        
        reload_user_data(st.session_state.username)
        st.rerun()

if __name__ == "__main__":
    main()
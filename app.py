import streamlit as st
import time

# --- 1. 基础配置与样式 (北欧简约风) ---
st.set_page_config(page_title="CareLink", layout="centered")

st.markdown("""
    <style>
    /* 全局背景与字体 */
    .stApp { background-color: #FBFBFB; }
    h1, h2, h3 { color: #4A4A4A; font-family: 'Inter', sans-serif; font-weight: 300; }
    
    /* 圆形头像样式 */
    .avatar {
        width: 100px; height: 100px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        color: white; font-weight: bold; margin: 0 auto;
        transition: transform 0.3s; cursor: pointer;
    }
    .avatar-u1 { background-color: #93E1ED; } /* 浅青色 */
    .avatar-u2 { background-color: #E979C1; } /* 浅粉色 */
    .avatar:hover { transform: scale(1.05); }

    /* 任务卡片样式 */
    .task-card {
        background: white; border-radius: 15px; padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        border: 1px solid #F0F0F0; margin-bottom: 20px;
    }
    
    /* 状态标签 */
    .status-tag {
        background: #DDF8A3; border-radius: 20px; padding: 5px 15px;
        font-size: 0.8rem; color: #555; display: inline-block;
    }
    .want-tag {
        background: #F4CE79; border-radius: 20px; padding: 5px 15px;
        font-size: 0.8rem; color: #555; display: inline-block;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. 数据初始化 (模拟数据库) ---
if 'db' not in st.session_state:
    st.session_state.db = {
        'tasks': [], # 格式: {"from": 1, "to": 2, "content": "喝水", "done": False}
        'mood': {1: "Energetic", 2: "Tired"},
        'want': {1: "Milk tea", 2: "Coffee"},
        'streak': 2,
        'reward_goal': 5,
        'reward_item': "Special Gift"
    }

# --- 3. 登录与配对逻辑 ---
if 'user_id' not in st.session_state:
    st.title("CareLink")
    col1, col2 = st.columns(2)
    with col1:
        user_input = st.number_input("输入你的号码", min_value=1, step=1)
    if st.button("进入空间"):
        st.session_state.user_id = user_input
        st.rerun()
    st.stop()

# 计算配对ID
my_id = st.session_state.user_id
partner_id = my_id + 1 if my_id % 2 != 0 else my_id - 1

# 当前查看的视角 (默认是自己)
if 'view_id' not in st.session_state:
    st.session_state.view_id = my_id

# --- 4. 页面头部：头像切换与连接感 ---
st.write(f"### Welcome to Room {min(my_id, partner_id)}-{max(my_id, partner_id)}")

col_u1, col_mid, col_u2 = st.columns([2, 3, 2])

with col_u1:
    u1_class = "avatar-u1" if st.session_state.view_id == 1 else "avatar-u1" # 这里可以根据ID改颜色
    st.markdown(f'<div class="avatar avatar-u1">User {min(my_id, partner_id)}</div>', unsafe_allow_html=True)
    if st.button(f"切换到 User {min(my_id, partner_id)} 视角", key="btn_u1"):
        st.session_state.view_id = min(my_id, partner_id)
        st.rerun()

with col_mid:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center;'>❤️ {st.session_state.db['streak']} days</p>", unsafe_allow_html=True)
    st.progress(st.session_state.db['streak'] / st.session_state.db['reward_goal'])
    st.markdown("<p style='text-align:center; font-size: 0.8rem;'>how many days both doing task</p>", unsafe_allow_html=True)

with col_u2:
    st.markdown(f'<div class="avatar avatar-u2">User {max(my_id, partner_id)}</div>', unsafe_allow_html=True)
    if st.button(f"切换到 User {max(my_id, partner_id)} 视角", key="btn_u2"):
        st.session_state.view_id = max(my_id, partner_id)
        st.rerun()

st.divider()

# --- 5. 个人状态区 (Mood & Want) ---
curr_view = st.session_state.view_id
st.write(f"#### User {curr_view}'s Status")

col_m, col_w = st.columns(2)
with col_m:
    st.write("**Mood**")
    if curr_view == my_id: # 只有自己的视角可以改
        new_mood = st.selectbox("How are you?", ["Energetic", "Tired", "Sad", "Happy"], 
                               index=["Energetic", "Tired", "Sad", "Happy"].index(st.session_state.db['mood'].get(curr_view, "Happy")))
        st.session_state.db['mood'][curr_view] = new_mood
    st.markdown(f'<div class="status-tag">{st.session_state.db["mood"].get(curr_view)}</div>', unsafe_allow_html=True)

with col_w:
    st.write("**Want to have**")
    if curr_view == my_id:
        new_want = st.text_input("What do you want?", value=st.session_state.db['want'].get(curr_view))
        st.session_state.db['want'][curr_view] = new_want
    st.markdown(f'<div class="want-tag">{st.session_state.db["want"].get(curr_view)}</div>', unsafe_allow_html=True)

# --- 6. 任务系统 (核心逻辑) ---
st.divider()

# A. Today's Task (我收到的任务)
st.write("### 📋 Today's Tasks")
my_received_tasks = [t for t in st.session_state.db['tasks'] if t['to'] == curr_view]

with st.container():
    st.markdown('<div class="task-card">', unsafe_allow_html=True)
    if not my_received_tasks:
        st.info(f"No tasks received for User {curr_view} today.")
    else:
        for i, task in enumerate(my_received_tasks):
            # 只有在自己的视角下才能勾选完成
            if curr_view == my_id:
                done = st.checkbox(task['content'], value=task['done'], key=f"recv_{i}")
                task['done'] = done
            else:
                st.write(f"{'✅' if task['done'] else '⏳'} {task['content']}")
    st.markdown('</div>', unsafe_allow_html=True)

# B. Tasks for linked user (我发出的任务)
st.write(f"### ✉️ Tasks for User {partner_id if curr_view == my_id else my_id}")
if curr_view == my_id:
    with st.expander("➕ Add a task for your partner"):
        new_t = st.text_input("Task description")
        if st.button("Send Task"):
            st.session_state.db['tasks'].append({"from": my_id, "to": partner_id, "content": new_t, "done": False})
            st.success("Task sent!")
            time.sleep(1)
            st.rerun()
else:
    st.info("You are viewing your partner's sent tasks.")

# --- 7. 奖励机制 (Reward) ---
st.divider()
st.write("### 🎁 Reward Progress")
col_r1, col_r2 = st.columns([3, 1])

with col_r1:
    days = st.session_state.db['reward_goal']
    gift = st.session_state.db['reward_item']
    st.write(f"If tasks are completed for **{days}** days, gain a gift of **{gift}**")

if st.session_state.db['streak'] >= st.session_state.db['reward_goal']:
    st.balloons()
    st.success("🎉 Reward Milestone Reached!")

# 底部退出
if st.sidebar.button("Log out"):
    del st.session_state.user_id
    st.rerun()

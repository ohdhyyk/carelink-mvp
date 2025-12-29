import streamlit as st
import random
import time

# --- 1. 页面配置与北欧风 CSS ---
st.set_page_config(page_title="CareLink - Nordic", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    
    /* 模拟图片中的心跳连接线 */
    .connection-container {
        display: flex; align-items: center; justify-content: center; margin-top: 20px;
    }
    .heart-beat {
        width: 150px; height: 60px;
        background: url('https://cdn0.iconfinder.com/data/icons/medical-2-10/512/ecg_pulse-512.png') no-repeat center;
        background-size: contain; margin: 0 20px;
    }
    .heart-center {
        position: absolute; border: 2px solid #E979C1; border-radius: 50%;
        width: 60px; height: 60px; background: white;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        font-size: 0.7rem; color: #4A4A4A;
    }

    /* 头像样式 */
    .avatar-large {
        width: 140px; height: 140px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.2rem; font-weight: 300; color: #333;
    }
    .u1-bg { background-color: #93E1ED; }
    .u2-bg { background-color: #E979C1; }

    /* 进度条样式 */
    .streak-bar {
        display: flex; align-items: center; justify-content: center; gap: 10px; margin: 30px 0;
    }
    .dot { height: 12px; width: 12px; background-color: #4B8E2E; border-radius: 50%; display: inline-block; }
    .line { height: 3px; width: 60px; background-color: #4B8E2E; }
    
    /* 输入框样式微调 */
    .stTextInput>div>div>input { background-color: #F4CE79 !important; border-radius: 20px !important; border:none !important; }
    .mood-box { background-color: #DDF8A3 !important; border-radius: 20px !important; padding: 5px 15px; }

    /* 卡片容器 */
    .task-container {
        border: 1px solid #EEEEEE; border-radius: 15px; padding: 30px; margin: 20px 0; min-height: 150px;
        text-align: center; color: #AAAAAA; font-size: 0.9rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. 模拟全局数据库 (在同一个 Session 内通过 Room ID 区分) ---
if 'global_rooms' not in st.session_state:
    st.session_state.global_rooms = {}

def get_room_data(room_key):
    if room_key not in st.session_state.global_rooms:
        st.session_state.global_rooms[room_key] = {
            'tasks_to_u1': [], 'tasks_to_u2': [],
            'mood': {1: "energetic", 2: "tired"},
            'want': {1: "milktea", 2: "coffee"},
            'streak': 2, 'reward_days': 5, 'reward_gift': "a special dinner"
        }
    return st.session_state.global_rooms[room_key]

# --- 3. 登录界面 ---
if 'user_id' not in st.session_state:
    st.title("CareLink")
    tab1, tab2 = st.tabs(["我有账号", "生成新 Room"])
    
    with tab1:
        u_id = st.number_input("输入你的 ID (1, 2, 3...)", step=1, min_value=1)
        if st.button("进入房间"):
            st.session_state.user_id = u_id
            st.rerun()
            
    with tab2:
        if st.button("✨ 生成新的一对号码"):
            new_u1 = random.randint(1000, 9000)
            new_u2 = new_u1 + 1
            st.success(f"已为您生成！你的号码是 **{new_u1}**，对方的号码是 **{new_u2}**。请记好！")
    st.stop()

# --- 4. 逻辑处理：计算配对与获取数据 ---
my_id = st.session_state.user_id
is_u1 = True if my_id % 2 != 0 else False
partner_id = my_id + 1 if is_u1 else my_id - 1
room_key = f"room_{min(my_id, partner_id)}_{max(my_id, partner_id)}"
data = get_room_data(room_key)

# 视角控制
if 'view_id' not in st.session_state:
    st.session_state.view_id = my_id

# --- 5. UI 设计还原 ---

# 头部：头像与心跳
st.markdown(f"""
    <div class="connection-container">
        <div class="avatar-large u1-bg">User {min(my_id, partner_id)}</div>
        <div class="heart-beat"></div>
        <div class="heart-center">
            <div style="color:#E979C1; font-size:1.2rem;">❤</div>
            <div>{data['streak']} days</div>
        </div>
        <div class="avatar-large u2-bg">User {max(my_id, partner_id)}</div>
    </div>
    <p style='text-align:center; font-size:0.8rem; color:#888;'>how many days both doing task</p>
""", unsafe_allow_html=True)

# 切换按钮 (放在头像下方)
c1, c2, c3 = st.columns([1,2,1])
with c1:
    if st.button(f"Switch to U{min(my_id, partner_id)}", use_container_width=True):
        st.session_state.view_id = min(my_id, partner_id)
with c3:
    if st.button(f"Switch to U{max(my_id, partner_id)}", use_container_width=True):
        st.session_state.view_id = max(my_id, partner_id)

# 中间进度条
st.markdown(f"""
    <div class="streak-bar">
        <div class="dot"></div><div class="line"></div>
        <div class="dot"></div><div class="line" style="background-color:#EEEEEE;"></div>
        <div class="dot" style="background-color:#EEEEEE;"></div><div class="line" style="background-color:#EEEEEE;"></div>
        <div class="dot" style="background-color:#EEEEEE;"></div>
        <span style="font-size:30px; margin-left:10px;">🎁</span>
    </div>
""", unsafe_allow_html=True)

# Mood & Want to have 区块
curr_view = st.session_state.view_id
col_left, col_right = st.columns(2)

with col_left:
    st.write("**mood**")
    if curr_view == my_id:
        data['mood'][1 if is_u1 else 2] = st.text_input("How are you?", value=data['mood'][1 if is_u1 else 2], key="mood_in", label_visibility="collapsed")
    else:
        st.markdown(f"<div class='mood-box'>{data['mood'][2 if is_u1 else 1]}</div>", unsafe_allow_html=True)

with col_right:
    st.write("**want to have**")
    if curr_view == my_id:
        data['want'][1 if is_u1 else 2] = st.text_input("Anything you want?", value=data['want'][1 if is_u1 else 2], key="want_in", label_visibility="collapsed")
    else:
        st.markdown(f"<div style='background-color:#F4CE79; border-radius:20px; padding:5px 15px;'>{data['want'][2 if is_u1 else 1]}</div>", unsafe_allow_html=True)

# 任务区块
st.write("### Today's task:")
my_received_list = data['tasks_to_u1'] if is_u1 else data['tasks_to_u2']

with st.container():
    if not my_received_list:
        st.markdown('<div class="task-container">No tasks received from your linked user today.</div>', unsafe_allow_html=True)
    else:
        for idx, task in enumerate(my_received_list):
            # 只有在自己视角才能勾选
            if curr_view == my_id:
                task['done'] = st.checkbox(task['content'], value=task['done'], key=f"t_{idx}")
            else:
                st.write(f"{'✅' if task['done'] else '⭕'} {task['content']}")

st.write("### Tasks for linked user")
if curr_view == my_id:
    new_task = st.text_input("Send a task to your partner...", key="send_task")
    if st.button("Send"):
        target_list = data['tasks_to_u2'] if is_u1 else data['tasks_to_u1']
        target_list.append({"content": new_task, "done": False})
        st.rerun()
else:
    st.markdown('<div class="task-container">You have already sent tasks to your linked user today. Check back tomorrow!</div>', unsafe_allow_html=True)

# 奖励设定
st.write("### Choose a reward for linked user")
r_col1, r_col2, r_col3, r_col4 = st.columns([2,1,2,2])
with r_col1: st.write("If he/she complete task for")
with r_col2: r_days = st.text_input("days", value=str(data['reward_days']), label_visibility="collapsed")
with r_col3: st.write("days, gain a gift of")
with r_col4: r_gift = st.text_input("gift", value=data['reward_gift'], label_visibility="collapsed")

if st.button("Save Reward"):
    data['reward_days'] = int(r_days)
    data['reward_gift'] = r_gift
    st.success("Reward updated!")

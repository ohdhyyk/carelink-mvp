import streamlit as st
import time

# --- 1. 全局数据同步 (使用 cache_resource 确保数据跨用户共享) ---
@st.cache_resource
def get_db():
    return {}

db = get_db()

# --- 2. 页面样式 ---
st.set_page_config(page_title="CareLink", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; font-family: 'Inter', sans-serif; }
    .avatar-large { width: 100px; height: 100px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1rem; margin: 0 auto; }
    .u1-bg { background-color: #93E1ED; }
    .u2-bg { background-color: #E979C1; }
    .heart-center { border: 2px solid #E979C1; border-radius: 50%; width: 60px; height: 60px; margin: 0 auto; display: flex; flex-direction: column; align-items: center; justify-content: center; background: white; }
    .streak-container { display: flex; align-items: center; justify-content: center; gap: 8px; margin: 20px 0; }
    .dot { height: 12px; width: 12px; border-radius: 50%; }
    .line { height: 2px; width: 40px; }
    .status-box { border-radius: 20px; padding: 6px 18px; font-size: 0.9rem; display: inline-block; }
    .mood-color { background-color: #DDF8A3; }
    .want-color { background-color: #F4CE79; }
    .task-card { border: 1px solid #F5F5F5; border-radius: 15px; padding: 20px; margin: 10px 0; background: #fafafa; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 登录与房间初始化 ---
if 'my_id' not in st.session_state:
    st.title("CareLink Login")
    u_id = st.number_input("Your Number (1 or 2...)", min_value=1, step=1)
    if st.button("Enter Space"):
        st.session_state.my_id = u_id
        st.session_state.view_id = u_id # 默认视角是自己
        st.rerun()
    st.stop()

my_id = st.session_state.my_id
is_u1_identity = (my_id % 2 != 0)
partner_id = my_id + 1 if is_u1_identity else my_id - 1
room_key = f"room_{min(my_id, partner_id)}_{max(my_id, partner_id)}"

# 确保房间存在
if room_key not in db:
    db[room_key] = {
        'u1_streak': 0, 'u1_goal': 5, 'u1_gift': "Coffee", 'u1_tasks': [], 'u1_mood': "Energetic", 'u1_want': "Tea",
        'u2_streak': 0, 'u2_goal': 5, 'u2_gift': "Cake", 'u2_tasks': [], 'u2_mood': "Tired", 'u2_want': "Nap"
    }

room = db[room_key]

# --- 4. 头部切换 (切换视角) ---
u1_id, u2_id = min(my_id, partner_id), max(my_id, partner_id)
col_a, col_b, col_c = st.columns([2, 1, 2])

with col_a:
    st.markdown(f'<div class="avatar-large u1-bg">User {u1_id}</div>', unsafe_allow_html=True)
    if st.button(f"View U{u1_id}", key="v1"): st.session_state.view_id = u1_id; st.rerun()
with col_b:
    st.markdown(f'<div class="heart-center"><span style="color:#E979C1;">❤</span></div>', unsafe_allow_html=True)
with col_c:
    st.markdown(f'<div class="avatar-large u2-bg">User {u2_id}</div>', unsafe_allow_html=True)
    if st.button(f"View U{u2_id}", key="v2"): st.session_state.view_id = u2_id; st.rerun()

# --- 5. 动态进度条 ---
# 逻辑：看谁的页面，就显示谁的进度
view_id = st.session_state.view_id
prefix = "u1" if view_id == u1_id else "u2"

v_streak = room[f'{prefix}_streak']
v_goal = room[f'{prefix}_goal']
v_gift = room[f'{prefix}_gift']

# 绘制进度条
dots_html = ""
for i in range(v_goal):
    dot_color = "#4B8E2E" if i < v_streak else "#E0E0E0"
    dots_html += f'<div class="dot" style="background-color:{dot_color};"></div>'
    if i < v_goal - 1:
        line_color = "#4B8E2E" if i < v_streak - 1 else "#E0E0E0"
        dots_html += f'<div class="line" style="background-color:{line_color};"></div>'

st.markdown(f'<div class="streak-container">{dots_html}<span style="filter:{"grayscale(0)" if v_streak >= v_goal else "grayscale(1)"}">🎁</span></div>', unsafe_allow_html=True)
st.markdown(f"<p style='text-align:center; font-size:0.8rem;'>{v_streak}/{v_goal} days until: {v_gift}</p>", unsafe_allow_html=True)

# --- 6. Mood & Want (读写逻辑) ---
st.divider()
c1, c2 = st.columns(2)
with c1:
    st.write("**Mood**")
    if view_id == my_id:
        room[f'{prefix}_mood'] = st.text_input("Mood", value=room[f'{prefix}_mood'], label_visibility="collapsed", key="m_edit")
    st.markdown(f"<div class='status-box mood-color'>{room[f'{prefix}_mood']}</div>", unsafe_allow_html=True)
with c2:
    st.write("**Want**")
    if view_id == my_id:
        room[f'{prefix}_want'] = st.text_input("Want", value=room[f'{prefix}_want'], label_visibility="collapsed", key="w_edit")
    st.markdown(f"<div class='status-box want-color'>{room[f'{prefix}_want']}</div>", unsafe_allow_html=True)

# --- 7. 任务区块 (逻辑修复点) ---
st.write("### Today's Task")
v_tasks = room[f'{prefix}_tasks']
if not v_tasks:
    st.info("No tasks.")
else:
    for idx, t in enumerate(v_tasks):
        # 权限：只有看自己页面时，才能勾选
        if view_id == my_id:
            checked = st.checkbox(t['content'], value=t['done'], key=f"tk_{view_id}_{idx}")
            if checked and not t['done']: # 刚完成
                t['done'] = True
                room[f'{prefix}_streak'] += 1
                st.rerun()
            elif not checked and t['done']: # 撤销完成
                t['done'] = False
                room[f'{prefix}_streak'] = max(0, room[f'{prefix}_streak'] - 1)
                st.rerun()
        else:
            st.write(f"{'✅' if t['done'] else '⏳'} {t['content']}")

# 发送任务：只有看自己页面时，可以发给 partner
if view_id == my_id:
    st.write("---")
    new_t = st.text_input("Add task for partner")
    if st.button("Send"):
        p_prefix = "u2" if is_u1_identity else "u1"
        room[f'{p_prefix}_tasks'].append({'content': new_t, 'done': False})
        st.rerun()

# --- 8. Promise 设定 (核心修正) ---
st.divider()
if view_id == my_id:
    # 场景：User1 设置给 User2 的礼物
    p_prefix = "u2" if is_u1_identity else "u1"
    st.write(f"### Your Promise to User {partner_id}")
    col_x, col_y = st.columns([1, 2])
    with col_x: room[f'{p_prefix}_goal'] = st.number_input("Days", value=room[f'{p_prefix}_goal'], min_value=1)
    with col_y: room[f'{p_prefix}_gift'] = st.text_input("Gift", value=room[f'{p_prefix}_gift'])
else:
    st.write(f"### Promise from User {partner_id}")
    st.info(f"Your partner promised you: {v_gift} after {v_goal} days")

# --- 9. 动画触发 ---
# 只有在自己视角完成时触发
if view_id == my_id and v_streak >= v_goal:
    st.balloons()
    st.success(f"Reward unlocked: {v_gift}!")

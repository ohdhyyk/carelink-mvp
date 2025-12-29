
import json
import os
import random
import uuid
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

import streamlit as st

DATA_PATH = "data.json"

# ----------------------------
# Utilities
# ----------------------------
def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

def new_id() -> str:
    return uuid.uuid4().hex

def load_data() -> Dict:
    if not os.path.exists(DATA_PATH):
        return {"tasks": [], "profiles": {}, "rewards": {}}
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    data.setdefault("tasks", [])
    data.setdefault("profiles", {})  # per account_id
    data.setdefault("rewards", {})   # per pair_id
    return data

def save_data(data: Dict) -> None:
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ----------------------------
# Pairing by account numbers (same as your file)
# ----------------------------
def pair_id_from_account(account_id: int) -> int:
    return account_id // 2

def gen_account_pair() -> tuple[int, int]:
    base = random.randrange(100000, 999998, 2)
    return base, base + 1

def normalize_pair_accounts(account_id: int) -> tuple[int, int]:
    # ensure (even, odd)
    if account_id % 2 == 0:
        return account_id, account_id + 1
    return account_id - 1, account_id

# ----------------------------
# Data model
# ----------------------------
@dataclass
class Task:
    id: str
    pair_id: int
    from_account: int
    to_account: int
    title: str
    created_at: str
    completions: Dict[str, bool]

def task_from_raw(raw: Dict) -> Task:
    raw = dict(raw)
    raw.setdefault("completions", {})
    return Task(**raw)

def is_done(task: Task, day: date) -> bool:
    return bool(task.completions.get(day.isoformat(), False))

def set_done(task: Task, day: date, done: bool) -> None:
    task.completions[day.isoformat()] = bool(done)

def created_on_or_before(task: Task, day: date) -> bool:
    try:
        # created_at stored as ISO datetime
        dt = datetime.fromisoformat(task.created_at.replace("Z", ""))
        return dt.date() <= day
    except Exception:
        return True

# ----------------------------
# Nordic minimal styling (close to your existing file + image layout)
# ----------------------------
st.set_page_config(page_title="CareLink Demo", page_icon="🎁", layout="centered")

st.markdown(
    """
<style>
:root{
  --bg: #F7F8F6;
  --card: rgba(255,255,255,.82);
  --border: rgba(15, 23, 42, .10);
  --text: rgba(15, 23, 42, .92);
  --muted: rgba(15, 23, 42, .58);
  --shadow: 0 10px 26px rgba(15, 23, 42, .06);
  --radius: 20px;
  --accent: #6FAF9E;
  --accent2: #E6C77A;
}
html, body, .stApp { background: var(--bg); color: var(--text); }
.block-container { padding-top: 1.2rem; max-width: 980px; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

.nl-card{
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px 18px;
  background: var(--card);
  box-shadow: var(--shadow);
}
.nl-title{ font-weight: 800; letter-spacing: -0.02em; margin: 0 0 6px 0; }
.nl-muted{ color: var(--muted); font-size: 12px; }
.nl-section{ font-weight: 800; margin: 10px 0 6px 0; }
.nl-chip{
  display:inline-flex; align-items:center; gap:8px;
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 12px;
  background: rgba(255,255,255,.65);
  margin-right: 8px; margin-top: 6px;
}
.nl-row{
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 10px 12px;
  background: rgba(255,255,255,.55);
}
.nl-row + .nl-row{ margin-top: 8px; }

.avatar-row{ display:flex; align-items:center; justify-content:center; gap: 14px; }
.avatar{
  width: 112px; height: 112px; border-radius: 999px;
  display:flex; align-items:center; justify-content:center;
  font-weight: 800; user-select: none;
  border: 2px solid transparent;
}
.a1{ background: rgba(88, 213, 232, 0.45); }
.a2{ background: rgba(235, 79, 207, 0.40); }
.active{ border-color: rgba(15,23,42,.28); }
.inactive{ opacity: .65; }

.midbox{ text-align:center; min-width: 240px; }
.kpi{ font-size: 30px; font-weight: 900; line-height: 1; }
.gift{ font-size: 26px; filter: grayscale(1); opacity: .45; }
.gift.on{ filter: grayscale(0); opacity: 1; }

.progress-wrap{ margin-top: 10px; }
.dotbar{ display:flex; gap: 14px; justify-content:center; align-items:center; margin-top: 8px; }
.dot{
  width: 10px; height: 10px; border-radius: 999px;
  background: rgba(15,23,42,.18);
}
.dot.on{ background: var(--accent); }
.dot.big{ width: 12px; height: 12px; }

.stButton > button{
  border-radius: 16px !important;
  border: 1px solid var(--border) !important;
  background: rgba(255,255,255,.7) !important;
}
div[data-testid="stTextInput"] input, textarea{
  border-radius: 16px !important;
  border: 1px solid var(--border) !important;
  background: rgba(255,255,255,.7) !important;
}
label[data-testid="stCheckbox"]{ font-size: 0.96rem; }
</style>
""",
    unsafe_allow_html=True,
)

data = load_data()

# ----------------------------
# Sidebar login (based on your uploaded file)
# ----------------------------
with st.sidebar:
    st.title("CareLink")
    st.caption("Login + single-user view (toggle User1/User2)")

    mode = st.radio("你有没有账号？", ["我有账号", "我没有账号"], horizontal=True)

    if mode == "我有账号":
        acc = st.text_input("输入你的账号编号", placeholder="例如：100123")
        if st.button("进入", use_container_width=True):
            if not acc.isdigit():
                st.error("请输入纯数字账号。")
            else:
                account_id = int(acc)
                st.session_state["account_id"] = account_id
                st.session_state["pair_id"] = pair_id_from_account(account_id)
                # default viewer is "me"
                st.session_state["viewer_account"] = account_id
                st.toast("已进入", icon="✅")
                safe_rerun()
    else:
        if st.button("生成一对账号", use_container_width=True):
            a, b = gen_account_pair()
            st.session_state["generated_a"] = a
            st.session_state["generated_b"] = b

        if "generated_a" in st.session_state:
            a = st.session_state["generated_a"]
            b = st.session_state["generated_b"]
            st.info("把“对方账号”发给对方；你们就能连到同一个空间。")
            st.code(f"你的账号：{a}\n对方账号：{b}", language="text")
            if st.button("我用我的账号进入", use_container_width=True):
                st.session_state["account_id"] = a
                st.session_state["pair_id"] = pair_id_from_account(a)
                st.session_state["viewer_account"] = a
                st.toast("已进入", icon="✅")
                safe_rerun()

    st.divider()
    if st.session_state.get("pair_id") is not None:
        if st.button("退出（本设备）", use_container_width=True):
            for k in ["account_id", "pair_id", "generated_a", "generated_b", "viewer_account"]:
                st.session_state.pop(k, None)
            safe_rerun()

pair_id = st.session_state.get("pair_id")
account_id = st.session_state.get("account_id")

if pair_id is None or account_id is None:
    st.markdown("## 🎁 CareLink demo")
    st.caption("请先在左侧登录或生成账号进入。")
    st.stop()

left_account, right_account = normalize_pair_accounts(int(account_id))
# In UI we call them User1/User2 (but mapped to account numbers for persistence)
acct_user1 = left_account
acct_user2 = right_account

# Ensure viewer exists and is one of the pair
if "viewer_account" not in st.session_state:
    st.session_state["viewer_account"] = int(account_id)
if st.session_state["viewer_account"] not in (acct_user1, acct_user2):
    st.session_state["viewer_account"] = int(account_id)

viewer = int(st.session_state["viewer_account"])
partner = acct_user2 if viewer == acct_user1 else acct_user1

# ----------------------------
# Load tasks for this pair
# ----------------------------
all_tasks: List[Task] = []
for raw in data.get("tasks", []):
    try:
        all_tasks.append(task_from_raw(raw))
    except TypeError:
        continue

pair_tasks = [t for t in all_tasks if int(t.pair_id) == int(pair_id)]
pair_tasks.sort(key=lambda t: t.created_at, reverse=True)

def tasks_sent_by(from_acc: int) -> List[Task]:
    return [t for t in pair_tasks if int(t.from_account) == int(from_acc)]

def tasks_received_by(to_acc: int) -> List[Task]:
    return [t for t in pair_tasks if int(t.to_account) == int(to_acc)]

def persist_task(updated: Task) -> None:
    for i, raw in enumerate(data.get("tasks", [])):
        if raw.get("id") == updated.id:
            data["tasks"][i] = asdict(updated)
            save_data(data)
            return
    data.setdefault("tasks", []).append(asdict(updated))
    save_data(data)

def create_task(from_acc: int, to_acc: int, title: str) -> None:
    title = title.strip()
    if not title:
        return
    t = Task(
        id=new_id(),
        pair_id=int(pair_id),
        from_account=int(from_acc),
        to_account=int(to_acc),
        title=title,
        created_at=datetime.utcnow().isoformat(timespec="seconds"),
        completions={},
    )
    data.setdefault("tasks", []).insert(0, asdict(t))
    save_data(data)

# ----------------------------
# Profiles (mood / want) stored per account, editable anytime
# ----------------------------
def profile_key(acc: int) -> str:
    return str(acc)

def ensure_profile(acc: int):
    profiles = data.setdefault("profiles", {})
    if profile_key(acc) not in profiles:
        profiles[profile_key(acc)] = {"mood": "tired", "want": ""}
        save_data(data)

def get_profile(acc: int) -> Dict:
    ensure_profile(acc)
    return data["profiles"][profile_key(acc)]

def set_profile(acc: int, mood: str, want: str):
    ensure_profile(acc)
    data["profiles"][profile_key(acc)]["mood"] = mood
    data["profiles"][profile_key(acc)]["want"] = want
    save_data(data)

# ----------------------------
# Reward config stored per pair_id, editable anytime
# ----------------------------
def reward_key(pid: int) -> str:
    return str(pid)

def ensure_reward(pid: int):
    rewards = data.setdefault("rewards", {})
    if reward_key(pid) not in rewards:
        rewards[reward_key(pid)] = {"days_required": 3, "gift": "milk tea ☕"}
        save_data(data)

def get_reward(pid: int) -> Dict:
    ensure_reward(pid)
    return data["rewards"][reward_key(pid)]

def set_reward(pid: int, days_required: int, gift: str):
    ensure_reward(pid)
    data["rewards"][reward_key(pid)]["days_required"] = int(days_required)
    data["rewards"][reward_key(pid)]["gift"] = gift
    save_data(data)

# ----------------------------
# Pair streak (both completed their received tasks for consecutive days)
# ----------------------------
def all_received_done_for_day(acc: int, day: date) -> bool:
    received = [t for t in tasks_received_by(acc) if created_on_or_before(t, day)]
    if not received:
        return True
    return all(is_done(t, day) for t in received)

def pair_streak(up_to: date) -> int:
    s = 0
    d = up_to
    while True:
        if all_received_done_for_day(acct_user1, d) and all_received_done_for_day(acct_user2, d):
            s += 1
            d -= timedelta(days=1)
        else:
            break
    return s

# ----------------------------
# Top header (like your image)
# ----------------------------
reward = get_reward(pair_id)
streak_days = pair_streak(date.today())
required = int(reward.get("days_required", 3))
unlocked = streak_days >= required

# clickable buttons for switching view (same page)
top = st.container()
with top:
    st.markdown('<div class="nl-card">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.1, 1.6, 1.1], vertical_alignment="center")

    with c1:
        if st.button("User1", use_container_width=True):
            st.session_state["viewer_account"] = acct_user1
            safe_rerun()

    with c2:
        gift_cls = "gift on" if unlocked else "gift"
        st.markdown(
            f"""
            <div class="midbox">
              <div class="kpi">{streak_days} day{"s" if streak_days!=1 else ""}</div>
              <div class="nl-muted">how many days both doing task</div>
              <div style="margin-top:6px;"><span class="{gift_cls}">🎁</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        # simple dotbar (max 5 dots) similar feel to your green dots
        dots = 5
        on = min(streak_days, dots)
        dot_html = "".join([f'<span class="dot {"on big" if i<on else "big"}"></span>' if i==dots-1 else f'<span class="dot {"on" if i<on else ""}"></span>' for i in range(dots)])
        st.markdown(f'<div class="dotbar">{dot_html}</div>', unsafe_allow_html=True)

    with c3:
        if st.button("User2", use_container_width=True):
            st.session_state["viewer_account"] = acct_user2
            safe_rerun()

    # avatars row
    a1_cls = "avatar a1 " + ("active" if viewer == acct_user1 else "inactive")
    a2_cls = "avatar a2 " + ("active" if viewer == acct_user2 else "inactive")
    st.markdown(
        f"""
        <div class="avatar-row" style="margin-top: 12px;">
          <div class="{a1_cls}">User1</div>
          <div style="width: 24px;"></div>
          <div class="{a2_cls}">User2</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

st.write("")  # spacing

# ----------------------------
# Mood + Want (editable anytime, per viewer)
# ----------------------------
prof = get_profile(viewer)
mood_options = ["tired", "energetic", "sad"]

st.markdown('<div class="nl-card">', unsafe_allow_html=True)
st.markdown('<div class="nl-section">mood</div>', unsafe_allow_html=True)
mood = st.radio(
    "mood",
    mood_options,
    index=mood_options.index(prof.get("mood", "tired")) if prof.get("mood", "tired") in mood_options else 0,
    horizontal=True,
    label_visibility="collapsed",
)
st.markdown('<div class="nl-section" style="margin-top:10px;">want to have</div>', unsafe_allow_html=True)
want = st.text_input(
    "want",
    value=prof.get("want", ""),
    placeholder="eg. milktea, coffee",
    label_visibility="collapsed",
)
set_profile(viewer, mood, want)

st.markdown(
    f"""
    <div class="nl-muted" style="margin-top:8px;">
      <span class="nl-chip">status: {mood}</span>
      <span class="nl-chip">{want if want else "eg. milktea, coffee"}</span>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

st.write("")

# ----------------------------
# Send task (text input) to partner
# ----------------------------
st.markdown('<div class="nl-card">', unsafe_allow_html=True)
st.markdown(f'<div class="nl-section">Tasks for linked user</div>', unsafe_allow_html=True)
st.caption("Task 内容通过文本输入，发送给对方。")

task_text = st.text_input(
    "send_task_text",
    placeholder="Type a task you want your partner to do…",
    label_visibility="collapsed",
)
send_cols = st.columns([1, 1, 3])
with send_cols[0]:
    if st.button("Send", use_container_width=True):
        if not task_text.strip():
            st.warning("请先输入 task 内容。")
        else:
            create_task(from_acc=viewer, to_acc=partner, title=task_text)
            st.toast("已发送", icon="📩")
            safe_rerun()
with send_cols[1]:
    if st.button("Clear", use_container_width=True):
        st.session_state["send_task_text"] = ""
        safe_rerun()

st.markdown("</div>", unsafe_allow_html=True)

st.write("")

# ----------------------------
# Tasks lists (match your image: received + sent)
# Rule: viewer can only tick tasks received by viewer (never tick ones they sent)
# ----------------------------
today = date.today()

st.markdown('<div class="nl-card">', unsafe_allow_html=True)
st.markdown('<div class="nl-section">Today’s task</div>', unsafe_allow_html=True)

# Received (tickable)
st.markdown("**Tasks from your linked user**")
received = tasks_received_by(viewer)

if not received:
    st.caption("No tasks received from your linked user today.")
else:
    for t in received[:30]:
        st.markdown('<div class="nl-row">', unsafe_allow_html=True)
        row = st.columns([8, 1.4], vertical_alignment="center")
        row[0].write(t.title)

        key = f"done_{t.id}_{viewer}_{today.isoformat()}"
        checked = row[1].checkbox("✅", value=is_done(t, today), key=key)
        if checked != is_done(t, today):
            set_done(t, today, checked)
            persist_task(t)
            st.toast("已更新", icon="✅")
        st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# Sent (read-only)
st.markdown("**Tasks for your linked user**")
sent = tasks_sent_by(viewer)

if not sent:
    st.caption("You have already sent tasks to your linked user today. Check back tomorrow!")
else:
    for t in sent[:30]:
        status = "✅" if is_done(t, today) else "⬜️"
        st.markdown(f"{status} {t.title}  <span class='nl-muted'>(completed by partner)</span>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

st.write("")

# ----------------------------
# Reward block (new)
# ----------------------------
st.markdown('<div class="nl-card">', unsafe_allow_html=True)
st.markdown('<div class="nl-section">Care Reward</div>', unsafe_allow_html=True)
st.caption("Rewards grow with consistency, not pressure.")

days_required = st.number_input(
    "days_required",
    min_value=1,
    max_value=30,
    value=int(reward.get("days_required", 3)),
    step=1,
    label_visibility="collapsed",
)
gift = st.text_input(
    "gift",
    value=reward.get("gift", "milk tea ☕"),
    placeholder="e.g. milk tea, coffee…",
    label_visibility="collapsed",
)
set_reward(pair_id, int(days_required), gift)

reward = get_reward(pair_id)
required = int(reward.get("days_required", 3))
unlocked = streak_days >= required

st.markdown(
    f"""
    <div style="margin-top:10px;">
      If he/she complete task for <b>{required}</b> days, gain a gift of <b>{reward.get("gift") or "—"}</b>
    </div>
    """,
    unsafe_allow_html=True,
)
if unlocked:
    st.success("🎉 Reward unlocked.")
else:
    remaining = max(required - streak_days, 0)
    st.info(f"{remaining} more day{'s' if remaining!=1 else ''} to unlock.")

st.markdown("</div>", unsafe_allow_html=True)

with st.expander("Demo controls (optional)"):
    c = st.columns(3)
    with c[0]:
        if st.button("Reset tasks"):
            data["tasks"] = [t for t in data.get("tasks", []) if int(t.get("pair_id", -1)) != int(pair_id)]
            save_data(data)
            safe_rerun()
    with c[1]:
        if st.button("Reset profiles"):
            for k in [str(acct_user1), str(acct_user2)]:
                data.get("profiles", {}).pop(k, None)
            save_data(data)
            safe_rerun()
    with c[2]:
        if st.button("Reset reward"):
            data.get("rewards", {}).pop(str(pair_id), None)
            save_data(data)
            safe_rerun()

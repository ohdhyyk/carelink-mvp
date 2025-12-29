
import json
import os
import random
import uuid
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from typing import Dict, List

import streamlit as st

DATA_PATH = "data.json"

# ----------------------------
# Helpers
# ----------------------------
def rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

def new_id():
    return uuid.uuid4().hex

def load_data():
    if not os.path.exists(DATA_PATH):
        return {"tasks": [], "profiles": {}, "rewards": {}}
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ----------------------------
# Pairing logic
# ----------------------------
def pair_id_from_account(account_id: int) -> int:
    return account_id // 2

def gen_account_pair():
    base = random.randrange(100000, 999998, 2)
    return base, base + 1

def normalize_pair_accounts(account_id: int):
    if account_id % 2 == 0:
        return account_id, account_id + 1
    return account_id - 1, account_id

# ----------------------------
# Data models
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

def task_from_raw(raw):
    raw.setdefault("completions", {})
    return Task(**raw)

def is_done(task: Task, day: date) -> bool:
    return task.completions.get(day.isoformat(), False)

def set_done(task: Task, day: date, done: bool):
    task.completions[day.isoformat()] = done

def created_on_or_before(task: Task, day: date) -> bool:
    return datetime.fromisoformat(task.created_at).date() <= day

# ----------------------------
# Streamlit config + style
# ----------------------------
st.set_page_config(page_title="CareLink Demo", page_icon="🎁", layout="centered")

st.markdown(
    """
<style>
html, body, .stApp { background: #F7F8F6; }
.card {
  background: white;
  border-radius: 18px;
  padding: 16px;
  border: 1px solid #eee;
}
</style>
""",
    unsafe_allow_html=True,
)

data = load_data()

# ----------------------------
# Sidebar login
# ----------------------------
with st.sidebar:
    st.title("CareLink")
    mode = st.radio("账号", ["已有账号", "生成账号"])

    if mode == "已有账号":
        acc = st.text_input("账号编号")
        if st.button("进入"):
            if acc.isdigit():
                st.session_state.account_id = int(acc)
                st.session_state.pair_id = pair_id_from_account(int(acc))
                st.session_state.viewer = int(acc)
                rerun()
    else:
        if st.button("生成一对账号"):
            a, b = gen_account_pair()
            st.session_state.gen_a = a
            st.session_state.gen_b = b

        if "gen_a" in st.session_state:
            st.code(f"你的账号: {st.session_state.gen_a}\n对方账号: {st.session_state.gen_b}")
            if st.button("进入"):
                st.session_state.account_id = st.session_state.gen_a
                st.session_state.pair_id = pair_id_from_account(st.session_state.gen_a)
                st.session_state.viewer = st.session_state.gen_a
                rerun()

if "account_id" not in st.session_state:
    st.stop()

account_id = st.session_state.account_id
pair_id = st.session_state.pair_id

u1, u2 = normalize_pair_accounts(account_id)
viewer = st.session_state.viewer
partner = u2 if viewer == u1 else u1

# ----------------------------
# Load tasks
# ----------------------------
tasks = [task_from_raw(t) for t in data.get("tasks", []) if t["pair_id"] == pair_id]

def save_task(task: Task):
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task.id]
    data["tasks"].append(asdict(task))
    save_data(data)

def create_task(text: str):
    t = Task(
        id=new_id(),
        pair_id=pair_id,
        from_account=viewer,
        to_account=partner,
        title=text,
        created_at=datetime.utcnow().isoformat(),
        completions={}
    )
    data["tasks"].append(asdict(t))
    save_data(data)

# ----------------------------
# Streak logic (SAFE)
# ----------------------------
def received_tasks(acc: int, day: date):
    return [
        t for t in tasks
        if t.to_account == acc and created_on_or_before(t, day)
    ]

def all_received_done(acc: int, day: date) -> bool:
    r = received_tasks(acc, day)
    if not r:
        return False
    return all(is_done(t, day) for t in r)

def pair_streak(today: date) -> int:
    streak = 0
    d = today
    for _ in range(366):
        if all_received_done(u1, d) and all_received_done(u2, d):
            streak += 1
            d -= timedelta(days=1)
        else:
            break
    return streak

streak_days = pair_streak(date.today())

# ----------------------------
# UI
# ----------------------------
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.markdown(f"### {streak_days} days both doing task 🎁")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='card'>", unsafe_allow_html=True)
text = st.text_input("Send a task to your partner")
if st.button("Send"):
    if text.strip():
        create_task(text)
        rerun()
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='card'>", unsafe_allow_html=True)
st.markdown("**Tasks from your linked user**")
today = date.today()
for t in tasks:
    if t.to_account == viewer:
        checked = st.checkbox(t.title, value=is_done(t, today))
        if checked != is_done(t, today):
            set_done(t, today, checked)
            save_task(t)
st.markdown("</div>", unsafe_allow_html=True)

import json
import os
import random
import uuid
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from typing import Dict, List

import streamlit as st

DATA_PATH = "data.json"

def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

def uid() -> str:
    return uuid.uuid4().hex

def load_data() -> Dict:
    if not os.path.exists(DATA_PATH):
        return {"tasks": [], "profiles": {}, "rewards": {}}
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {"tasks": [], "profiles": {}, "rewards": {}}
    data.setdefault("tasks", [])
    data.setdefault("profiles", {})
    data.setdefault("rewards", {})
    return data

def save_data(data: Dict) -> None:
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def pair_id_from_account(account_id: int) -> int:
    return account_id // 2

def gen_account_pair() -> tuple[int, int]:
    base = random.randrange(100000, 999998, 2)
    return base, base + 1

def normalize_pair_accounts(account_id: int) -> tuple[int, int]:
    if account_id % 2 == 0:
        return account_id, account_id + 1
    return account_id - 1, account_id

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

def persist_task(data: Dict, updated: Task) -> None:
    for i, raw in enumerate(data.get("tasks", [])):
        if raw.get("id") == updated.id:
            data["tasks"][i] = asdict(updated)
            save_data(data)
            return
    data.setdefault("tasks", []).append(asdict(updated))
    save_data(data)

def create_task(data: Dict, pair_id: int, from_acc: int, to_acc: int, title: str) -> None:
    t = Task(
        id=uid(),
        pair_id=int(pair_id),
        from_account=int(from_acc),
        to_account=int(to_acc),
        title=title.strip(),
        created_at=datetime.utcnow().isoformat(timespec="seconds"),
        completions={},
    )
    data.setdefault("tasks", []).insert(0, asdict(t))
    save_data(data)

def tasks_received(pair_tasks: List[Task], acc: int) -> List[Task]:
    return [t for t in pair_tasks if int(t.to_account) == int(acc)]

def day_done(pair_tasks: List[Task], acc: int, day: date) -> bool:
    recv = tasks_received(pair_tasks, acc)
    if not recv:
        return False
    return all(is_done(t, day) for t in recv)

def shared_streak_days(pair_tasks: List[Task], a: int, b: int, up_to: date) -> int:
    d = up_to
    s = 0
    while True:
        if day_done(pair_tasks, a, d) and day_done(pair_tasks, b, d):
            s += 1
            d -= timedelta(days=1)
        else:
            break
    return s

st.set_page_config(page_title="CareLink MVP", page_icon="🤝", layout="wide")
st.markdown(
    """
<style>
:root{
  --bg:#f6f7f9;
  --surface:rgba(255,255,255,.86);
  --surface2:rgba(255,255,255,.62);
  --border:rgba(15,23,42,.10);
  --text:rgba(15,23,42,.92);
  --muted:rgba(15,23,42,.62);
  --shadow:0 10px 30px rgba(15,23,42,.06);
  --r:22px;
}
html, body, .stApp { background: var(--bg); color: var(--text); }
.block-container { padding-top: 1.1rem; max-width: 1100px; }
#MainMenu, footer { visibility:hidden; }

section[data-testid="stSidebar"]{
  background: rgba(255,255,255,.55);
  border-right: 1px solid var(--border);
  backdrop-filter: blur(10px);
}
.nl-card{
  border: 1px solid var(--border);
  border-radius: var(--r);
  background: var(--surface);
  box-shadow: var(--shadow);
  padding: 18px 18px 10px 18px;
  animation: fadeUp .24s ease-out;
}
@keyframes fadeUp{ from{opacity:0; transform:translateY(8px);} to{opacity:1; transform:translateY(0);} }

.top-wrap{
  display:flex; align-items:center; justify-content:center;
  gap:24px; margin: 6px 0 14px 0;
}
.avatar{
  width:84px; height:84px; border-radius:999px;
  display:flex; align-items:center; justify-content:center;
  font-weight:700;
  border: 1px solid var(--border);
  background: #a7e6ea;
  box-shadow: 0 10px 24px rgba(15,23,42,.08);
  transition: transform .12s ease, box-shadow .12s ease;
}
.avatar.pink{ background:#f3a0d8; }
.avatar.active{ outline: 3px solid rgba(15,23,42,.10); transform: translateY(-1px); }
.mid{
  display:flex; flex-direction:column; align-items:center; gap:10px;
  min-width: 290px;
}
.heartline{
  font-size: 18px;
  color: rgba(220,38,38,.8);
  letter-spacing: 1px;
  animation: pulse 1.4s ease-in-out infinite;
  user-select:none;
}
@keyframes pulse { 0%,100%{opacity:.65} 50%{opacity:1} }

.pill{
  display:inline-flex; align-items:center; gap:8px;
  border:1px solid var(--border);
  border-radius:999px;
  padding:6px 10px;
  font-size:12px;
  color: var(--muted);
  background: var(--surface2);
}
.labelcol{
  font-weight:700;
  color: var(--muted);
  width:130px;
  padding-top: 8px;
}
.rowbox{
  border:1px solid var(--border);
  border-radius: 16px;
  padding: 10px 12px;
  background: rgba(255,255,255,.58);
  transition: transform .12s ease, box-shadow .12s ease;
  margin-bottom: 10px;
}
.rowbox:hover{ transform: translateY(-1px); box-shadow: 0 10px 24px rgba(15,23,42,.07); }

.stButton > button{
  border-radius: 16px !important;
  padding: .62rem .9rem !important;
  border: 1px solid var(--border) !important;
  background: rgba(255,255,255,.72) !important;
  transition: transform .12s ease, box-shadow .12s ease;
}
.stButton > button:hover{ transform: translateY(-1px); box-shadow: 0 10px 24px rgba(15,23,42,.08); }

div[data-testid="stTextInput"] input, textarea{
  border-radius: 16px !important;
  border: 1px solid var(--border) !important;
  background: rgba(255,255,255,.72) !important;
}
.smallcap{ color: var(--muted); font-size: 12px; }
</style>
""",
    unsafe_allow_html=True,
)

data = load_data()

with st.sidebar:
    st.title("CareLink")
    st.caption("MVP demo")

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
                if "view_as" not in st.session_state:
                    st.session_state["view_as"] = account_id
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
                st.session_state["view_as"] = a
                safe_rerun()

    st.divider()
    if st.session_state.get("pair_id") is not None:
        if st.button("退出（本设备）", use_container_width=True):
            for k in ["account_id", "pair_id", "generated_a", "generated_b", "view_as"]:
                st.session_state.pop(k, None)
            safe_rerun()

pair_id = st.session_state.get("pair_id")
account_id = st.session_state.get("account_id")

if pair_id is None or account_id is None:
    st.markdown("## 🤝 关系任务 MVP")
    st.caption("先在左侧登录/生成账号。")
    st.stop()

u1, u2 = normalize_pair_accounts(int(account_id))
if "view_as" not in st.session_state:
    st.session_state["view_as"] = int(account_id)

view_as = int(st.session_state["view_as"])
if view_as not in (u1, u2):
    view_as = int(account_id)
other = u2 if view_as == u1 else u1

today = date.today()
today_iso = today.isoformat()

all_tasks: List[Task] = []
for raw in data.get("tasks", []):
    try:
        all_tasks.append(task_from_raw(raw))
    except TypeError:
        continue
pair_tasks = [t for t in all_tasks if int(t.pair_id) == int(pair_id)]
pair_tasks.sort(key=lambda t: t.created_at, reverse=True)

st.markdown("###")
shared = shared_streak_days(pair_tasks, u1, u2, today)

pair_rewards = data.get("rewards", {}).get(str(pair_id), {})
targets = []
for cfg in pair_rewards.values():
    try:
        targets.append(int(cfg.get("days", 0)))
    except Exception:
        pass
target = min([t for t in targets if t > 0], default=7)
progress = min(1.0, shared / max(1, target))

btnL, btnM, btnR = st.columns([1.2, 2.2, 1.2], vertical_alignment="center")
with btnL:
    if st.button("👤 User1", use_container_width=True):
        st.session_state["view_as"] = u1
        safe_rerun()
with btnR:
    if st.button("👤 User2", use_container_width=True):
        st.session_state["view_as"] = u2
        safe_rerun()

st.markdown(
    f"""
<div class="top-wrap">
  <div class="avatar {'active' if view_as==u1 else ''}">User1</div>
  <div class="mid">
    <div class="heartline">─╲╱─╲╱─╲╱─</div>
    <div class="pill"><b>{shared}</b>&nbsp;days &nbsp;•&nbsp; how many days both doing task</div>
  </div>
  <div class="avatar pink {'active' if view_as==u2 else ''}">User2</div>
</div>
""",
    unsafe_allow_html=True,
)
st.progress(progress)

st.markdown("---")

profiles = data.setdefault("profiles", {})
pair_prof = profiles.setdefault(str(pair_id), {})
me_prof = pair_prof.setdefault(str(view_as), {"mood": "tired", "want": ""})

labels, inputs = st.columns([1.2, 4], vertical_alignment="top")
with labels:
    st.markdown('<div class="labelcol">mood</div>', unsafe_allow_html=True)
    st.markdown('<div class="labelcol">want to have</div>', unsafe_allow_html=True)
with inputs:
    mood_options = ["tired", "energetic", "sad"]
    mood_idx = mood_options.index(me_prof.get("mood", "tired")) if me_prof.get("mood") in mood_options else 0
    mood = st.selectbox("mood", mood_options, index=mood_idx, label_visibility="collapsed", key=f"mood_{view_as}")
    want = st.text_input("want", value=me_prof.get("want", ""), placeholder="e.g. milktea, coffee", label_visibility="collapsed", key=f"want_{view_as}")

if mood != me_prof.get("mood") or want != me_prof.get("want"):
    me_prof["mood"] = mood
    me_prof["want"] = want
    save_data(data)

st.markdown("---")

st.markdown("### Today's task:")
st.markdown('<div class="nl-card">', unsafe_allow_html=True)
st.markdown("**📌 Tasks from Your Linked User**")

received = tasks_received(pair_tasks, view_as)

if not received:
    st.markdown('<div class="smallcap">No tasks received from your linked user today.</div>', unsafe_allow_html=True)
else:
    for t in received[:20]:
        st.markdown('<div class="rowbox">', unsafe_allow_html=True)
        row = st.columns([6, 1.2], vertical_alignment="center")
        row[0].write(t.title)

        key = f"done_{t.id}_{view_as}_{today_iso}"
        checked = row[1].checkbox("✅", value=is_done(t, today), key=key)
        if checked != is_done(t, today):
            set_done(t, today, checked)
            persist_task(data, t)
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("### Tasks for linked user")
st.markdown('<div class="nl-card">', unsafe_allow_html=True)
st.markdown("**📝 Tasks for Your Linked User**")

def sent_today_count(pair_tasks: List[Task], sender: int, day_iso: str) -> int:
    c = 0
    for t in pair_tasks:
        if int(t.from_account) == int(sender) and str(t.created_at)[:10] == day_iso:
            c += 1
    return c

sent_count = sent_today_count(pair_tasks, view_as, today_iso)
limit = 5
st.caption(f"{sent_count}/{limit}")

task_title = st.text_input("给对方一个 task", placeholder="e.g. drink water, walk 10 min", label_visibility="collapsed", key=f"send_input_{view_as}")
send = st.button("发送给对方", use_container_width=True, disabled=(sent_count >= limit))
if send:
    if not task_title.strip():
        st.warning("先写一个 task 再发送。")
    elif sent_count >= limit:
        st.warning("今天发送已达上限（5）。")
    else:
        create_task(data, pair_id=int(pair_id), from_acc=view_as, to_acc=other, title=task_title)
        safe_rerun()

st.markdown("---")
st.markdown('<div class="smallcap">Sent (read-only):</div>', unsafe_allow_html=True)
sent = [t for t in pair_tasks if int(t.from_account) == int(view_as)]
sent.sort(key=lambda t: t.created_at, reverse=True)

if not sent:
    st.markdown('<div class="smallcap">You have not sent any tasks yet.</div>', unsafe_allow_html=True)
else:
    for t in sent[:15]:
        status = "✅" if t.completions.get(today_iso, False) else "—"
        st.markdown(f"- **{status}**  {t.title}")

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("### Choose a reward for linked user")
st.markdown('<div class="nl-card">', unsafe_allow_html=True)
st.markdown("If he/she complete task for __ days, gain a gift of __")

rw_col1, rw_col2 = st.columns(2)
pair_rewards = data.setdefault("rewards", {}).setdefault(str(pair_id), {})
my_reward = pair_rewards.setdefault(str(view_as), {"days": 7, "gift": ""})

with rw_col1:
    days = st.number_input("days", min_value=1, max_value=365, value=int(my_reward.get("days", 7)), step=1)
with rw_col2:
    gift = st.text_input("gift", value=my_reward.get("gift", ""), placeholder="e.g. coffee / 100kr / a small gift")

if days != int(my_reward.get("days", 7)) or gift != my_reward.get("gift", ""):
    my_reward["days"] = int(days)
    my_reward["gift"] = gift
    save_data(data)

other_reward = pair_rewards.get(str(other), {})
if other_reward.get("gift"):
    st.caption(f"对方设置的奖励：连续 {other_reward.get('days')} 天 → {other_reward.get('gift')} 🎁")

st.markdown("</div>", unsafe_allow_html=True)

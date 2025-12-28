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
    else:
        return

def new_id() -> str:
    return uuid.uuid4().hex

def load_data() -> Dict:
    if not os.path.exists(DATA_PATH):
        return {"tasks": []}
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {"tasks": []}
    data.setdefault("tasks", [])
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

def streak(task: Task, up_to: date) -> int:
    d = up_to
    s = 0
    while True:
        if is_done(task, d):
            s += 1
            d -= timedelta(days=1)
        else:
            break
    return s

st.set_page_config(page_title="CareLink MVP", page_icon="🤝", layout="wide")

st.markdown(
    """
<style>
.block-container { padding-top: 1.2rem; max-width: 1200px; }
h1,h2,h3 { letter-spacing: -0.02em; }
.c-card {
  border: 1px solid rgba(49,51,63,.12);
  border-radius: 18px;
  padding: 16px 16px 6px 16px;
  background: rgba(255,255,255,.6);
  box-shadow: 0 6px 20px rgba(0,0,0,.04);
  animation: fadeUp .22s ease-out;
}
.c-pill {
  display:inline-block;
  border: 1px solid rgba(49,51,63,.12);
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 12px;
  opacity: .9;
}
@keyframes fadeUp { from { opacity:0; transform: translateY(6px);} to { opacity:1; transform: translateY(0);} }
.stButton > button { border-radius: 14px; padding: 0.6rem 0.9rem; }
</style>
""",
    unsafe_allow_html=True,
)

data = load_data()

with st.sidebar:
    st.header("进入（无注册）")
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
                safe_rerun()

    st.divider()
    if st.session_state.get("pair_id") is not None:
        if st.button("退出（本设备）", use_container_width=True):
            for k in ["account_id", "pair_id", "generated_a", "generated_b"]:
                st.session_state.pop(k, None)
            safe_rerun()

pair_id = st.session_state.get("pair_id")
account_id = st.session_state.get("account_id")

if pair_id is None or account_id is None:
    st.title("🤝 关系任务 MVP（双人对称界面）")
    st.caption("保持现在的登录方式；进入后左右分别代表两个人。")
    st.info("请先在左侧输入账号或生成一对账号进入。")
    st.stop()

left_account, right_account = normalize_pair_accounts(int(account_id))

st.title("🤝 关系任务 MVP")
st.caption("左右对称：输入 task 会发送到对方列表；对方用 ✅ 勾选今天完成。")

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
    t = Task(
        id=new_id(),
        pair_id=int(pair_id),
        from_account=int(from_acc),
        to_account=int(to_acc),
        title=title.strip(),
        created_at=datetime.utcnow().isoformat(timespec="seconds"),
        completions={},
    )
    data.setdefault("tasks", []).insert(0, asdict(t))
    save_data(data)

colL, colR = st.columns(2, gap="large")

def render_user_panel(col, me: int, other: int):
    today_iso = date.today().isoformat()
    with col:
        st.markdown('<div class="c-card">', unsafe_allow_html=True)

        st.markdown(f"### 用户 **{me}**")
        st.markdown(f'<span class="c-pill">对方：{other}</span>', unsafe_allow_html=True)

        st.divider()

        st.subheader("给对方一个 task")
        task_title = st.text_input(
            "Task 内容",
            key=f"new_task_{me}",
            placeholder="例如：晚饭后走 10 分钟",
            label_visibility="collapsed",
        )
        if st.button("发送给对方", key=f"send_{me}", use_container_width=True):
            if not task_title.strip():
                st.warning("先写一个 task 再发送。")
            else:
                create_task(from_acc=me, to_acc=other, title=task_title)
                safe_rerun()

        st.divider()

        st.subheader("我收到的 tasks（我来✅）")
        received = tasks_received_by(me)
        if not received:
            st.info("还没有收到 task。")
        else:
            for t in received[:20]:
                row = st.columns([4, 1.2], vertical_alignment="center")
                row[0].write(t.title)

                key = f"done_{t.id}_{me}_{today_iso}"
                checked = row[1].checkbox("✅", value=is_done(t, date.today()), key=key)
                if checked != is_done(t, date.today()):
                    set_done(t, date.today(), checked)
                    persist_task(t)

                st.caption(f"连续完成：{streak(t, date.today())} 天")

        st.divider()

        st.subheader("我发出的 tasks（对方✅）")
        sent = tasks_sent_by(me)
        if not sent:
            st.info("你还没发出 task。")
        else:
            for t in sent[:20]:
                # IMPORTANT: show receiver completion only
                status = "✅" if t.completions.get(today_iso, False) else "—"
                st.write(f"{status}  {t.title}")

        st.markdown("</div>", unsafe_allow_html=True)

render_user_panel(colL, left_account, right_account)
render_user_panel(colR, right_account, left_account)

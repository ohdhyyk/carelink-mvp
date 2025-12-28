import json
import os
import random
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from typing import Dict, List

import streamlit as st


def safe_rerun():
    """Version-safe rerun for Streamlit Cloud/local."""
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        safe_rerun()
    else:
        return

DATA_PATH = "data.json"

# ----------------------------
# Data model
# ----------------------------
@dataclass
class Task:
    id: str
    pair_id: int
    title: str
    description: str
    created_by: str
    created_at: str
    start_date: str
    target_days: int
    pledge_enabled: bool
    pledge_amount: float
    pledge_currency: str
    pledge_note: str
    completions: Dict[str, bool]  # {"YYYY-MM-DD": true/false}


def new_task_id() -> str:
    return datetime.utcnow().strftime("%Y%m%d%H%M%S%f")


def load_data() -> Dict:
    if not os.path.exists(DATA_PATH):
        return {"tasks": []}
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        # If file exists but is corrupted, start fresh (demo-friendly)
        data = {"tasks": []}
    data.setdefault("tasks", [])
    return data


def save_data(data: Dict) -> None:
    # Best-effort save for demo; Streamlit Cloud may reset local FS
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ----------------------------
# Account & pairing
# ----------------------------
def pair_id_from_account(account_id: int) -> int:
    # adjacent accounts map to same pair
    return account_id // 2


def gen_account_pair() -> tuple[int, int]:
    # random even + next odd
    base = random.randrange(100000, 999998, 2)
    return base, base + 1


# ----------------------------
# Task / completion logic
# ----------------------------
def get_done(task: Task, day: date) -> bool:
    return bool(task.completions.get(day.isoformat(), False))


def set_done(task: Task, day: date, done: bool) -> None:
    task.completions[day.isoformat()] = bool(done)


def current_streak(task: Task, up_to: date) -> int:
    start = date.fromisoformat(task.start_date)
    d = up_to
    streak = 0
    while d >= start:
        if get_done(task, d):
            streak += 1
            d -= timedelta(days=1)
        else:
            break
    return streak


def total_done(task: Task) -> int:
    return sum(1 for v in task.completions.values() if v)


# ----------------------------
# "AI" suggestions (rule-based; demo)
# ----------------------------
def suggest_task_improvements(title: str, description: str, target_days: int) -> List[str]:
    tips: List[str] = []
    text = (title + " " + description).lower()

    if len(title.strip()) < 4:
        tips.append("标题可以更具体一点（行为 + 强度 + 场景），例如：‘晚饭后散步 10 分钟’。")

    pressure_words = ["必须", "绝对", "一定要", "不能失败", "惩罚", "罚"]
    if any(w in description for w in pressure_words):
        tips.append("措辞有点“压力型”。可以改成承诺式表达：‘尽量做到；没做到就复盘原因’，更可持续。")

    if "运动" in text and not any(x in text for x in ["分钟", "步", "km", "千米", "次"]):
        tips.append("运动类 task 建议加一个最低标准（分钟/步数/次数），降低执行门槛。")

    if "早睡" in text and not any(x in text for x in ["点", "pm", "am", "22", "23", "21"]):
        tips.append("作息类 task 建议给一个最小可行目标，例如：‘23:30 前上床’。")

    if target_days >= 14:
        tips.append("目标天数较长。早期验证建议先做 5–7 天一个小周期，成功后再延长。")

    tips.append("建议把 task 设计成“最小可行版本”：再忙也能完成；第 3 天允许你们小调整一次。")
    tips.append("可以加一句：‘如果没完成，原因是什么/下次怎么更容易’，把失败变成信息而不是负担。")
    return tips


# ----------------------------
# UI
# ----------------------------
st.set_page_config(page_title="Relationship Tasks MVP", page_icon="🤝", layout="wide")
st.title("🤝 关系驱动的健康任务 MVP（Demo）")
st.caption("进入后生成/输入账号，两个人共享同一对关系空间。无社交、无排行榜、AI 只给建议。")

data = load_data()

with st.sidebar:
    st.header("进入方式（无注册）")

    mode = st.radio("你有没有账号？", options=["我有账号", "我没有账号"], horizontal=True)

    if mode == "我有账号":
        acc = st.text_input("输入你的账号编号", placeholder="例如：100123")
        if st.button("进入", use_container_width=True):
            if not acc.isdigit():
                st.error("请输入纯数字账号。")
            else:
                account_id = int(acc)
                st.session_state["account_id"] = account_id
                st.session_state["pair_id"] = pair_id_from_account(account_id)
                st.success(f"进入成功：Pair {st.session_state['pair_id']}")
                safe_rerun()

    else:
        if st.button("给我生成一对账号", use_container_width=True):
            a, b = gen_account_pair()
            st.session_state["generated_a"] = a
            st.session_state["generated_b"] = b

        if "generated_a" in st.session_state:
            a = st.session_state["generated_a"]
            b = st.session_state["generated_b"]
            st.info("已生成一对账号（同一对关系空间）")
            st.code(
                f"你的账号：{a}\n"
                f"对方账号：{b}",
                language="text",
            )
            st.caption("把“对方账号”发给对方；你们分别用各自账号进入即可连接到同一空间。")

            if st.button("我用“我的账号”进入", use_container_width=True):
                st.session_state["account_id"] = a
                st.session_state["pair_id"] = pair_id_from_account(a)
                st.success(f"进入成功：Pair {st.session_state['pair_id']}")
                safe_rerun()

    st.divider()
    if st.session_state.get("pair_id") is not None:
        st.write(f"当前 Pair：**{st.session_state['pair_id']}**")
        if st.button("退出（本设备）", use_container_width=True):
            for k in ["account_id", "pair_id", "generated_a", "generated_b"]:
                st.session_state.pop(k, None)
            safe_rerun()

pair_id = st.session_state.get("pair_id")
if pair_id is None:
    st.info("请先在左侧进入：有账号就输入账号；没有账号就生成一对账号并进入。")
    st.stop()

# Load tasks and filter by pair
tasks: List[Task] = []
for raw in data.get("tasks", []):
    raw.setdefault("pair_id", -1)
    raw.setdefault("description", "")
    raw.setdefault("pledge_enabled", False)
    raw.setdefault("pledge_amount", 0.0)
    raw.setdefault("pledge_currency", "NOK")
    raw.setdefault("pledge_note", "")
    raw.setdefault("completions", {})
    tasks.append(Task(**raw))

pair_tasks = [t for t in tasks if t.pair_id == pair_id]

left, right = st.columns([1.2, 1])

with left:
    st.subheader("➕ 创建一个 task（你给对方 / 对方给你）")

    creator = st.selectbox("谁创建这个 task？", options=["对方", "我"], index=0)
    title = st.text_input("Task 标题", placeholder="例如：午饭后走 10 分钟")
    description = st.text_area("Task 说明（可选）", placeholder="最低标准、为什么做、没做到怎么办…", height=110)
    start_date = st.date_input("开始日期", value=date.today())
    target_days = st.number_input("目标：连续完成天数", min_value=2, max_value=60, value=5, step=1)

    pledge_enabled = st.checkbox("开启：关系承诺/奖励（可选）", value=False)
    pledge_amount = 0.0
    pledge_currency = "NOK"
    pledge_note = ""
    if pledge_enabled:
        c1, c2 = st.columns(2)
        pledge_amount = c1.number_input("金额", min_value=0.0, value=100.0, step=10.0)
        pledge_currency = c2.selectbox("币种", options=["NOK", "GBP", "EUR", "CNY"], index=0)
        pledge_note = st.text_input("备注", placeholder="例如：连续 5 天完成就给红包/请吃饭/买书…")

    if st.button("创建 task", type="primary"):
        if not title.strip():
            st.error("请填写 Task 标题。")
        else:
            t = Task(
                id=new_task_id(),
                pair_id=int(pair_id),
                title=title.strip(),
                description=description.strip(),
                created_by=creator,
                created_at=datetime.utcnow().isoformat(timespec="seconds"),
                start_date=start_date.isoformat(),
                target_days=int(target_days),
                pledge_enabled=bool(pledge_enabled),
                pledge_amount=float(pledge_amount),
                pledge_currency=str(pledge_currency),
                pledge_note=str(pledge_note).strip(),
                completions={},
            )
            data["tasks"].insert(0, asdict(t))
            save_data(data)
            st.success("已创建。")
            safe_rerun()

    st.divider()
    st.subheader("📌 当前 Pair 的 tasks")

    if not pair_tasks:
        st.info("这个 Pair 还没有 task。先创建一个。")
        st.stop()

    option_map = {f"{t.title}（来自：{t.created_by}）": t.id for t in pair_tasks}
    selected_label = st.selectbox("选择一个 task", options=list(option_map.keys()))
    selected_id = option_map[selected_label]
    task = next(t for t in pair_tasks if t.id == selected_id)

    st.markdown(f"### {task.title}")
    if task.description:
        st.write(task.description)

    st.write(f"创建者：**{task.created_by}** · 开始：**{task.start_date}** · 目标：**{task.target_days} 天连续完成**")

    if task.pledge_enabled:
        st.success(
            f"🤝 承诺/奖励：{task.pledge_amount:g} {task.pledge_currency}  | 备注：{task.pledge_note or '（无）'}"
        )
        st.caption("这是关系里的自愿承诺，不参与排名、不对外展示。")

    st.divider()
    st.subheader("✅ 今日完成了吗？")
    today_done = st.checkbox("我今天完成了这个 task", value=get_done(task, date.today()))
    set_done(task, date.today(), today_done)

    st.divider()
    st.subheader("📅 最近 14 天记录")
    start = max(date.fromisoformat(task.start_date), date.today() - timedelta(days=13))
    days = [start + timedelta(days=i) for i in range((date.today() - start).days + 1)]
    days.reverse()
    for d in days:
        cols = st.columns([1, 2])
        cols[0].write(d.isoformat())
        key = f"done_{task.id}_{d.isoformat()}"
        checked = cols[1].checkbox("完成", value=get_done(task, d), key=key)
        set_done(task, d, checked)

    st.divider()
    st.subheader("🧠 AI 建议（克制版）")
    st.caption("只提可持续性建议：不替你们做决定，也不干预你们的目标。")
    if st.button("生成建议"):
        tips = suggest_task_improvements(task.title, task.description, task.target_days)
        for i, tip in enumerate(tips, 1):
            st.write(f"{i}. {tip}")

    # Persist updates
    for i, raw in enumerate(data["tasks"]):
        if raw.get("id") == task.id:
            data["tasks"][i] = asdict(task)
            break
    save_data(data)

with right:
    st.subheader("🔎 这不是监督，是关系动力")
    st.write(
        "- 你完成 task 的主要原因是：**你在意对方**，不想让对方失望。\n"
        "- 系统不做排行榜、社交、强激励。\n"
        "- 记录的意义：帮助你们 **一起看、一起讨论、一起调整**。\n"
    )

    st.divider()
    st.subheader("📈 进度概览（当前选中 task）")
    streak = current_streak(task, date.today())
    st.metric("当前连续完成", f"{streak} 天")
    st.metric("累计完成天数", f"{total_done(task)} 天")
    if streak >= task.target_days:
        st.success("🎉 已达成这一轮目标。建议你们做一次小复盘：哪些有效、哪些要调整。")

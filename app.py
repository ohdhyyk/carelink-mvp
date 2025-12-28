
# Relationship Tasks MVP (Streamlit Demo)
# See chat for full explanation

import json
import os
import random
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from typing import Dict, List

import streamlit as st

DATA_PATH = "data.json"

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
    completions: Dict[str, bool]

def new_task_id():
    return datetime.utcnow().strftime("%Y%m%d%H%M%S%f")

def load_data():
    if not os.path.exists(DATA_PATH):
        return {"tasks": []}
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def pair_id_from_account(account_id: int) -> int:
    return account_id // 2

def gen_account_pair():
    base = random.randrange(100000, 999998, 2)
    return base, base + 1

def get_done(task, day):
    return task.completions.get(day.isoformat(), False)

def set_done(task, day, done):
    task.completions[day.isoformat()] = done

def current_streak(task, up_to):
    d = up_to
    streak = 0
    while True:
        if task.completions.get(d.isoformat(), False):
            streak += 1
            d -= timedelta(days=1)
        else:
            break
    return streak

st.set_page_config(page_title="Relationship MVP", page_icon="🤝", layout="wide")
st.title("🤝 Relationship-driven Tasks (Demo)")

data = load_data()

with st.sidebar:
    st.header("Enter")
    mode = st.radio("Do you have an account?", ["I have one", "I don't have one"])

    if mode == "I have one":
        acc = st.text_input("Account number")
        if st.button("Enter"):
            if acc.isdigit():
                acc = int(acc)
                st.session_state["pair_id"] = pair_id_from_account(acc)
                st.success("Entered")
            else:
                st.error("Digits only")

    else:
        if st.button("Generate account pair"):
            a, b = gen_account_pair()
            st.session_state["a"] = a
            st.session_state["b"] = b

        if "a" in st.session_state:
            st.code(f"Your account: {st.session_state['a']}
Partner account: {st.session_state['b']}")
            if st.button("Enter with my account"):
                st.session_state["pair_id"] = pair_id_from_account(st.session_state["a"])

pair_id = st.session_state.get("pair_id")
if pair_id is None:
    st.stop()

tasks = []
for raw in data.get("tasks", []):
    raw.setdefault("completions", {})
    tasks.append(Task(**raw))

pair_tasks = [t for t in tasks if t.pair_id == pair_id]

st.subheader("Create task")
title = st.text_input("Title")
if st.button("Create"):
    t = Task(
        id=new_task_id(),
        pair_id=pair_id,
        title=title,
        description="",
        created_by="Partner",
        created_at=datetime.utcnow().isoformat(),
        start_date=date.today().isoformat(),
        target_days=5,
        pledge_enabled=False,
        pledge_amount=0.0,
        pledge_currency="",
        pledge_note="",
        completions={}
    )
    data["tasks"].append(asdict(t))
    save_data(data)
    st.experimental_rerun()

if pair_tasks:
    t = pair_tasks[0]
    done = st.checkbox("Done today", value=get_done(t, date.today()))
    set_done(t, date.today(), done)
    st.write("Current streak:", current_streak(t, date.today()))
    for i, raw in enumerate(data["tasks"]):
        if raw["id"] == t.id:
            data["tasks"][i] = asdict(t)
    save_data(data)

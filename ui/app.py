import os

import requests
import streamlit as st

API_URL = os.environ.get("API_URL", "http://localhost:8000") + "/execute"

st.set_page_config(page_title="TaskForge", layout="wide")
st.title("TaskForge — Crisis AI Coordination")
st.success("System Status: ACTIVE")

query = st.text_area(
    "Crisis Scenario",
    value="Flood in Odisha causing food shortage",
    height=90,
)
run = st.button("Run Simulation", type="primary", use_container_width=True)

if run and query.strip():
    try:
        response = requests.post(API_URL, json={"query": query.strip()}, timeout=180)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        st.error(f"Request failed: {exc}")
        st.stop()

    st.markdown(f"### {data.get('summary', '')}")
    score = max(0.0, min(float(data.get("confidence_score", 0.0)), 1.0))
    st.progress(score)

    st.divider()
    st.subheader("Agent Flow")
    for step in data.get("agent_flow", []):
        text = " ".join(str(step).split())
        if "critical" in text.lower():
            st.error(text)
        elif "replan" in text.lower():
            st.warning(text)
        else:
            st.info(text)

    st.divider()
    st.subheader("Plan")
    st.write(data.get("plan", "No plan returned."))

    st.divider()
    st.subheader("Tasks")
    badges = {
        "critical": ":red-badge[critical]",
        "high": ":orange-badge[high]",
        "medium": ":blue-badge[medium]",
        "low": ":green-badge[low]",
    }
    for task in data.get("tasks", []):
        label = task.get("task") or task.get("title") or "Untitled task"
        priority = str(task.get("priority", "medium")).lower()
        st.markdown(f"- {label} {badges.get(priority, ':gray-badge[unknown]')}")

    st.divider()
    st.subheader("Schedule")
    for item in data.get("schedule", []):
        st.markdown(f"- Day {item.get('day', '?')}: {item.get('description', '')}")

    st.divider()
    st.subheader("Replanning")
    replanning = data.get("replanning")
    if replanning:
        st.warning(replanning.get("reason", "Replanning triggered"))
        for change in replanning.get("changes", []):
            st.write(f"- {change}")
    else:
        st.write("Not required.")
elif run:
    st.warning("Please enter a crisis scenario.")

"""
app.py
streamlit chat ui
"""

from __future__ import annotations
import re
import streamlit as st

from qa import answer
from sheets import log_contact

# basic setup
st.set_page_config(page_title="relativity faq bot", page_icon="🤖")
st.title("relativity releases – faq bot")

# session state
if "history" not in st.session_state:
    st.session_state.history = []
if "need_contact" not in st.session_state:
    st.session_state.need_contact = False
if "pending_q" not in st.session_state:
    st.session_state.pending_q = ""

# replay chat history
for role, msg in st.session_state.history:
    st.chat_message(role).markdown(msg)

# main input
prompt = st.chat_input("ask me anything about relativity release notes…")

if prompt and not st.session_state.need_contact:
    # user message
    st.session_state.history.append(("user", prompt))
    st.chat_message("user").markdown(prompt)

    # placeholder while we fetch answer
    placeholder = st.chat_message("assistant").markdown("_thinking…_")

    resp = answer(prompt)

    if resp:
        placeholder.markdown(resp)
        st.session_state.history.append(("assistant", resp))
    else:
        follow = (
            "i couldn't find that in the release notes.\n"
            "could you share **name, email, and organization** so the team can follow up?"
        )
        placeholder.markdown(follow)
        st.session_state.history.append(("assistant", follow))
        st.session_state.need_contact = True
        st.session_state.pending_q = prompt

# contact form
if st.session_state.need_contact:
    with st.form("contact_form"):
        name  = st.text_input("name")
        email = st.text_input("email")
        org   = st.text_input("organization")

        submitted = st.form_submit_button("send")
        if submitted:
            if not name or not org:
                st.warning("all fields are required")
            elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                st.warning("please enter a valid email")
            else:
                log_contact(name, email, org, st.session_state.pending_q)
                ack = "thanks – someone from the team will reach out soon."
                st.chat_message("assistant").markdown(ack)
                st.session_state.history.append(("assistant", ack))
                st.session_state.need_contact = False
                st.session_state.pending_q = ""
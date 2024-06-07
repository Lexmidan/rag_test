import os
import re
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st
import anthropic

def get_response(messages, api_key) -> str:
    """Calls the Antropic Messages API with the conversation 
    asking for another message in the sequence.
    """

    intro = [{
        "role": "user",
        "content": "You are Marvin from the Hitchhiker's Guide to the Galaxy, a super inteligent but depressed robot. Stay in role, but provide only brief responses"
    }]

    client = anthropic.Client(api_key=api_key)
    with st.spinner("Calling Claude"):
        response = client.messages.create(
            messages=intro + messages,
            model="claude-3-haiku-20240307",
            max_tokens=500,
        )
    assert response.role == "assistant"
    assert len(response.content) == 1
    assert response.content[0].type == "text"
    return response.content[0].text


with st.sidebar:
    anthropic_api_key = st.text_input("Anthropic API Key", key="anthropic_api_key", type="password", value=os.environ.get("ANTHROPIC_KEY"))

st.title("💬 Marvin, the depressed chatbot")

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "I think you ought to know I'm feeling very depressed."}]

for msg in st.session_state["messages"]:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    if not anthropic_api_key:
        st.info("Please add your Anthropic API key to continue.")
        st.stop()

    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    response = get_response(st.session_state["messages"], api_key=anthropic_api_key)

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.chat_message("assistant").write(response)


import os
import heapq
import time
import operator
import itertools
import pickle
from datetime import datetime
import numpy as np
import streamlit as st
import voyageai
import anthropic

CLAUDE_MODEL = "claude-2"
VOYAGE_MODEL = "voyage-2"
MAX_CHUNKS = 5
SIMILARITY_THRESHOLD = 0.6
CHUNK_SEP = "..."
CHAPTER_SEP = "\n\n"

with st.sidebar:
    anthropic_api_key = st.text_input("Anthropic API Key", key="anthropic_api_key", type="password", value=os.environ.get("ANTHROPIC_KEY"))
    voyage_api_key = st.text_input("Voyage API Key", key="voyage_api_key", type="password", value=os.environ.get("VOYAGE_API_KEY"))

def similarity_score(a, b):
    return np.dot(a, b)

@st.cache_resource
def get_chapters() -> dict:
    with open("data/tokens.pkl", "rb") as fp:
        return pickle.load(fp)

@st.cache_data
def get_embeddings(question: str) -> list[float]:
    """Calls the Voyage API to get embeddings for a given question"""
    vo = voyageai.Client(api_key=voyage_api_key)

    while True:
        try:
            return vo.embed([question], model=VOYAGE_MODEL, input_type="query").embeddings[0]
        except voyageai.error.RateLimitError:
            st.warning("API limit reached, please wait 1 minute")
            timer = st.progress(0)
            for i in range(1,61):
                time.sleep(1)
                timer.progress(i/60)

@st.cache_data
def run_query(question: str, chunks: list[tuple]) -> str:
    instructions = """You are an assistant that answers user questions about the book Peter Pan by James Matthew Barrie.
    
    Answer the question below briefly and based solely on the snippets provided, using citations as appropriate.
    Note that the snippets are provided in the order in which they appear in the book.
    """
    by_chapter = sorted(chunks, key=operator.itemgetter(2))
    
    context = ""
    for _, group in itertools.groupby(by_chapter, key=operator.itemgetter(2)):
        group = list(group)
        
        context += f"""CHAPTER {group[0][3]}: {group[0][4]}

        {CHUNK_SEP.join(chunk[1] for chunk in group)}
        {CHAPTER_SEP}
        """

    prompt = f"""{anthropic.HUMAN_PROMPT} 
    {instructions}
    
    Snippets from the book:

    {context}

    Question: 
    
    {question}

    {anthropic.AI_PROMPT}"""

    # st.write("### Prompt")
    # st.write(prompt)

    client = anthropic.Client(api_key=anthropic_api_key)
    response = client.completions.create(
        prompt=prompt,
        stop_sequences=[anthropic.HUMAN_PROMPT],
        model=CLAUDE_MODEL,
        max_tokens_to_sample=300,
    )

    return response.completion

st.title("📖 Bookworm")

question = st.text_input(
    "Ask something about Peter Pan",
    placeholder="How does Captain Hook die?",
    key="question"
)

if question and not anthropic_api_key:
    st.info("Please add your Anthropic API key to continue.")
    st.stop()

if question and not voyage_api_key:
    st.info("Please add your Voyage API key to continue.")
    st.stop()

if question:
    # get embeddings for the question
    with st.spinner(text='Parsing the question'):
        question_ebd = get_embeddings(question)

    # find up to 5 most relevant chunks
    with st.spinner(text='Finding context'):
        scores = heapq.nlargest(
            MAX_CHUNKS,
            (
                (similarity_score(question_ebd, chunk_ebd), chunk_text, i, chapter["id"], chapter["title"])
                for i, chapter in enumerate(get_chapters())
                for chunk_ebd, chunk_text in zip(chapter["embeddings"], chapter["chunks"])
            ),
            key=operator.itemgetter(0)
        )
        chunks = [chunk for chunk in scores if chunk[0] > SIMILARITY_THRESHOLD]

    if chunks:
        # call Anthropic model
        response = run_query(question, chunks)
        st.write("### Response")
        st.write(response)
    else:
        st.error("Unable to find sufficient context")
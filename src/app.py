import os
import re
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st
import anthropic


with st.sidebar:
    anthropic_api_key = st.text_input("Anthropic API Key", key="anthropic_api_key", type="password", value=os.environ.get("ANTHROPIC_KEY"))

@st.cache_data
def run_query(question: str) -> str:
    hardcoded_context = """
    Assume a database about TV shows and movies on Netflix with the following tables and columns exists:

    titles
    * show_id (string): Unique ID for every Movie / TV Show (example: "s8804")
    * type (string): Identifier - A Movie or TV Show (examples: "Movie", "TV Show")
    * title (string): Title of the Movie / TV Show (example: "Jailbirds New Orleans")
    * director (string): Director of the Movie (example: "Rajiv Chilaka")
    * starring (string): Actors involved in the movie / show (example: "David Attenborough")
    * country (string): Country where the movie / show was produced (example: "Unites States")
    * date_added (date): Date it was added on Netflix (example: "2021-09-24")
    * release_year (int): Actual Release year of the move / show (example: 2022)
    * rating (string): TV Rating of the movie / show (example: "TV-MA")
    * duration (string): Total Duration - in minutes or number of seasons (examples: "2 Seasons")
    * listed_in (string): Categories in which the show is listed (example: "Docuseries, Reality TV")
    * description (string): Description of the Movie / TV show (example: "Dragged from civilian life, a former superhero...")

    Generate a SQL command between <sql> and </sql> that answers user's question.
    """

    prompt = f"""{anthropic.HUMAN_PROMPT} In case you don't have the information in the context provided, please respond with 'I don't know'.
    <context>
    {hardcoded_context}
    </context>
    <question>
    {question}
    </question>
    {anthropic.AI_PROMPT}"""

    st.write(f"Calling Claude at {datetime.now()}")

    client = anthropic.Client(api_key=anthropic_api_key)
    response = client.completions.create(
        prompt=prompt,
        stop_sequences=[anthropic.HUMAN_PROMPT],
        model="claude-2",
        max_tokens_to_sample=100,
    )
    return response.completion

st.title("📝 Netflix Q&A with Anthropic")

question = st.text_input(
    "Ask something about Netflix shows",
    placeholder="What is the most recent movie with Bruce Willis in it?",
    key="question"
)

if question and not anthropic_api_key:
    st.info("Please add your Anthropic API key to continue.")
    st.stop()

if question:
    # call Anthropic model
    response = run_query(question)
    st.write("### Response")
    st.write(response)

    # Disply the answer
    st.write("### Query")
    if match := re.search(r"<sql>(.*)</sql>", response, re.DOTALL):
        query = match.group(1)
        st.write(query)

        # Run the query and display the result
        st.write("### Result")
        with sqlite3.connect('data/netflix_titles.db') as conn:
            st.write(pd.read_sql(query, conn))
    else:
        st.warning("No query found")


        
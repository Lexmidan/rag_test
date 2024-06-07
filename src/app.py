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
    You are given a database about TV shows and movies on Netflix with the following table and columns in it.

    table name: titles

    columns:
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
    * listed_in (string): Comma separated list of categories in which the show is listed (example: "Docuseries, Reality TV")
    * description (string): Description of the Movie / TV show (example: "Dragged from civilian life, a former superhero...")

    """

    prompt = f"""{anthropic.HUMAN_PROMPT} You must generate an SQL query that would help a user with his question in the <question> tag. Use additional info in <context>. 

    Respond ONLY with the SQL code between a pair of <sql> and </sql> tags. Do not output any other text, description or explanation. See <examples> for reference.

    <examples>
        <example>
            <question>How many French TV shows are there?</question>
            <answer><sql>SELECT COUNT(*) FROM titles WHERE type = 'TV Show' AND country = 'France';</sql></answer>
        </example>
        <example>
            <question>What is the current weather in Paris?</question>
            <answer>I don't know</answer>
        </example>
        <example>
            <question>In what movie did Leonardo DiCaprio appear together with Kate Winslet? Display name, director and year or release</question>
            <answer><sql>SELECT title, director, release_year FROM titles WHERE starring LIKE '%Leonardo DiCaprio%' AND starring LIKE '%Kate Winslet%'</sql></answer>
        </example>
        <example>
            <question>Who won the 2024 Ice Hockey Championship?</question>
            <answer>I don't know</answer>
        </example>
        <example>
            <question>List the titles, actors and descriptions of the 5 most recent TV shows from the US</question>
            <answer><sql> SELECT title, starring, description FROM titles WHERE type = 'TV Show' AND country = 'United States' ORDER BY date_added DESC LIMIT 5</sql></answer>
        </example>
        <example>
            <question>Who will be the next US president?</question>
            <answer>I don't know</answer>
        </example>
    </examples>

    <context>
    {hardcoded_context}
    </context>
    <question>
    {question}
    </question>
    {anthropic.AI_PROMPT}<answer>"""

    st.write(f"Calling Claude at {datetime.now()}")

    client = anthropic.Client(api_key=anthropic_api_key)
    response = client.completions.create(
        prompt=prompt,
        stop_sequences=[anthropic.HUMAN_PROMPT, "</answer>"],
        model="claude-2",
        max_tokens_to_sample=300,
    )
    return response.completion


@st.cache_data
def check_querry(llm_output: str) -> str:
    prompt = f"""{anthropic.HUMAN_PROMPT} You will be given a chatbot output. Check if it contain any legit SQL query. If it does extract it and return JUST the query. If it doesn't contain any query return 'SELECT 1 WHERE 1 = 0;' 

    Respond ONLY with the SQL code between a pair of <sql> and </sql> tags. Do not output any other text, description or explanation. See <examples> for reference.

    <examples>
        <example>
            <output>Certainly! I can help you to build the querry. Here it is <sql>SELECT COUNT(*) FROM titles WHERE type = 'TV Show' AND country = 'France';</sql> </output>
            <answer><sql>SELECT COUNT(*) FROM titles WHERE type = 'TV Show' AND country = 'France';</sql></answer>
        </example>
        <example>
            <output>I don't know</output>
            <answer><sql>SELECT 1 WHERE 1 = 0;</sql></answer>
        </example>
        <example>
            <output>You can find films with Leonardo DiCaprio using this querry SELECT title, director, release_year FROM titles WHERE starring LIKE '%Leonardo DiCaprio%' AND starring LIKE '%Kate Winslet%'</sql> This querry sekects title, director and release year...</output>
            <answer><sql>SELECT title, director, release_year FROM titles WHERE starring LIKE '%Leonardo DiCaprio%' AND starring LIKE '%Kate Winslet%'</sql></answer>
        </example>
        <example>
            <output>Sorry I'm not sure how to do it</output>
            <answer><sql>SELECT 1 WHERE 1 = 0;</sql></answer>
        </example>
    </examples>

    <output>
    {llm_output}
    </output>
    {anthropic.AI_PROMPT}<answer>"""

    st.write(f"Calling Claude at {datetime.now()} for querry checking")

    client = anthropic.Client(api_key=anthropic_api_key)
    response = client.completions.create(
        prompt=prompt,
        stop_sequences=[anthropic.HUMAN_PROMPT, "</answer>"],
        model="claude-2",
        max_tokens_to_sample=300,
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

    # Check if there is a SQL query in the response, extract it and run it
    sql_query = check_querry(response)

    # Disply the answer
    st.write("### Query")
    if match := re.search(r"<sql>(.*)</sql>", sql_query, re.DOTALL):
        query = match.group(1)
        st.write(query)

        # Run the query and display the result
        st.write("### Result")
        with sqlite3.connect('data/netflix_titles.db') as conn:
            st.write(pd.read_sql(query, conn))
    else:
        st.warning("No query found")


        
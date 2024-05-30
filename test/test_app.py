"""test_app.py"""
from streamlit.testing.v1 import AppTest

def test_initia_view():
    """A user increments the number input, then clicks Add"""
    at = AppTest.from_file("src/app.py")
    at.run()

    # empty api key, no messages
    assert at.text_input("anthropic_api_key").value is None
    assert len(at.info) == 0

    # try asking a question
    question = at.text_input("question")
    question.set_value("Are there any movies from the Czech Republic?").run()

    # new message is displayed
    assert "Please add your Anthropic API key" in at.info[-1].value




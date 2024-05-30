"""test_app.py"""
from streamlit.testing.v1 import AppTest

def test_increment_and_add():
    """A user increments the number input, then clicks Add"""
    at = AppTest.from_file("src/app.py").run()
    at.number_input[0].increment().increment().run()
    at.button[0].click().run()
    assert at.markdown[0].value == "Beans counted: 2"
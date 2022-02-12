from bs4 import BeautifulSoup


def extract_html(html_string: str):
    soup = BeautifulSoup(html_string, "html.parser")
    text = soup.body.get_text().strip()
    return text
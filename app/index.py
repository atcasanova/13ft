import flask
import requests
from flask import request
from bs4 import BeautifulSoup, Comment
from urllib.parse import urlparse, urljoin

app = flask.Flask(__name__)
googlebot_headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.119 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
}
SKIP_TEXT_TRANSFORM_TAGS = {"script", "style", "textarea", "pre", "code"}
VOWELS = "aeiouAEIOU"


def replace_n_vowel_m_vowel(text):
    transformed = []
    index = 0

    while index < len(text):
        if (
            index + 3 < len(text)
            and text[index] in "nN"
            and text[index + 1] in VOWELS
            and text[index + 2] in "mM"
            and text[index + 3] in VOWELS
        ):
            first_m = "M" if text[index].isupper() else "m"
            second_m = "M" if text[index + 2].isupper() else "m"
            transformed.append(first_m + text[index + 3] + second_m + text[index + 3])
            index += 4
            continue

        transformed.append(text[index])
        index += 1

    return "".join(transformed)


def replace_r_at_word_start_or_between_letters(text):
    transformed = []

    for index, char in enumerate(text):
        if char in "rR":
            previous_is_letter = index > 0 and text[index - 1].isalpha()
            next_is_letter = index + 1 < len(text) and text[index + 1].isalpha()
            starts_word = not previous_is_letter and next_is_letter
            is_between_letters = previous_is_letter and next_is_letter

            if starts_word or is_between_letters:
                transformed.append("L" if char.isupper() else "l")
                continue

        transformed.append(char)

    return "".join(transformed)


def prank_text(text):
    return replace_r_at_word_start_or_between_letters(replace_n_vowel_m_vowel(text))


def apply_prank_text_transform(soup):
    for node in soup.find_all(string=True):
        if isinstance(node, Comment):
            continue
        if node.parent and node.parent.name in SKIP_TEXT_TRANSFORM_TAGS:
            continue
        node.replace_with(prank_text(str(node)))

def add_base_tag(html_content, original_url):
    soup = BeautifulSoup(html_content, 'html.parser')
    parsed_url = urlparse(original_url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"
    
    # Handle paths that are not root, e.g., "https://x.com/some/path/w.html"
    if parsed_url.path and not parsed_url.path.endswith('/'):
        base_url = urljoin(base_url, parsed_url.path.rsplit('/', 1)[0] + '/')
    base_tag = soup.find('base')
    
    print(base_url)
    if not base_tag:
        new_base_tag = soup.new_tag('base', href=base_url)
        if soup.head:
            soup.head.insert(0, new_base_tag)
        else:
            head_tag = soup.new_tag('head')
            head_tag.insert(0, new_base_tag)
            soup.insert(0, head_tag)

    apply_prank_text_transform(soup)
    
    return str(soup)

def bypass_paywall(url):
    """
    Bypass paywall for a given url
    """
    if url.startswith("http"):
        response = requests.get(url, headers=googlebot_headers)
        response.encoding = response.apparent_encoding
        return add_base_tag(response.text, response.url)

    try:
        return bypass_paywall("https://" + url)
    except requests.exceptions.RequestException as e:
        return bypass_paywall("http://" + url)


@app.route("/")
def main_page():
    return flask.send_from_directory(".", "index.html")


@app.route("/article", methods=["POST"])
def show_article():
    link = flask.request.form["link"]
    try:
        return bypass_paywall(link)
    except requests.exceptions.RequestException as e:
        return str(e), 400
    except Exception as exc:
        raise exc


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>", methods=["GET"])
def get_article(path):
    full_url = request.url
    parts = full_url.split("/", 4)
    if len(parts) >= 5:
        actual_url = "https://" + parts[4].lstrip("/")
        try:
            return bypass_paywall(actual_url)
        except requests.exceptions.RequestException as e:
            return str(e), 400
        except e:
            raise e
    else:
        return "Invalid URL", 400


app.run(debug=False)

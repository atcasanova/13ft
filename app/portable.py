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
META_TEXT_FIELDS = {
    ("name", "description"),
    ("name", "twitter:description"),
    ("name", "twitter:title"),
    ("property", "og:description"),
    ("property", "og:site_name"),
    ("property", "og:title"),
    ("itemprop", "description"),
    ("itemprop", "name"),
}
META_URL_FIELDS = {
    ("name", "twitter:url"),
    ("property", "og:url"),
    ("itemprop", "url"),
}


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
    index = 0

    while index < len(text):
        char = text[index]

        if char in "rR":
            previous_is_letter = index > 0 and text[index - 1].isalpha()
            next_is_letter = index + 1 < len(text) and text[index + 1].isalpha()
            starts_word = not previous_is_letter and next_is_letter
            is_between_letters = previous_is_letter and next_is_letter
            has_double_r = index + 1 < len(text) and text[index + 1] in "rR"
            is_between_vowels = (
                index > 0
                and index + 2 < len(text)
                and text[index - 1] in VOWELS
                and text[index + 2] in VOWELS
            )

            if has_double_r and is_between_vowels:
                transformed.append("L" if char.isupper() else "l")
                index += 2
                continue

            if starts_word or is_between_letters:
                transformed.append("L" if char.isupper() else "l")
                index += 1
                continue

        transformed.append(char)
        index += 1

    return "".join(transformed)


def prank_text(text):
    return replace_r_at_word_start_or_between_letters(replace_n_vowel_m_vowel(text))


def apply_prank_meta_transform(soup, proxy_url=None):
    for meta_tag in soup.find_all("meta"):
        if not meta_tag.has_attr("content"):
            continue

        for attribute_name, attribute_value in META_TEXT_FIELDS:
            if meta_tag.get(attribute_name, "").strip().lower() == attribute_value:
                meta_tag["content"] = prank_text(meta_tag["content"])
                break

        if proxy_url is not None:
            for attribute_name, attribute_value in META_URL_FIELDS:
                if meta_tag.get(attribute_name, "").strip().lower() == attribute_value:
                    meta_tag["content"] = proxy_url
                    break


def apply_prank_share_url_transform(soup, proxy_url):
    if proxy_url is None:
        return

    for link_tag in soup.find_all("link", href=True):
        rel_values = {value.lower() for value in link_tag.get("rel", [])}
        if rel_values.intersection({"canonical", "shortlink", "shorturl"}):
            link_tag["href"] = proxy_url


def apply_prank_text_transform(soup):
    for node in soup.find_all(string=True):
        if isinstance(node, Comment):
            continue
        if node.parent and node.parent.name in SKIP_TEXT_TRANSFORM_TAGS:
            continue
        node.replace_with(prank_text(str(node)))


html = """
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>13ft Ladder</title>
    <link href="https://fonts.googleapis.com/css2?family=Open+Sans&display=swap" rel="stylesheet" async>
    <style>
        body {
            font-family: 'Open Sans', sans-serif;
            background-color: #FFF;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 90vh;
            transition: background-color 0.3s, color 0.3s;
        }

        h1 {
            font-size: 1.5rem;
            margin-bottom: 20px;
            text-align: center;
            color: #333;
        }

        label {
            display: block;
            margin-bottom: 10px;
            font-weight: bold;
        }

        input[type=text] {
            padding: 10px;
            margin-bottom: 10px;
            border: 1px solid #ccc;
            border-radius: 5px;
            width: 100%;
            font-size: 1rem;
            box-sizing: border-box;
        }

        input[type="submit"] {
            padding: 10px;
            background-color: #6a0dad;
            color: #fff;
            border: none;
            border-radius: 5px;
            width: 100%;
            text-transform: uppercase;
            font-weight: 600;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }

        input[type="submit"]:hover {
            background-color: #4e0875;
        }

        /* Toggle switch styles */
        .dark-mode-toggle {
            position: absolute;
            top: 10px;
            right: 10px;
        }

        .dark-mode-toggle input {
            display: none;
        }

        .dark-mode-toggle label {
            cursor: pointer;
            text-indent: -9999px;
            width: 52px;
            height: 27px;
            background: grey;
            display: block;
            border-radius: 100px;
            position: relative;
        }

        .dark-mode-toggle label:after {
            content: '';
            position: absolute;
            top: 2px;
            left: 2px;
            width: 23px;
            height: 23px;
            background: #fff;
            border-radius: 90px;
            transition: 0.3s;
        }

        .dark-mode-toggle input:checked+label {
            background: #6a0dad;
        }

        .dark-mode-toggle input:checked+label:after {
            left: calc(100% - 2px);
            transform: translateX(-100%);
        }

        /* Responsive adjustments */
        @media only screen and (max-width: 600px) {
            form {
                padding: 10px;
            }

            h1 {
                font-size: 1.2rem;
            }
        }

        /* Dark mode styles */
        body.dark-mode {
            background-color: #333;
            color: #FFF;
        }

        body.dark-mode h1 {
            color: #FFF;
        }

        body.dark-mode input[type=text] {
            background-color: #555;
            border: 1px solid #777;
            color: #FFF;
        }

        body.dark-mode input[type="submit"] {
            background-color: #9b30ff;
        }

        body.dark-mode input[type="submit"]:hover {
            background-color: #7a1bb5;
        }
    </style>
</head>

<body>
    <div class="dark-mode-toggle">
        <input type="checkbox" id="dark-mode-toggle">
        <label for="dark-mode-toggle" title="Toggle Dark Mode"></label>
    </div>
    <form action="/article" method="post">
        <h1>Enter Website Link</h1>
        <label for="link">Link of the website you want to remove paywall for:</label>
        <input type="text" id="link" name="link" required autofocus>
        <input type="submit" value="Submit">
    </form>

    <script>
        const toggleSwitch = document.getElementById('dark-mode-toggle');
        const currentTheme = localStorage.getItem('theme') || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");

        if (currentTheme === "dark") {
            document.body.classList.add("dark-mode");
            toggleSwitch.checked = true;
        }

        toggleSwitch.addEventListener('change', function () {
            if (this.checked) {
                document.body.classList.add("dark-mode");
                localStorage.setItem('theme', 'dark');
            } else {
                document.body.classList.remove("dark-mode");
                localStorage.setItem('theme', 'light');
            }
        });
    </script>
</body>

</html>
"""

def add_base_tag(html_content, original_url, proxy_url=None):
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

    apply_prank_meta_transform(soup, proxy_url)
    apply_prank_share_url_transform(soup, proxy_url)
    apply_prank_text_transform(soup)
    
    return str(soup)

def bypass_paywall(url, proxy_url=None):
    """
    Bypass paywall for a given url
    """
    if url.startswith("http"):
        response = requests.get(url, headers=googlebot_headers)
        response.encoding = response.apparent_encoding
        return add_base_tag(response.text, response.url, proxy_url)

    try:
        return bypass_paywall("https://" + url, proxy_url)
    except requests.exceptions.RequestException as e:
        return bypass_paywall("http://" + url, proxy_url)


@app.route("/")
def main_page():
    return html


@app.route("/article", methods=["POST"])
def show_article():
    link = flask.request.form["link"]
    try:
        return bypass_paywall(link, request.url)
    except requests.exceptions.RequestException as e:
        return str(e), 400
    except e:
        raise e


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>", methods=["GET"])
def get_article(path):
    full_url = request.url
    parts = full_url.split("/", 4)
    if len(parts) >= 5:
        actual_url = "https://" + parts[4].lstrip("/")
        try:
            return bypass_paywall(actual_url, request.url)
        except requests.exceptions.RequestException as e:
            return str(e), 400
        except e:
            raise e
    else:
        return "Invalid URL", 400


app.run(host="0.0.0.0", port=5000, debug=False)

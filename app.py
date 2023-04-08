from flask import Flask


app = Flask(__name__)
@app.route("/")

def hello():
    html_string = open_html()
    return html_string

def open_html():
    with open('test.html', 'r') as f:
        return f.read()




html = '''<html>
        <head></head>
        <body>
            <a href="javascript:browseLink('https://online.personalcarecouncil.org/jsp/CIRList.jsp?id=2135', 'Link', 'scrollbars=yes,status=no,resizable=yes,toolbar=yes,location=yes')">
                Acacia Catechu
            </a>
        </body>
    </html>'''

from flask import Flask
from code_doc import development_bp  # assuming your file is named code_doc.py

app = Flask(__name__)
app.register_blueprint(development_bp, url_prefix="/")

if __name__ == "__main__":
    app.run(debug=True)

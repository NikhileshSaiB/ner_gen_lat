from flask import Flask, request, render_template, redirect
import os
from ner import *

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Handle file upload
        if "file" not in request.files:
            return redirect(request.url)
        file = request.files["file"]
        if file.filename == "":
            return redirect(request.url)

        upload_document(file)
        document_content = read_pdf_document(file.filename)
        # print(document_content)
        ner_json_result,ner_df_result,generated_text = perform_ner(document_content)
        print(generated_text)

        upload_output(ner_json_result, file.filename)

        return render_template("result.html", result=ner_df_result)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)
    # app.run(debug=True)

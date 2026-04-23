import os
import uuid
import json

from flask import Flask, request, jsonify, render_template, redirect, url_for
from psycopg2.extras import RealDictCursor
from werkzeug.utils import secure_filename
from database import get_connection

app = Flask(__name__)

# ================= CONFIG UPLOAD =================
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ================= FUNÇÃO VALIDAÇÃO =================
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ================= ROTAS =================

# Teste API
@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "API de catalogo de filmes"}), 200


# Ping
@app.route('/ping', methods=['GET'])
def ping():
    conn = get_connection()
    conn.close()
    return jsonify({"message": "pong! API Rodando!", "db": str(conn)}), 200


# Listar filmes
@app.route('/filmes', methods=['GET'])
def listar_filmes():
    sql = "SELECT * FROM filmes"
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(sql)
        filmes = cursor.fetchall()
        conn.close()
        return render_template("index.html", filmes=filmes)
    except Exception as ex:
        print('erro: ', str(ex))
        return jsonify({"message": "erro ao listar filmes"}), 500


# ================= NOVO FILME COM UPLOAD =================
@app.route("/novo", methods=["GET", "POST"])
def novo_filme():
    try:
        if request.method == "POST":
            titulo = request.form["titulo"]
            genero = request.form["genero"]
            ano = request.form["ano"]

            # pega o arquivo enviado
            if "imagem" not in request.files:
                return "Nenhuma imagem enviada"

            file = request.files["imagem"]

            if file.filename == "":
                return "Nenhuma imagem selecionada"

            if file and allowed_file(file.filename):

                # gera nome único
                extensao = file.filename.rsplit('.', 1)[1].lower()
                nome_arquivo = f"{uuid.uuid4().hex}.{extensao}"

                # cria pasta se não existir
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

                caminho = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
                file.save(caminho)

                # caminho que vai para o banco
                caminho_db = f"uploads/{nome_arquivo}"

                sql = """
                INSERT INTO filmes (titulo, genero, ano, url_capa)
                VALUES (%s, %s, %s, %s)
                """
                params = [titulo, genero, ano, caminho_db]

                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(sql, params)
                conn.commit()
                conn.close()

                return redirect(url_for("listar_filmes"))

            return "Formato inválido (apenas jpg, jpeg, png)"

        return render_template("novo_filme.html")

    except Exception as ex:
        print('erro: ', str(ex))
        return jsonify({"message": "erro ao cadastrar filme"}), 500


# ================= EDITAR FILME =================
@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar_filme(id):
    try:
        conn = get_connection()

        if request.method == "POST":
            titulo = request.form["titulo"]
            genero = request.form["genero"]
            ano = request.form["ano"]

            file = request.files.get("imagem")

            # se enviar nova imagem
            if file and file.filename != "" and allowed_file(file.filename):
                extensao = file.filename.rsplit('.', 1)[1].lower()
                nome_arquivo = f"{uuid.uuid4().hex}.{extensao}"

                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

                caminho = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
                file.save(caminho)

                caminho_db = f"uploads/{nome_arquivo}"

                sql_update = """
                UPDATE filmes
                SET titulo = %s, genero = %s, ano = %s, url_capa = %s
                WHERE id = %s
                """
                params = [titulo, genero, ano, caminho_db, id]

            else:
                # mantém imagem antiga
                sql_update = """
                UPDATE filmes
                SET titulo = %s, genero = %s, ano = %s
                WHERE id = %s
                """
                params = [titulo, genero, ano, id]

            cursor = conn.cursor()
            cursor.execute(sql_update, params)
            conn.commit()
            conn.close()

            return redirect(url_for("listar_filmes"))

        # GET → buscar filme
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        sql = "SELECT * FROM filmes WHERE id = %s"
        cursor.execute(sql, [id])
        filme = cursor.fetchone()
        conn.close()

        if filme is None:
            return redirect(url_for("listar_filmes"))

        return render_template("editar_filme.html", filme=filme)

    except Exception as ex:
        print('erro: ', str(ex))
        return jsonify({"message": "erro ao editar filme"}), 500


# ================= DELETAR =================
@app.route("/deletar/<int:id>", methods=["POST"])
def deletar_filme(id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        sql = "DELETE FROM filmes WHERE id = %s"
        cursor.execute(sql, [id])

        conn.commit()
        conn.close()

        return redirect(url_for("listar_filmes"))

    except Exception as ex:
        print('erro: ', str(ex))
        return jsonify({"message": "erro ao deletar filme"}), 500


# ================= RUN =================
if __name__ == '__main__':
    app.run(debug=True)
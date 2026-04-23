import psycopg2
import os

def get_connection():
    DATABASE_URL = os.environ.get("postgresql://neondb_owner:npg_FTGRenBtKp89@ep-empty-mode-anhr8pxl-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require")

    # PRODUÇÃO (Render + Neon)
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL)

    # LOCAL (se rodar no seu PC)
    return psycopg2.connect(
        host="localhost",
        user="postgres",
        password="1234",
        database="catalogo_filmes"
    )
import sqlite3
from datetime import date
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Controle de Gastos")

DB = "gastos.db"

def conectar():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row 
    return con 

with conectar() as con:
    con.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            categoria TEXT NOT NULL,
            data TEXT NOT NULL
        )
    """)

class GastoIn(BaseModel):
    descricao: str = Field(min_length=1)
    valor: float = Field(gt=0)
    categoria: str
    data: date

@app.get("/")
def raiz():
    return {"mensagem": "API no ar"}

@app.post("/gastos", status_code=201)
def criar(g: GastoIn):
    with conectar() as con:
        cur = con.execute(
            "INSERT INTO gastos (descricao, valor, categoria, data) VALUES (?, ?, ?, ?)",
            (g.descricao, g.valor, g.categoria, g.data.isoformat()),
        )
    return {"id": cur.lastrowid, **g.model_dump()}


@app.get("/gastos")
def listar():
    with conectar() as con:
        linhas = con.execute("SELECT * FROM gastos ORDER BY data DESC").fetchall()
    return [dict(l) for l in linhas]
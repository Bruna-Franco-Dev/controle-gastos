import sqlite3
from datetime import date
from fastapi import FastAPI, HTTPException
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


@app.delete("/gastos/{gasto_id}")
def apagar(gasto_id: int):
    with conectar() as con:
        cur = con.execute("DELETE FROM gastos WHERE id = ?", (gasto_id,))
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Gasto não encontrado")
    return {"ok": True}


@app.get("/resumo")
def resumo():
    with conectar() as con:
        por_categoria = con.execute(
            "SELECT categoria, ROUND(SUM(valor), 2) AS total "
            "FROM gastos GROUP BY categoria ORDER BY total DESC"
        ).fetchall()

        mes_atual = date.today().strftime("%Y-%m")
        total_mes = con.execute(
            "SELECT COALESCE(ROUND(SUM(valor), 2), 0) FROM gastos WHERE data LIKE ?",
            (f"{mes_atual}%",),
        ).fetchone()[0]

    return {
        "por_categoria": [dict(l) for l in por_categoria],
        "total_mes": total_mes,
    }
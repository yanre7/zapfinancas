"""Exporta os gastos do banco para CSV (abre direto no Excel em português).

Exemplos:
    python exportar.py                          # tudo -> gastos_export.csv
    python exportar.py --mes 2026-11            # só novembro de 2026
    python exportar.py --saida relatorio.csv
"""
import argparse
import csv

from dotenv import load_dotenv

load_dotenv()

import db  


def main():
    parser = argparse.ArgumentParser(description="Exporta os gastos para CSV.")
    parser.add_argument("--mes", help="filtra por mês no formato AAAA-MM")
    parser.add_argument("--saida", default="gastos_export.csv", help="arquivo de saída")
    args = parser.parse_args()

    db.init_db()
    gastos = db.listar_para_exportar(args.mes)

    # utf-8-sig + ';' + vírgula decimal = formato que o Excel brasileiro abre sem bagunça
    with open(args.saida, "w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.writer(arquivo, delimiter=";")
        escritor.writerow(["id", "data", "item", "categoria", "valor"])
        for g in gastos:
            escritor.writerow(
                [g["id"], g["criado_em"], g["item"], g["categoria"],
                 f"{g['valor']:.2f}".replace(".", ",")]
            )

    print(f"{len(gastos)} gasto(s) exportado(s) para {args.saida}")


if __name__ == "__main__":
    main()

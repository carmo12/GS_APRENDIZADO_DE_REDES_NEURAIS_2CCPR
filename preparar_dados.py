"""
Preparação da base: SSP-SP "Celulares subtraídos" 2025 -> amostra tabular roubo x furto
da cidade de São Paulo, com um registro por boletim de ocorrência.

Fonte: https://www.ssp.sp.gov.br/estatistica/consultas  (seção "Bases de Dados" > "Celulares subtraídos" > 2025)
Arquivo: CelularesSubtraidos_2025.xlsx

Uso:
    python preparar_dados.py caminho/CelularesSubtraidos_2025.xlsx

Saída:
    data/ocorrencias_sp_2025.csv   (amostra de 20.000 boletins, colunas já limpas, sem dados pessoais)
"""
import sys
import unicodedata
import re
from pathlib import Path

import pandas as pd

TAMANHO_AMOSTRA = 20_000
SEMENTE = 42

REGIOES = {
    "DEL.SEC.1º CENTRO": "Centro",
    "DEL.SEC.2º SUL": "Sul",
    "DEL.SEC.3º OESTE": "Oeste",
    "DEL.SEC.4º NORTE": "Norte",
    "DEL.SEC.5º LESTE": "Leste",
    "DEL.SEC.6º SANTO AMARO": "Santo Amaro",
    "DEL.SEC.7º ITAQUERA": "Itaquera",
    "DEL.SEC.8º SAO MATEUS": "São Mateus",
}

PERIODOS_TEXTO = {
    "De madrugada": "Madrugada",
    "Pela manhã": "Manhã",
    "A tarde": "Tarde",
    "A noite": "Noite",
    "Em hora incerta": "Hora incerta",
}

DIAS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
MARCAS = {"Apple", "Samsung", "Motorola", "Xiaomi"}


def ler_planilha(caminho: str) -> pd.DataFrame:
    """Lê a aba de dados da planilha da SSP (python-calamine é bem mais rápido que openpyxl)."""
    try:
        from python_calamine import CalamineWorkbook

        wb = CalamineWorkbook.from_path(caminho)
        nome_aba = [s for s in wb.sheet_names if s.upper().startswith("CELULAR")][0]
        linhas = wb.get_sheet_by_name(nome_aba).to_python()
        return pd.DataFrame(linhas[1:], columns=linhas[0])
    except ImportError:
        xls = pd.ExcelFile(caminho)
        nome_aba = [s for s in xls.sheet_names if s.upper().startswith("CELULAR")][0]
        return pd.read_excel(xls, sheet_name=nome_aba)


def normalizar_bairro(nome) -> str:
    """Padroniza grafias: sem acento, maiúsculas, abreviações comuns expandidas."""
    if nome is None or str(nome).strip().upper() in ("", "NULL", "NAN"):
        return "NAO INFORMADO"
    s = unicodedata.normalize("NFKD", str(nome)).encode("ascii", "ignore").decode()
    s = re.sub(r"\s+", " ", s.upper()).strip()
    s = re.sub(r"^JD\.? ", "JARDIM ", s)
    s = re.sub(r"^VL\.? ", "VILA ", s)
    s = re.sub(r"^PQ\.? ", "PARQUE ", s)
    s = s.replace("CENTRO HISTORICO DE SAO PAULO", "SE")
    return s


def periodo_do_dia(hora, periodo_texto) -> str:
    """O R.D.O. traz a hora e o S.P.J. traz só o período: unifica tudo em 5 faixas."""
    if hora is not None and str(hora) not in ("NULL", "", "nan", "NaT"):
        h = int(str(hora)[:2])
        if h < 6:
            return "Madrugada"
        if h < 12:
            return "Manhã"
        if h < 18:
            return "Tarde"
        return "Noite"
    return PERIODOS_TEXTO.get(str(periodo_texto), "Hora incerta")


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    total_linhas = len(df)

    # 1) Recorte geográfico: município do LOCAL DO FATO (circunscrição), não o da delegacia de registro
    df = df[df["NOME_MUNICIPIO_CIRC"] == "S.PAULO"].copy()

    # 2) Rótulo: só as naturezas Furto (art. 155) e Roubo (art. 157)
    df["RUBRICA"] = df["RUBRICA"].astype(str)
    df = df[df["RUBRICA"].isin(["Furto (art. 155)", "Roubo (art. 157)"])]

    # 3) Fatos ocorridos em 2025 (a planilha tem BOs de 2025 sobre fatos antigos)
    df["DATA_OCORRENCIA_BO"] = pd.to_datetime(df["DATA_OCORRENCIA_BO"].astype(str), errors="coerce")
    df = df[df["DATA_OCORRENCIA_BO"].dt.year == 2025]

    # 4) Um registro por boletim: a planilha tem uma linha por objeto/natureza
    chave = ["NOME_DELEGACIA", "ANO_BO", "NUM_BO"]
    naturezas_por_bo = df.groupby(chave)["RUBRICA"].transform("nunique")
    ambiguos = df.loc[naturezas_por_bo > 1, chave].drop_duplicates().shape[0]
    df = df[naturezas_por_bo == 1]  # BO com roubo E furto ao mesmo tempo é ambíguo: sai
    df = df.drop_duplicates(subset=chave, keep="first")

    # 5) Região: só as 8 seccionais da capital
    df = df[df["NOME_SECCIONAL_CIRC"].isin(REGIOES)]

    saida = pd.DataFrame({
        "regiao": df["NOME_SECCIONAL_CIRC"].map(REGIOES),
        "bairro": df["BAIRRO"].map(normalizar_bairro),
        "tipo_local": df["DESCR_SUBTIPOLOCAL"].astype(str).replace({"NULL": "Não informado", "Casas": "Casa"}),
        "periodo": [periodo_do_dia(h, p) for h, p in zip(df["HORA_OCORRENCIA"], df["DESCR_PERIODO"])],
        "dia_semana": df["DATA_OCORRENCIA_BO"].dt.dayofweek.map(lambda d: DIAS[d]),
        "marca_celular": df["MARCA_OBJETO"].astype(str).map(lambda m: m if m in MARCAS else "Outras"),
        "classe": df["RUBRICA"].map({"Furto (art. 155)": "furto", "Roubo (art. 157)": "roubo"}),
    })

    print(f"Linhas na planilha .................: {total_linhas:,}")
    print(f"BOs ambíguos (roubo e furto) removidos: {ambiguos:,}")
    print(f"BOs únicos de roubo/furto na capital (2025): {len(saida):,}")
    print(saida["classe"].value_counts().to_string())

    # 6) Amostra estratificada de 20 mil BOs, mantendo a proporção real roubo/furto
    from sklearn.model_selection import train_test_split

    amostra, _ = train_test_split(
        saida, train_size=TAMANHO_AMOSTRA, stratify=saida["classe"], random_state=SEMENTE
    )
    return amostra.reset_index(drop=True)


if __name__ == "__main__":
    origem = sys.argv[1] if len(sys.argv) > 1 else "data/CelularesSubtraidos_2025.xlsx"
    bruto = ler_planilha(origem)
    amostra = preparar(bruto)
    Path("data").mkdir(exist_ok=True)
    amostra.to_csv("data/ocorrencias_sp_2025.csv", index=False)
    print(f"\nAmostra salva em data/ocorrencias_sp_2025.csv: {len(amostra):,} BOs")
    print(amostra["classe"].value_counts(normalize=True).round(3).to_string())

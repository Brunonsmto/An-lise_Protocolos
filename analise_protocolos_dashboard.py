import streamlit as st
import pandas as pd

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Dashboard de Análise de Protocolos",
    page_icon="📊",
    layout="wide"
)

# --- FUNÇÕES AUXILIARES ---

def carregar_dados_upload(arquivo_csv, arquivo_xlsx):
    """
    Carrega e processa os dados a partir dos arquivos enviados pelo usuário.
    Retorna dois DataFrames.
    """
    try:
        # --- CORREÇÃO APLICADA AQUI ---
        # Agora lemos as colunas pela sua POSIÇÃO, não pelo nome no cabeçalho.
        # header=None: Informa ao Pandas que o arquivo não tem linha de cabeçalho.
        # usecols=[2, 19]: Pega a 3ª (índice 2) e a 20ª (índice 19) colunas.
        # sep=None: Deixa o Pandas detectar o separador (vírgula ou ponto e vírgula)
        # engine='python': Necessário para o sep=None funcionar bem.
        df_algar = pd.read_csv(
            arquivo_csv,
            header=None,
            usecols=[2, 19],
            encoding='latin1',
            dtype={2: str}, # Aplica o tipo string à coluna de protocolo (que agora é a de índice 2)
            sep=None,
            engine='python'
        )
        df_algar.columns = ['PROTOCOLO', 'STATUS_ALGAR']

        # --- CORREÇÃO APLICADA AQUI TAMBÉM ---
        # Lendo o Excel pela posição das colunas para manter a consistência.
        # usecols=[0, 3]: Pega a 1ª (índice 0) e a 4ª (índice 3) colunas.
        df_data = pd.read_excel(
            arquivo_xlsx,
            header=None,
            usecols=[0, 3],
            dtype={3: str} # Aplica o tipo string à coluna de protocolo
        )
        # Reordena as colunas para consistência
        df_data = df_data[[3, 0]]
        df_data.columns = ['PROTOCOLO', 'STATUS_AG']

        return df_algar, df_data
    except Exception as e:
        st.error(f"Ocorreu um erro ao ler os arquivos. Verifique se as planilhas contêm dados nas colunas esperadas (A e D no Excel; C e T no CSV).")
        st.error(f"Detalhe do erro: {e}")
        return None, None


def processar_e_comparar(df_algar, df_data):
    """
    Limpa, mescla e compara os status dos protocolos.
    Retorna dois DataFrames: um com status divergentes e outro com status iguais.
    """
    # Remove linhas que foram importadas completamente vazias
    df_algar.dropna(subset=['PROTOCOLO'], inplace=True)
    df_data.dropna(subset=['PROTOCOLO'], inplace=True)

    # --- LIMPEZA E PADRONIZAÇÃO ---
    # Remove espaços em branco antes/depois dos dados nas colunas
    for df in [df_algar, df_data]:
        df['PROTOCOLO'] = df['PROTOCOLO'].astype(str).str.strip()
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].str.strip().str.upper()

    # --- MESCLAGEM DOS DADOS ---
    df_merged = pd.merge(df_algar, df_data, on='PROTOCOLO', how='inner')
    df_merged.dropna(subset=['STATUS_ALGAR', 'STATUS_AG'], inplace=True)

    # --- LÓGICA DE COMPARAÇÃO ---
    df_merged['STATUS_ALGAR_NORM'] = df_merged['STATUS_ALGAR'].replace('FECHADO', 'INSTALADO')
    df_merged['STATUS_AG_NORM'] = df_merged['STATUS_AG'].replace('FECHADO', 'INSTALADO')

    divergencias_mask = df_merged['STATUS_ALGAR_NORM'] != df_merged['STATUS_AG_NORM']
    df_divergente = df_merged[divergencias_mask][['PROTOCOLO', 'STATUS_ALGAR', 'STATUS_AG']]
    df_igual = df_merged[~divergencias_mask][['PROTOCOLO', 'STATUS_ALGAR', 'STATUS_AG']]

    return df_divergente, df_igual

# --- INTERFACE DO DASHBOARD ---

st.title("📊 Dashboard de Análise de Protocolos")
st.markdown("---")

# --- BARRA LATERAL PARA UPLOAD ---
st.sidebar.header("Carregue os Arquivos")
arquivo_algar = st.sidebar.file_uploader(
    "1. Carregue a planilha 'algar' (.csv)",
    type=["csv"]
)
arquivo_data = st.sidebar.file_uploader(
    "2. Carregue a planilha 'data' (.xlsx)",
    type=["xlsx"]
)

if arquivo_algar is not None and arquivo_data is not None:
    df_algar, df_data = carregar_dados_upload(arquivo_algar, arquivo_data)

    if df_algar is not None and df_data is not None:
        df_divergente, df_igual = processar_e_comparar(df_algar, df_data)

        # --- INFORMAÇÃO GERAL ---
        st.subheader("INFORMAÇÃO GERAL")
        col1, col2 = st.columns(2)
        col1.metric(
            "✅ STATUS COMPATÍVEL",
            len(df_igual),
            help="Quantidade de protocolos com status iguais ou equivalentes ('FECHADO' = 'INSTALADO')."
        )
        col2.metric(
            "⚠️ STATUS DIVERGENTE",
            len(df_divergente),
            help="Quantidade de protocolos com status diferentes entre as planilhas."
        )
        st.markdown("\n\n")

        # --- DASHBOARD DE DIVERGÊNCIAS ---
        st.subheader("⚠️ STATUS DIVERGENTE")
        st.markdown("Protocolos encontrados em ambas as planilhas, mas com status de venda diferentes.")
        if df_divergente.empty:
            st.success("Nenhuma divergência encontrada!")
        else:
            st.dataframe(df_divergente, use_container_width=True, hide_index=True)

        st.markdown("\n\n")

        # --- DASHBOARD DE COMPATIBILIDADES ---
        st.subheader("✅ STATUS IGUAL")
        st.markdown("Protocolos com status compatíveis em ambas as planilhas.")
        if df_igual.empty:
            st.info("Nenhum protocolo com status igual foi encontrado.")
        else:
            st.dataframe(df_igual, use_container_width=True, hide_index=True)
else:
    st.info("⬅️ Por favor, carregue os arquivos `algar.csv` e `data.xlsx` na barra lateral para iniciar a análise.")
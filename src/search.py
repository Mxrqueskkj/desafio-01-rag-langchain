# RESPONSABILIDADE: Abrir a coleção correta no PostgreSQL e recuperar os trechos mais relevantes para uma pergunta, com k=10.
# DICA DE PESQUISA: pesquise "similarity_search_with_score LangChain" e "pgvector distância de cosseno".

from langchain_core.documents import Document

from config import get_vector_store

TOP_K = 10


def search(query: str, k: int = TOP_K) -> list[tuple[Document, float]]:
    """Busca os trechos mais próximos da pergunta.

    O QUE FAZ:
        Consulta a base vetorial e devolve cada Document junto com o score
        de similaridade, sem imprimir nada e sem gerar resposta.

    COMO FUNCIONA:
        1. Obtém o vector store com get_vector_store().
        2. Chama similarity_search_with_score(query, k=k).
        3. Devolve a lista de pares (Document, score).

    RECEBE / DEVOLVE:
        Recebe: query — pergunta em texto; k — quantidade máxima de trechos.
        Devolve: list[tuple[Document, float]].

    POR ONDE COMEÇAR:
        Pesquise "similarity_search_with_score LangChain" e
        "pgvector distância de cosseno".
    """
    raise NotImplementedError("a implementar")


def format_context(results: list[tuple[Document, float]]) -> str:
    """Junta o texto dos trechos recuperados em um bloco de contexto.

    O QUE FAZ:
        Transforma a lista de resultados da busca em uma única string
        pronta para ser colocada no prompt.

    COMO FUNCIONA:
        1. Percorre a lista de resultados.
        2. Extrai o page_content de cada Document.
        3. Junta os textos com um separador claro.
        4. Devolve o contexto como uma única string.

    RECEBE / DEVOLVE:
        Recebe: results — lista de pares (Document, score).
        Devolve: str com o contexto concatenado.

    POR ONDE COMEÇAR:
        Pesquise "Python join strings" e "LangChain Document page_content".
    """
    raise NotImplementedError("a implementar")

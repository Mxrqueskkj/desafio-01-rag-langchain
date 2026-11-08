# RESPONSABILIDADE: Validar a configuração e o PDF, extrair o texto, dividir em chunks com metadados e persistir os vetores no PostgreSQL.
# DICA DE PESQUISA: pesquise "LangChain PyPDFLoader" e "RecursiveCharacterTextSplitter".

import hashlib
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import create_engine, text

from config import get_embeddings, get_vector_store, load_settings

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


def validate_environment() -> None:
    """Confere o ambiente antes de iniciar a ingestão.

    O QUE FAZ:
        Verifica se o PDF existe, se as variáveis obrigatórias estão
        preenchidas e se o banco responde antes de gerar embeddings.

    COMO FUNCIONA:
        1. Carrega as configurações com load_settings().
        2. Verifica se PDF_PATH aponta para um arquivo existente.
        3. Confere as variáveis obrigatórias e a chave do provedor.
        4. Tenta abrir uma conexão com o PostgreSQL.
        5. Interrompe com uma mensagem clara se algo estiver faltando.

    RECEBE / DEVOLVE:
        Recebe: nada.
        Devolve: None; levanta exceção quando o ambiente está inválido.

    POR ONDE COMEÇAR:
        Pesquise "pathlib Path exists Python" e
        "SQLAlchemy create_engine test connection".
    """
    settings = load_settings()
    pdf = Path(settings.pdf_path)

    if not pdf.exists():
        raise FileNotFoundError(f"PDF não encontrado: {pdf.resolve()}")
    if pdf.stat().st_size == 0:
        raise ValueError("O PDF está vazio.")

    engine = create_engine(settings.database_url)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        raise RuntimeError(f"Não foi possível conectar ao PostgreSQL: {exc}") from exc
    finally:
        engine.dispose()


def load_pdf(path: str | Path) -> list[Document]:
    """Lê o PDF página por página.

    O QUE FAZ:
        Extrai o texto do document.pdf e devolve uma lista de Documents,
        mantendo a origem e a página de cada trecho.

    COMO FUNCIONA:
        1. Converte o caminho recebido para Path.
        2. Cria um PyPDFLoader com mode="page".
        3. Chama loader.load() para extrair o texto.
        4. Devolve a lista de páginas como Documents.

    RECEBE / DEVOLVE:
        Recebe: path — caminho do arquivo PDF.
        Devolve: list[Document], com uma entrada por página.

    POR ONDE COMEÇAR:
        Pesquise "LangChain PyPDFLoader" e "PyPDFLoader mode page".
    """
    loader = PyPDFLoader(str(path), mode="page")
    pages = loader.load()

    if not pages or not any(page.page_content.strip() for page in pages):
        raise ValueError(
            "O PDF não produziu texto. Ele pode ser escaneado (imagem) e precisar de OCR."
        )

    return pages


def split_documents(pages: list[Document]) -> list[Document]:
    """Divide as páginas em chunks menores.

    O QUE FAZ:
        Quebra o texto em partes de até CHUNK_SIZE caracteres, com
        sobreposição de CHUNK_OVERLAP caracteres.

    COMO FUNCIONA:
        1. Cria um RecursiveCharacterTextSplitter com CHUNK_SIZE,
           CHUNK_OVERLAP e length_function=len.
        2. Chama split_documents(pages).
        3. Devolve os chunks gerados.

    RECEBE / DEVOLVE:
        Recebe: pages — lista de Documents vinda do PDF.
        Devolve: list[Document] com os chunks.

    POR ONDE COMEÇAR:
        Pesquise "LangChain RecursiveCharacterTextSplitter".
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )
    return splitter.split_documents(pages)


def add_metadata(chunks: list[Document]) -> list[Document]:
    """Adiciona metadados de rastreabilidade aos chunks.

    O QUE FAZ:
        Acrescenta a cada chunk a origem, a página, o índice e o hash
        do documento PDF.

    COMO FUNCIONA:
        1. Calcula o hash SHA-256 do arquivo PDF.
        2. Percorre os chunks em ordem.
        3. Adiciona source, page, chunk_index e document_hash em metadata.
        4. Devolve os chunks com os metadados atualizados.

    RECEBE / DEVOLVE:
        Recebe: chunks — lista de Documents já divididos.
        Devolve: list[Document] com metadados de rastreabilidade.

    POR ONDE COMEÇAR:
        Pesquise "LangChain Document metadata" e "hashlib sha256 Python".
    """
    settings = load_settings()
    pdf_path = Path(settings.pdf_path)
    document_hash = hashlib.sha256(pdf_path.read_bytes()).hexdigest()

    for index, chunk in enumerate(chunks):
        chunk.metadata["source"] = pdf_path.name
        chunk.metadata["page"] = chunk.metadata.get("page", 0)
        chunk.metadata["chunk_index"] = index
        chunk.metadata["document_hash"] = document_hash
        chunk.metadata["embedding_model"] = settings.embedding_model

    return chunks


def save_to_database(chunks: list[Document]) -> None:
    """Gera embeddings e grava os chunks no PostgreSQL.

    O QUE FAZ:
        Persiste o texto, os vetores e os metadados dos chunks na
        collection configurada do pgvector.

    COMO FUNCIONA:
        1. Obtém os embeddings com get_embeddings().
        2. Obtém o vector store com get_vector_store().
        3. Envia os chunks com add_documents().
        4. Confirma que a gravação terminou sem erro.

    RECEBE / DEVOLVE:
        Recebe: chunks — lista de Documents com metadados.
        Devolve: None.

    POR ONDE COMEÇAR:
        Pesquise "LangChain PGVector add_documents" e
        "langchain-postgres PGVector".
    """
    if not chunks:
        raise ValueError("Nenhum chunk para gravar.")

    store = get_vector_store()
    ids = [
        f"{chunk.metadata['document_hash']}-{chunk.metadata['chunk_index']}"
        for chunk in chunks
    ]
    store.add_documents(chunks, ids=ids)


def ingest() -> dict[str, int]:
    """Executa o fluxo completo de preparação da base.

    O QUE FAZ:
        Orquestra validação, leitura do PDF, divisão, metadados e gravação,
        devolvendo um resumo do que foi processado.

    COMO FUNCIONA:
        1. Valida o ambiente com validate_environment().
        2. Lê o PDF com load_pdf().
        3. Divide o texto com split_documents().
        4. Adiciona metadados com add_metadata().
        5. Grava no banco com save_to_database().
        6. Devolve {"pages": ..., "chunks": ...}.

    RECEBE / DEVOLVE:
        Recebe: nada.
        Devolve: dict[str, int] com as chaves "pages" e "chunks".

    POR ONDE COMEÇAR:
        Pesquise "Python função main" e "LangChain ingestão de documentos".
    """
    validate_environment()
    settings = load_settings()

    pages = load_pdf(settings.pdf_path)
    chunks = split_documents(pages)
    chunks = add_metadata(chunks)
    save_to_database(chunks)

    resumo = {"pages": len(pages), "chunks": len(chunks)}
    print(f"Ingestão concluída: {resumo['pages']} páginas, {resumo['chunks']} chunks.")
    return resumo


if __name__ == "__main__":
    ingest()

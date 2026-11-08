# RESPONSABILIDADE: Centralizar a leitura do ambiente, os nomes dos modelos, a conexão com o banco e o nome da collection usados pelos demais scripts.
# DICA DE PESQUISA: pesquise "python-dotenv load_dotenv".

import os

from dataclasses import dataclass

from dotenv import load_dotenv
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector


@dataclass
class Settings:
    """Agrupa as configurações compartilhadas por ingestão, busca e chat.

    O QUE FAZ:
        Representa em um único objeto os valores de ambiente usados pelos
        três scripts do projeto.

    COMO FUNCIONA:
        Cada campo corresponde a uma variável do .env; o preenchimento
        acontece em load_settings().

    RECEBE / DEVOLVE:
        Recebe: os valores informados na criação da instância.
        Devolve: um objeto Settings com os campos abaixo.

    POR ONDE COMEÇAR:
        Pesquise "dataclass Python" e "type hints Python".
    """

    database_url: str                  # URL de conexão com o PostgreSQL
    collection_name: str               # Nome da collection do pgvector
    pdf_path: str                      # Caminho do document.pdf
    chat_model: str                    # Modelo de linguagem usado no chat
    embedding_model: str               # Modelo de embeddings da ingestão e busca
    openai_api_key: str | None = None  # Chave da OpenAI, se for o provedor
    google_api_key: str | None = None  # Chave do Google, se for o provedor


def load_settings() -> Settings:
    """Carrega a configuração do projeto a partir do ambiente.

    O QUE FAZ:
        Lê o arquivo .env e devolve um objeto Settings com banco,
        collection, PDF, modelos e chaves.

    COMO FUNCIONA:
        1. Carrega o .env com load_dotenv().
        2. Lê DATABASE_URL, PG_VECTOR_COLLECTION_NAME, PDF_PATH,
           CHAT_MODEL, EMBEDDING_MODEL, OPENAI_API_KEY e GOOGLE_API_KEY.
        3. Confere se as variáveis obrigatórias estão preenchidas.
        4. Devolve um Settings com os valores encontrados.

    RECEBE / DEVOLVE:
        Recebe: nada.
        Devolve: Settings com a configuração centralizada.

    POR ONDE COMEÇAR:
        Pesquise "python-dotenv load_dotenv" e "os.getenv Python".
    """
    load_dotenv()

    database_url = os.getenv("DATABASE_URL", "").strip()
    collection_name = os.getenv("PG_VECTOR_COLLECTION_NAME", "").strip()
    pdf_path = os.getenv("PDF_PATH", "").strip()
    chat_model = os.getenv("CHAT_MODEL", "").strip()
    embedding_model = os.getenv("EMBEDDING_MODEL", "").strip()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    google_api_key = os.getenv("GOOGLE_API_KEY")

    obrigatorias = {
        "DATABASE_URL": database_url,
        "PG_VECTOR_COLLECTION_NAME": collection_name,
        "PDF_PATH": pdf_path,
        "CHAT_MODEL": chat_model,
        "EMBEDDING_MODEL": embedding_model,
    }
    faltando = [nome for nome, valor in obrigatorias.items() if not valor]
    if faltando:
        raise ValueError("Preencha no .env: " + ", ".join(faltando))

    if not openai_api_key and not google_api_key:
        raise ValueError("Preencha OPENAI_API_KEY ou GOOGLE_API_KEY no .env")

    return Settings(
        database_url=database_url,
        collection_name=collection_name,
        pdf_path=pdf_path,
        chat_model=chat_model,
        embedding_model=embedding_model,
        openai_api_key=openai_api_key,
        google_api_key=google_api_key,
    )


def get_embeddings() -> Embeddings:
    """Cria o objeto de embeddings usado na ingestão e na busca.

    O QUE FAZ:
        Escolhe o provedor configurado e devolve um modelo de embeddings
        compatível com a collection existente.

    COMO FUNCIONA:
        1. Carrega as configurações com load_settings().
        2. Verifica qual provedor tem chave disponível.
        3. Instancia OpenAIEmbeddings ou GoogleGenerativeAIEmbeddings.
        4. Devolve o objeto pronto para gerar vetores.

    RECEBE / DEVOLVE:
        Recebe: nada.
        Devolve: objeto Embeddings do LangChain.

    POR ONDE COMEÇAR:
        Pesquise "LangChain OpenAIEmbeddings" e
        "LangChain GoogleGenerativeAIEmbeddings".
    """
    settings = load_settings()

    if settings.openai_api_key:
        return OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=settings.openai_api_key,
        )

    if settings.google_api_key:
        return GoogleGenerativeAIEmbeddings(
            model=settings.embedding_model,
            google_api_key=settings.google_api_key,
        )

    raise ValueError("Nenhuma chave de embeddings configurada.")


def get_vector_store() -> VectorStore:
    """Abre a collection vetorial no PostgreSQL.

    O QUE FAZ:
        Devolve o acesso à base pgvector com a mesma collection e o mesmo
        modelo de embeddings usados na ingestão.

    COMO FUNCIONA:
        1. Carrega as configurações com load_settings().
        2. Cria os embeddings com get_embeddings().
        3. Conecta ao PostgreSQL usando DATABASE_URL.
        4. Devolve o vector store apontando para a collection configurada.

    RECEBE / DEVOLVE:
        Recebe: nada.
        Devolve: VectorStore conectado à base.

    POR ONDE COMEÇAR:
        Pesquise "langchain-postgres PGVector" e "PGVectorStore".
        O curso usa PGVector; a biblioteca atual recomenda PGVectorStore.
    """
    settings = load_settings()

    return PGVector(
        embeddings=get_embeddings(),
        connection=settings.database_url,
        collection_name=settings.collection_name,
        use_jsonb=True,
    )

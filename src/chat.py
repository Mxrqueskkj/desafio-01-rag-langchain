# RESPONSABILIDADE: Manter o loop de perguntas no terminal, chamar a busca, montar o prompt com o contexto e exibir a resposta da LLM.
# DICA DE PESQUISA: pesquise "LangChain PromptTemplate" e "Python loop input() no terminal".

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from config import load_settings
from search import format_context, search

REFUSAL_MESSAGE = "Não tenho informações necessárias para responder sua pergunta."


def build_prompt(context: str, question: str) -> str:
    """Monta o prompt enviado ao modelo de linguagem.

    O QUE FAZ:
        Une o contexto recuperado e a pergunta do usuário em um único
        texto, seguindo a estrutura pedida pelo desafio.

    COMO FUNCIONA:
        1. Cria a seção CONTEXTO com o texto vindo da busca.
        2. Cria a seção REGRAS com as instruções de resposta e recusa.
        3. Cria a seção EXEMPLOS com perguntas fora do contexto.
        4. Cria a seção PERGUNTA DO USUÁRIO com a pergunta recebida.
        5. Devolve o prompt completo como string.

    RECEBE / DEVOLVE:
        Recebe: context — texto concatenado dos trechos; question — pergunta.
        Devolve: str com o prompt montado.

    POR ONDE COMEÇAR:
        Pesquise "LangChain PromptTemplate" e "ChatPromptTemplate".
    """
    return f"""CONTEXTO:
{context}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."
Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."
Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
{question}

RESPONDA A "PERGUNTA DO USUÁRIO"
"""


def call_llm(prompt: str) -> str:
    """Chama o modelo de linguagem configurado.

    O QUE FAZ:
        Envia o prompt para o modelo de chat e devolve o texto da resposta.

    COMO FUNCIONA:
        1. Carrega as configurações com load_settings().
        2. Escolhe ChatOpenAI ou ChatGoogleGenerativeAI conforme o provedor.
        3. Chama o modelo com invoke(prompt).
        4. Extrai e devolve o conteúdo textual da resposta.

    RECEBE / DEVOLVE:
        Recebe: prompt — texto completo montado por build_prompt().
        Devolve: str com a resposta do modelo.

    POR ONDE COMEÇAR:
        Pesquise "LangChain ChatOpenAI invoke" e
        "LangChain ChatGoogleGenerativeAI".
    """
    settings = load_settings()

    if settings.openai_api_key:
        llm = ChatOpenAI(
            model=settings.chat_model,
            api_key=settings.openai_api_key,
            temperature=0,
        )
    elif settings.google_api_key:
        llm = ChatGoogleGenerativeAI(
            model=settings.chat_model,
            google_api_key=settings.google_api_key,
            temperature=0,
        )
    else:
        raise ValueError("Nenhuma chave de LLM configurada.")

    resposta = llm.invoke(prompt)
    conteudo = resposta.content
    return conteudo if isinstance(conteudo, str) else str(conteudo)


def answer(question: str) -> str:
    """Responde uma pergunta usando somente o contexto do PDF.

    O QUE FAZ:
        Recupera os trechos relevantes e devolve uma resposta fundamentada
        ou a frase de recusa quando não houver evidência.

    COMO FUNCIONA:
        1. Chama search(question) para recuperar os trechos.
        2. Se a lista estiver vazia, devolve REFUSAL_MESSAGE sem chamar a LLM.
        3. Junta os trechos com format_context().
        4. Monta o prompt com build_prompt().
        5. Chama call_llm() e devolve o texto.

    RECEBE / DEVOLVE:
        Recebe: question — pergunta do usuário.
        Devolve: str com a resposta ou a frase de recusa.

    POR ONDE COMEÇAR:
        Pesquise "LangChain RAG tutorial" e "retrieval augmented generation".
    """
    resultados = search(question)

    if not resultados:
        return REFUSAL_MESSAGE

    contexto = format_context(resultados)
    prompt = build_prompt(contexto, question)
    return call_llm(prompt)


def run_chat() -> None:
    """Mantém o loop de perguntas e respostas no terminal.

    O QUE FAZ:
        Lê perguntas, chama answer() e imprime as respostas até o usuário
        decidir sair.

    COMO FUNCIONA:
        1. Exibe uma mensagem inicial e o comando de saída.
        2. Lê a pergunta com input().
        3. Ignora entradas vazias.
        4. Encerra quando o usuário digitar o comando de saída.
        5. Chama answer() e imprime a resposta.
        6. Trata KeyboardInterrupt para sair de forma limpa.

    RECEBE / DEVOLVE:
        Recebe: nada.
        Devolve: None.

    POR ONDE COMEÇAR:
        Pesquise "Python loop input() no terminal" e
        "KeyboardInterrupt Python".
    """
    print("Chat RAG. Digite 'sair' para encerrar.")

    while True:
        try:
            pergunta = input("\nPergunta: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nAté logo!")
            break

        if not pergunta:
            continue

        if pergunta.lower() in {"sair", "exit", "quit"}:
            print("Até logo!")
            break

        try:
            resposta = answer(pergunta)
        except Exception as exc:
            print(f"Erro ao responder: {exc}")
            continue

        print(f"\nResposta: {resposta}")


if __name__ == "__main__":
    run_chat()

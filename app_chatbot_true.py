from dotenv import load_dotenv
import os
import openai
from langchain.chains import RetrievalQA
from langchain.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.chat_models import AzureChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
import panel as pn  # Importe a biblioteca Panel

# Carregue as variáveis de ambiente
load_dotenv()

# Defina as variáveis de ambiente (adapte para o seu ambiente)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_DEPLOYMENT_ENDPOINT = os.getenv("OPENAI_DEPLOYMENT_ENDPOINT")
OPENAI_DEPLOYMENT_NAME = os.getenv("OPENAI_DEPLOYMENT_NAME")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME")
OPENAI_DEPLOYMENT_VERSION = os.getenv("OPENAI_DEPLOYMENT_VERSION")

OPENAI_ADA_EMBEDDING_DEPLOYMENT_NAME = os.getenv("OPENAI_ADA_EMBEDDING_DEPLOYMENT_NAME")
OPENAI_ADA_EMBEDDING_MODEL_NAME = os.getenv("OPENAI_ADA_EMBEDDING_MODEL_NAME")

# Funções do Chatbot
def ask_question(qa, question):
    result = qa({"query": question})
    print("Pergunta:", question)
    print("Resposta:", result["result"])

def ask_question_with_context(qa, question, chat_history):
    query = "O que é o serviço Azure OpenAI?"
    result = qa({"question": question, "chat_history": chat_history})
    print("Resposta:", result["answer"])
    chat_history = [(query, result["answer"])]
    return chat_history

# Configuração da API OpenAI
openai.api_type = "azure"
openai.api_base = os.getenv('OPENAI_API_BASE')
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_version = os.getenv('OPENAI_API_VERSION')
llm = AzureChatOpenAI(deployment_name=OPENAI_DEPLOYMENT_NAME,
                      model_name=OPENAI_MODEL_NAME,
                      openai_api_base=OPENAI_DEPLOYMENT_ENDPOINT,
                      openai_api_version=OPENAI_DEPLOYMENT_VERSION,
                      openai_api_key=OPENAI_API_KEY,
                      openai_api_type="azure")

embeddings = OpenAIEmbeddings(deployment=OPENAI_ADA_EMBEDDING_DEPLOYMENT_NAME,
                              model=OPENAI_ADA_EMBEDDING_MODEL_NAME,
                              openai_api_base=OPENAI_DEPLOYMENT_ENDPOINT,
                              openai_api_type="azure",
                              chunk_size=1)

# Inicialização do chatbot
# Carregue o índice do Faiss na memória
vectorStore = FAISS.load_local("./data/documentation/faiss_index/", embeddings)

# Use o índice do Faiss para pesquisar o documento local
retriever = vectorStore.as_retriever(search_type="similarity", search_kwargs={"k": 2})

QUESTION_PROMPT = PromptTemplate.from_template("""Responda sempre em português. Dada a seguinte conversa e uma pergunta de acompanhamento, reformule a pergunta de acompanhamento para ser uma pergunta autônoma.

Conversa:
{chat_history}
Pergunta de acompanhamento: {question}
Pergunta autônoma:""")

qa = ConversationalRetrievalChain.from_llm(llm=llm,
                                            retriever=retriever,
                                            condense_question_prompt=QUESTION_PROMPT,
                                            return_source_documents=True,
                                            verbose=False)

chat_history = []

conversation_text = ""
# Função para carregar o banco de dados
def load_database(event):
    if event:
        # Coloque aqui o código para carregar o banco de dados
        print("Banco de dados carregado com sucesso!")

# Função para limpar o histórico da conversa
def clear_history(event):
    if event:
        chat_history.clear()
        print("Histórico da conversa limpo!")

# Função para enviar uma pergunta
def send_question(event):
    global conversation_text  # Declare a variável como global para modificá-la
    if event.new:
        question = inp.value  # Obtenha a pergunta digitada pelo usuário
        if question:
            # Chame a função do chatbot para obter a resposta aqui
            result = ask_question_with_context(qa, question, chat_history)
            
            if result and len(result) > 0:
                answer = result[0][1]  # Obtenha apenas a resposta da primeira posição da lista
                chat_history.append((question, answer))  # Adicione a pergunta e resposta ao histórico
                update_conversation_history()  # Chame a função para atualizar o histórico de conversa
            
            inp.value = ''  # Limpe o campo de entrada após o envio da pergunta



def update_conversation_history():
    global conversation_text  # Declare a variável como global para modificá-la
    conversation_text = ""  # Limpe a conversa atual
    for q, a in chat_history:
        conversation_text += f"Pergunta: {q}\nResposta: {a}\n\n"
    conversation.object = conversation_text  # Atualize a interface com a nova conversa

file_input = pn.widgets.FileInput(accept='.pdf')
button_load = pn.widgets.Button(name="Carregar BD", button_type='primary')
button_clearhistory = pn.widgets.Button(name="Limpar Histórico", button_type='warning')
inp = pn.widgets.TextInput(placeholder='Digite aqui…')
conversation = pn.pane.Markdown(conversation_text)

# Associe as funções aos eventos dos widgets
button_load.on_click(load_database)
button_clearhistory.on_click(clear_history)
inp.param.watch(send_question, 'value')

# Crie as abas e o layout da interface web
# Crie os widgets do Panel
# ...

# Adicione widgets para a aba "Conversa"
tab1 = pn.Column(
    pn.Row(inp),
    pn.layout.Divider(),
    pn.panel(conversation, loading_indicator=True, height=400),
)

tab3 = pn.Column
# Adicione widgets para a aba "Histórico de Conversa"
# Certifique-se de adaptar esta aba ao seu chatbot

tab4 = pn.Column(
    pn.Row(file_input, button_load, button_clearhistory),
    pn.layout.Divider(),
    # pn.Row(jpg_pane.clone(width=400)),
)

# Crie o painel principal
dashboard = pn.Column(
    pn.Row(pn.pane.Markdown('# ChatComSeuBotDeDados')),
    pn.Tabs(('Conversa', tab1), ('Histórico de Conversa', tab3), ('Configuração', tab4))
)
dashboard.show()
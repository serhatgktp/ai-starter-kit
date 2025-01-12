import os
import sys
import json
import base64  

sys.path.append("../") 
import streamlit as st
from src.edgar_sec import SecFiling
from dotenv import load_dotenv

PERSIST_DIRECTORY = "../data/vectordbs"
COMPANY_TICKERS_PATH = '../data/company_tickers.json'

load_dotenv('../../export.env')

@st.cache_resource
def set_retrieval_comparative_process(config):
    sec_multiturn = SecFiling(config=config)
    sec_multiturn.init_llm_model()
    sec_multiturn.create_load_vector_store()
    sec_multiturn.retrieval_comparative_process()
    return sec_multiturn

def handle_userinput(user_question: str):
    """Gets response based on user question and shows them in app

    Args:
        user_question (str): user's question
    """
    
    if user_question:
        response = st.session_state.sec_multiturn.answer_sec(user_question)
        st.session_state.chat_history.append(user_question)
        st.session_state.chat_history.append(response["output_text"])

        # List of sources
        sources = [
            f'{document.metadata["company_ticker"]} (report {document.metadata["report_type"]})'
            for document in response["input_documents"]
        ]
        
        # Create a Markdown string with each source on a new line as a numbered list with links
        sources_text = ""
        for index, source in enumerate(sources, start=1):
            source_link = source
            sources_text += (
                f'<font size="2" color="grey">{index}. {source_link}</font>  \n'
            )
            
        st.session_state.sources_history.append(sources_text)

    for question, answer, source in zip(
        st.session_state.chat_history[::2],
        st.session_state.chat_history[1::2],
        st.session_state.sources_history,
    ):
        with st.chat_message("user"):
            st.write(f"{question}")

        with st.chat_message(
            "ai",
            avatar="https://sambanova.ai/wp-content/uploads/2021/05/logo_icon-footer.svg",
        ):
            st.write(f"{answer}")
            if st.session_state.show_sources:
                with st.expander("Sources"):
                    st.markdown(
                        f'<font size="2" color="grey">{source}</font>',
                        unsafe_allow_html=True,
                    )
                    
def get_ticker_options() -> dict:
    """Gets the list of tickers supported by Edgar filing reports

    Returns:
        list: dict with tickers as keys and tickers - company names as values 
    """
    with open(COMPANY_TICKERS_PATH,'r') as file:
        company_tickers_dict = json.loads(file.read())   
    tickers_dict = {value['ticker'].lower(): f"{value['ticker']} - {value['title']}" for _, value in company_tickers_dict.items()}
    return tickers_dict
    

st.set_page_config(
    page_title="AI Starter Kit",
    page_icon="https://sambanova.ai/wp-content/uploads/2021/05/logo_icon-footer.svg",
)

if "conversation" not in st.session_state:
    st.session_state.conversation = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "sources_history" not in st.session_state:
    st.session_state.sources_history = []
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None

st.title(":orange[SambaNova] Analyst Assistant")
user_question = st.chat_input("Ask questions about your data")
handle_userinput(user_question)

tickers_dict = get_ticker_options()

with st.sidebar:
    st.title("Setup")
    st.markdown("**1. Pick your datasources**")

    ticker_company_1 = st.selectbox(
        label = "Specify first company Ticker to do Comparative QnA on most recent annual report (10-K)",
        options = tickers_dict.keys(),
        index = 0,
        format_func = lambda x: tickers_dict[x] 
    )
    
    ticker_company_2 = st.selectbox(
        "Specify second company Ticker to do Comparative QnA on most recent annual report (10-K)",
        options = tickers_dict.keys(),
        index = 1,
        format_func = lambda x: tickers_dict[x] 
    )
    
    st.markdown("**2. Load your datasource**")
    st.markdown(
        "**Note:** Depending on the size of the reports, this could take a few seconds"
    )
    
    force_reload = st.checkbox("Select if you want to force load", value=False, help="If selected, it'll recreate the data base.")
    
    if st.button("Load"):
        with st.spinner("Loading vector DB..."):
            tickers = sorted([ticker_company_1, ticker_company_2])
            path_suffix = '_'.join(tickers)
            st.session_state.sec_multiturn = set_retrieval_comparative_process(config={'persist_directory': f"{PERSIST_DIRECTORY}/multisource_{path_suffix}", 
                                                                                     'tickers': tickers, 
                                                                                     'force_reload': force_reload})
            st.toast("Database loaded")

    st.markdown("**3. Ask questions about your data!**")

    with st.expander("Additional settings", expanded=True):
        st.markdown("**Interaction options**")
        st.markdown(
            "**Note:** Toggle these at any time to change your interaction experience"
        )
        show_sources = st.checkbox("Show sources", value=True, key="show_sources")

        st.markdown("**Reset chat**")
        st.markdown(
            "**Note:** Resetting the chat will clear all conversation history"
        )
        if st.button("Reset conversation"):
            tickers = sorted([ticker_company_1, ticker_company_2])
            path_suffix = '_'.join(tickers)
            st.session_state.sec_multiturn = set_retrieval_comparative_process(config={'persist_directory': f"{PERSIST_DIRECTORY}/multisource_{path_suffix}", 
                                                                                     'tickers': tickers, 
                                                                                     'force_reload': force_reload})
            st.session_state.chat_history = []
            st.toast(
                "Conversation reset. The next response will clear the history on the screen"
            )


    

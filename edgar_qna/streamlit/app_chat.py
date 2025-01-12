import os
import sys

sys.path.append("../") 
import streamlit as st
from src.edgar_sec import SecFiling
from dotenv import load_dotenv

PERSIST_DIRECTORY = "../data/vectordbs"

load_dotenv('../../export.env')

@st.cache_resource
def set_retrieval_conversational_chain(config):
    sec_multiturn = SecFiling(config=config)
    sec_multiturn.init_llm_model()
    sec_multiturn.create_load_vector_store()
    sec_multiturn.retrieval_conversational_chain()
    return sec_multiturn

def handle_userinput(user_question):
    """Gets response based on user question and shows them in app

    Args:
        user_question (_type_): user's question
    """
    
    if user_question:
        response = st.session_state.sec_multiturn.answer_sec(user_question)
        st.session_state.chat_history.append(user_question)
        st.session_state.chat_history.append(response["answer"])

        # List of sources
        sources = [
            # f'{sd.metadata["filename"].name} (page {sd.metadata["page"]})' # original
            'metadata' # temporal
            for sd in response["source_documents"]
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

with st.sidebar:
    st.title("Setup")
    st.markdown("**1. Pick a datasource**")

    db_path = st.text_input(
        "Absolute path to your Vector DB folder",
        placeholder="E.g., /Users/<username>/Downloads/<vectordb_folder>",
    ).strip()
    
    st.markdown("**2. Load your datasource**")
    st.markdown(
        "**Note:** Depending on the size of your vector database, this could take a few seconds"
    )
    
    if st.button("Load"):
        with st.spinner("Loading vector DB..."):
            if db_path == "":
                st.error("You must provide a path", icon="🚨")
            else:
                if os.path.exists(db_path):
                    st.session_state.db_path = db_path
                    st.session_state.sec_multiturn = set_retrieval_conversational_chain(config={'persist_directory': db_path})
                    st.toast("Database loaded")

                else:
                    st.error("Database not present at " + db_path, icon="🚨")

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
            # reset create conversation chain
            db_path = st.session_state.db_path
            st.session_state.sec_multiturn = set_retrieval_conversational_chain(config={'persist_directory': db_path})
            st.session_state.chat_history = []
            st.toast(
                "Conversation reset. The next response will clear the history on the screen"
            )


    

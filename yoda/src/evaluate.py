import argparse
import json
import os

import numpy as np
from tqdm import tqdm
import yaml
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceInstructEmbeddings
from transformers import AutoTokenizer
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate


import sys

sys.path.append("../")
from utils.sambanova_endpoint import SambaNovaEndpoint
from vectordb.vector_db import VectorDb
from yoda.prompts.prompts import RAG_prompt_template, LLAMA_CHAT_PROMPT_PREFIX, LLAMA_CHAT_PROMPT_POSTFIX



load_dotenv('.env')

llm = SambaNovaEndpoint(
    base_url=os.getenv('YODA_BASE_URL'),
    project_id=os.getenv('YODA_PROJECT_ID'),
    endpoint_id=os.getenv('FINETUNED_ENDPOINT_ID'),
    api_key=os.getenv('FINETUNED_API_KEY'),
    model_kwargs={
        'do_sample': False,
        'max_tokens_to_generate': 256
    },
)

llm_baseline = SambaNovaEndpoint(
    base_url=os.getenv('YODA_BASE_URL'),
    project_id=os.getenv('YODA_PROJECT_ID'),
    endpoint_id=os.getenv('BASELINE_ENDPOINT_ID'),
    api_key=os.getenv('BASELINE_API_KEY'),
    model_kwargs={
        'do_sample': False,
        'max_tokens_to_generate': 256
    },
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/sn_expert_conf.yaml",
                        type=str, help="Path to config file")
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()

    # read config from yaml file
    with open(args.config) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    base_dir = config['src_folder']
    data_dir = config['dest_folder']
    PERSIST_DIRECTORY = os.path.join(config['vector_db_path'], 'yoda_db')
    print(f"persist directory will be stored at: {PERSIST_DIRECTORY}")
    # collect all context articles in one folder

    RAG_CONTEXT_TOP_K = config['RAG_CONTEXT_TOP_K']

    RESULTS_DIR = "./results"
    os.makedirs(RESULTS_DIR, exist_ok=True)
    RESULTS_FILE_PATH = os.path.join(RESULTS_DIR, "generations.json")

    CUSTOMPROMPT = PromptTemplate(
        template=RAG_prompt_template, input_variables=["context", "question"]
    )

    LLAMA_2_70B_CHAT_PATH = config["tokenizer_path"]
    tokenizer = AutoTokenizer.from_pretrained(LLAMA_2_70B_CHAT_PATH)

    # read in evaluation samples
    qa_eval_file = os.path.join(
        data_dir, "processed_data", "synthetic_qa_eval.jsonl")

    eval_data = []
    with open(qa_eval_file) as reader:
        for obj in reader:
            eval_data.append(eval(obj))

    results = []
    golden_retrieved_list = []

    if os.path.isdir(PERSIST_DIRECTORY):
        embedding_model = HuggingFaceInstructEmbeddings(
            query_instruction="Represent the query for retrieval: "
        )
        vectordb = VectorDb().load_vdb(persist_directory=PERSIST_DIRECTORY, embedding_model=embedding_model,
                                       db_type="chroma")
    else:
        vectordb = VectorDb().create_vdb(input_path=base_dir,
                                         output_db=PERSIST_DIRECTORY,
                                         chunk_size=config["chunk_size"],
                                         chunk_overlap=config["chunk_overlap"],
                                         db_type="chroma",
                                         recursive=True,
                                         tokenizer = tokenizer
                                         )

    retriever = vectordb.as_retriever(search_kwargs={"k": RAG_CONTEXT_TOP_K})

    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        input_key="question",
        output_key="response",
        return_source_documents=True,
    )

    qa.combine_documents_chain.llm_chain.prompt = CUSTOMPROMPT

    for example in tqdm(eval_data):
        golden_context_filepath = example["context_filepath"]
        question = example["question"]

        # Ignorant baseline with out-of-the-box llama-7b
        prompt = example["question"]
        ignorant_pred_answer = llm_baseline(prompt=LLAMA_CHAT_PROMPT_PREFIX + prompt + LLAMA_CHAT_PROMPT_POSTFIX)

        # Generate answer with question and golden context
        golden_context_prompt = example["question_with_context"]
        golden_context_answer = llm(prompt=LLAMA_CHAT_PROMPT_PREFIX + golden_context_prompt + LLAMA_CHAT_PROMPT_POSTFIX)

        # Generate answer with only question
        prompt = example["question"]
        pred_answer = llm(prompt=LLAMA_CHAT_PROMPT_PREFIX + prompt + LLAMA_CHAT_PROMPT_POSTFIX)

        # Generate answer with RAG
        response = qa(question)
        rag_answer = response['response']
        retrieved_files = list(set([met.metadata['source'] for met in response['source_documents']]))

        golden_is_retrieved = True if golden_context_filepath in retrieved_files else False

        result = {
            "question": question,
            "ignorant_pred_answer": ignorant_pred_answer,
            "pred_answer": pred_answer,
            "pred_answer_with_rag": rag_answer,
            "pred_answer_with_golden_context": golden_context_answer,
            "ground_truth_answer": example["answer"],
            "retrieved_rag_files": retrieved_files,
            "golden_context_filepath": golden_context_filepath,
            "golden_context_is_retrieved": str(golden_is_retrieved)
        }
        results.append(result)
        golden_retrieved_list.append(golden_is_retrieved)

    results.append(
        {"percentage of golden context being retrieved": np.mean(golden_retrieved_list)})
    with open(RESULTS_FILE_PATH, 'w') as file:
        json.dump(results, file, indent=4)

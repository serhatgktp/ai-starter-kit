<a href="https://sambanova.ai/">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./images/SambaNova-light-logo-1.png" height="60">
  <img alt="SambaNova logo" src="./images/SambaNova-dark-logo-1.png" height="60">
</picture>
</a>

SambaNova AI Starter Kits
====================

# Overview
SambaNova AI Starter Kits are a collection of open-source examples and guides to facilitate the deployment of AI-driven use cases in the enterprise.

To run these examples, you’ll need access to a SambaStudio environment with your models deployed to endpoints. Most code examples are written in Python, though the concepts can be applied in any language.

If you have any issues with the examples or would be willing to provide feedback, please let us know by [creating an issue](https://github.com/sambanova/ai-starter-kit/issues/new/choose) in GitHub.

# Available AI Starter Kits
|  Starter Kit | About |
| ------------ | ------------ |
| [Prompt Engineering](prompt_engineering/README.md)  |  An starting point demo for prompt engineering using Sambanova's API to experiment with diferent use case templates. It also provides useful resources to improve prompt crafting, making it an ideal entry point for those new to this AISK. |
| [EDGAR Q&A](edgar_qna/README.md)  |  An example workflow on using the SambaNova platform to answer questions about organizations using their 10-K annual reports. Includes a runnable local demo and a docker container to simplify remote deployment.  |
| [Enterprise Knowledge Retrieval](enterprise_knowledge_retriever/README.md) | A sample implementation of the semantic search workflow using the SambaNova platform to get answers to questions off your documents. Includes a runnable demo.  |
| [Web Crawled Data Retrieval](web_crawled_data_retriever/README.md) | A sample implementation of the semantic search workflow built using the SambaNova platform to get answers to your questions using website crawled information as the source. Includes a runnable demo.  |
| [Fine Tuning: SQL model](fine_tuning_sql/README.md) | A sample training recipe to build fine-tuned SQL model over Llama 7B base. |
| [Data Extraction](data_extraction/README.md) | A series of notebooks that demonstrates various methods for extracting text from documents in different input formats. |

# SambaNova Large language model endpoints usage:

## 1. Deploy your model in SambaStudio
Begin by deploying your LLM of choice (e.g. Llama 2 13B chat, etc) to an endpoint for inference in SambaStudio either through the GUI or CLI, as described in the [SambaStudio endpoint documentation](https://docs.sambanova.ai/sambastudio/latest/endpoints.html).

## 2. Integrate your model in the starter kit
Integrate your LLM deployed on SambaStudio with this AI starter kit  in two simple steps:
1. Clone this repo.
```
  git clone https://github.com/sambanova/ai-starter-kit.git
```
2. Update API information for the SambaNova LLM.

 These are represented as configurable variables in the environment variables file in sn-ai-starter-kit/<starter_kit>/export.env. For example, an endpoint with the URL
"https://api-stage.sambanova.net/api/predict/nlp/12345678-9abc-def0-1234-56789abcdef0/456789ab-cdef-0123-4567-89abcdef0123"
would be entered in the config file (with no spaces) as:
```
BASE_URL="https://api-stage.sambanova.net"
PROJECT_ID="12345678-9abc-def0-1234-56789abcdef0"
ENDPOINT_ID="456789ab-cdef-0123-4567-89abcdef0123"
API_KEY="89abcdef-0123-4567-89ab-cdef01234567"
``` 
3.  Import in your starterkit the samabanova_endponit  lanchain whaper 
``` python
from src.models.sambanova_endpoint import SambaNovaEndpoint

load_dotenv('export.env')

llm = SambaNovaEndpoint(
    model_kwargs={"do_sample": False, "temperature": 0.0},
)
```

**Note:** These AI Starter Kit cade samples are provided "as-is," and are not production-ready or supported code. Bugfix/support will be on a best-effort basis only. Code may use third-party open-source software. We recommend performing due diligence per your organization policies for use in your applications.
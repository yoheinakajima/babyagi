from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import UnstructuredHTMLLoader
from langchain.document_loaders import UnstructuredFileLoader
from langchain.document_loaders import PyPDFLoader
from langchain.document_loaders.csv_loader import CSVLoader
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.embeddings import LlamaCppEmbeddings
import os


# OS configuration
DOC_DIRECTORY = os.getenv("DOC_DIRECTORY", "")
DOCUMENT_MODEL_PATH = os.getenv("DOCUMENT_MODEL_PATH", "")
DOCUMENT_DB_PATH = "test-db"
DOC_CONTEXT = int(os.getenv("DOC_CONTEXT", 1000))
DOC_CTX_MAX = int(os.getenv("DOC_CTX_MAX", 1024))
LLAMA_THREADS_NUM = int(os.getenv("LLAMA_THREADS_NUM", 8))

doc_embeddings = ""
doc_search = ""


# Embedding documents in vector store
def document_embedding():
    if DOCUMENT_MODEL_PATH:
        doc_embeddings = LlamaCppEmbeddings(
            model_path=DOCUMENT_MODEL_PATH,
            n_ctx=DOC_CTX_MAX,
            n_threads=LLAMA_THREADS_NUM,
            n_batch=512,
            use_mlock=False,
            ) 
    else:
        doc_embeddings = OpenAIEmbeddings()

    doc_search = Chroma.from_documents(
        documents_load_and_split(chunk_size=int(DOC_CONTEXT/5)),
        doc_embeddings,
        persist_directory=DOCUMENT_DB_PATH
        )
    return doc_search


# Similiarity search for documents
def get_embedded_storage(query: str, num_extracts: str):
    return doc_search


# Read-in selectable document types from folder '/document_search' and prepare chunks for embeddeding in vector store
def documents_load_and_split(chunk_size: int):
    buffers = []
    texts = []
    documents = []
    epub_names = []
    directory = DOC_DIRECTORY
    extensions = ['.pdf', '.txt', '.csv', '.epub']  # Fügen Sie hier die gewünschten Dateitypen hinzu

    files = []
    for filename in os.listdir(DOC_DIRECTORY):
        if any(filename.endswith(ext) for ext in extensions):
            files.append(os.path.join(directory, filename))
            print(f"Found '{filename}'")

    # Embedd all document types
    for doc_name in files:
        if ".pdf" in doc_name:
            loader = PyPDFLoader(doc_name)
            texts += loader.load_and_split()
            print(f"Loading '{doc_name}'")

        if ".csv" in doc_name:
            loader = CSVLoader(doc_name)
            texts += loader.load_and_split()
            print(f"Loading '{doc_name}'")

        if ".txt" in doc_name:
            loader = UnstructuredFileLoader(doc_name)
            texts += loader.load_and_split()
            print(f"Loading '{doc_name}'")

        if ".epub" in doc_name:
            epub_names.append(doc_name)
            print(f"Locating epub '{doc_name}'")

    # The epub mode is experimental, the formats below have been designed for my test documents, but may not match yours
    # The range of the epub files and file type is hardcoded, so you have to adjust it to your needs
    for book in epub_names:
        # Try different formats (up to now only with static range and file type)
        # Extract book content with langchain unstructured HTML loader
        # TBD: Add more formats and dynamic range
        for j in range(1, 11):
            try:
                loader = UnstructuredHTMLLoader(f"{book}/OEBPS/{str(book).split(DOC_DIRECTORY)[1].split('.')[0]}-{j}.xhtml")
                print(f"Loading {book}/OEBPS/{str(book).split(DOC_DIRECTORY)[1].split('.')[0]}-{j}.xhtml")
            except:
                break
            data = loader.load()
            buffers += data
            print(f"Loaded chunk with length: {len(data)} of '{book}'")

            print(f"Loading '{book}' with {len(buffers)} part(s)")
            texts += buffers
            buffers = []
    
    # Split text into chunks and return documents
    if texts:
        text_splitter = CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=0)
        documents = text_splitter.split_documents(texts)
        print(f"Store {len(texts)} parts with chunk size: {chunk_size} and split into {len(documents)} chunks...")
    else:
        print(f'Error: No documents found.')

    return documents


# Initialize pinecone
#pinecone.init(
#    api_key=os.getenv("PINECONE_API_KEY", ""),  # find at app.pinecone.io
#    environment=os.getenv("PINECONE_ENVIRONMENT", "")  # next to api key in console
#)
#index_name = "worldhunger-table"
#doc_search = Pinecone.from_documents(epub_search(), doc_embeddings, index_name=index_name)
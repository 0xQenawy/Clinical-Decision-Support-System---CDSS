from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from src.config import CHUNK_SIZE, CHUNK_OVERLAP, RAW_DATA_DIR

def load_pdfs():
    all_pages = []
    for pdf_path in RAW_DATA_DIR.glob('*.pdf'):
        loader = PyPDFLoader(str(pdf_path))
        pages = loader.load()
        for page in pages:
            page.metadata['document_name'] = pdf_path.name
            page.metadata['page_number'] = page.metadata.get('page', 0) + 1
        all_pages.extend(pages)
    return all_pages
def chunk_documents(pages):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=['\n\n', '\n', '. ', ' ', '']
    )
    return text_splitter.split_documents(pages)

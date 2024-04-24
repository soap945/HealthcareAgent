# 首先导入所需第三方库
from langchain_community.document_loaders import (
    UnstructuredFileLoader,
    UnstructuredMarkdownLoader,
    UnstructuredWordDocumentLoader,
    PyPDFLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import VectorStore, VectorStoreRetriever
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from tqdm import tqdm
import os
from utils import get_filename, format_references


# 获取文件路径函数
# 获取文件路径函数
def get_files(dir_path: str) -> list:
    # args：dir_path，目标文件夹路径
    file_list = []
    for filepath, dirnames, filenames in os.walk(dir_path):
        # os.walk 函数将递归遍历指定文件夹
        for filename in filenames:
            # 只读取pdf
            if filename.endswith(".pdf"):
                file_list.append(os.path.join(filepath, filename))
            # 通过后缀名判断文件类型是否满足要求
            # if filename.endswith((".txt", ".md", ".docx", ".doc", ".pdf")):
            #     file_list.append(os.path.join(filepath, filename))
    return file_list


# 加载文件函数
def get_text(dir_path: str) -> list:
    # args：dir_path，目标文件夹路径
    # 首先调用上文定义的函数得到目标文件路径列表
    file_lst = get_files(dir_path)
    # docs 存放加载之后的纯文本对象
    docs = []
    # 遍历所有目标文件
    for one_file in tqdm(file_lst):
        if one_file.endswith(".txt"):
            # txt, md, docx, doc: pip install unstructured
            loader = UnstructuredFileLoader(one_file)
        elif one_file.endswith(".md"):
            loader = UnstructuredMarkdownLoader(one_file)
        elif one_file.endswith((".docx", ".doc")):
            # pip install python-docx
            loader = UnstructuredWordDocumentLoader(one_file)
        elif one_file.endswith(".pdf"):
            # pip install pypdf
            loader = PyPDFLoader(one_file)
        docs.extend(loader.load())
    return docs


def create_chroma_vectordb(
    tar_dirs: str = "./data",
    embedding_model_path: str = "./models/paraphrase-multilingual-MiniLM-L12-v2",
    persist_directory: str = "./vector_db/chroma"
):
    from langchain_community.vectorstores import Chroma

    dirs = os.listdir(tar_dirs)
    dirs = [os.path.join(tar_dirs, dir) for dir in dirs]
    dirs = [dir for dir in dirs if os.path.isdir(dir)]

    # 加载目标文件
    docs = []
    for dir_path in dirs:
        docs.extend(get_text(dir_path))

    # 对文本进行分块
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 500,
        chunk_overlap = 150
    )
    split_docs = text_splitter.split_documents(docs)

    # 加载开源词向量模型
    embeddings = HuggingFaceEmbeddings(
        model_name = embedding_model_path,
        model_kwargs = {'device': 'cuda'},
        encode_kwargs = {
            'normalize_embeddings': True
        }
    )

    # 构建向量数据库
    vectordb = Chroma.from_documents(
        documents = split_docs,
        embedding = embeddings,
        persist_directory = persist_directory  # 允许我们将persist_directory目录保存到磁盘上
    )

    # 将加载的向量数据库持久化到磁盘上
    vectordb.persist()


def load_chroma_retriever(
    embedding_model_path: str = "./models/paraphrase-multilingual-MiniLM-L12-v2",
    persist_directory: str = "./vector_db/chroma",
    similarity_top_k: int = 4,
    score_threshold: float = 0.15,
) -> VectorStoreRetriever:
    from langchain_community.vectorstores import Chroma

    # 加载开源词向量模型
    embeddings = HuggingFaceEmbeddings(
        model_name = embedding_model_path,
        model_kwargs = {'device': 'cuda'},
        encode_kwargs = {
            'normalize_embeddings': True
        }
    )

    # 加载数据库
    vectordb = Chroma(
        embedding_function = embeddings,
        persist_directory = persist_directory,
    )

    # 转换为retriever
    retriever = vectordb.as_retriever(
        search_type = "similarity_score_threshold",
        search_kwargs = {"k": similarity_top_k, "score_threshold": score_threshold}
    )

    return retriever


def create_faiss_vectordb(
    tar_dirs: str = "./data",
    embedding_model_path: str = "./models/paraphrase-multilingual-MiniLM-L12-v2",
    persist_directory: str = "./vector_db/faiss"
):
    from langchain_community.vectorstores import FAISS

    dirs = os.listdir(tar_dirs)
    dirs = [os.path.join(tar_dirs, dir) for dir in dirs]
    dirs = [dir for dir in dirs if os.path.isdir(dir)]

    # 加载目标文件
    docs = []
    for dir_path in dirs:
        docs.extend(get_text(dir_path))

    # 对文本进行分块
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 500,
        chunk_overlap = 150
    )
    split_docs = text_splitter.split_documents(docs)

    # 加载开源词向量模型
    embeddings = HuggingFaceEmbeddings(
        model_name = embedding_model_path,
        model_kwargs = {'device': 'cuda'},
        encode_kwargs = {
            'normalize_embeddings': True
        }
    )

    # 构建向量数据库
    vectordb = FAISS.from_documents(
        documents = split_docs,
        embedding = embeddings,
    )

    # 将加载的向量数据库持久化到磁盘上
    vectordb.save_local(folder_path = persist_directory)


def load_faiss_retriever(
    embedding_model_path: str = "./models/paraphrase-multilingual-MiniLM-L12-v2",
    persist_directory: str = "./vector_db/faiss",
    similarity_top_k: int = 4,
    score_threshold: float = 0.15,
) -> VectorStoreRetriever:
    from langchain_community.vectorstores import FAISS
    from langchain_community.vectorstores.utils import DistanceStrategy

    # 加载开源词向量模型
    embeddings = HuggingFaceEmbeddings(
        model_name = embedding_model_path,
        model_kwargs = {'device': 'cuda'},
        encode_kwargs = {
            'normalize_embeddings': True
        }
    )

    # 加载数据库
    vectordb = FAISS.load_local(
        folder_path = persist_directory,
        embeddings = embeddings,
        allow_dangerous_deserialization = True, # 允许读取pickle
        distance_strategy = DistanceStrategy.MAX_INNER_PRODUCT,  # refer: https://github.com/InternLM/HuixiangDou/blob/main/huixiangdou/service/retriever.py
        normalize_L2 = False,
    )

    # search_type: 'similarity', 'similarity_score_threshold', 'mmr'
    retriever = vectordb.as_retriever(
        search_type = "similarity_score_threshold",
        search_kwargs = {"k": similarity_top_k, "score_threshold": score_threshold, "fetch_k": similarity_top_k  * 5}
    )

    return retriever


def similarity_search(
    retriever: VectorStoreRetriever,
    query: str,
) -> tuple[str, str]:
    # similarity search
    documents = retriever.invoke(query)
    documents_str = "\n".join([doc.page_content for doc in documents])
    # 获取参考文档并去重
    references = list(set([get_filename(doc.metadata['source']) for doc in documents]))
    references_str = format_references(references)
    return documents_str, references_str


def test_chroma():
    # create_chroma_vectordb()

    retriever = load_chroma_retriever()

    documents_str, references_str = similarity_search(retriever, "Eye Pressure Lowering Effect of Vitamin C")
    print(f"{len(documents_str) = }")
    print(references_str)

    print("-"*100)

    documents_str, references_str = similarity_search(retriever, "今天吃了吗")
    print(f"{len(documents_str) = }")
    print(references_str)


def test_faiss():
    # create_faiss_vectordb()
    retriever = load_faiss_retriever()

    documents_str, references_str = similarity_search(retriever, "Eye Pressure Lowering Effect of Vitamin C")
    print(f"{len(documents_str) = }")
    print(references_str)

    print("-"*100)

    documents_str, references_str = similarity_search(retriever, "今天吃了吗")
    print(f"{len(documents_str) = }")
    print(references_str)


if __name__ == "__main__":
    test_chroma()
    print("#" * 100)
    test_faiss()


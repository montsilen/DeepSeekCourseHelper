from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

def load_vectorstore():
    embedding = HuggingFaceEmbeddings(model_name="BAAI/bge-base-zh-v1.5")
    vectorstore = FAISS.load_local(
        "course_vector_store",
        embedding,
        allow_dangerous_deserialization=True
    )
    return vectorstore.as_retriever(search_kwargs={"k": 10})

def basic_size():
    from langchain_text_splitters import CharacterTextSplitter
    text_splitter = CharacterTextSplitter(chunk_size=500,chunk_overlap=50)
    docs = text_splitter.create_documents(["Gen Ai is leading area in IT sector , it replace humans but create new opportunity"])
    print(docs)

from langchain_text_splitters import RecursiveCharacterTextSplitter
text_splitter = RecursiveCharacterTextSplitter(chunk_size=800,chunk_overlap=100,separators=["\n\n","\n"," ",""])
docs=text_splitter.split_documents(["Gen Ai is leading area in IT sector "," it replace humans but create new opportunity"])
print(docs)
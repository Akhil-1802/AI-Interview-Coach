from langchain_community.document_loaders import PyPDFLoader


def load_pdf(filePath : str) -> str:
    data = PyPDFLoader(filePath)
    result = data.load()
    pdf_data = ""

    for i in range(0,len(result)):
        pdf_data += result[i].page_content + "\n"
    return pdf_data

# print(load_pdf("helper/Main_Resume.pdf"))
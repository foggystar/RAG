from langchain_community.document_loaders import PDFMinerPDFasHTMLLoader
import os
from bs4 import BeautifulSoup
import re
from langchain.docstore.document import Document

def load_pdf(
        pdf_path: str
):

    # 如果传入的是相对路径，则转换为绝对路径
    if not os.path.isabs(pdf_path):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        pdf_path = os.path.join(os.path.dirname(current_dir), pdf_path)

    loader = PDFMinerPDFasHTMLLoader(pdf_path)


    data = loader.load()[0]   # entire pdf is loaded as a single Document
    
    soup = BeautifulSoup(data.page_content,'html.parser')
    content = soup.find_all('div')
    
    cur_fs = None
    cur_text = ''
    snippets = []   # first collect all snippets that have the same font size
    for c in content:
        sp = c.find('span')
        if not sp:
            continue
        st = sp.get('style')
        if not st:
            continue
        fs = re.findall(r'font-size:(\d+)px',st)
        if not fs:
            continue
        fs = int(fs[0])
        if not cur_fs:
            cur_fs = fs
        if fs == cur_fs:
            cur_text += c.text
        else:
            snippets.append((cur_text,cur_fs))
            cur_fs = fs
            cur_text = c.text
    snippets.append((cur_text,cur_fs))
    # Note: The above logic is very straightforward. One can also add more strategies such as removing duplicate snippets (as
    # headers/footers in a PDF appear on multiple pages so if we find duplicatess safe to assume that it is redundant info)
    # print(snippets)


    
    cur_idx = -1
    semantic_snippets = []
    current_page = 1  # 初始化页码计数器
    # Assumption: headings have higher font size than their respective content
    for s in snippets:
        # 检测换页符或页面分隔符，更新页码
        if '\f' in s[0] or 'page' in s[0].lower():
            current_page += 1
        
        # if current snippet's font size > previous section's heading => it is a new heading
        if not semantic_snippets or s[1] > semantic_snippets[cur_idx].metadata['heading_font']:
            metadata={'heading':s[0], 'content_font': 0, 'heading_font': s[1], 'page_number': current_page}
            metadata.update(data.metadata)
            semantic_snippets.append(Document(page_content='',metadata=metadata))
            cur_idx += 1
            continue
        
        # if current snippet's font size <= previous section's content => content belongs to the same section (one can also create
        # a tree like structure for sub sections if needed but that may require some more thinking and may be data specific)
        if not semantic_snippets[cur_idx].metadata['content_font'] or s[1] <= semantic_snippets[cur_idx].metadata['content_font']:
            semantic_snippets[cur_idx].page_content += s[0]
            semantic_snippets[cur_idx].metadata['content_font'] = max(s[1], semantic_snippets[cur_idx].metadata['content_font'])
            continue
        
        # if current snippet's font size > previous section's content but less tha previous section's heading than also make a new 
        # section (e.g. title of a pdf will have the highest font size but we don't want it to subsume all sections)
        metadata={'heading':s[0], 'content_font': 0, 'heading_font': s[1], 'page_number': current_page}
        metadata.update(data.metadata)
        semantic_snippets.append(Document(page_content='',metadata=metadata))
        cur_idx += 1

    # print(semantic_snippets[0].page_content)
    # print(semantic_snippets[0].metadata)
    return semantic_snippets
import streamlit as st

text_area = st.text_area("tabela de componentes")
serie_text = st.text_input("serie associada")

import re

def split_text_into_columns(text):
    pattern = r'\w - (\d+) - (.*?)\s*-\d+\s*'
    matches = re.findall(pattern, text)
    
    columns = {}
    for match in matches:
        columns.update({match[1]: match[0]})
    
    return columns



columns = split_text_into_columns(text_area)
st.json(columns)

# for turma_abrv  in eval(serie_text):
#     print(turma_abrv)
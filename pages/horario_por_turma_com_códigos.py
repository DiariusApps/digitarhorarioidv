import streamlit as st
import httpx
import pandas as pd
import pymongo
from replaced import reversed_dic_comps
from comps_code import dc_comps_code
st.set_page_config(layout="wide")
# secretes
import os
try:
    cred = os.environ['cred_service_name']
    chdata = os.environ['chdata']
    colecz = os.environ['colecz']
    project_id = os.environ['project_id']
    school = os.environ['id_school']
except:
    cred = st.secrets["cred_service_name"]
    chdata = st.secrets["chdata"]
    colecz = st.secrets["colecz"]
    project_id = st.secrets["project_id"]
    school = st.secrets["id_school"]

client = pymongo.MongoClient(cred)
db = client[chdata]
collection = db[colecz]
# make a request to the server to freeze the classes
def freeze_classes():
    from data import from_ch_maker
    return from_ch_maker

def on_change():
    del st.session_state.json
    
def principal():
    st.title("DISTRIBUIÇÃO DAS AULAS")

    if st.session_state.get("json") is None:
        username = project_id.split('__')[0]
        project_name = project_id.split('__')[1]
        req = freeze_classes()
        json = req[-1]
        pro = req[-2]
        st.session_state.json = json
        st.session_state.lprofs = pro
        st.session_state.ch_individuais = req[0][0]
        alias_col = db['aliases']
        alias = alias_col.find_one({'_id': project_id})
        st.session_state.alias = alias['aliases']

        
    json = st.session_state.json
    ch_individuais = st.session_state.ch_individuais
    matrículas = [item['matricula'] for item in st.session_state.lprofs if item['matricula'] in ch_individuais.keys()]
    dict_matrícula_apelido = {item['matricula']:item['apelido'] for item in st.session_state.lprofs if item['matricula'] in ch_individuais.keys()}
    assert len(matrículas) == len(dict_matrícula_apelido)
    turnos = ['DIURNO', 'NOTURNO']
    turno_choice = st.selectbox("Selecione o turno", turnos, on_change=on_change)
    dict_turno = {
        'DIURNO': ['MAT', 'INT7H'],
        'NOTURNO':['NOT']
    }
    turmas =  {subkey:json[key][subkey] for key in json for subkey in json[key] if key in dict_turno[turno_choice]}
    turmas_do_turno = turmas.keys()
    selected_turma = st.selectbox("Selecione o dia da semana", turmas_do_turno)
    if 'NOT' in selected_turma:
        dc_comps = dc_comps_code['NOT']
    elif 'RFM' in selected_turma:
        dc_comps = dc_comps_code['RFM']
    elif 'INT' in selected_turma:
        dc_comps = dc_comps_code['INT']
    else:
        dc_comps = dc_comps_code['NEM']
    df_data = [['-' for _ in ['SEG', 'TER', 'QUA', 'QUI', 'SEX']] for __ in ['1°H', '2°H', '3°H', '4°H', '5°H', '6°H', '7°H']]
    df = pd.DataFrame(df_data, index=['1°H', '2°H', '3°H', '4°H', '5°H', '6°H', '7°H'], columns=['SEG', 'TER', 'QUA', 'QUI', 'SEX'])

    for my_matrícula, my_ch in ch_individuais.items():
        try:
            dados = collection.find_one({
                    'matrícula': my_matrícula,
                    'turno': turno_choice
                }
            )
            data_frame = pd.DataFrame(dados['schedule'])
        except:
            continue
        for selected_day in ['SEG', 'TER', 'QUA', 'QUI', 'QUI', 'SEX']:
            no_dia = data_frame.T[selected_day]
            for hora, aula in no_dia.items():
                try: 
                    turmaz, comp = aula.split(' § ')
                    if turmaz != st.session_state.alias.get(selected_turma, turmaz):
                        continue
                    new_comp0 = reversed_dic_comps.get(comp, comp)
                    new_comp = dc_comps.get(new_comp0, new_comp0)
                    df.at[hora, selected_day] = f"{new_comp} ________________ {my_matrícula}"
                except ValueError:
                    continue

    mask = df.eq('-').all(axis=1)
    df = df[~mask]
    st.table(df)
    df.to_clipboard(sep='\t', index=True, header=True)
    if df.shape[0] == 5:
        from pandas_to_xlsx import by_class_5h as by_class
    else:
        from pandas_to_xlsx import by_class
    turma_nome_parte1 = st.session_state.alias.get(selected_turma, selected_turma).replace('1', '1°').replace('2', '2°').replace('3', '3°')
    turma_nome_parte2 = selected_turma
    st.download_button(
        label="Baixar planilha", 
        data=by_class(df.T, turma=f'{turma_nome_parte1} ({turma_nome_parte2})'), 
        file_name=f'{selected_turma}.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    


if __name__ == "__main__":
    principal()


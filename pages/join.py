import streamlit as st
import httpx
import pandas as pd
import pymongo
from replaced import to_replacement_of_columns
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
def freeze_classes(project_id, vinculo, username):
    url = f"https://che.herokuapp.com/freezech?project_id={project_id}&v%C3%ADnculo={vinculo}&username={username}"
    response = httpx.get(url, timeout=10)
    return response.json()

def on_change():
    del st.session_state.json
    
def principal():
    st.title("DISTRIBUIÇÃO DAS AULAS")

    if st.session_state.get("json") is None:
        username = project_id.split('__')[0]
        project_name = project_id.split('__')[1]
        req = freeze_classes(project_name, school, username)
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
    selected_day = st.selectbox("Selecione o dia da semana", ['SEG', 'TER', 'QUA', 'QUI', 'SEX'])
    df_data = [['-' for _ in range(7)] for __ in turmas_do_turno]
    df = pd.DataFrame(df_data, index=turmas_do_turno, columns=['1°H', '2°H', '3°H', '4°H', '5°H', '6°H', '7°H'])
    df.index = [st.session_state.alias.get(turma, turma) for turma in df.index]
    for my_matrícula, my_ch in ch_individuais.items():
        my_plans = []
        try:
            dados = collection.find_one({
                    'matrícula': my_matrícula,
                    'turno': turno_choice
                }
            )
            data_frame = pd.DataFrame(dados['schedule'])
        except:
            st.info(dict_matrícula_apelido.get(my_matrícula, my_matrícula))
            continue
        no_dia = data_frame.T[selected_day]
        for hora, aula in no_dia.items():
            try: 
                turmaz, comp = aula.split(' § ')
                if comp.startswith('ES '):
                    comp = comp[3:]
                new_comp = comp.replace(' - VPE: ', '_')
                if df.at[turmaz, hora] != '-':

                    st.warning(f"O professor {dict_matrícula_apelido.get(my_matrícula, my_matrícula)} está com aula duplicada")
                    st.warning(f' ou o professor {df.at[turmaz, hora]} está com aula duplicada')
                df.at[turmaz, hora] = f"{dict_matrícula_apelido.get(my_matrícula, my_matrícula).replace('Dudu', 'Nival')}   {new_comp}"
            except ValueError:
                continue

    st.dataframe(df)
    from pandas_to_xlsx import pandas_to_xlsx
    # st download
    st.download_button(
        label="Baixar planilha", 
        data=pandas_to_xlsx(df, selected_day), 
        file_name=f'{selected_day}.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    


if __name__ == "__main__":
    principal()


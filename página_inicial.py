import streamlit as st
import httpx
import pandas as pd
import pymongo
st.set_page_config(layout="wide")
# secretes
import os
try:
    cred = os.environ['cred_service_name']
    chdata = os.environ['chdata']
    colecz = os.environ['colecz']
    project_id = os.environ['project_id']
except:
    cred = st.secrets["cred_service_name"]
    chdata = st.secrets["chdata"]
    colecz = st.secrets["colecz"]
    project_id = st.secrets["project_id"]

client = pymongo.MongoClient(cred)
db = client[chdata]
collection = db[colecz]
# make a request to the server to freeze the classes
def freeze_classes(project_id, vinculo, username):
    url = f"https://che.herokuapp.com/freezech?project_id={project_id}&v%C3%ADnculo={vinculo}&username={username}"
    response = httpx.get(url, timeout=10)
    return response.json()

def on_change(matrícula):
    if matrícula in st.session_state:
        del st.session_state[matrícula]
    

def principal():
    st.title("DISTRIBUIÇÃO DAS AULAS")

    if st.session_state.get("json") is None:
        # project_id = st.text_input("ID do Projeto")
        # username = st.text_input("Nome de Usuário")
        # vínculo = st.text_input("Vínculo")
        # req = freeze_classes(project_id, vínculo, username)
        req = freeze_classes('projeto03', 'estadualbahia@ue_cetibc', '114507413')
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
    turmas =  {subkey:json[key][subkey] for key in json for subkey in json[key]}
    matrículas = [item['matricula'] for item in st.session_state.lprofs]
    dict_matrícula_apelido = {item['matricula']:item['apelido'] for item in st.session_state.lprofs}
    assert len(matrículas) == len(dict_matrícula_apelido)
    prof_choose = st.selectbox("Selecione o professor", list(dict_matrícula_apelido.values()))
    my_matrícula = {v:k for k,v in dict_matrícula_apelido.items()}[prof_choose]
    turnos = ['DIURNO', 'NOTURNO']
    turno_choice = st.selectbox("Selecione o turno", turnos, on_change=on_change, args=(my_matrícula,))
    dict_turno = {
        'DIURNO': ['MAT', 'INT7H'],
        'NOTURNO':['NOT']
    }
    my_ch = ch_individuais[my_matrícula]
    my_plans = []
    for turno, ch_turno in my_ch.items():
        if turno not in dict_turno[turno_choice]:
            continue
        for turma, list_de_aula in ch_turno.items():
            for aula in list_de_aula:
                my_plans.append(f"{st.session_state.alias.get(turma, turma)} § {aula}")
    no_repeat = ['-'] + list(set(my_plans))
    column_config={
        HORA: st.column_config.SelectboxColumn(
            HORA,
            help="Selecione o planejamento",
            options=no_repeat,
            required=True,
            default="-"
        )
        for HORA in ['1°H', '2°H', '3°H', '4°H', '5°H', '6°H', '7°H']
    }
    if my_matrícula not in st.session_state:
        try:
            dados = collection.find_one({
                    'matrícula': my_matrícula,
                    'turno': turno_choice
                }
            )
            st.session_state[my_matrícula] = pd.DataFrame(dados['schedule'])
            st.success("possui registro no banco de dados")
        except:
            st.session_state[my_matrícula] = pd.DataFrame([['-' for _ in range(7)] for __ in range(5)], index=['SEG', 'TER', 'QUA', 'QUI', 'SEX'], columns=['1°H', '2°H', '3°H', '4°H', '5°H', '6°H', '7°H'])
    df = st.session_state[my_matrícula]
    df2 = st.data_editor(
        df,
        column_config=column_config,
        use_container_width=True
    )
    # counts how many plans are at the set of my_plans - df.values
    copy_of_my_plans = my_plans.copy()
    for valores in df2.values:
        for valor in valores:
            if valor in copy_of_my_plans:
                copy_of_my_plans.remove(valor)
        # if valor[0] in copy_of_my_plans:
        #     copy_of_my_plans.remove(valor[0])
    st.write(f"PLANEJAMENTOS RESTANTES **{len(copy_of_my_plans)}** ")
    if st.button("Salvar"):
        dict_from_df = df2.to_dict()

        receive = collection.update_one(
            {
                'matrícula': my_matrícula,
                'turno': turno_choice
            },
            {'$set': {'schedule': dict_from_df}},
            upsert=True
        )
        del st.session_state[my_matrícula]
        st.rerun()
    


if __name__ == "__main__":
    principal()


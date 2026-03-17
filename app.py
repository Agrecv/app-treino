import streamlit as st
from supabase import create_client

# --- Configuração da Página ---
# Define o título da aba do navegador e o layout adaptável para mobile
st.set_page_config(page_title="App de Treino", page_icon="💪", layout="centered")

# --- Inicialização do Supabase ---
# O st.cache_resource garante que a conexão não seja recriada a cada interação
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# --- Funções de Banco de Dados (CRUD) ---
def get_exercises(day_id):
    """Busca os exercícios de um dia específico, ordenados pela ordem de criação"""
    res = supabase.table("exercises").select("*").eq("day_id", day_id).order("id").execute()
    return res.data

def toggle_complete(ex_id, current_status):
    """Marca ou desmarca um exercício como concluído"""
    supabase.table("exercises").update({"completed": not current_status}).eq("id", ex_id).execute()

def update_exercise(ex_id, name, sets_reps, weight):
    """Atualiza os detalhes de um exercício"""
    supabase.table("exercises").update({
        "name": name, 
        "sets_reps": sets_reps, 
        "weight": weight
    }).eq("id", ex_id).execute()
    st.success("Exercício atualizado com sucesso!")
    st.rerun()

def delete_exercise(ex_id):
    """Remove um exercício do banco de dados"""
    supabase.table("exercises").delete().eq("id", ex_id).execute()
    st.success("Exercício removido!")
    st.rerun()

def add_exercise(day_id, name, sets_reps, weight):
    """Adiciona um novo exercício"""
    supabase.table("exercises").insert({
        "day_id": day_id, 
        "name": name, 
        "sets_reps": sets_reps, 
        "weight": weight, 
        "completed": False
    }).execute()
    st.success("Exercício adicionado!")
    st.rerun()

def reset_day(day_id):
    """Desmarca todos os exercícios de um dia específico (para o próximo treino)"""
    exercises = get_exercises(day_id)
    for ex in exercises:
        supabase.table("exercises").update({"completed": False}).eq("id", ex['id']).execute()
    st.rerun()

# --- Interface de Usuário (UI) ---
st.title("💪 Treino da Esposa")
st.write("Acompanhamento de séries e cargas.")

# Criamos abas para separar os dias de treino e a área de gerenciamento
tab1, tab2, tab3, tab4 = st.tabs(["Dia 1", "Dia 2", "Dia 3", "⚙️ Gerenciar"])

# Mapeamento das abas de treino
days_tabs = {1: tab1, 2: tab2, 3: tab3}

# --- Abas de Treino (Dias 1, 2 e 3) ---
for day_id, tab in days_tabs.items():
    with tab:
        st.subheader(f"Treino - Dia {day_id}")
        exercises = get_exercises(day_id)
        
        if not exercises:
            st.info("Nenhum exercício cadastrado para este dia. Vá na aba '⚙️ Gerenciar' para adicionar.")
        
        # Lista os exercícios com checkbox
        for ex in exercises:
            # Exibe Nome, Séries e Carga. Se não tiver carga, mostra '--'
            carga_display = ex['weight'] if ex['weight'] else "--"
            label = f"**{ex['name']}** \n*{ex['sets_reps']}* | Carga: {carga_display}"
            
            # O key único garante que o Streamlit saiba qual checkbox foi clicado
            checked = st.checkbox(label, value=ex['completed'], key=f"chk_{ex['id']}")
            
            # Se o usuário clicar, atualiza no banco de dados e recarrega
            if checked != ex['completed']:
                toggle_complete(ex['id'], ex['completed'])
                st.rerun()
        
        st.divider()
        # Botão para zerar os "vistos" ao terminar o treino
        if st.button(f"🔄 Zerar Vistos do Dia {day_id}", key=f"reset_{day_id}"):
            reset_day(day_id)

# --- Aba de Gerenciamento ---
with tab4:
    st.header("Gerenciar Exercícios")
    
    # Seção para ADICIONAR novo exercício
    with st.expander("➕ Adicionar Novo Exercício"):
        with st.form("add_form"):
            new_day = st.selectbox("Adicionar no:", ["Dia 1", "Dia 2", "Dia 3"])
            # Converte 'Dia X' para o número inteiro correspondente
            day_num = int(new_day.split(" ")[1]) 
            
            new_name = st.text_input("Nome do Exercício")
            new_sets = st.text_input("Séries x Repetições (ex: 4x 12)")
            new_weight = st.text_input("Carga Atual (ex: 20kg)")
            
            if st.form_submit_button("Salvar Novo Exercício"):
                if new_name and new_sets:
                    add_exercise(day_num, new_name, new_sets, new_weight)
                else:
                    st.error("Preencha o nome e as séries!")

    st.divider()
    st.subheader("Editar ou Remover Existentes")
    
    # Busca todos os exercícios para listagem no gerenciamento
    all_exercises = supabase.table("exercises").select("*").order("day_id").order("id").execute().data
    
    if not all_exercises:
        st.write("Sem exercícios para editar.")
        
    for ex in all_exercises:
        # Usa expanders para manter a tela limpa no celular
        with st.expander(f"Dia {ex['day_id']} - {ex['name']}"):
            with st.form(f"edit_form_{ex['id']}"):
                edit_name = st.text_input("Nome", value=ex['name'])
                edit_sets = st.text_input("Séries x Reps", value=ex['sets_reps'])
                edit_weight = st.text_input("Carga", value=ex['weight'] if ex['weight'] else "")
                
                colA, colB = st.columns(2)
                with colA:
                    if st.form_submit_button("💾 Salvar Alterações"):
                        update_exercise(ex['id'], edit_name, edit_sets, edit_weight)
                with colB:
                    # Botão em vermelho/primário para atenção
                    if st.form_submit_button("🗑️ Excluir", type="primary"):
                        delete_exercise(ex['id'])

# --- Rodapé ---
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray; font-size: 0.85em;'>Desenvolvido para otimizar os treinos 💪</p>", unsafe_allow_html=True)
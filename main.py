# Import
import streamlit as st
import mysql.connector
import pandas as pd
from datetime import date

# Style
st.set_page_config(layout="wide", page_title="Covid Tracer", menu_items={
    'About': "Réalisé par Antonin"
})

st.markdown("""
<style>
.first_titre {
    font-size:75px !important;
    font-weight: bold;
    box-sizing: border-box;
    text-align: center;
    width: 100%;
    // border: solid #4976E4 5px;
    // padding: 5px;
}
</style>
""", unsafe_allow_html=True)
st.markdown('<p class="first_titre">Covid Tracer</p>', unsafe_allow_html=True)
st.write("---")

# Initialize connection.
list_col_names_eleve = ['id_eleve', 'Nom_eleve', 'Prenom_eleve', 'Debut_isolement', 'Duree_isolement', 'id_professeur']
list_col_names_professeur = ['id_professeur', 'Nom_professeur', 'Prenom_professeur']

# Uses st.cache to only run once.
conn = mysql.connector.connect(**st.secrets["mysql"])


# Perform query.
# Uses st.cache to only rerun when the query changes or after 10 min.
@st.cache(ttl=600)
def run_query(query):
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()


def run_update_query(query):
    with conn.cursor() as cur:
        cur.execute(query)
    conn.commit()


def get_data(request, con=conn):
    """Retourne le résultat de la requete sous forme de dataframe"""
    df = pd.read_sql(request, con)
    return df


def liste_classe(prof):
    """Retourn les infos des élèves du prof"""
    return get_data(
        f"SELECT Nom_eleve, Prenom_eleve, Debut_isolement, Durée_isolement from Eleve, Professeur WHERE Eleve.id_professeur=Professeur.id_professeur AND Professeur.Nom_professeur='{prof}'")


def liste_prof():
    """Retourn le nom des professeurs"""
    return get_data(f"SELECT Nom_professeur, Prenom_professeur, id_professeur from Professeur")


def update_isolement(nom_eleve, prenom_eleve, debut_isol, duree):
    sql = f"UPDATE Eleve SET Debut_isolement = '{debut_isol}', Durée_isolement = '{duree}' WHERE Nom_eleve = '{nom_eleve}' AND Prenom_eleve = '{prenom_eleve}'"
    return run_update_query(sql)


# Main page
c1, c2, c3 = st.columns((1, 0.1, 1))
with c1:
    prof = st.selectbox(options=['-- Nom du professeur --'] + list(liste_prof()['Nom_professeur']),
                        label="Qui êtes vous ?")

if prof != '-- Nom du professeur --':
    with c3:
        st.write(liste_classe(prof))

    with c1:
        st.write("##")
        with st.form("Modifier ou ajouter une date d'isolement"):
            st.write("Modifier ou ajouter une date d'isolement")
            eleve = st.selectbox(options=[" ".join((i, j)) for i, j in zip(list(liste_classe(prof)['Nom_eleve']),
                                                                           list(liste_classe(prof)['Prenom_eleve']))],
                                 label='Choisir un élève')
            debut_isol = st.date_input(label="Date de début d'isolement", max_value=date.today(), help="Format date = AAAA/MM/JJ")
            duree = st.number_input(label="Durée d'isolement", min_value=1, max_value=30, help="Nombre de jours d'isolement")
            submitted = st.form_submit_button("Submit")
            if submitted:
                update_isolement(eleve.split(" ")[0], eleve.split(" ")[1], debut_isol, duree)
                st.success("Modification effectuée avec succès !")

        st.write("##")
        date_fin_isole = st.date_input(label="Elève en fin d'isolement ce jour", min_value=date.today(), help="Format date = AAAA/MM/JJ")
        st.write("##")
        res_date_fin_isole = get_data(
            f"SELECT Nom_eleve, Prenom_eleve from Eleve, Professeur WHERE Eleve.id_professeur=Professeur.id_professeur AND Professeur.Nom_professeur='{prof}' AND DATE_ADD(Debut_isolement, INTERVAL Durée_isolement DAY)='{date_fin_isole}'")
        if len(res_date_fin_isole) == 0:
            st.info("Aucun élève ne rentre ce jour")
        else:
            st.write(res_date_fin_isole)

    st.write("---")

    # st.write(liste_prof())

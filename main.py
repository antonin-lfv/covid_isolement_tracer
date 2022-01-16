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
list_col_names_eleve = ['id_eleve', 'Nom_eleve', 'Prenom_eleve', 'Debut_isolement', 'Duree_isolement', 'id_professeur',
                        'Est_isole']
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
    conn.cursor().execute(query)
    conn.commit()


def get_data(request, con=conn):
    """Retourne le résultat de la requete sous forme de dataframe"""
    df = pd.read_sql(request, con)
    return df


def liste_classe(prof):
    """Retourn les infos des élèves du prof"""
    return get_data(
        f"SELECT Nom_eleve AS 'Nom', Prenom_eleve AS 'Prenom', Debut_isolement AS 'Début isolement', Durée_isolement AS 'Durée isolement', Est_isole AS 'En isolement' from Eleve, Professeur WHERE Eleve.id_professeur=Professeur.id_professeur AND Professeur.Nom_professeur='{prof}'")


def liste_prof():
    """Retourn le nom des professeurs"""
    return get_data(f"SELECT Nom_professeur, Prenom_professeur, id_professeur from Professeur")


def update_isolement(nom_eleve, prenom_eleve, debut_isol, duree, prof):
    sql = f"UPDATE Eleve SET Debut_isolement = '{debut_isol}', Durée_isolement = '{duree}', Est_isole = CASE WHEN DATE_ADD(Debut_isolement, INTERVAL Durée_isolement DAY) > DATE( NOW() ) THEN 'oui' ELSE 'non' END WHERE Nom_eleve = '{nom_eleve}' AND Prenom_eleve = '{prenom_eleve}' AND id_professeur = (SELECT id_professeur FROM Professeur WHERE Nom_professeur='{prof}')"
    return run_update_query(sql)


# Main page
prof = st.sidebar.selectbox(options=['-- Nom du professeur --'] + list(liste_prof()['Nom_professeur']),
                            label="Qui êtes vous ?")

mot_de_passe = st.sidebar.text_input("Saisissez le mot de passe", max_chars=20, placeholder="Mot de passe",
                                     type="password")
c1, c2, c3 = st.columns((0.5, 0.1, 1))

if mot_de_passe == st.secrets['pass']['mdp'] and prof != '-- Nom du professeur --':
    with c3:
        run_update_query(
            f"UPDATE Eleve SET Est_isole = CASE WHEN DATE_ADD(Debut_isolement, INTERVAL Durée_isolement DAY) > DATE( NOW() ) THEN 'oui' ELSE 'non' END")
        liste = liste_classe(prof).fillna("")
        liste["Durée isolement"] = liste["Durée isolement"].apply(
            lambda x: str(int(x)) + ' jour' + ('s' if x != 1 else "") if isinstance(x, float) else "")
        st.dataframe(liste, height=500)

    with c1:
        with st.form("Modifier ou ajouter une date d'isolement"):
            st.write("Modifier ou ajouter une date d'isolement")
            eleve = st.selectbox(options=[" ".join((i, j)) for i, j in zip(list(liste_classe(prof)['Nom']),
                                                                           list(liste_classe(prof)['Prenom']))],
                                 label='Choisir un élève')
            debut_isol = st.date_input(label="Date de début d'isolement", max_value=date.today(),
                                       help="Format date = AAAA/MM/JJ")
            duree = st.number_input(label="Durée d'isolement", min_value=1, max_value=30,
                                    help="Nombre de jours d'isolement")
            submitted = st.form_submit_button("Submit")
            if submitted:
                update_isolement(eleve.split(" ")[0], eleve.split(" ")[1], debut_isol, duree, prof)
                st.success("Modification effectuée avec succès !")
                st.experimental_rerun()

        st.write("##")
        date_fin_isole = st.date_input(label="Elève(s) en fin d'isolement ce jour", min_value=date.today(),
                                       help="Format date = AAAA/MM/JJ")
        st.write("##")
        res_date_fin_isole = get_data(
            f"SELECT Nom_eleve AS 'Nom', Prenom_eleve AS 'Prénom' from Eleve, Professeur WHERE Eleve.id_professeur=Professeur.id_professeur AND Professeur.Nom_professeur='{prof}' AND DATE_ADD(Debut_isolement, INTERVAL Durée_isolement DAY)='{date_fin_isole}'")
        if len(res_date_fin_isole) == 0:
            st.info("Aucun élève ne rentre ce jour")
        else:
            st.dataframe(res_date_fin_isole)

    st.write("##")
    st.write("---")

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from io import BytesIO

# Holt's Double Exponential Smoothing function
def holt_forecast(data, alpha=0.2, beta=0.1, periods=1):
    if len(data) < 2:
        return np.nan

    level = data[0]
    trend = data[1] - data[0]
    forecasts = []

    for i in range(1, len(data)):
        level_prev = level
        level = alpha * data[i] + (1 - alpha) * (level + trend)
        trend = beta * (level - level_prev) + (1 - beta) * trend

    for _ in range(periods):
        forecast = level + trend
        forecasts.append(forecast)
        level_prev = level
        level = alpha * forecast + (1 - alpha) * (level + trend)
        trend = beta * (level - level_prev) + (1 - beta) * trend

    return forecasts

# Load articles from Excel
@st.cache_data
def load_articles():
    df = pd.read_excel("articles.xlsx", engine='openpyxl')
    df.columns = df.columns.str.replace('\n', ' ', regex=True)
    df.columns = df.columns.str.strip().str.lower()
    df['code ean uvc'] = df['code ean uvc'].astype(str)
    return df

def reset_session():
    for key in st.session_state.keys():
        del st.session_state[key]

def main():
    st.set_page_config(layout="wide")
    st.markdown("# Série à prévoir")

    # Reset button
    if st.button("🔄 Réinitialiser"):
        reset_session()
        st.rerun()

    # Load data
    try:
        df_articles = load_articles()
    except Exception as e:
        st.error(f"Erreur de chargement du fichier articles.xlsx : {e}")
        st.stop()

    # Article selection
    col1, col2 = st.columns(2)
    with col1:
        selected_ean = st.selectbox(
            "Code article :",
            options=[""] + df_articles['code ean uvc'].unique().tolist(),
            index=0
        )

    if selected_ean == "":
        st.warning("Veuillez sélectionner un code article.")
        st.stop()

    # Vérifier que le code article existe
    if selected_ean not in df_articles['code ean uvc'].values:
        st.error("Le code article sélectionné n'existe pas dans le fichier.")
        st.stop()

    article_info = df_articles[df_articles['code ean uvc'] == selected_ean].iloc[0]

    with col1:
        st.text_input("Nom article :", value=article_info['nom article(25car)'], disabled=True)
        st.text_input("Fournisseur :", value=article_info['libellé fournisseur'], disabled=True)

    st.markdown("---")

    # Forecast generation section
    st.markdown("## Générer les prévisions")
    st.markdown("### Donnée historique des 12 derniers mois:")

    # Upload file
    uploaded_file = st.file_uploader(
        "Importer un fichier Excel avec données historiques",
        type=['xlsx', 'xls'],
        help="Le fichier doit contenir 2 colonnes: 'mois' et 'value'"
    )

    months = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
              "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]

    historical_data = []

    if uploaded_file is not None:
        try:
            df_history = pd.read_excel(uploaded_file, engine='openpyxl')
            if {'mois', 'value'}.issubset(df_history.columns):
                if len(df_history) >= 12:
                    historical_data = df_history['value'].head(12).tolist()
                    st.success("Données historiques importées avec succès!")
                else:
                    st.warning("Le fichier doit contenir au moins 12 mois de données")
            else:
                st.error("Le fichier doit contenir les colonnes 'mois' et 'value'")
        except Exception as e:
            st.error(f"Erreur de lecture du fichier: {e}")

    # Saisie manuelle si pas de fichier
    if not historical_data:
        st.info("Ou saisir manuellement les données:")
        cols = st.columns(12)
        historical_data = []
        for i, col in enumerate(cols):
            with col:
                historical_data.append(col.number_input(
                    f"{i+1}",
                    min_value=0.0,
                    value=0.0,
                    step=1.0,
                    key=f"hist_{i}"
                ))

    # Toujours visible : nombre de périodes à prévoir
    st.markdown("### Nombre de période à prévoir")
    periods = st.number_input(
        "Sélectionnez le nombre de mois à prévoir :",
        min_value=1,
        max_value=120,
        value=6,
        step=1
    )

    # Générer les prévisions
    if st.button("Générer les prévisions"):
        if all(v == 0 for v in historical_data):
            st.error("Veuillez entrer des données historiques")
        else:
            with st.spinner(f"Calcul des prévisions pour {periods} mois..."):
                forecasts = holt_forecast(historical_data, periods=periods)

                # Afficher résultats
                st.markdown("### Résultats des prévisions")

                forecast_months = []
                current_date = datetime.now()
                for i in range(periods):
                    forecast_date = current_date + timedelta(days=30*(i+1))
                    forecast_months.append(forecast_date.strftime("%B %Y"))

                # Historique
                st.markdown("#### Valeurs historiques")
                st.dataframe(pd.DataFrame({
                    "Mois": months,
                    "Valeurs": historical_data
                }), height=400)

                # Prévisions
                st.markdown(f"#### Prévisions ({periods} mois)")
                forecast_df = pd.DataFrame({
                    "Mois": forecast_months,
                    "Prévision": [round(val, 2) for val in forecasts],
                    "Tendance": ["↑" if i > 0 and forecasts[i] > forecasts[i-1] else "↓" for i in range(len(forecasts))]
                })
                st.dataframe(forecast_df, height=600)

                # Graphique
                st.line_chart(forecast_df.set_index("Mois")["Prévision"], height=400)

                # Export Excel
                output_excel = BytesIO()
                with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                    forecast_df.to_excel(writer, index=False, sheet_name="Prévisions")
                    writer.close()
                    output_excel.seek(0)

                st.download_button(
                    label="📤 Exporter au format Excel (.xlsx)",
                    data=output_excel,
                    file_name=f"previsions_{selected_ean}_{periods}mois.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                # Export CSV
                csv = forecast_df.to_csv(index=False, sep=";").encode('utf-8')
                st.download_button(
                    "📥 Exporter au format CSV",
                    csv,
                    f"previsions_{selected_ean}_{periods}mois.csv",
                    "text/csv"
                )

if __name__ == "__main__":
    main()

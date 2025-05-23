import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

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

# Main app
def main():
    st.set_page_config(layout="wide")
    st.markdown("# Série à prévoir")

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
            options=df_articles['code ean uvc'].unique(),
            index=0
        )

    article_info = df_articles[df_articles['code ean uvc'] == selected_ean].iloc[0]

    with col1:
        st.text_input("Nom article :", value=article_info['nom article(25car)'], disabled=True)
        st.text_input("Fournisseur :", value=article_info['libellé fournisseur'], disabled=True)

    st.markdown("---")

    # Forecast generation section
    st.markdown("## Générer les prévisions")
    st.markdown("### Donnée historique des 12 derniers mois:")

    months = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
              "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]

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

    # Number of periods to forecast
    st.markdown("### Nombre de période à prévoir")
    periods = st.slider(
        "Sélectionnez le nombre de mois à prévoir :",
        min_value=1,
        max_value=12,
        value=6,
        step=1
    )

    if st.button("Générer les prévisions"):
        if all(v == 0 for v in historical_data):
            st.error("Veuillez entrer des données historiques")
        else:
            forecasts = holt_forecast(historical_data, periods=periods)

            # Display results in table format
            st.markdown("### Résultats des prévisions")

            forecast_months = []
            current_date = datetime.now()
            for i in range(periods):
                forecast_date = current_date + timedelta(days=30*(i+1))
                forecast_months.append(forecast_date.strftime("%B"))

            # Show values
            st.markdown("#### Valeurs historiques")
            st.write(pd.DataFrame({
                "Mois": months,
                "Valeurs": historical_data
            }))

            st.markdown("#### Prévisions")
            st.write(pd.DataFrame({
                "Mois": forecast_months,
                "Prévision": [round(val, 2) for val in forecasts]
            }))

            # Export button
            csv_data = pd.DataFrame({
                "Mois": forecast_months,
                "Prévision": forecasts
            })
            csv = csv_data.to_csv(index=False, sep=";").encode('utf-8')

            st.download_button(
                "Exporter les prévisions",
                csv,
                f"previsions_{selected_ean}.csv",
                "text/csv"
            )

if __name__ == "__main__":
    main()

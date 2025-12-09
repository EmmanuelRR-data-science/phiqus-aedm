# 📊 Automatización de Estudios de Mercado

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![n8n](https://img.shields.io/badge/n8n-Workflow_Automation-FF6584?style=for-the-badge&logo=n8n&logoColor=white)
![AI Powered](https://img.shields.io/badge/AI-Powered_Analysis-success?style=for-the-badge)


## 📖 Descripción

El objetivo de esta aplicación es automatizar la extracción, transformación y visualización de indicadores económicos clave de México y el mundo, enriqueciéndolos con **análisis cualitativo generado por Inteligencia Artificial**.

La aplicación elimina la talacha manual de descargar Excel y redactar reportes, permitiendo a los consultores enfocarse en la estrategia.

## 🚀 Características Principales

* **📡 Conexión Multi-Fuente:** Integración en tiempo real con APIs y datos de:
    * INEGI (BIE/BISE)
    * Banxico (SIE)
    * Banco Mundial / FMI
    * Datatur
* **🤖 Análisis Cualitativo con IA:** Arquitectura desacoplada donde **n8n** orquesta agentes de IA para interpretar tendencias (Alza/Baja) o Snapshots (Valores actuales) y generar *insights* de negocios.
* **📈 Visualización Interactiva:** Gráficas dinámicas con Plotly y Streamlit.
* **🧠 Lógica Híbrida:** Sistema inteligente que decide si analizar una serie histórica (tendencia) o un dato puntual, evitando alucinaciones de la IA.

## 🛠️ Arquitectura del Sistema

El sistema utiliza un enfoque híbrido **Frontend (Streamlit)** + **Orquestador (n8n)**

## 🌐 Demo en Vivo

Puedes interactuar con la app en tiempo real y probar las funcionalidades sin necesidad de instalación:

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://phiqus-aedm.streamlit.app/)

🔗 **Link directo:** [https://phiqus-aedm.streamlit.app/](https://phiqus-aedm.streamlit.app/)

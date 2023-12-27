import streamlit as st
from streamlit_extras.app_logo import add_logo 
import configuration

add_logo("gallery/bauchat_logo.png", height=100)

configuration.conf_session_state()

col1, col2 = st.columns(2)
with col1:
        st.write("Diese Seite ermöglicht es eine Frage an eine Sammlung von PDF Dokumenten zu stellen. "
                "Die Frage wird beantwortet und die relevanten Quellen werden angegeben. "
                "Suchen Sie entweder in den vorkonfigurierten Verzeichnissen oder laden Sie selber Dokumente hoch. "
                "Um viele Dokumente gleichzeitig zu durchsuchen, "
                "zum Beispiel alle Dokumente die zu einem Bauprojekt gehören, können Sie sich anmelden. "
                "Die Dokumente werden dann in ihrem Benutzerkonto zwischengespeichert und sind beim nächsten Aufruf wieder verfügbar")
                
        st.write("Dieses Seite ist noch in Entwicklung. "
                "Bei Fragen oder Anregungen, melden Sie sich:")
        st.write("Fabio Indergand: info@bauchat.ch")


import os
from dotenv import load_dotenv
from ai import get_llm, get_embedding_model

# Im .env file local oder cloud einrichten und die benötigten Keys eintragen
# für webseite cloud-modus wird open ai verwendetund speicherung unter aws
# Local kann ein eigenes LLM und ein embedder vorgegeben werden. über huggingface laden


# Schritt 1: .env laden
print("🔄 Lade .env-Datei...")
load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME")
MODEL_PATH = os.getenv("MODEL_PATH")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

print(f"✅ MODEL_NAME: {MODEL_NAME}")
print(f"✅ MODEL_PATH: {MODEL_PATH}")
print(f"✅ EMBEDDING_MODEL: {EMBEDDING_MODEL}")

# Schritt 2: LLM initialisieren und testen
print("\n⚙️ Initialisiere LLM über ai.py...")
try:
    llm_fn = get_llm()  # llm_fn ist eine Funktion!
    print("✅ LLM erfolgreich geladen.\n")

    prompt = "Nenne drei Vorteile von Photovoltaik auf Dächern."
    print(f"📨 Test-Prompt: {prompt}")

    response, usage = llm_fn(prompt)  # <-- so musst du sie aufrufen
    print("✅ Antwort:")
    print(response)
    print("📊 Usage:")
    print(usage)

except Exception as e:
    print(f"❌ Fehler beim Laden oder Ausführen des LLM: {e}")

# Schritt 3: Embedding-Modell initialisieren und testen
print("\n⚙️ Initialisiere Embedding-Modell über ai.py...")
try:
    embedder = get_embedding_model()
    print("✅ Embedding-Modell erfolgreich geladen.")

    sample_text = "Photovoltaikanlagen auf Dächern leisten einen wichtigen Beitrag zur Energiewende."
    embedding = embedder.embed_query(sample_text)
    print(f"📈 Embedding-Vektor für Beispieltext (Länge {len(embedding)}):")
    print(embedding[:10], "...")  # Nur ersten 10 Werte anzeigen
except Exception as e:
    print(f"❌ Fehler beim Embedding: {e}")
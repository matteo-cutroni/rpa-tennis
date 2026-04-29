from selenium import webdriver
import time

def main():
    # URL della pagina di login del tuo circolo
    login_url = "https://asdtennisroma.it/prenotazioni/"

    print("Inizializzazione di Safari...")
    
    try:
        # Avviamo il driver nativo di Safari
        driver = webdriver.Safari()

        # 1. Apre la pagina desiderata
        print(f"Navigazione in corso verso: {login_url}")
        driver.get(login_url)

        # 2. Pausa temporanea per farti vedere che la pagina si è aperta correttamente
        time.sleep(5) 

        # --- QUI ANDRANNO I PROSSIMI PASSAGGI ---
        # - Inserimento Username
        # - Inserimento Password
        # - Click sul pulsante "Accedi"
        # ----------------------------------------

        print("Pagina caricata con successo in Safari! Pronto per i prossimi step.")

    except Exception as e:
        print(f"Si è verificato un errore durante l'esecuzione: {e}")
        print("💡 Suggerimento: Assicurati di aver spuntato 'Consenti automazione remota' nel menu Sviluppo di Safari!")
    
    finally:
        # Chiude il browser alla fine delle operazioni (se è stato aperto con successo)
        if 'driver' in locals():
            print("Chiusura di Safari in corso...")
            driver.quit()

if __name__ == "__main__":
    main()
from selenium import webdriver
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from dotenv import load_dotenv
import os
import functions as f

load_dotenv()

def main():
    login_url = "https://asdtennisroma.it/prenotazioni/"
    print("Inizializzazione di Safari...")
    
    try:
        driver = webdriver.Safari()
        driver.maximize_window()
        print(f"Navigazione verso: {login_url}")
        driver.get(login_url)

        print("Inizio procedura di login...")
        f.esegui_login(driver, "formlogin:username", "formlogin:password", "formlogin:btnlogin")

        # Verifica finale login
        print("Verifica definitiva login...")
        wait = WebDriverWait(driver, 100)
        wait.until(EC.invisibility_of_element_located((By.ID, "formlogin:btnlogin")))
        print("Login effettuato con successo!")

        time.sleep(2)

        print("Selezione tipologia: Singolare...")
        f.clicca_elemento(driver, "form-prenota:opt1")


        print("Selezione del secondo giorno...")
        f.clicca_elemento(driver, "form-prenota:j_idt90:1")

        print("Selezione del Campo N° 3...")
        # Clicchiamo l'input corrispondente al Campo N° 3
        f.clicca_elemento(driver, "form-prenota:j_idt94:2")

        # Definiamo la lista in ordine di priorità: prima 19, poi 18:30, infine 19:30
        preferenze_orari = ["19:00", "18:30", "19:30"]
        print(f"Inizio ricerca miglior orario disponibile...")
        
        # Passiamo l'intera lista alla nostra funzione
        f.seleziona_orario(driver, preferenze_orari)

        print("Attendo il caricamento delle opzioni per i giocatori...")
        time.sleep(2)

        print("Imposto il tipo di giocatore su 'Socio'...")
        # L'ID del select nascosto termina con '_input'. Il valore '0' corrisponde a 'Socio'
        f.imposta_dropdown(driver, "form-prenota:j_idt117_input", "0")

        cognome_partner = os.getenv("COGNOME_SOCIO")
        
        print(f"Inserimento socio: {cognome_partner}...")
        f.compila_autocomplete(driver, "form-prenota:j_idt124_input", cognome_partner)


        print("🚀 INVIO PRENOTAZIONE: Clicco su 'PRENOTA ORA'...")
        f.clicca_elemento(driver, "form-prenota:j_idt263")
        # -------------------

    except Exception as e:
        print(f"Si è verificato un errore: {e}")
    
    finally:
        if 'driver' in locals():
            print("Chiusura in corso...")
            driver.quit()

if __name__ == "__main__":
    main()
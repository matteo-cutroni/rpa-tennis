from selenium import webdriver
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from dotenv import load_dotenv
import os
import sys
import functions as f

load_dotenv()

def main():
    login_url = "https://asdtennisroma.it/prenotazioni/"
    print("Inizializzazione di Safari...")
    
    try:
        # 1. RICEVE L'ORARIO DAL MAC (Se non c'è, usa 19:00)
        input_ora = sys.argv[1] if len(sys.argv) > 1 else "19:00"
        
        # 2. GENERA LA LISTA DELLE PREFERENZE
        preferenze_orari = f.genera_ordine_preferenze(input_ora)
        
        print(f"Orario scelto: {input_ora}. Proverò in quest'ordine: {preferenze_orari}")

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
        time.sleep(1)

        print("Selezione del secondo giorno...")
        f.seleziona_radio_primefaces(driver, "1")
        time.sleep(1)

        print("Selezione del Campo N° 3...")
        # Clicchiamo l'input corrispondente al Campo N° 3
        f.seleziona_radio_primefaces(driver, "3")
        time.sleep(1)
        # Passiamo l'intera lista alla nostra funzione
        f.seleziona_orario(driver, preferenze_orari)

        print("Attendo il caricamento delle opzioni per i giocatori...")
        time.sleep(1)

        # 1. Troviamo la tendina cercando l'elemento che contiene l'opzione "Socio"
        xpath_select = "//select[.//option[text()='Socio']]"
        select_socio = driver.find_element(By.XPATH, xpath_select)
        
        # 2. Estraiamo il suo ID segreto di oggi (es. form-prenota:j_idt120_input)
        id_tendina = select_socio.get_attribute("id")
        
        # 3. Chiamiamo la tua funzione originale usando l'ID appena rubato!
        print("Imposto il tipo di giocatore su 'Socio'...")
        f.imposta_dropdown(driver, id_tendina, "0")

        cognome_partner = os.getenv("COGNOME_SOCIO")
        
        # Troviamo il campo di input per l'autocomplete in base alla sua classe strutturale
        xpath_autocomplete = "//span[contains(@class, 'ui-autocomplete')]/input"
        input_nome = driver.find_element(By.XPATH, xpath_autocomplete)
        
        # Estraiamo l'ID di oggi
        id_autocomplete = input_nome.get_attribute("id")
        
        print(f"Scrivo il nome {cognome_partner}...")
        f.compila_autocomplete(driver, id_autocomplete, cognome_partner)
        time.sleep(1)

        # 1. Cerca il bottone che contiene la parola "PRENOTA" o "Prenota"
        xpath_prenota = "//button[.//span[contains(text(), 'PRENOTA') or contains(text(), 'Prenota')]]"
        bottone_finale = driver.find_element(By.XPATH, xpath_prenota)
        
        # 2. Scorriamo la pagina fino al bottone per evitare che sia coperto da banner
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", bottone_finale)
        time.sleep(1)

        # 3. Click "nucleare" in Javascript (infallibile su PrimeFaces)
        driver.execute_script("arguments[0].click();", bottone_finale)
        
        print("✅ PRENOTAZIONE INVIATA CON SUCCESSO! 🎉")
        time.sleep(5)

    except Exception as e:
        print(f"Si è verificato un errore: {e}")
    
    finally:
        if 'driver' in locals():
            print("Chiusura in corso...")
            driver.quit()

if __name__ == "__main__":
    main()
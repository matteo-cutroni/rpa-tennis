import os
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
import time

# Carica le variabili d'ambiente dal file .env
load_dotenv()

def esegui_login(driver, id_user, id_pass, id_btn):
    """
    Forza il login eseguendo direttamente il comando AJAX di PrimeFaces.
    """
    user = os.getenv("TENNIS_USER")
    password = os.getenv("TENNIS_PASS")
    
    # 1. Compila i campi
    compila_campo(driver, id_user, user)
    compila_campo(driver, id_pass, password)
    
    # 2. Breve pausa per far registrare i dati
    time.sleep(1)
    
    # 3. L'arma finale: iniettiamo ed eseguiamo la funzione nativa del sito
    print("Forzatura della chiamata di login al server...")
    comando_primefaces = "PrimeFaces.ab({s:'formlogin:btnlogin',f:'formlogin',u:'formlogin:error-messages'});"
    driver.execute_script(comando_primefaces)

def compila_campo(driver, id_elemento, testo_da_inserire):
    """
    Scrive nel campo e scatena gli eventi JS per attivare i pulsanti dipendenti.
    """
    if not testo_da_inserire:
        raise ValueError(f"ERRORE: Nessun testo per {id_elemento}")

    wait = WebDriverWait(driver, 10)
    campo = wait.until(EC.presence_of_element_located((By.ID, id_elemento)))
    
    campo.clear()
    campo.send_keys(testo_da_inserire)
    
    # FORZIAMO GLI EVENTI JS: PrimeFaces ha bisogno di sentire il 'keyup' e il 'change'
    driver.execute_script("arguments[0].dispatchEvent(new Event('keyup'));", campo)
    driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", campo)
    time.sleep(0.2) # Micro pausa per permettere al JS del sito di elaborare

def clicca_elemento(driver, id_elemento):
    """
    Funzione universale potenziata per PrimeFaces: clicca la Label associata all'input 
    o lancia direttamente l'evento 'change' per forzare l'aggiornamento della pagina.
    """
    wait = WebDriverWait(driver, 10)
    for tentativo in range(5):
        try:
            time.sleep(0.5)
            elemento = wait.until(EC.presence_of_element_located((By.ID, id_elemento)))
            
            # Script JS infallibile: cerca la Label e la clicca, se non c'è forza l'evento change.
            script_infallibile = """
                var el = arguments[0];
                var label = document.querySelector("label[for='" + el.id + "']");
                if (label) {
                    label.click();  // Clicca l'etichetta testuale
                } else {
                    el.click();     // Clicca l'input nascosto
                    el.dispatchEvent(new Event('change', { bubbles: true })); // Sveglia il server
                }
            """
            driver.execute_script(script_infallibile, elemento)
            return
            
        except StaleElementReferenceException:
            print(f"Tentativo {tentativo + 1}: Elemento instabile, riprovo...")
            
    raise Exception(f"Impossibile cliccare su {id_elemento}")

def seleziona_orario(driver, lista_orari):
    """
    Cerca l'orario e simula l'intera sequenza di un mouse umano (giù, su, click) 
    per ingannare i sensori di PrimeFaces.
    """
    wait = WebDriverWait(driver, 2)
    
    for ora in lista_orari:
        print(f"🔍 Verifico disponibilità per le ore {ora}...")
        # Puntiamo alla cella (td) esatta
        xpath = f"//tr[td[1][normalize-space()='{ora}']]/td[1]"
        
        try:
            cella = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            
            # Portiamo la tabella al centro dello schermo
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", cella)
            time.sleep(0.5)
            
            # Creiamo la sequenza perfetta di un click umano
            script_mouse_reale = """
                var el = arguments[0];
                var eventi = ['mouseover', 'mousedown', 'mouseup', 'click'];
                
                eventi.forEach(function(nomeEvento) {
                    var evento = new MouseEvent(nomeEvento, {
                        bubbles: true,
                        cancelable: true,
                        view: window
                    });
                    el.dispatchEvent(evento);
                });
            """
            driver.execute_script(script_mouse_reale, cella)
            
            print(f"✅ Successo! Orario {ora} trovato e cliccato con sequenza mouse.")
            return ora 
            
        except TimeoutException:
            print(f"❌ Orario {ora} non trovato (o già occupato). Passo alla prossima scelta...")
            
    raise Exception(f"ERRORE CRITICO: Nessuno degli orari preferiti ({lista_orari}) è disponibile!")

def imposta_dropdown(driver, id_select_nascosto, valore):
    """
    Funzione universale per i menu a tendina PrimeFaces: 
    cambia il valore del <select> nascosto e scatena l'aggiornamento.
    """
    wait = WebDriverWait(driver, 10)
    
    select = wait.until(EC.presence_of_element_located((By.ID, id_select_nascosto)))
    
    # SCRIPT CORRETTO: Aggiunte le doppie parentesi graffe su {{ bubbles: true }}
    script_dropdown = f"""
        var sel = arguments[0];
        sel.value = '{valore}';
        sel.dispatchEvent(new Event('change', {{ bubbles: true }}));
        
        var labelId = sel.id.replace('_input', '_label');
        var label = document.getElementById(labelId);
        if(label && sel.selectedIndex >= 0) {{
            label.innerText = sel.options[sel.selectedIndex].text;
        }}
    """
    driver.execute_script(script_dropdown, select)

def compila_autocomplete(driver, id_input, testo):
    """
    Versione specifica per tabelle autocomplete PrimeFaces.
    """
    wait = WebDriverWait(driver, 10)
    
    # 1. Trova il campo e scrive il testo
    campo = wait.until(EC.presence_of_element_located((By.ID, id_input)))
    campo.clear()
    
    # Scriviamo il testo carattere per carattere
    for char in testo:
        campo.send_keys(char)
        time.sleep(0.1)
    
    print(f"Digitazione '{testo}' completata. Ricerca riga nel pannello...")
    
    # 2. XPath mirato alla riga della tabella dei suggerimenti
    # Cerchiamo un 'tr' che abbia la classe 'ui-autocomplete-item'
    xpath_riga = "//tr[contains(@class, 'ui-autocomplete-item')]"
    
    try:
        # Aspettiamo che la riga appaia e sia visibile
        riga = wait.until(EC.visibility_of_element_located((By.XPATH, xpath_riga)))
        time.sleep(0.8) # Pausa extra per permettere al JS di legare gli eventi alla tabella
        
        # Sequenza mouse "schiacciasassi" sulla riga trovata
        script_mouse = """
            var el = arguments[0];
            var eventi = ['mouseover', 'mousedown', 'mouseup', 'click'];
            eventi.forEach(function(n) {
                el.dispatchEvent(new MouseEvent(n, {bubbles:true, cancelable:true, view:window}));
            });
        """
        driver.execute_script(script_mouse, riga)
        print(f"✅ Riga per '{testo}' selezionata con successo.")
        
    except TimeoutException:
        raise Exception(f"ERRORE: La tabella dei suggerimenti non è apparsa per '{testo}'.")
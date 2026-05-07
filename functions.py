import os
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import time
from datetime import datetime, timedelta

# Carica le variabili d'ambiente dal file .env
load_dotenv()
    

def seleziona_radio_primefaces(driver, valore):
    """
    Trova un radio button in base al suo 'value' (es. '1' per domani, '2' per il terzo campo)
    e clicca il box visibile associato.
    """
    wait = WebDriverWait(driver, 10)
    
    # Questo XPath è magico: cerca l'input nascosto con il valore corretto, 
    # torna indietro e clicca il div visibile subito dopo (la scatolina del pallino)
    xpath = f"//input[contains(@name, 'form-prenota:') and @type='radio' and @value='{valore}']/parent::div/following-sibling::div[contains(@class, 'ui-radiobutton-box')]"
    
    try:
        # Troviamo tutti i box che corrispondono (potrebbero essercene per i giorni e per i campi)
        # Selezioniamo il box specifico in base a dove ci troviamo (è gestito nell'XPath o dal click JS)
        box = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        
        # Scorriamo la pagina fino all'elemento per essere sicuri che sia visibile
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", box)
        time.sleep(0.5)
        
        # Il click tramite Javascript è immensamente più stabile su PrimeFaces
        driver.execute_script("arguments[0].click();", box)
        
    except Exception as e:
        raise Exception(f"Non sono riuscito a cliccare il pallino con valore '{valore}'. Dettaglio: {e}")

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
    Funzione universale potenziata per PrimeFaces: clicca l'elemento
    e attende che tutte le chiamate AJAX (caricamenti della pagina) siano terminate.
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
            
            # --- 🛡️ LA MAGIA ANTI-CRASH PER PRIMEFACES 🛡️ ---
            # Diciamo a Selenium di aspettare finché jQuery e PrimeFaces non dichiarano di aver finito i caricamenti
            wait.until(lambda d: d.execute_script(
                "return (typeof jQuery === 'undefined' || jQuery.active === 0) && "
                "(typeof PrimeFaces === 'undefined' || PrimeFaces.ajax.Queue.isEmpty());"
            ))
            
            # Un micro-riposo per dare tempo al browser di "disegnare" i nuovi elementi a schermo
            time.sleep(0.5) 
            
            return
            
        except StaleElementReferenceException:
            print(f"Tentativo {tentativo + 1}: Elemento instabile, riprovo...")
            
    raise Exception(f"Impossibile cliccare su {id_elemento} o timeout caricamento pagina.")

def seleziona_orario(driver, orari_preferiti):
    """
    Scorre la lista degli orari e clicca in modo nativo la cella corrispondente, 
    risvegliando gli eventi AJAX di PrimeFaces.
    """
    wait = WebDriverWait(driver, 3) 
    
    for orario in orari_preferiti:
        print(f"🔍 Verifico disponibilità per le ore {orario}...")
        
        # Puntiamo direttamente alla cella esatta all'interno di una riga "selezionabile"
        xpath_cella = f"//div[contains(@class, 'tableorari')]//tr[contains(@class, 'ui-datatable-selectable')]/td[1][text()='{orario}']"
        
        try:
            # NOVITÀ 1: Usiamo element_to_be_clickable invece di presence_of_element_located
            cella = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_cella)))
            
            # Scorriamo la pagina e diamo mezzo secondo per fermare l'animazione di scroll
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", cella)
            time.sleep(0.5)
            
            # NOVITÀ 2: Click nativo di Selenium (il metodo più affidabile per triggerare AJAX)
            try:
                cella.click()
            except Exception as inner_e:
                # Se per caso un banner copre il click nativo, fallback sulla riga intera
                print("Click nativo fallito, provo sulla riga intera...")
                riga = cella.find_element(By.XPATH, "./parent::tr")
                ActionChains(driver).move_to_element(riga).click().perform()
            
            print(f"✅ Successo! Orario {orario} trovato e cliccato.")
            return True 
            
        except Exception as e:
            print(f"❌ Orario {orario} non cliccabile o non disponibile. Passo oltre...")
            
    raise Exception("Nessuno degli orari scelti è disponibile. Prenotazione fallita.")

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
    

def genera_ordine_preferenze(orario_scelto):
    """
    Prende un orario (es. '19:00') e restituisce una lista:
    [orario_scelto, orario_scelto - 30min, orario_scelto + 30min]
    """
    fmt = "%H:%M"
    ora_dt = datetime.strptime(orario_scelto, fmt)
    
    meno_trenta = (ora_dt - timedelta(minutes=30)).strftime(fmt)
    piu_trenta = (ora_dt + timedelta(minutes=30)).strftime(fmt)
    
    return [orario_scelto, meno_trenta, piu_trenta]
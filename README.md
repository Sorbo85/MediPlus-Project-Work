# MediPlus — gestione appuntamenti sanitari

Prototipo didattico full-stack per il Project Work 16: API REST per un'organizzazione sanitaria.

## Funzionalità
- Dashboard con indicatori e appuntamenti recenti.
- Elenco appuntamenti con ricerca per paziente, medico o motivo e filtro per stato.
- Creazione prenotazioni con validazione, controllo medico/orario e rilevamento conflitti.
- Aggiornamento dello stato ed eliminazione di una prenotazione.
- Elenco medici e dati demo persistenti in SQLite.
- API JSON documentate in `docs/openapi.yaml`.

## Requisiti
Python 3.10 o superiore.

## Avvio locale
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Aprire http://127.0.0.1:5000. Il database `mediplus.db` viene creato al primo avvio.

## Endpoint principali
| Metodo | Endpoint | Descrizione |
|---|---|---|
| GET | `/api/health` | Stato del servizio |
| GET | `/api/dashboard` | Indicatori sintetici |
| GET | `/api/doctors` | Elenco medici |
| GET | `/api/patients` | Elenco pazienti demo |
| GET | `/api/appointments` | Appuntamenti; filtri `status` e `q` |
| POST | `/api/appointments` | Crea una prenotazione |
| PATCH | `/api/appointments/{id}` | Modifica lo stato |
| DELETE | `/api/appointments/{id}` | Elimina una prenotazione |

### Esempio POST
```json
{
  "patient_id": 1,
  "doctor_id": 2,
  "appointment_date": "2027-01-15T10:30",
  "reason": "Visita dermatologica"
}
```
La data deve essere futura. Il server risponde con `201` in caso di creazione, `400` per input non valido, `404` se paziente/medico non esiste e `409` se il medico è già occupato in quell'orario.

## Struttura
- `app.py`: backend Flask, accesso dati e logica applicativa.
- `frontend/`: HTML, CSS, JavaScript.
- `docs/openapi.yaml`: specifica API OpenAPI 3.
- `docs/architettura.md`: diagramma ER, classi e architettura.
- `tests/test_api.py`: test automatici di base.

## Test
```bash
pip install -r requirements.txt
python -m unittest discover -s tests -v
```

## Limiti e sicurezza
Questa è una demo universitaria con pazienti e visite fittizi. Non inserire dati personali o sanitari reali. Prima di un uso reale occorrono autenticazione e autorizzazione, audit log, protezione dei dati, gestione dei consensi, backup, HTTPS, migrazioni DB e verifiche di conformità GDPR. Il server Flask in modalità debug è solo per sviluppo.

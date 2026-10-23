# Architettura e progettazione MediPlus

## Scenario organizzativo
MediPlus è un centro medico fittizio che vuole semplificare la pianificazione delle visite. Il personale amministrativo consulta gli appuntamenti, registra una nuova prenotazione e aggiorna lo stato. Il prototipo usa esclusivamente dati sintetici.

## Architettura logica
```mermaid
flowchart LR
  U[Operatore] --> FE[Frontend HTML CSS JavaScript]
  FE -->|HTTP JSON| API[Backend REST Flask]
  API --> S[Servizi e validazioni]
  S --> DB[(SQLite)]
```

## Modello ER
```mermaid
erDiagram
  PATIENTS ||--o{ APPOINTMENTS : prenota
  DOCTORS ||--o{ APPOINTMENTS : visita
  PATIENTS {
    int id PK
    string name
    string email
    string phone
  }
  DOCTORS {
    int id PK
    string name
    string specialty
    string email
  }
  APPOINTMENTS {
    int id PK
    int patient_id FK
    int doctor_id FK
    string appointment_date
    string reason
    string status
    string created_at
  }
```

## Classi / responsabilità
```mermaid
classDiagram
  class AppointmentAPI {
    +list_appointments()
    +create_appointment()
    +update_appointment(id)
    +delete_appointment(id)
  }
  class Doctor {
    +id
    +name
    +specialty
    +email
  }
  class Patient {
    +id
    +name
    +email
    +phone
  }
  class Appointment {
    +id
    +patient_id
    +doctor_id
    +appointment_date
    +reason
    +status
  }
  AppointmentAPI ..> Appointment : gestisce
  Appointment --> Patient : appartiene a
  Appointment --> Doctor : assegnato a
```

## Principali regole di business
1. Paziente, medico, data/ora e motivo sono obbligatori.
2. La visita deve essere programmata nel futuro.
3. Il paziente e il medico devono esistere.
4. Un medico non può avere due appuntamenti non annullati allo stesso orario.
5. Lo stato è uno tra Prenotata, Confermata, Completata e Annullata.

## Note progettuali
Le route Flask costituiscono il livello API; le funzioni di validazione applicano le regole di business e SQLite conserva i dati. Per un progetto di produzione è consigliato separare API, servizi e repository in moduli distinti, aggiungere autenticazione, logging e migrazioni.

# Python-ETABS---EXCEL-Interface
Aplicatie sub forma unei interfete ce permite utilizatorului schimbul de date dintre ETABS si EXCEL.

Funcționalități:
Asigura stocarea intr-o baza de date a proprietatilor de tip Frame din ETABS.
Vizualizarea bazei de date de catre utilizator se face prin intermediul fisierelor EXCEL.
Asigura schimbul de date dintre fisierele EXCEL si ETABS , astfel incat orice modificare intr-o parte sa se transleze si in cealalta.

Librarii utilizate:
tkinter
sqlite3
xlwings
math

Python-ETABS---EXCEL-Interface
├── src/
│ ├── gui/
│ │ ├── main_window.py 
│ │ ├── widgets.py 
│ │ └── temp_data_manager.py
│ ├── db/
│ │ └── operations.py 
│ ├── etabs_api/ 
│ │ ├── connection.py
│ │ └── operations.py
│ ├── excel/
|   ├── templates
|   | ├── deaful.xlsx
│   └── operations.py
├── run.py
└── README.md

🚨 DECLINARI DE RESPONSABILITATI IMPORTANTE 🚨
 - NU ESTE INCLUSA DOCUMENTATIA ETABS: Acest repo. nu contine documentatia ETABS. Documentatia ETABS este detinuta si raspandita de Computers & Structures, Inc. (CSI).
 - USERUL TREBUIE SA DETINA LICENTE VALIDE: Userul trebuie sa detina licente valide pentru a lucra cu programul ETABS atat si cu EXCEL.
 - FARA AFILIERE: Acest proiect nu este afiliat sau sponsorizat de Computers & Structures, Inc. (CSI).

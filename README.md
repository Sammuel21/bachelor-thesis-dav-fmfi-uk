# bachelor-thesis-dav-fmfi-uk
Bachelor's thesis - Comenius University - FMFI UK - Connectedness between financial assets

Dokumentácia aplikačného systému pre analýzu aktív.

Pre lokálne spustenie klonujte repozitár alebo repozitár extrahujte z elektronickej prílohy práce (ten obsahuje aj dáta).

Program sa delí na dve hlavné časti:

1. Backend: tu prebiehajú výpočty konfigurácií, komunikácia so serverom Shiny a komunikácia so serverom API.
2. Frontend: zastrešuje vizualizačnú aplikáciu Shiny.

Pre otestovanie funkčnosti výpočtovej časti prejdite do priečinka ./API. Následne spustite skript ./API/main.py, ten zastrešuje bežanie API. Prejdite do súboru test.py, ktorý obsahuje šablónu JSONu. Tu môžete bud test.py prepísať alebo si vytvoriť vlastný skript (prípade využiť postmana), ktorý bude obsahovať POST request na URL API endpointu.

Opis JSON atribútov:
- source:
    - jedná sa o dátový zdroj časových radov, s ktorými chceme pracovať (default = 'Yahoo')

- content:
    - obsahuje nadstavenie konfigurácie, ukladania dát a dáta tickerov aktív, ktoré chceme analyzovať

    - output_params:
        - output_dir: výstupný priečinok (default = 'Data/CQ/Tests/')
        - output_file: názov výstupného priečinka
        - save_file: uložiť alebo nie

    - source_params:
        - parametre časových radov
        - start: začiatok časového radu
        - end: koniec časového radu

    - cqgram_params:
        - tau1_list: list kvantilov pre aktívum X
        - tau2_list: list kvantilov pre aktívum Y

    - tickers:
        - JSON analyzovaných aktív vo formáte meno (voľné) : ticker (určený dátovým zdrojom)

Pre testovanie Shiny web app prejdite do domovského priečinku projektu a spustite ./app.py
využitím príkazu 'shiny run --reload --launch-browser app.py' alebo využitím VSCode extenzie Shiny.

IMPORTANT: vizualizácia vlastných výsledkov nieje ešte plne podporovaná, nájdete ju ale na DEV branch. Výpočty fungujú správne.
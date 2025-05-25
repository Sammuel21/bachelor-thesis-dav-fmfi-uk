# bachelor-thesis-dav-fmfi-uk
Bachelor's thesis - Comenius University - FMFI UK - Connectedness between financial assets

Dokumentácia aplikačného systému pre analýzu aktív.

Pre lokálne spustenie klonujte repozitár alebo repozitár extrahujte z elektronickej prílohy práce (ten obsahuje aj dáta).

Program sa delí na dve hlavné časti:

1. Backend: tu prebiehajú výpočty konfigurácií, komunikácia so serverom Shiny a komunikácia so serverom API.
2. Frontend: zastrešuje vizualizačnú aplikáciu Shiny.

Pre otestovanie funkčnosti výpočtovej časti prejdite do priečinka ./API. Následne spustite skript ./API/main.py, ten zastrešuje bežanie API. Prejdite do súboru test.py, ktorý obsahuje šablónu JSONu. Tu môžete bud test.py prepísať alebo si vytvoriť vlastný skript (prípade využiť postmana), ktorý bude obsahovať POST request na URL API endpointu.


Pre testovanie Shiny web app prejdite do domovského priečinku projektu a spustite ./app.py
využitím príkazu 'shiny run --reload --launch-browser app.py' alebo využitím VSCode extenzie Shiny.
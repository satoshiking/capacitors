## Парсер бот на Scrapy  

### Техническое задание
Нужно написать на Scrapy робота который должен со стартовой страницы:

https://ru.mouser.com/Passive-Components/Capacitors/Ceramic-Capacitors/_/N-5g8m

Собрать продукты (в данном случае конденсаторы) и их характеристики.

Необходимые характеристики:
- Номер произв. (например C3225X7R1N106K250AC)
- Производитель (например TDK )
- Описание
- Параметры продукта - Ёмкость, Номинальное напряжение постоянного тока Диэлектрический, Допустимое отклонение и т.д. (список берется со страницы)

Продукты собираются со стартовой страницы + 2 случайных страницы относящихся к этой же категории товаров (на одной странице показывается только часть товаров, остальные доступны по листалке внизу страницы).

Собранные продукты складываются в MongoDB в виде документов (1 продукт - 1 документ).

Нужно написать инструмент который, используя данные MongoDB о собранных документах и используя встроенный функционал MongoDB, формирует аналитические данные о параметрах продуктов - их возможные значения, и также складывает их в MongoDB в виде отдельных документов. Один параметр - один документ. У каждого параметра должно быть название и список его возможных значений. Т.е. в базе в итоге должно появиться содержимое таблички параметров вверху стартовой страницы, но с учетом ранее собранного подмножества продуктов.<br>

Задание оформляется в виде проекта в любом доступном месте.<br>
Проект должен в себя включать:
- Docker compose для запуска Mongo
- Инструкции по запуску в README.md:
#### Для работы скрипта должны быть установлены Python3 и Docker 
### Установка
- git clone https://github.com/satoshiking/capacitors.git<br/>
- cd capacitors<br/>
- python3 -m venv venv<br/>
- source venv/bin/activate<br/>
- pip install -r requirements.txt<br/>
- sudo docker-compose up -d <br/>
- В файле capacitors/settings.py находим строчку: "CRAWLERA_APIKEY = ''"<br>
и вписываем туда ключ от сервиса crawlera*  https://app.scrapinghub.com/ <br/>

________________________________________
*сервис crawlera необходим для обхода ПО "Distil Networks" установленного на сайте по блокированию ботов и средств автоматизации. 

### Запуск приложения
"scrapy crawl capacitors" - для общего запуска приложения <br/>
"python results.py" - только вывод сохранненной информации из mongoDB <br/>

### После завершения работы
sudo docker-compose down

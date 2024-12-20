# Установка и настройка сервиса CAdESS (CAdES Service)
## win service

### подготовка
Пакеты, необходимые для сборки: 
- python3.11

Установите зависимости: 
`$ pip install -r reqs-win.txt`

### сборка
Сборка осуществляется под Windows 11. 
Была попытка собрать сервис под win7, но в какой-то момент она перестала работать. 
Т.к. оффициального пакета python3.11 для win7 не существует, попытки исправить ситуацию прекратились.
Сборка в exe файл осуществляется с помощью пакета `pyinstaller`.
Зависимости: `python3.11`

в проекте есть скрипт `build.bat`. В нём находится команда запуска pyinstaller'а. 
Также имеется файл winsrv.spec.

сборка: 
```
> build.bat
```
после завершения процесса должна быть создана примерно такая структура директорий:
```
dist\
dist\winsrv\
dist\winsrv\_internal\
dist\winsrv\_internal\*
dist\winsrv\winsrv.exe

```
Всё содержимое директории необходимо разместить в директории, определённой под сервис. 
Далее воспользоваться пунктом "установка готовой сборки"

### установка готовой сборки
1. распакуйте и разместите содержимое пакета в любом месте (например `C:\cades`)
2. перейдите в директорию, в которую выполнили распаковку: `cd C:\cades`
3. выполните установку win-сервиса: `winsrv.exe install --startup auto`
(либо `winsrv.exe install --startup manual` если вам нужен ручной запук сервиса)
Сервис появится в srvmngr
4. создайте конфгурационный файл `cades.yaml` в директории сервиса. Вида: 

```yaml
diadoc:
  client-id: <ключ ДИАДОК, выданный ООО Контур> 
  login: <логин пользователя диадок>
  password: <пароль пользователя диадок>
  url: https://diadoc-api.kontur.ru
settings:
  certificate-store: <1|2|3|4 - код хранилища> 
  certnumber: <SerialNumber сертификата, которым будет подписан документ>
  fake-logic: <true|false - для тестов> 
  pincode: <пин-код хранилища (HDIMAGE или аппаратного токена)>
users:
  <user>: <token> # Имя пользователя + токен
whitelist: # Список IP адресов, которым можно обращаться к сервису
- 127.0.0.1
- 192.168.103.1
callbacks: # список URL для обратного вызова.
- http://localhost/test
- https://someserver/suffix
db-connection-string: scheme:///path/to/db-file
```
см. [Пример файла конфигурации](#пример-файла-конфигурации)


## Linux docker container
### Сборка

#### 1. Сборка docker-образа

Пример:
```bash
$ docker build . -t cadess:0.1 \
  --build-arg LICENSE=<ID лицензии> \
  --build-arg PFX_FILE=./path/to/sign-certificate.pfx \
  --build-arg ROOT_PFX_FILE=./path/to/cacert.pfx \
  --build-arg PINCODE=<pin устанавливаемый сертификату>
```

Если у вас есть лицензия КриптоПРО - укажите её через переменную `LICENSE`
В переменную `PFX_FILE` нужно указать путь до сертификата, которым будут подписываться документы
В переменную `ROOT_PFX_FILE` нужно указать путь до корневого сертификата
`PINCODE` - пинкод для контейнера. Он будет установлен. Его же нужно указать в файле конфига cades.yaml
Сертификаты будут помещены в контейнер и импотрированы в процессе сборки образа    

#### 2. Запуск контейнера через docker-compose

Пример:

`$ docker-compose up`


## Пример файла конфигурации
```yaml
diadoc:
  client-id: <ключ ДИАДОК, выданный ООО Контур> 
  login: <логин пользователя диадок>
  password: <пароль пользователя диадок>
  url: https://diadoc-api.kontur.ru
settings:
  certificate-store: <1|2|3|4 - код хранилища> 
  certnumber: <SerialNumber сертификата, которым будет подписан документ>
  fake-logic: <true|false - для тестов> 
  pincode: <пин-код хранилища (HDIMAGE или аппаратного токена)>
users:
  <user>: <token> # Имя пользователя + токен
whitelist: # Список IP адресов, которым можно обращаться к сервису
- 127.0.0.1
- 192.168.103.1
callbacks: # список URL для обратного вызова.
- http://localhost/test
- https://someserver/suffix
db-connection-string: sqlite+aiosqlite:///opt/cades/cades.db
```

### описание некоторых параметров конфига:
- `settings`:
  - `certificate-store`: полностью соответствует вариантам значений из перечисления [CAPICOM_STORE_LOCATION](https://learn.microsoft.com/ru-ru/windows/win32/seccrypto/capicom-store-location)
  - `fake-logic` - для продакшна можно не указывать этот параметр или указать `false`. Нужен для тестов (значение `true`).
      в случае если указано значение `true`, подпись не выполняется и документ в ДИАДОК не отправляется
- `users.<user>:<token>` - нужен для авторизации в сервисе CasCades, передаётся в заголовке Authorization в виде: 
  `Cades <token>`
- `callbacks` - по всем перечисленным URL будет вызван метод POST (с некоторыми полями структуры документа), если произошло изменение статуса документа
    содержимое запроса POST будет примерно таким: 
```json
{
  "uuid": "91f61370-ac63-40bd-824b-c802fc2bf33f",
  "status": "sent",
  "edo_status": "Finish",
  "edo_status_descr": "Документооборот завершен"
} 
```

## Конфигурирование БД
Сервис позволяет работать с разными СУБД. Одним из проверенных и протестированных вариантов является [SQLite](SQLITE-INSTALL.md)
Другим вариантом может быть также [PostgreSQL](PG-INSTALL.md)

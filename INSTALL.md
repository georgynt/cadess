## Установка и настройка сервиса CasCAdES
### win service
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
```

### описание некоторых параметров:
секция `settings`:
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

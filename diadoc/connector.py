import asyncio
from urllib.parse import urljoin
from uuid import UUID

from requests import Response, Session

from diadoc.exceptions import AuthError
from diadoc.struct import (Counteragent, CounteragentList, DocflowStatusModel, DocumentId, DocumentV3,
                           GetDocflowBatchRequest, GetDocflowRequest, Message, MessageToPost, Organization,
                           OrganizationList)
from singleton import Singleton


SUCCESS_CODES = [200, 201]

AUTH = 'Authorization'
AUTH_PREFIX = "DiadocAuth"
APP_JSON = 'application/json'

client_id_param_name = "ddauth_api_client_id"
ddauth_token_param_name = "ddauth_token"


class AuthContainer(metaclass=Singleton):
    def __init__(self):
        from config import Config

        self.conf = Config()
        self._login = self.conf.diadoc_login
        self._password = self.conf.diadoc_password
        self._api_client_id = self.conf.client_id

    @property
    def login(self) -> str:
        return self._login

    @login.setter
    def login(self, value: str):
        self._login = value

    @property
    def password(self) -> str:
        return self._password

    @password.setter
    def password(self, value: str):
        self._password = value

    @property
    def api_token(self) -> str:
        return getattr(self,'_api_token',None)

    @api_token.setter
    def api_token(self, value: str):
        self._api_token = value

    @api_token.deleter
    def api_token(self):
        if hasattr(self,'_api_token'):
            del self._api_token

    @property
    def api_client_id(self) -> str:
        return getattr(self,'_api_client_id',None)

    @api_client_id.setter
    def api_client_id(self, value: str):
        self._api_client_id = value

    @property
    def header(self) -> str:
        ddauth_token_header = ""
        if self.api_token:
            ddauth_token_header = f",{ddauth_token_param_name}={self.api_token}"
        return f"{AUTH_PREFIX} {client_id_param_name}={self.api_client_id}{ddauth_token_header}"

    @property
    def is_authenticated(self) -> bool:
        return bool(hasattr(self, '_api_token') and self.api_token)


class DiadocSession(Session):
    def __init__(self, url_base: str, api_obj: 'DiadocAPI'):
        super().__init__()
        self.url_base = url_base
        self._api_obj = api_obj
        self.headers['Content-Type'] = APP_JSON
        self.headers['Accept'] = APP_JSON
        self.auth_c = AuthContainer()

    def request(self, method, url, *args, **kwargs):
        self.headers[AUTH] = self.auth_c.header
        joined_url = urljoin(self.url_base, url)
        self._resp = super().request(method, joined_url, *args, **kwargs)
        if self._resp.status_code == 401:
            del self.auth_c.api_token
            self._api_obj.reauthenticate()
            self.headers[AUTH] = self.auth_c.header
            self._resp = super().request(method, joined_url, *args, **kwargs)
        return self._resp

    def is_status_ok(self) -> bool:
        return self._resp.status_code in SUCCESS_CODES


class DiadocAPI:
    def __init__(self, url, api_client_id):
        self.url = url
        self.sess = DiadocSession(self.url, self)
        self.auth_c = AuthContainer()
        self.auth_c.api_client_id = api_client_id

    def authenticate(self, login: str, password: str) -> bool:
        self.auth_c.login = login
        self.auth_c.password = password
        res = self.sess.post("/V3/Authenticate",
                             json={"login"   : self.auth_c.login,
                                   "password": self.auth_c.password},
                             params={"type": "password"})
        if res.status_code in SUCCESS_CODES:
            self.auth_c.api_token = res.content.decode()
            return True
        raise AuthError(res.content)

    def reauthenticate(self) -> bool:
        return self.authenticate(self.auth_c.login, self.auth_c.password)

    def is_last_ok(self) -> bool:
        return self.sess.is_status_ok()

    def get_my_orgs(self, autoreg: bool = True) -> list[Organization]:
        res = self.sess.get('/GetMyOrganizations',
                            params={'autoRegister': 'true' if autoreg else 'false'})
        if res.status_code in SUCCESS_CODES:
            orgs = OrganizationList.parse_raw(res.content)
            return orgs.Organizations
        else:
            return []

    def get_ctgs(self, box: UUID,
                 ctg_status: str|None = None,
                 aindex_key: str|None = None,
                 query: str|None = None) -> list|str:
        params = {'myBoxId': str(box)}
        if ctg_status:
            params['counteragentStatus'] = ctg_status
        if aindex_key:
            params['afterIndexKey'] = aindex_key
        if query:
            params['query'] = query

        res = self.sess.get('/V3/GetCounteragents', params=params)
        if res.status_code in SUCCESS_CODES:
            return CounteragentList.parse_raw(res.content).Counteragents
        return res.content.decode()

    def post_message(self,
                     msg: MessageToPost,
                     boxId: UUID|None = None,
                     operationId: str|None = None) -> Message|Response|None:
        rd = msg.model_dump_json()

        # params = {'boxId': boxId}
        params = {}
        if boxId:
            params['boxId'] = str(boxId)
        if operationId:
            params['operationId'] = operationId

        res = self.sess.post("/V3/PostMessage",
                             params=params,
                             data=rd)
        if res.status_code in SUCCESS_CODES:
            return Message.parse_raw(res.content)
        else:
            return res

    async def apost_message(self,
                            msg: MessageToPost,
                            boxId: UUID|None = None,
                            operationId: str|None = None) -> Message|Response|None:
        return await asyncio.to_thread(self.post_message, msg, boxId, operationId)

    def get_orgs_by_innkpp(self, inn: str|None = None, kpp: str|None = None) -> list[Organization]:
        params = {
            **{'inn': inn for _ in [inn] if inn},
            **{'kpp': kpp for _ in [kpp] if kpp},
        }

        res = self.sess.get("/GetOrganizationsByInnKpp", params=params)
        if res.status_code in SUCCESS_CODES:
            return OrganizationList.parse_raw(res.content).Organizations
        return []

    def get_ctg(self, myBoxId: UUID, counteragentBoxId: UUID) -> Counteragent|str:
        res = self.sess.get("/V3/GetCounteragent",
                            params={
                                'myBoxId'          : str(myBoxId),
                                'counteragentBoxId': str(counteragentBoxId)
                            })
        if res.status_code in SUCCESS_CODES:
            return Counteragent.parse_raw(res.content)
        return res.content.decode()

    def get_message(self, boxId: UUID, messageId: UUID, entityId: UUID|None = None) -> dict|str:
        res = self.sess.get("/V5/GetMessage",
                            params={
                                "boxId"    : str(boxId),
                                "messageId": str(messageId),
                                **{"entityId": str(entityId)
                                   for _ in [0]
                                   if entityId}})
        if res.status_code in SUCCESS_CODES:
            return res.json()
        return res.content.decode()

    def get_docflows(self, boxId: UUID, messageId: UUID, documentId: UUID) -> list|str:
        data = GetDocflowBatchRequest(GetDocflowsRequests=[
            GetDocflowRequest(DocumentId=DocumentId(MessageId=messageId, EntityId=documentId))
        ]).model_dump_json()
        res = self.sess.post("/V3/GetDocflows",
                             params={"boxId": str(boxId)},
                             data=data)
        if self.is_last_ok():
            return res.json()['Documents']
        return res.content.decode()

    def get_document(self, boxId: UUID, messageId: UUID, documentId: UUID) -> DocumentV3|str:
        res = self.sess.get("/V3/GetDocument", params={"boxId"    : str(boxId),
                                                       "messageId": str(messageId),
                                                       "entityId" : str(documentId)})
        if self.is_last_ok():
            return DocumentV3.parse_raw(res.content)
        return res.content.decode()

    def get_document_status(self, boxId: UUID, messageId: UUID, documentId: UUID) -> DocflowStatusModel|None:
        if isinstance(doc := self.get_document(boxId, messageId, documentId), DocumentV3):
            return doc.DocflowStatus.PrimaryStatus
        return None

    async def aget_document_status(self, boxId: UUID, messageId: UUID, documentId: UUID) -> DocflowStatusModel|None:
        return await asyncio.to_thread(self.get_document_status, boxId, messageId, documentId)


class ConfiguredDiadocAPI(DiadocAPI):
    def __init__(self):
        from config import Config

        self.cnf = Config()
        super().__init__(self.cnf.diadoc_url, self.cnf.client_id)


class AuthdDiadocAPI(ConfiguredDiadocAPI):
    def __init__(self):
        super().__init__()
        self.authenticate(self.cnf.diadoc_login, self.cnf.diadoc_password)  # ИМЕННО от SUPER!

    def authenticate(self, login: str, password: str) -> bool:
        if not self.auth_c.is_authenticated:
            return super().authenticate(login, password)
        return True

    def reauthenticate(self) -> bool:
        return super().authenticate(self.auth_c.login, self.auth_c.password)

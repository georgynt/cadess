from urllib.parse import urljoin
from uuid import UUID, uuid4

from requests import Response, Session

from diadoc.struct import (Counteragent, CounteragentList, DocumentId, GetDocflowBatchRequest, GetDocflowRequest,
                           Message,
                           MessageToPost, Organization,
                           OrganizationList)


SUCCESS_CODES = [200, 201]

AUTH = 'Authorization'
AUTH_PREFIX = "DiadocAuth"
APP_JSON = 'application/json'

clid = "priceplan-50855e2a-2640-4f6f-bae8-8ffff4722a4f"
client_id_param_name = "ddauth_api_client_id"
ddauth_token_param_name = "ddauth_token"


class DiadocSession(Session):
    def __init__(self, url_base):
        super().__init__()
        self.url_base = url_base
        self.headers['Content-Type'] = APP_JSON
        self.headers['Accept'] = APP_JSON

    def request(self, method, url, *args, **kwargs):
        joined_url = urljoin(self.url_base, url)
        self._resp = super().request(method, joined_url, *args, **kwargs)
        return self._resp

    def is_status_ok(self) -> bool:
        return self._resp.status_code in SUCCESS_CODES


class DiadocAPI:

    def __init__(self, api_client_id=None):
        self.url = 'https://diadoc-api.kontur.ru'
        self.sess = DiadocSession(self.url)
        self.api_client_id = api_client_id
        self.sess.headers[AUTH] = self.header

    @property
    def api_client_id(self) -> str:
        return getattr(self, '_api_client_id', "")

    @api_client_id.setter
    def api_client_id(self, value: str):
        self._api_client_id = value

    @property
    def api_token(self) -> str:
        return getattr(self, '_api_token', "")

    @api_token.setter
    def api_token(self, value: str):
        self._api_token = value

    @property
    def header(self) -> str:
        return (f"{AUTH_PREFIX} {client_id_param_name}={self.api_client_id}" +
                (f",{ddauth_token_param_name}={self.api_token}" if self.api_token else ""))

    def authenticate(self):
        res = self.sess.post("/V3/Authenticate",
                             json={"login"   : "georgynt@mail.ru",
                                   "password": "Z.HB6Qv7:Apg)'%"},
                             params={"type": "password"})
        if res.status_code in SUCCESS_CODES:
            self.api_token: str = res.content.decode()
            self.sess.headers[AUTH] = self.header
            return True
        return False

    def is_authenticated(self) -> bool:
        return bool(hasattr(self, '_api_token') and self.api_token)

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

    def get_orgs_by_innkpp(self, inn: str|None = None, kpp: str|None = None) -> list[Organization]:
        params = {}
        if inn:
            params['inn'] = inn
        if kpp:
            params['kpp'] = kpp

        res = self.sess.get("/GetOrganizationsByInnKpp", params=params)
        if res.status_code in SUCCESS_CODES:
            return OrganizationList.parse_raw(res.content).Organizations
        return []

    def get_ctg(self, myBoxId: UUID, counteragentBoxId: UUID) -> Counteragent|str:
        res = self.sess.get("/V3/GetCounteragent",
                            params={
                                'myBoxId': str(myBoxId),
                                'counteragentBoxId': str(counteragentBoxId)
                            })
        if res.status_code in SUCCESS_CODES:
            return Counteragent.parse_raw(res.content)
        return res.content.decode()

    def get_message(self, boxId: UUID, messageId: UUID, entityId: UUID|None = None) -> dict|str:
        res = self.sess.get("/V5/GetMessage",
                            params={
                                "boxId": str(boxId),
                                "messageId": str(messageId),
                                **{"entityId": str(entityId)
                                        for _ in [0]
                                            if entityId}})
        if res.status_code in SUCCESS_CODES:
            return res.json()
        return res.content.decode()

    def get_docflows(self, boxId: UUID) -> list|str:
        data = GetDocflowBatchRequest(GetDocflowsRequests=[
                GetDocflowRequest(DocumentId=DocumentId(MessageId='39bb9074-76a4-4c93-babb-50c05367398e'))
            ]).model_dump_json()
        res = self.sess.post("/V3/GetDocflows",
                             params={
                                 "boxId": str(boxId)
                             },
                             data=data)
        if self.is_last_ok():
            return res.json()['Documents']
        return res.content.decode()


class AuthdDiadocAPI(DiadocAPI):
    def __init__(self):
        from config import Config

        cnf = Config()
        super().__init__(cnf.client_id)

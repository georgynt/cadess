from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel
from .enums import *


class CadesStruct(BaseModel):
    def model_dump_json(self, **kwargs) -> str:
        kwargs['exclude_none'] = True
        kwargs['exclude_unset'] = True
        return super().model_dump_json(**kwargs)


class StructuredDataAttachment(CadesStruct):
    Content: bytes
    FileName: str
    DocumentId: str
    # ParentCustomDocumentId: str


class DocumentId(CadesStruct):
    MessageId: UUID
    # MessageId: str
    EntityId: UUID|None = None
    # EntityId: str


class CustomDataItem(CadesStruct):
    Key: str
    Value: Optional[str] = None


class MetadataItem(CadesStruct):
    Key: str
    Value: str


class SignedContent(CadesStruct):
    Content: Optional[bytes] = None
    Signature: Optional[bytes] = None
    NameOnShelf: Optional[str] = None
    SignWithTestSignature: Optional[bool] = False
    SignatureNameOnShelf: Optional[str] = None
    # Пока что bytes, потом доделаем. Там капец как много всяких структур
    PowerOfAttorney: Optional[bytes] = None


class DocumentAttachment(CadesStruct):
    SignedContent: SignedContent
    Comment: Optional[str] = None
    NeedRecipientSignature: bool = False
    InitialDocumentIds: Optional[list[DocumentId]] = None
    SubordinateDocumentIds: Optional[list[DocumentId]] = None
    CustomDocumentId: Optional[str] = None
    NeedReceipt: bool = False
    CustomData: Optional[list[CustomDataItem]] = None
    TypeNamedId: str
    Function: Optional[str] = None
    Version: Optional[str] = None
    Metadata: list[MetadataItem]
    WorkflowId: Optional[int] = None
    IsEncrypted: bool = False
    EditingSettingId: Optional[str] = None


class MessageToPost(CadesStruct):
    FromBoxId: str
    ToBoxId: str
    StructuredDataAttachments: Optional[list[StructuredDataAttachment|DocumentAttachment]] = None
    ToDepartmentId: Optional[str] = None
    IsDraft: bool = False
    LockDraft: bool = False
    StrictDraftValidation: bool = True
    IsInternal: bool = False
    FromDepartmentId: Optional[str] = None
    DelaySend: bool = False
    ProxyBoxId: Optional[str] = None
    ProxyDepartmentId: Optional[str] = None
    LockPacket: bool = False
    DocumentAttachments: Optional[list[DocumentAttachment]] = None
    LockMode: LockModeEnum = LockModeEnum.NONE


class Message(CadesStruct):
    MessageId: str
    TimestampTicks: int
    LastPatchTimestampTicks: int
    FromBoxId: str
    FromTitle: str
    ToBoxId: Optional[str] = None
    ToTitle: Optional[str] = None
    Entities: list[dict]
    IsDraft: bool = False
    DraftIsLocked: bool = False
    DraftIsRecycled: bool = False
    CreatedFromDraftId: Optional[str] = None
    DraftIsTransformedToMessageIdList: list[str]
    IsDeleted: bool = False
    IsTest: bool = False
    IsInternal: bool = False
    IsProxified: bool = False
    ProxyBoxId: Optional[str] = None
    ProxyTitle: Optional[str] = None
    PacketIsLocked: bool = False
    LockMode: Optional[LockModeEnum|str] = None
    MessageType: object
    TemplateToLetterTransformationInfo: Optional[Any] = None
    IsReusable: bool = False


class Box(CadesStruct):
    BoxId: str
    Title: str
    Organization: Optional[dict] = None
    InvoiceFormatVersion: Optional[OrganizationInvoiceFormatVersion] = OrganizationInvoiceFormatVersion.v5_02
    EncryptedDocumentsAllowed: bool = False
    BoxIdGuid: str


class Organization(CadesStruct):
    OrgId: str
    Inn: str
    Kpp: Optional[str] = None
    FullName: str
    ShortName: Optional[str] = None
    Boxes: Optional[list[Box]] = None
    Ogrn: Optional[str] = None
    FnsParticipantId: Optional[str] = None
    Address: Optional[dict] = None
    FnsRegistrationDate: Optional[str] = None
    Departments: Optional[list[dict]] = None
    IfnsCode: Optional[str] = None
    IsPilot: Optional[bool] = None
    IsActive: Optional[bool] = None
    IsTest: Optional[bool] = None
    IsBranch: Optional[bool] = None
    IsRoaming: Optional[bool] = None
    IsEmployee: Optional[bool] = None
    InvitationCount: Optional[int] = None
    SearchCount: Optional[int] = None
    Sociability: dict|str
    LiquidationDate: Optional[str] = None
    CertificateOfRegistryInfo: Optional[str] = None
    IsForeign: Optional[bool] = None
    HasCertificateToSign: Optional[bool] = None


class OrganizationList(CadesStruct):
    Organizations: list[Organization]


class Counteragent(CadesStruct):
    IndexKey: Optional[str] = None
    Organization: Organization
    CurrentStatus: Optional[CounteragentStatus] = CounteragentStatus.UnknownCounteragentStatus
    LastEventTimestampTicks: float
    MessageFromCounteragent: Optional[str] = None
    MessageToCounteragent: Optional[str] = None
    InvitationDocumentId: Optional[DocumentId] = None
    CounteragentGroupId: Optional[str] = None

class CounteragentList(CadesStruct):
    TotalCount: int
    Counteragents: list[Counteragent]
    TotalCountType: str

class GetDocflowRequest(CadesStruct):
    DocumentId: DocumentId
    LastEventId: str|None = None
    InjectEntityContent: bool = False


class GetDocflowBatchRequest(CadesStruct):
    GetDocflowsRequests: list[GetDocflowRequest]


class DocflowStatusModel(CadesStruct):
    Severity: Optional[str] = None
    StatusText: Optional[str] = None


class DocflowStatus(CadesStruct):
    PrimaryStatus: DocflowStatusModel
    SecondaryStatus: Optional[DocflowStatusModel] = None
    PowerOfAttorneyGeneralStatus: Optional[dict] = None
    GeneralRoamingSendingStatus: Optional[dict] = None


class DocumentV3(CadesStruct):
    DocflowStatus: DocflowStatus

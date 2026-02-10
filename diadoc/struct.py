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
    EntityId: UUID | None = None
    # EntityId: str


class CustomDataItem(CadesStruct):
    Key: str
    Value: str | None = None


class MetadataItem(CadesStruct):
    Key: str
    Value: str


class PowerOfAttorneyFullId(CadesStruct):
    RegistrationNumber: str
    IssuerInn: str
    RepresentativeInn: str


class Content_v3(CadesStruct):
    Content: bytes | None
    NameOnShelf: str | None
    EntityId: DocumentId | None
    PatchedContentId: str | None


class PowerOfAttorneySignedContent(CadesStruct):
    Content: Content_v3
    Signature: Content_v3


class PowerOfAttorneyToPost(CadesStruct):
    FullId: PowerOfAttorneyFullId | None = None
    UseDefault: bool = False
    # Content: PowerOfAttorneySignedContent | None = None # deprecated. use Contents
    SendAsFile: bool | None = None
    Contents: list[PowerOfAttorneySignedContent] = []
    UseDocumentContent: bool | None = None


class SignedContent(CadesStruct):
    Content: bytes | None = None
    Signature: bytes | None = None
    NameOnShelf: str | None = None
    SignWithTestSignature: bool | None = False
    SignatureNameOnShelf: str | None = None
    PowerOfAttorney: PowerOfAttorneyToPost | None = None


class DocumentAttachment(CadesStruct):
    SignedContent: SignedContent
    Comment: str | None = None
    NeedRecipientSignature: bool = False
    InitialDocumentIds: Optional[list[DocumentId]] = None
    SubordinateDocumentIds: Optional[list[DocumentId]] = None
    CustomDocumentId: str | None = None
    NeedReceipt: bool = False
    CustomData: Optional[list[CustomDataItem]] = None
    TypeNamedId: str
    Function: str | None = None
    Version: str | None = None
    Metadata: list[MetadataItem]
    WorkflowId: int | None = None
    IsEncrypted: bool = False
    EditingSettingId: str | None = None


class MessageToPost(CadesStruct):
    FromBoxId: str
    ToBoxId: str
    StructuredDataAttachments: Optional[list[StructuredDataAttachment | DocumentAttachment]] = None
    ToDepartmentId: str | None = None
    IsDraft: bool = False
    LockDraft: bool = False
    StrictDraftValidation: bool = True
    IsInternal: bool = False
    FromDepartmentId: str | None = None
    DelaySend: bool = False
    ProxyBoxId: str | None = None
    ProxyDepartmentId: str | None = None
    LockPacket: bool = False
    DocumentAttachments: Optional[list[DocumentAttachment]] = None
    LockMode: LockModeEnum = LockModeEnum.NONE


class Message(CadesStruct):
    MessageId: str
    TimestampTicks: int
    LastPatchTimestampTicks: int
    FromBoxId: str
    FromTitle: str
    ToBoxId: str | None = None
    ToTitle: str | None = None
    Entities: list[dict]
    IsDraft: bool = False
    DraftIsLocked: bool = False
    DraftIsRecycled: bool = False
    CreatedFromDraftId: str | None = None
    DraftIsTransformedToMessageIdList: list[str]
    IsDeleted: bool = False
    IsTest: bool = False
    IsInternal: bool = False
    IsProxified: bool = False
    ProxyBoxId: str | None = None
    ProxyTitle: str | None = None
    PacketIsLocked: bool = False
    LockMode: Optional[LockModeEnum | str] = None
    MessageType: object
    TemplateToLetterTransformationInfo: Any | None = None
    IsReusable: bool = False


class Box(CadesStruct):
    BoxId: str
    Title: str
    Organization: dict | None = None
    InvoiceFormatVersion: OrganizationInvoiceFormatVersion | None = OrganizationInvoiceFormatVersion.v5_02
    EncryptedDocumentsAllowed: bool = False
    BoxIdGuid: str


class Organization(CadesStruct):
    OrgId: str
    Inn: str
    Kpp: str | None = None
    FullName: str
    ShortName: str | None = None
    Boxes: Optional[list[Box]] = None
    Ogrn: str | None = None
    FnsParticipantId: str | None = None
    Address: dict | None = None
    FnsRegistrationDate: str | None = None
    Departments: Optional[list[dict]] = None
    IfnsCode: str | None = None
    IsPilot: bool | None = None
    IsActive: bool | None = None
    IsTest: bool | None = None
    IsBranch: bool | None = None
    IsRoaming: bool | None = None
    IsEmployee: bool | None = None
    InvitationCount: int | None = None
    SearchCount: int | None = None
    Sociability: dict | str
    LiquidationDate: str | None = None
    CertificateOfRegistryInfo: str | None = None
    IsForeign: bool | None = None
    HasCertificateToSign: bool | None = None


class OrganizationList(CadesStruct):
    Organizations: list[Organization]


class Counteragent(CadesStruct):
    IndexKey: str | None = None
    Organization: Organization
    CurrentStatus: CounteragentStatus | None = CounteragentStatus.UnknownCounteragentStatus
    LastEventTimestampTicks: float
    MessageFromCounteragent: str | None = None
    MessageToCounteragent: str | None = None
    InvitationDocumentId: DocumentId | None = None
    CounteragentGroupId: str | None = None


class CounteragentList(CadesStruct):
    TotalCount: int
    Counteragents: list[Counteragent]
    TotalCountType: str


class GetDocflowRequest(CadesStruct):
    DocumentId: DocumentId
    LastEventId: str | None = None
    InjectEntityContent: bool = False


class GetDocflowBatchRequest(CadesStruct):
    GetDocflowsRequests: list[GetDocflowRequest]


class DocflowStatusModel(CadesStruct):
    Severity: str | None = None
    StatusText: str | None = None


class DocflowStatus(CadesStruct):
    PrimaryStatus: DocflowStatusModel
    SecondaryStatus: DocflowStatusModel | None = None
    PowerOfAttorneyGeneralStatus: dict | None = None
    GeneralRoamingSendingStatus: dict | None = None


class DocumentV3(CadesStruct):
    DocflowStatus: DocflowStatus

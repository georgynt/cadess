from enum import StrEnum


class LockModeEnum(StrEnum):
    NONE = 'None'
    SEND = 'Send'
    FULL = 'Full'


class OrganizationInvoiceFormatVersion(StrEnum):
    v5_01 = 'v5_01'
    v5_02 = 'v5_02'


class CounteragentStatus(StrEnum):
    UnknownCounteragentStatus = 'UnknownCounteragentStatus'
    IsMyCounteragent = 'IsMyCounteragent'
    InvitesMe = 'InvitesMe'
    IsInvitedByMe = 'IsInvitedByMe'
    RejectsMe = 'RejectsMe'
    IsRejectedByMe = 'IsRejectedByMe'
    NotInCounteragentList = 'NotInCounteragentList'


class DiadocDocumentType(StrEnum):
    ProformaInvoice = 'ProformaInvoice'

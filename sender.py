import asyncio
from asyncio import sleep
from uuid import uuid4

from requests import Response
from sqlalchemy import select

import logger
from const import DocumentStatus
from db import Document, Session
from diadoc.connector import AuthdDiadocAPI
from diadoc.enums import DiadocDocumentType
from diadoc.struct import Counteragent, DocumentAttachment, Message, MessageToPost, MetadataItem, SignedContent


def send_document(doc: Document) -> Document:
    dda = AuthdDiadocAPI()
    dda.authenticate()

    doc.status = DocumentStatus.PROGRESS

    sbox = doc.source_box
    if not (dbox := doc.dest_box):
        orgs = dda.get_orgs_by_innkpp(doc.dest_inn, doc.dest_kpp)
        if not len(orgs):
            doc.tries+=1
            return doc

        org = orgs[0]
        dbox = org.Boxes[0].BoxIdGuid

    if isinstance(ctg := dda.get_ctg(sbox, dbox), Counteragent):
        try:
            sc = SignedContent(Content=doc.signed_data,
                               Signature=doc.sign)
            if not doc.message_id:
                doc.message_id = uuid4()

            da = DocumentAttachment(
                SignedContent=sc,
                TypeNamedId=DiadocDocumentType.ProformaInvoice,
                Metadata=[
                    MetadataItem(Key='FileName', Value=doc.name),
                    MetadataItem(Key='DocumentNumber', Value=doc.number),
                    MetadataItem(Key="DocumentDate", Value=doc.date_as_str),
                    MetadataItem(Key="Grounds", Value=doc.name),
                    MetadataItem(Key="TotalSum", Value=str(doc.amount)),
                    MetadataItem(Key="TotalVat", Value=str(doc.vat))]
            )

            postmsg = MessageToPost(
                FromBoxId=str(sbox),
                ToBoxId=dbox,
                DocumentAttachments=[da]
            )

            if isinstance(msg := dda.post_message(postmsg), Message):
                logger.info(msg)
                doc.status = DocumentStatus.SENT # тут надо сделать проверку, какой ответ получили
                doc.error_msg = None
            elif isinstance(msg, Response):
                if msg.status_code not in (200,201):
                    logger.error(msg.content)
                    doc.status = DocumentStatus.FAIL
                    doc.error_msg = msg.content
                else:
                    logger.info(msg.content)

        except Exception as e:
            doc.tries += 1
            doc.error_msg = str(e)
            logger.error(doc.error_msg)
    elif isinstance(ctg, str):
        doc.status = DocumentStatus.FAIL
        doc.error_msg = f"Ошибка: {ctg}"
        doc.tries = 5

    return doc


async def handle_documents() -> None:
    """ Запускается в единственном экземпляре. Более одного инстанса одновременно не работает,
        что в общем-то и требуется
    """
    while True:
        try:
            async with Session() as ss:
                docs = await ss.execute(select(Document)
                                        .where(Document.status.in_([DocumentStatus.RECEIVED, DocumentStatus.PROGRESS])
                                               & (Document.tries < 5)).with_for_update(skip_locked=True))
                for (doc,) in docs:

                    doc = await asyncio.to_thread(send_document, doc)
                    ss.add(doc)

                await ss.commit()

        except Exception as e:
            logger.error(str(e))

        await sleep(60)


async def init_repeat_task() -> None:
    asyncio.create_task(handle_documents())

import datetime
import hashlib
import hmac
from urllib.parse import urlparse

from constants import YANDEX_ACCESS_KEY, YANDEX_SECRET_KEY


class AwsSignatureV4:
    """
    Подписывание запросов
    https://cloud.yandex.ru/docs/storage/s3/signing-requests
    """
    def __init__(self, service):
        self.service = service
        self.access_key = YANDEX_ACCESS_KEY
        self.secret_key = YANDEX_SECRET_KEY
        self.region = 'ru-central1'

    def __call__(self, method: str, url: str, payload) -> dict:

        date_time = datetime.datetime.utcnow()

        self.amz_date = date_time.strftime('%Y%m%dT%H%M%SZ')
        self.datestamp = date_time.strftime('%Y%m%d')

        url_obj = urlparse(url)
        host = url_obj.hostname

        path = url_obj.path

        if len(url_obj.query) > 0:
            query_dict = dict(map(lambda i: i.split('='), url_obj.query.split('&')))
        else:
            query_dict = dict()

        canonical_querystring = "&".join(map(lambda param: "=".join(param), sorted(query_dict.items())))

        if method == 'GET':
            payload_hash = hashlib.sha256(''.encode('utf-8')).hexdigest()
        else:
            if payload:

                if isinstance(payload, bytes):
                    payload_hash = hashlib.sha256(payload).hexdigest()
                else:
                    payload_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()
            else:
                payload_hash = hashlib.sha256(b'').hexdigest()

        headers = {
            'Host': host,
            'Content-Type': 'image/jpeg',
            'x-amz-date': self.amz_date,
            'x-amz-content-sha256': payload_hash
        }

        headers_to_sign = sorted(filter(lambda h: h.startswith('x-amz-') or h == 'Host',
                                        map(lambda hed: hed.lower(), headers.keys())))
        canonical_headers = ''.join(map(lambda h: ":".join((h, headers[h])) + '\n', headers_to_sign))

        signed_headers = ';'.join(headers_to_sign)

        canonical_request = '\n'.join([method, path, canonical_querystring,
                                       canonical_headers, signed_headers, payload_hash])

        credential_scope = '/'.join([self.datestamp, self.region, self.service, 'aws4_request'])

        string_to_sign = '\n'.join(['AWS4-HMAC-SHA256', self.amz_date,
                                    credential_scope, hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()])

        date = self.sign_msg(('AWS4' + self.secret_key).encode('utf-8'), self.datestamp)
        region = self.sign_msg(date, self.region)
        service = self.sign_msg(region, self.service)
        signing = self.sign_msg(service, 'aws4_request')
        signature = hmac.new(signing, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

        headers['Authorization'] = "AWS4-HMAC-SHA256 Credential={}/{}, SignedHeaders={}, Signature={}".format(
            self.access_key, credential_scope, signed_headers, signature)

        return headers

    @staticmethod
    def sign_msg(key, msg):

        return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

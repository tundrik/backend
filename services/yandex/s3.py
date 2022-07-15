import asyncio
import os
import time
import httpx
import dhash
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile

from base.helpers import generate_uuid
from services.yandex.signature import AwsSignatureV4


class YandexUploader:
    def __init__(self):
        self.aws_auth = AwsSignatureV4('s3')
        self.endpoint = 'https://storage.yandexcloud.net/graph'
        self.client = httpx.AsyncClient(timeout=None)
        self.files = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self.client.aclose()

    async def profile_upload(self, file):
        with Image.open(file) as pil_image:
            new_image_300 = self._crop_center(pil_image, min(pil_image.size), min(pil_image.size))
            image_name = self._get_hash_hex(new_image_300)

        await self.upload_image(new_image_300, name=image_name, width="profile")
        return image_name

    async def image_upload(self, file):
        new_image_420, new_image_1200, image_name = self.preparation_file(file)
        await self.upload_image(new_image_420, name=image_name, width=420)
        await self.upload_image(new_image_1200, name=image_name, width=1200)
        return image_name

    async def video_upload(self, file):
        image_name = await self.upload_video(file)
        return image_name

    async def tasks_executor_upload(self, images: list[InMemoryUploadedFile]):
        cpu_count = os.cpu_count()
        loop = asyncio.get_event_loop()

        with ThreadPoolExecutor(max_workers=cpu_count) as executor:
            tasks = []
            for index, file in enumerate(images, start=0):

                if isinstance(file, InMemoryUploadedFile):
                    task = loop.run_in_executor(executor, self.preparation_file, file)
                    tasks.append(task)

            futures = await asyncio.gather(*tasks, return_exceptions=True)

        # TODO: Мы можем вернуть ответ или подождать пока все загрузим в Яндекс
        names = []
        tasks = []

        for new_image_420, new_image_1200, image_name in futures:
            task_420 = asyncio.ensure_future(self.upload_image(new_image_420, name=image_name, width=420))
            task_1200 = asyncio.ensure_future(self.upload_image(new_image_1200, name=image_name, width=1200))
            tasks.append(task_420)
            tasks.append(task_1200)
            names.append(image_name)

        result = await asyncio.gather(*tasks, return_exceptions=True)
        print(result)
        return names

    def preparation_file(self, file):
        with Image.open(file) as pil_image:
            new_image_420 = self._image_resize(pil_image, width=420)
            new_image_1200 = self._image_resize(pil_image, width=1200)
            image_name = self._get_hash_hex(new_image_420)

        return new_image_420, new_image_1200, image_name

    async def upload_video(self, file):
        name = "video_" + str(generate_uuid())
        url = f'{self.endpoint}/video/{name}.mp4'
        buffer = BytesIO()
        buffer.seek(0)
        buffer_bytes = file.read()
        headers = self.aws_auth(method='PUT', url=url, payload=buffer_bytes)
        response = await self.client.request('PUT', url, content=buffer_bytes, headers=headers)
        return name

    async def upload_image(self, new_image, *, name, width):
        """
        Загружает изображения в Yandex s3
        :param new_image: Объект Image Pillow
        :param name:  hash hex (или md5 hash, должна быть уникальная строка для ключа)
        :param width: Ширина (для именования пути)
        :return: status code

        Чтобы убедиться, что объект передан по сети без повреждений, используйте заголовок Content-MD5.
        Object Storage вычислит MD5 для сохраненного объекта и если вычисленная MD5 не совпадет
        с переданной в заголовке, вернет ошибку. Эту проверку можно выполнить и на стороне клиента,
        сравнив ETag из ответа Object Storage с предварительно вычисленной MD5.
            md5_hash_hex = hashlib.md5(buffer_bytes)
            print("md5_hash_hex", md5_hash_hex.hexdigest())
        """
        buffer = BytesIO()
        new_image.save(buffer, "JPEG", progressive=True)
        buffer.seek(0)
        buffer_bytes = buffer.read()
        url = f'{self.endpoint}/{width}/{name}.jpeg'
        headers = self.aws_auth(method='PUT', url=url, payload=buffer_bytes)
        response = await self.client.request('PUT', url, content=buffer_bytes, headers=headers)
        print(response)
        if response.status_code == 200:
            return response.status_code
        return response.status_code

    async def delete_image(self, *, name, width):
        url = f'{self.endpoint}/{width}/{name}.jpeg'
        headers = self.aws_auth(method='DELETE', url=url, payload=None)
        response = await self.client.request('DELETE', url, headers=headers)
        print(response)
        if response.status_code == 200:
            return response.status_code
        return response.status_code

    @staticmethod
    def _get_hash_hex(new_image):
        """
        Вычесляет dhash
        :param new_image: Объект Image Pillow
        :return: hash hex
        """
        row, col = dhash.dhash_row_col(new_image)
        hash_hex = dhash.format_hex(row, col)
        return hash_hex

    @staticmethod
    def _image_resize(pil_image, *, width: int = 420):
        """
        Пропорционально уменьшает изображение до указанной ширины
        :param pil_image: Объект Image Pillow
        :param width: Ширина
        :return: Объект Image Pillow
        """
        if pil_image.mode in ("RGBA", "P"):
            pil_image = pil_image.convert("RGB")

        cent = (width / float(pil_image.size[0]))
        size = int((float(pil_image.size[1]) * float(cent)))
        new_image = pil_image.resize((width, size), Image.ANTIALIAS)
        return new_image

    @staticmethod
    def _crop_center(pil_image, crop_width, crop_height):
        img_width, img_height = pil_image.size
        crop = pil_image.crop(((img_width - crop_width) // 2,
                               (img_height - crop_height) // 2,
                               (img_width + crop_width) // 2,
                               (img_height + crop_height) // 2))
        return crop.resize((300, 300), Image.ANTIALIAS)

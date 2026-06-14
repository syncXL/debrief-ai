# services/storage.py
import abc
import asyncio
import cloudinary
import cloudinary.uploader
import io

class AudioStorage(abc.ABC):

    @abc.abstractmethod
    async def upload(self, audio_bytes: bytes, filename: str) -> str:
        """Upload audio and return public URL"""
        raise NotImplementedError

    @abc.abstractmethod
    async def delete(self, filename: str) -> None:
        raise NotImplementedError


class CloudinaryStorage(AudioStorage):

    def __init__(self, cloud_name: str, api_key: str, api_secret: str):
        
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
        )

    async def upload(self, audio_bytes: bytes, filename: str) -> str:
        public_id = filename.replace(".mp3", "")
        response = await asyncio.to_thread(
            cloudinary.uploader.upload,
            io.BytesIO(audio_bytes),
            resource_type="video",  # Cloudinary treats audio as video
            public_id=public_id,
            format="mp3",
        )
        return response["secure_url"]

    async def delete(self, filename: str) -> None:
        
        await asyncio.to_thread(
            cloudinary.uploader.destroy,
            filename,
            resource_type="video",
        )
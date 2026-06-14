from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    azure_openai_api_key : str
    azure_resource_endpoint : str
    kb_uri : str
    kb_username : str
    kb_password : str
    database_url : str
    n_story : str
    cloudinary_cloud_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str


settings = Settings()
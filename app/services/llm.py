import abc
from langchain_openai import ChatOpenAI
from app.services.retry import llm_retry

class ModelProvider(abc.ABC):
    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name

    @abc.abstractmethod
    async def ainvoke(self, messages: list, tools=None, schema=None):
        raise NotImplementedError


class AzureOpenAIProvider(ModelProvider):
    def __init__(self, api_key: str, resource_endpoint: str, model_name: str, **additional_params):
        super().__init__(api_key, model_name)
        self.resource_endpoint = resource_endpoint
        self.client = ChatOpenAI(
            base_url=self.resource_endpoint,
            model=self.model_name,
            api_key=self.api_key,
            **additional_params
        )

    @llm_retry
    async def ainvoke(self, messages: list, tools=None, schema=None):
        return await self._call_llm(self.client, messages, tools, schema)
    
    async def _call_llm(self, llm, messages: list, tools=None, schema=None):
        if tools:
            llm = llm.bind_tools(tools)
        if schema:
            llm = llm.with_structured_output(schema)
        return await llm.ainvoke(messages)
from abc import ABC, abstractmethod

from instructor import OpenAISchema


class BaseTool(ABC, OpenAISchema):
    @abstractmethod
    def run(self):
        pass

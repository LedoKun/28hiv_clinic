from abc import ABC, abstractmethod


class Importer(ABC):
    @abstractmethod
    def getDermographic(self, hn: str) -> dict:
        pass

    @abstractmethod
    def getVisits(self, hn: str) -> list:
        pass

    @abstractmethod
    def getInvestigations(self, hn: str) -> list:
        pass

    @abstractmethod
    def getMedications(self, hn: str) -> list:
        pass

    @abstractmethod
    def getPatientList(self, hn: str) -> list:
        pass

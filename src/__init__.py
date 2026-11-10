from src.base import BaseScraper, AcademicRecord
from src.brapci_scraper import BrapciScraper
from src.pubmed_scraper import PubmedScraper
from src.acm_scraper import AcmScraper
from src.ieee_scraper import IeeeScraper
from src.scopus_scraper import ScopusScraper
from src.capes_scraper import CapesScraper
from src.qualis_service import QualisService
from src.openalex_service import OpenAlexService

__all__ = [
    "BaseScraper",
    "AcademicRecord",
    "BrapciScraper",
    "PubmedScraper",
    "AcmScraper",
    "IeeeScraper",
    "ScopusScraper",
    "CapesScraper",
    "QualisService",
    "OpenAlexService",
]

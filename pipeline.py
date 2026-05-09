import logging

from src.data_collector.omie_collector import OMIECollector


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
if __name__ == '__main__':

    collecor = OMIECollector().collect_all()
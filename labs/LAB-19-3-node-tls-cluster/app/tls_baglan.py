"""3-node TLS cluster'a Python client ile baglanir: once CA vermeden, sonra ca_certs ile."""
import os

from elasticsearch import Elasticsearch
from elastic_transport import TlsError

URL = "https://127.0.0.1:19208"
PAROLA = os.environ["CLUSTER_ELASTIC_PASSWORD"]
CA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".ca", "ca.crt")

try:
    Elasticsearch(URL, basic_auth=("elastic", PAROLA), max_retries=0).info()
except TlsError as hata:
    print("CA yok    :", type(hata).__name__, "(sertifika dogrulanamadi)")

es = Elasticsearch(URL, basic_auth=("elastic", PAROLA), ca_certs=CA)
saglik = es.cluster.health()
print("ca_certs  :", es.info()["cluster_name"], saglik["status"], saglik["number_of_nodes"], "node")

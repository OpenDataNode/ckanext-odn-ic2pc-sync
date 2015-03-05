import urllib2
from ckan_api_client.tests.conftest import data_dir
import ssl
__author__ = 'janci'
from ckan_api_client.high_level import CkanHighlevelClient
from ckan_api_client.objects import CkanDataset
client = CkanHighlevelClient('http://192.168.128.19', api_key='48155aab-f1c0-4cfc-96db-a3530de09acc')

datasets = client.list_datasets();
for dataset in datasets:
    dataset = client.get_dataset(dataset)

    for resource in dataset.resources:
        proxy_support = urllib2.ProxyHandler({"http":"http://proxy.in.eea.sk:3128"})
        opener = urllib2.build_opener(proxy_support)
        urllib2.install_opener(opener)
        try:
         html = urllib2.urlopen(resource.url).read()
        except Exception as e:
            print dataset.name, resource.url, e
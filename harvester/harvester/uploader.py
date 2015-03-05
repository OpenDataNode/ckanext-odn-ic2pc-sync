import json
import urllib2
import urllib

class Uploader(): 
    def __init__(self, url, api_key):
        self.url = url
        self.api_key = api_key
        
        
    def send_request(self, data_string, url):
        request = urllib2.Request(url)
        # Creating a dataset requires an authorization header.
        request.add_header('Authorization', self.api_key)
        # Make the HTTP request.
        response = urllib2.urlopen(request, data_string)
        assert response.code == 200
        # Use the json module to load CKAN's response into a dictionary.
        response_dict = json.loads(response.read())
        assert response_dict['success'] is True
        # package_create returns the created package as its result.
        created_package = response_dict['result']
        return created_package
    
    
    def package_update(self, dataset):
        print "package update:" + str(dataset) 
        dataset_dict = dataset.tojson_without_resource()
        data_string = urllib.quote(json.dumps(dataset_dict))
        url = self.url + "/api/action/package_update"
        self.send_request(data_string, url)
        
        
    def resource_update(self, dataset, resource_id):
        print "resource update:" + dataset 
        dataset_dict = dataset.tojson_resource();
        dataset_dict["id"] = resource_id
        data_string = urllib.quote(json.dumps(dataset_dict))
        url = self.url + "/api/action/resource_update"
        self.send_request(data_string, url)
     
    def create_resource(self, dataset):
        print "create resource:" + str(dataset) 
        resources = dataset.tojson_resource()
        data_string = urllib.quote(json.dumps(resources))
        url = self.url + "/api/action/resource_create"
        self.send_request(data_string, url)
        

    def search_resource(self, dataset):
        dataset_dict = {}
        resource = dataset.tojson_resource()
        dataset_dict['query'] = 'name:' + resource['name'] 
        data_string = urllib.quote(json.dumps(dataset_dict))
        url = self.url + "/api/action/resource_search"
        result_ckan = self.send_request(data_string, url)      
        
        id_resource = None
        if result_ckan['count'] == 1:
            results = result_ckan['results']
            result = results[0]
            id_resource = result['id']
            found = True
        else:
            found = False
            
        return found, id_resource


    def create_package(self, dataset):
        print "create package:" + dataset 
        dataset_dict = dataset.tojson_without_resource()
        data_string = urllib.quote(json.dumps(dataset_dict))
        url = self.url + "/api/action/package_create"
        self.send_request(data_string, url)
        

    def package_search(self, dataset):
        dataset_dict = {}
        dataset_dict['q'] = 'name:' + dataset.name
        data_string = urllib.quote(json.dumps(dataset_dict))
        url = self.url + "/api/action/package_search"
        result = self.send_request(data_string, url)        
        if result['count'] > 0:
            found = True
        else:
            found = False
            
        return found
    
    
    def get_modified(self, dataset): 
        modified = None

        for e in dataset.extras:
            if e['key'] == 'modified' :
                modified = e['value']
                break
            
        return modified

    
    
    def change_happend(self, dataset):
        dataset_dict = {}
        modified = self.get_modified(dataset)
        modified = modified.replace(":", "\:")
        
        query = 'name:' + dataset.name
        if modified != None:
            query += " modified:" + modified
            
        dataset_dict['q'] = 'name:' + dataset.name + " modified:" + modified
        data_string = urllib.quote(json.dumps(dataset_dict))
        url = self.url + "/api/action/package_search"
        result = self.send_request(data_string, url)        
        if result['count'] > 0:
            found = False
        else:
            found = True
            
        return found
    
    
    def create_or_update_resouce(self, dataset):
        found, resource_id = self.search_resource(dataset)
        
        if found:
            self.resource_update(dataset, resource_id)
        else:
            self.create_resource(dataset)        

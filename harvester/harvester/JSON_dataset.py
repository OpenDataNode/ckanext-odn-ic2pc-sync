
class JSON_Dataset():
    def __init__(self):
        self.name = ''
        self.title = ''
        self.notes = ''
        self.author = ''
        self.extras = []
        self.resources = []
        # license is creative commons by default 
        self.license = 'cc-by'
   
    def tostring(self):
        return   "[%s] name: [%s] title: [%s] notes: [%s] author: [%s] extras: [%s] resource: [%s]" % (self.__class__.__name__, self.name, self.title , self.notes , self.author, self.extras, self.resources)  
        
    def tojson_without_resource(self):
        return { "name" : str(self.name), "title" :  str(self.title), "notes": str(self.notes), "author": self.author, "extras": self.extras , "license_id"  : self.license}
    
    def tojson_all(self):
        return { "name" : str(self.name), "title" :  str(self.title), "notes": str(self.notes), "author": self.author, "extras": self.extras , "license_id"  : self.license, "resources" : self.resources}

    def tojson_resource(self):
        if len(self.resources) > 0:
            result = self.resources[0]
        else:
            result = { }
            
        return result
    
    def __str__(self):
        return str(self.tostring())

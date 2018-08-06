class RevealAccess(object):
    """A data descriptor that sets and returns values
       normally and prints a message logging their access.
    """

    def __init__(self):
        self.val = "10"
        self.name = "name"

    def __get__(self, obj, objtype):
        print 'Retrieving', self.name
        return self.val

    def __set__(self, obj, val):
        print 'Updating', self.name
        self.val = val
        
class MyClass():
    x = RevealAccess()
    y = 5
    
m = MyClass()
print(RevealAccess.__dict__)
m.x   
abc=m.x   
m.x = "456"

m.x   
abc=m.x  
abc=m.x  

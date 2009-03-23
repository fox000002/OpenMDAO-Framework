# pylint: disable-msg=C0111,C0103
import unittest

from openmdao.main import Container,Wrapper,Float
from openmdao.main.variable import INPUT, OUTPUT

import random

class Person(object): 
    def __init__(self,name,charm=.5):
        self.fullname = name
        self.charm = charm
        
        self.friends = set()
        self.enemies = []
        
    def greet(self, newperson): 
        if newperson in friends or newperson.charm >= self.charm:
            self.friends.add(newperson)
            return True
        else:
            self.enemies.add(newperson)
            return False
            
    def __eq__(self,other):
        if not isinstance(other,type(self)): 
            return False
        if self.fullname == other.fullname and self.charm == other.charm:
            return True
        return False
            
class test_Variable_as_Wrapper(unittest.TestCase):
    def setUp(self):
        self.hobj = Container('h1', None)
        self.hobj.Justin = Person('Justin',.5)
        self.Justin = Wrapper('Justin',self.hobj,INPUT)
    def tearDown(self):
        pass
        
    def test_createVariable(self):
        self.assertEqual(self.Justin.value,Person('Justin',.5))
        
    def test_attrAccess(self):
        self.assertEqual(self.Justin.get().fullname,'Justin')
        self.assertEqual(self.Justin.get().charm,.5)
        
        self.Justin.get().charm =.8
        self.assertEqual(self.Justin.get().charm,.8)
        
    def test_validation(self):
        x = Float('x',self.hobj,INPUT,default = 2.5)
        Scott = Person('Scott',1.0)
        y = Wrapper('y',self.hobj,OUTPUT,default=Person('Bret',.2))
        
        self.Justin.set(None,Person('Scott',1.0))
        self.assertEqual(self.Justin.get().charm,1.0)

        self.hobj.setvar('Justin',y)
        self.assertEqual(self.Justin.get().charm,.2)
        
        try: 
            self.hobj.setvar('Justin',x)
        except TypeError,err: 
            self.assertEqual(str(err),"h1.Justin contains an object of type: <class 'test_wrapperVariable.Person'> which is incompatible with the type contained in h1.x: <type 'float'>")
        else: 
            self.fail("Expecting TypeError")
        
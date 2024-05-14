class A:
    def __init__(self):
        self.a = 0

    def get_a(self):
        a = 10
        print(a)
        return self.a




obj = A()
print(obj.get_a())


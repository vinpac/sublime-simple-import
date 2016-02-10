class Test:
	def __init__(self, **agrs):
		a = {"caseInsesitive":True}
		self.run(**a)

	def f(a,b,x,y):
		print(a,b,x,y)


	def run(self, caseInsesitive=False):
		print(caseInsesitive)

Test()
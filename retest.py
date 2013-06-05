import re

str = "fecksticks"

print re.match(r':([\S]+)!([\S]+) ([\S]+)(.+)?', str)
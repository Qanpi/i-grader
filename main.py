from bs4 import BeautifulSoup

import re

import numpy as np
import matplotlib.pyplot as plt

from collections import Counter


#Opening the file and initialzing the bs4 parser ----------------------------------------------------------------
with open("test2.html") as html_doc:
    soup = BeautifulSoup(html_doc, "html.parser")

#MOVING LATER


#IB [0,8] to finnish grade [4,10] using linear mapping
def to_finnish_grade(x, denom):
    grade = x/denom*6+4
    return grade - (grade%0.25)

#Parsing the data and putting it into a dictionary --------------------------------------------------------------
rows = soup.find("tbody").find_all("tr")
parsed_data = np.empty(len(rows), list)

class Cell:
    types = ["Date", "Teacher", "Subject", "Info", "Grade", "IB"]

    grade_exceptions = {
        "91/2": "9½"
    }

    grade_modifiers = {
    "+": 0.25,
    "-": -0.25,
    "½": 0.5,
    "" : 0
    } 

    def __init__(self, j, s):
        self.type = Cell.types[j]
        self.string = s

    def remove_whitespaces(self):
        self.string = re.sub(r"\s+", " ", self.string)
        
    def parse(self):
        if self.type == "Subject":
            match = re.search(r": *([\w+, ]*$)", self.string)
            output = match.group(1) if match else None

        elif self.type == "Grade":
            if self.string in Cell.grade_exceptions: self.string = Cell.grade_exceptions[self.string] #check for predefined edge cases

            if match := re.findall(r"(\d+)\W*/\W*(\d+)", self.string): #format 1, e.g. A: 8/8
                grades = [to_finnish_grade(int(num), int(denom)) for num, denom in match]
                output = np.mean(grades)
            elif match := re.findall(r"[A-Da-d]\D*(\d)", self.string): #format 2, e.g. C8
                grades = [to_finnish_grade(int(num), 8) for num in match]
                output = np.mean(grades)
            elif match := re.search(r"(\d+)(\D*)", self.string): #format 3, e.g. 9+
                grade, mod = match.groups()
                output = int(grade) + Cell.grade_modifiers[mod]
            else: output = None
        
        else: output = self.string
        return output 

for i, row in enumerate(rows):
    cols = row.find_all("td")
    col = []

    for j, cell in enumerate(cols):
        cell = Cell(j, cell.get_text(strip=True))
        cell.remove_whitespaces()
        col.append(cell.parse())

    parsed_data[i] = col
        
#Histogram of grades
grades   = [value[4] for value in parsed_data]
subjects = [value[2] for value in parsed_data]

data = list(zip(subjects, grades))
data = list(filter(lambda x: x[1] != None, data))

count = dict(Counter([v[1] for v in data]))
print(count.keys(), count.values())

print("Mean: ", np.mean([v[1] for v in data]))

plt.pie(count.values(), labels=count.keys())
plt.show()

# plt.bar()
# plt.show()



# plt.hist(grades, 3)
# plt.show()



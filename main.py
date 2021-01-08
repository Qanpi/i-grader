from bs4 import BeautifulSoup

import re

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from collections import Counter
from datetime import datetime

#PARSING --------------------------------------------------------------------------------------------

#Opening the file and initialzing the bs4 parser 
with open("test_full.html") as html_doc:
    soup = BeautifulSoup(html_doc, "html.parser")

#IB [0,8] to finnish grade [4,10] using linear mapping
def to_finnish_grade(x, denom):
    grade = x/denom*6+4
    return grade - (grade%0.25)

#Parsing the data and putting it into a dictionary 
rows = soup.find("tbody").find_all("tr")
parsed_data = np.empty((5, len(rows)), "U50")

class Cell:
    #Exceptions and notations
    grade_exceptions = {
        "91/2": "9½"
    }

    grade_modifiers = {
    "+": 0.25,
    "-": -0.25,
    "½": 0.5,
    "" : 0
    } 

    def __init__(self, t, s):
        self.type = t
        self.string = s

    def remove_whitespaces(self):
        self.string = re.sub(r"\s+", " ", self.string)
        
    def parse(self):
        output = ""
        if self.type == "Subject":
            match = re.search(r": *([\w+, ]*$)", self.string)
            if match: output = match.group(1)

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
        
        else: output = self.string
        return str(output) 

#The "engine" which pushes the data to parse
types = ["Date", "Teacher", "Subject", "Grade", "IB"]

for i, row in enumerate(rows):
    cols = row.find_all("td")
    cols.pop(3) #remove the additional information column as it is useless and impractical

    for j, cell in enumerate(cols):
        cell = Cell(types[j], cell.get_text(strip=True))
        cell.remove_whitespaces()
        parsed_data[j,i] = cell.parse()

        
#CHARTS AND DATA --------------------------------------------------------------------------------------------

#Setup
fig, axes = plt.subplots(2,2)

#Extract data

dates, teachers, subjects, grades, ibs = np.split(parsed_data.flatten(), 5)

#CHART 0 ----------------------------------------------

#Cleaning up/purifying
grades_clean = grades[grades != ""].astype(np.float)
grades_clean = grades_clean[grades_clean > 0]

unique, counts = np.unique(grades_clean, return_counts=True)
print(unique, counts)
#Graphing
axes[0,1].bar(unique, counts, width=0.25, align="center")
axes[0,1].axvline(grades_clean.mean(), color="firebrick", linestyle="dashed", linewidth=1.5)



#CHART 1 ----------------------------------------------
mask = (dates != "") & (grades != "")

dates_parsed = [datetime.strptime(s, "%a %d.%m.%Y") for s in dates[mask][::-1]]
grades_parsed = grades[mask].astype(np.float)

months = [d.month for d in dates_parsed]

split_indeces = np.where(np.abs(np.diff(months))>1)[0] + 1
print(np.diff(months))

data10 = np.split(dates_parsed, split_indeces)
data11 = np.split(grades_parsed, split_indeces)

full_range = sorted(set(grades_parsed))
test2 = np.empty(0)
print(full_range)
terms = ["Autumn", "Spring"]

for i in range(len(data11)):
    data10[i] = terms[data10[i][0].month // 7] + " " + str(data10[i][0].year)
    data11[i] = dict(Counter(data11[i]))
    
    test = [data11[i][g] if g in data11[i] else 0 for g in full_range]
    test2 = np.append(test2, test)


test2 = np.reshape(test2, (-1, len(full_range)))
test2_cum = test2.cumsum(axis=1)

# data10 = [d.strftime("%b %y") for d in data10]
# data10 = [label if i%2==0 else "\n" + label for i,label in enumerate(data10)]

for i in range(8):
    heights = test2[:, i]
    starts = test2_cum[:, i] - heights
    axes[0,0].bar(data10, heights, bottom=starts, width=0.5)

plt.show()



from bs4 import BeautifulSoup

import re

import numpy as np
import matplotlib.pyplot as plt

from collections import Counter
from collections import defaultdict
from datetime import datetime

# PARSING --------------------------------------------------------------------------------------------

# Opening the file and initialzing the bs4 parser 
with open("test_full.html") as html_doc:
    soup = BeautifulSoup(html_doc, "html.parser")

# IB [0,8] to finnish grade [4,10] using linear mapping
def to_finnish_grade(x, denom):
    grade = x/denom*6+4
    return grade - (grade%0.25)

# Parsing the data and putting it into a dictionary 
rows = soup.find("tbody").find_all("tr")
parsed_data = np.empty((4, len(rows)), "U50")

class Cell:
    # Exceptions and notations
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

# The "engine" which pushes the data to parse
types = ["Date", "Teacher", "Subject", "Grade", "IB"]

for i, row in enumerate(rows):
    cols = row.find_all("td")
    cols.pop(3) # remove the additional information column as it is useless and impractical
    cols.pop(4) # remove the ib (verbal assesment) column as it is useless and impractical

    for j, cell in enumerate(cols):
        cell = Cell(types[j], cell.get_text(strip=True))
        cell.remove_whitespaces()
        parsed_data[j,i] = cell.parse()

        
# CHARTS AND DATA --------------------------------------------------------------------------------------------

def purify(arrs):
    """Purify a given input array of other numpy arrays. 
    Does so by cross-removing all the values which aren't defined from the arrays."""
    mask = np.ones(arrs[0].shape, dtype=bool)
    output = []

    for u in arrs: 
        mask = mask & (u != "")
    for u in arrs: 
        u = u[mask]
        output.append(u)
    return np.stack(output)

# Setup
fig, axes = plt.subplots(2,2)

# Extract data
dates, teachers, subjects, grades = purify(parsed_data)

# Specific parsing for certain data categories
grades = grades.astype(np.float) 
dates = [datetime.strptime(s, "%a %d.%m.%Y") for s in dates]


# CHART 0,0 ----------------------------------------------

labels00, data00 = np.unique(grades, return_counts=True)

# Graphing
axes[0,0].bar(labels00, data00, width=0.25, align="center")
axes[0,0].axvline(grades.mean(), color="firebrick", linestyle="dashed", linewidth=1.5)

# CHART 0,1 ----------------------------------------------

# Determine where the edges of the terms were by finding where the 
# difference in months is over 1 
months = [d.month for d in dates]
split_indeces = np.where(np.abs(np.diff(months))>3)[0] + 1 

# the below data is reversed so that it is sorted oldest to newest
terms_dates = np.split(dates, split_indeces)[::-1] 
terms_grades = np.split(grades, split_indeces)[::-1] 

labels01 = []
data01 = [] # number of certain grades in each term 

for t in terms_dates:
    terms = ["Autumn", "Spring"]
    first = t[0] #get only the first element as we just need to determine the season based on the month

    season = terms[first.month // 7]
    year = str(first.year)

    labels01.append(season + " " + year)

for t in terms_grades:
    grades_range = sorted(set(grades))
    count = dict(Counter(t))
    
    t_count = [count[g] if g in count else 0 for g in grades_range] # if the grade is not in the dict, add 0 to create an aligned array
    data01.append(t_count)

data01 = np.asarray(data01).T # transpose to have each layer/color in its own row
data01_cum = np.cumsum(data01, axis=0) # used to place several pillars on top of each other in the graph

for i in range(len(data01)):
    heights = data01[i]
    starts = data01_cum[i] - heights
    axes[0,1].bar(labels01, heights, bottom=starts, width=0.5)

# Percentage of 10s from the total number of grades in the term
for i in range(len(labels01)):
    last = data01.T[i][-1] # the last layer aka the 10s layer
    sum_ = sum(data01.T[i])

    y = sum_ - last/2 
    v = int(round(last / sum_ * 100))
    text = axes[0,1].text(i, y, str(v) + "%", ha="center", va="center", c="w")


#CHART 1, 0 ----------------------------------------------

years = [d.year for d in dates]
split_indeces = np.nonzero(np.diff(years))[0] + 1 

years_dates = np.split(dates, split_indeces)[::-1] 

xlabels10 = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"] # the month labels
ylabels10 = [] # the year labels
data10 = []

for y in years_dates:
    m = [d.month for d in y][::-1]
    count = Counter(m)
    m_count = [count[m] if m in dict(count) else 0 for m in range(1,13)] # if the month is not in dict, add 0 to create an aligned array

    data10.append(m_count)
    ylabels10.append(y[0].year)

im = axes[1,0].imshow(np.array(data10, dtype=np.float))

# To show all the tick values
axes[1,0].set_xticks(np.arange(len(xlabels10)))
axes[1,0].set_yticks(np.arange(len(ylabels10)))

axes[1,0].set_xticklabels(xlabels10)
axes[1,0].set_yticklabels(ylabels10)


# Text annotation on each square of the heatmap
for i in range(len(xlabels10)):
    for j in range(len(ylabels10)):
        if xlabels10[i] in ["Jun", "Jul", "Aug"] and data10[j][i] == 0: # easter egg: put (duh) on summer months
            text = axes[1,0].text(i, j, "(duh)", ha="center", va="center", color="w", size="x-small") 
        else: text = axes[1,0].text(i, j, data10[j][i], ha="center", va="center", color="w")


#CHART 1, 1 ----------------------------------------------
subjects_sums = defaultdict(list) # create a default dict so that it would automatically add keys if they don't exist

for i in range(len(grades)):
    s = subjects[i]
    subjects_sums[s].append(grades[i])

data11 = np.array([np.mean(s) for s in subjects_sums.values()]) 
labels11 = np.array([l if len(l) < 10 else l[:9] + "..." for l in subjects_sums.keys()]) # limit the length of the subject as to avoid overlapping

#Sort data in ascending order from left to right
sort_indeces = data11.argsort()
data11 = data11[sort_indeces]
labels11 = labels11[sort_indeces]

labels11 = np.array([l if i%2==0 else "\n"+l for i, l in enumerate(labels11)]) # prevents overlapping labels by making some hop over others

axes[1,1].set_ylim(np.min(grades),10) # manually setting the y lim to get a better close-up view on the data
axes[1,1].bar(labels11, data11)

plt.show()
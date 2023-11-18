import argparse
import pandas as pd
import math
import re
from datetime import datetime


parser = argparse.ArgumentParser(description="Erstellt eine Umsatzanzeige geordnet nach Kategorien")
parser.add_argument('Datafile')
parser.add_argument('Categoryfile')
parser.add_argument('-out','--Outputfile')
parser.add_argument('-a','--addToCategory',nargs=2,help='neue Kategorie oder neues Element einer Kategorie hinzufügen. In der Form Kategorie Element der Kategorie (ohne Komma)')
parser.add_argument('-t','--timeInterval',nargs=2,help='Start- und Enddatum des zu betrachtenden Zeitraums eingeben in der form dd.mm.yyyy (ohne Komma zwischen den beiden Datumsangaben)')
parser.add_argument('--details',nargs='*')
args = parser.parse_args()

# columns:
# ['Bezeichnung Auftragskonto', 'IBAN Auftragskonto', 'BIC Auftragskonto',
#        'Bankname Auftragskonto', 'Buchungstag', 'Valutadatum',
#        'Name Zahlungsbeteiligter', 'IBAN Zahlungsbeteiligter',
#        'BIC (SWIFT-Code) Zahlungsbeteiligter', 'Buchungstext',
#        'Verwendungszweck', 'Betrag', 'Waehrung', 'Saldo nach Buchung',
#        'Bemerkung', 'Kategorie', 'Steuerrelevant', 'Glaeubiger ID',
#        'Mandatsreferenz']
data = pd.read_csv(args.Datafile,sep=';',header=0)


## initialize categories
# firstCat = pd.DataFrame()
# firstCat['paypal'] = ['paypal']
# firstCat = pd.concat([firstCat,pd.DataFrame({'grocery':['alnatura', 'rewe', 'edeka', 'kaufland', 'marktladen']})],ignore_index=False,axis=1)
# firstCat = pd.concat([firstCat,pd.DataFrame({'drogerie':['dm markt','mueller','muller']})],ignore_index=False,axis=1)
# firstCat = pd.concat([firstCat,pd.DataFrame({'pharmacy':['apotheke']})],ignore_index=False,axis=1)
# firstCat = pd.concat([firstCat,pd.DataFrame({'income':['elvira','gommeringer','landesoberkasse']})],ignore_index=False,axis=1)
# firstCat = pd.concat([firstCat,pd.DataFrame({'amazon':['amazon']})],ignore_index=False,axis=1)
# firstCat = {'paypal':['paypal'],'grocery':['alnatura', 'rewe', 'edeka', 'kaufland', 'marktladen'],'drogerie':['dm markt','mueller','muller'],
#             'pharmacy':['apotheke'],'income':['elvira','gommeringer','landesoberkasse'],'amazon':['amazon']}


# with open('Categories.csv','w') as file:
#     rowidx = 0
#     for keys in firstCat.keys():
#         if (rowidx==0):
#             rowidx+=1
#         else:
#             file.write("\n")
#         file.write(f"{keys}:")
#         i = 0
#         for item in firstCat[keys]:
#             if (i==0):
#                 file.write(f"{item}")
#                 i+=1
#             else:
#                 file.write(f",{item}")

## Functions to manipulate DataFrame
def replace(string):
    return float(string.replace(',','.'))

def find(entry,cat):
    # if (type(entry)==str):
    #     print(entry.lower())
    for cat_inst in categories[cat]:
        if (type(entry)==str and entry.lower().find(cat_inst)!=-1):
            return True
        
    return False

def findrest(entry):
    match = False
    for category in categories.keys():
        match = match | find(entry,category)
    return not match

def lookForSubjekt(entry):
    if (type(entry)==str):
        m = re.search(r"(([a-z]{3,30})(\s*)([0-9]{0,2}))+",entry.lower())
        return m.group(0)
    else:
        return ""

def changeToDatetime(entry):
    return datetime.strptime(entry,"%d.%m.%Y")

def datetimeToString(entry):
    return entry.strftime("%d.%m.%Y")

def setTimeInterval(entry,start,end):
    return (entry>=start and entry<=end)


categories = dict()
with open(args.Categoryfile,'r') as file:
    for line in file:
        key, val = line.rstrip('\n').split(':')
        categories[key] = val.split(',')

if args.addToCategory:
    if (args.addToCategory[0] in categories.keys()):
        categories[args.addToCategory[0]].append(args.addToCategory[1])
    else:
        categories[args.addToCategory[0]]= [args.addToCategory[1]]
    with open('Categories.csv','w') as file:
        rowidx = 0
        for keys in categories.keys():
            if (rowidx==0):
                rowidx+=1
            else:
                file.write("\n")
            file.write(f"{keys}:")
            i = 0
            for item in categories[keys]:
                if (i==0):
                    file.write(f"{item}")
                    i+=1
                else:
                    file.write(f",{item}")


## pre-processing data

data['Betrag'] = data['Betrag'].apply(replace)

data["Buchungstag"]= data['Buchungstag'].apply(changeToDatetime)

if args.timeInterval:
    try:
        start = datetime.strptime(args.timeInterval[0],"%d.%m.%Y")
        end = datetime.strptime(args.timeInterval[1],"%d.%m.%Y")
    except:
        print("wrong data format")
        exit()
    data = data.loc[data['Buchungstag'].apply(setTimeInterval,args=[start,end])]
if args.Outputfile:
    outfile = open(args.Outputfile,'w')


## processing data
sum = 0
ordered = dict()
currentFlow = dict()
for cat in categories.keys():
    ordered[cat] = data.loc[data['Name Zahlungsbeteiligter'].apply(find,args=[cat])]
    val =  ordered[cat]['Betrag'].sum()
    currentFlow[cat] = [val]
    sum +=val
total = data['Betrag'].sum()
currentFlow['rest'] = [total - sum]
currentFlow['total'] = [total]
currentFlow = pd.DataFrame.from_dict(currentFlow)
print(currentFlow)
if args.Outputfile:
    currentFlow.to_string(outfile,col_space=2,index=False)
rest = pd.DataFrame()
rest[['transaction','value','date']] = data.loc[data['Name Zahlungsbeteiligter'].apply(findrest)][['Name Zahlungsbeteiligter','Betrag','Buchungstag']]
rest['date'] = rest['date'].apply(datetimeToString) 
print('rest:')
print(rest)
if args.Outputfile:
    outfile.write('\n\nrest:\n')
    rest.to_string(outfile,col_space=2,index=False)

for catis in args.details:
    details = pd.DataFrame()
    details["transaction"] = ordered[catis]['Verwendungszweck'].apply(lookForSubjekt)
    details['value'] = ordered[catis]['Betrag']
    details['date of transaction'] = ordered[catis]['Buchungstag'].apply(datetimeToString)
    print(catis+":")
    print(details)
    if args.Outputfile:
        outfile.write("\n\n"+catis+":\n")
        details.to_string(outfile,col_space=2,index=False)
if args.Outputfile:
    outfile.close()


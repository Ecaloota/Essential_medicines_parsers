'''
MIT License

Copyright (c) 2020 E$$ENTIAL MEDICINE$ Project

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

from datetime import datetime as dt
import csv

class Drug(object):
    def __init__(self,ingredient,df_route,trade_name,applicant,strength,appl_type,appl_no,\
                product_no,approval_date,typeval,applicant_full_name):
        self.ingredient = ingredient
        self.df_route = df_route
        self.trade_name = trade_name
        self.applicant = applicant
        self.strength = strength
        self.application_type = appl_type ## N or A
        self.application_number = appl_no ## format nnnnnn
        self.product_number = product_no # format nnn
        self.approval_date = approval_date
        self.type_val = typeval #DISCN, OTC, RX
        self.applicant_full_name = applicant_full_name
        self.under_patent = None
        self.latest_patent_date = None
        self.exclusivity_agreement = None
        self.latest_exclusivity_date = None
        self.latest_expiration_date = None
        self.generic_forms = [] ## this could get complicated
        self.fda_approved = False

        self.properties = {
            "Ingredient":self.parse_ingredient(),
            "DF_Route":self.df_route, ## split into df and route easily
            "Trade_Name":self.trade_name,
            "Applicant":self.applicant,
            "Strength":self.parse_strength(),
            "Appl_Type":self.application_type, ## New (N) or not (A)
            "Appl_No":self.application_number, ## unique identifier? (yes, when combined with product_no);
            "Product_No":self.product_number,
            "Approval_Date":self.parse_approval_date(),
            "Type":self.type_val,
            "Applicant_Full_Name":self.applicant_full_name,
            "Under_Patent":self.under_patent,
            "Latest_Patent_Date":self.latest_patent_date,
            "Exclusivity_Agreement":self.exclusivity_agreement,
            "Latest_Exclusivity_Date":self.latest_exclusivity_date,
            "Latest_Expiration_Date":self.latest_expiration_date,
            "Generic_Forms":self.generic_forms,
            "FDA_Approved":self.fda_approved
        }

    def __repr__(self):
        return self.properties['Trade_Name']

    def parse_ingredient(self):
        '''handles ingredient names; we should split on semicolons.'''
        ingredient = self.ingredient.lower()
        ingredient = ingredient.split(';')
        return [i.lstrip().rstrip() for i in ingredient] ## only remove trailing or leading whitespace

    def parse_approval_date(self):
        try:
            date = dt.strptime(self.approval_date, "%b %d, %Y")
        # I assume the only reason to fail here is because we have a string explaining that the approval occured
        # prior to Jan 1, 1982. Per instructions, settting date to Jan 1, 1982. 
        except ValueError:
            date = dt.strptime("Jan 1, 1982", "%b %d, %Y")
        return date

    def parse_strength(self):
        if "**Federal Register determination that product was not discontinued or withdrawn for safety or efficacy reasons**" in self.strength:
            strength=self.strength.replace("**Federal Register determination that product was not discontinued or withdrawn for safety or efficacy reasons**",'')
        else:
            strength=self.strength
        
        return strength


    @staticmethod
    def condense_generics(essential_drugs):
        '''determine if self is a generic form of other. DOESN'T WORK YET. GENERICS have identical active ingredients, dosage forms, routes of admin., and strength
        List applicant holders, FDA approval date, market status. Should we remove generics from the list of drugs, given that the information on them is contained
        in the respective Drug.properties['Generics'] property? I vote yes.'''

        for drug in essential_drugs:
            ## this is a new drug which might have generic forms
            if drug.properties['Appl_Type']=="N" and drug.properties['Under_Patent'] is None and drug.properties['Exclusivity_Agreement'] is None:
                for other in essential_drugs:
                    if other.properties['Appl_Type']=="A" and drug.properties['Ingredient']==other.properties['Ingredient'] and drug.properties['DF_Route']==other.properties['DF_Route']\
                                        and drug.properties['Strength']==other.properties['Strength']:
                        ## `other` is a generic form of `drug`
                        drug.properties['Generic_Forms'].append(list((other.properties['Applicant_Full_Name'],other.properties['Approval_Date'],other.properties['Type'])))
                        essential_drugs.remove(other) ## could fail
        return essential_drugs

    @staticmethod
    def get_drugs_from_products_file(filename="products.txt"):
        '''reads the filename into a list of dictionaries. Doesn't do error checking'''
        drug_list = []
        with open(filename,'r') as fh:
            header = fh.readline().strip().split('~') ## dictionary keys
            for line in fh:
                l = line.split('~')
                drug_list.append(Drug(l[0],l[1],l[2],l[3],l[4],l[5],l[6],l[7],l[9],l[12],l[13]))
        return drug_list

    @staticmethod
    def find_drugs_under_patent(drug_list, filename="patent.txt"):
        '''receives a list of Drug dictionaries, then looks to see if the unique identifier for a particular drug 
        is in the patents file. If so, modifies that Drug's Under_Patent key to True and updates Latest_Expiration_Date, 
        otherwise sets it to False'''
        with open(filename, 'r') as fh:
            header = fh.readline().strip().split('~')
            for line in fh:
                l = line.split('~') ## l[1] is appl_no, l[2] is prod_no, l[4] is Patent_Expire_Date_Text
                for drug in drug_list:
                    if drug.properties['Appl_No'] == l[1] and drug.properties['Product_No'] == l[2]:
                        drug.properties['Under_Patent']=True
                        if drug.properties['Latest_Patent_Date'] is None:
                            drug.properties['Latest_Patent_Date']=dt.strptime(l[4], "%b %d, %Y")
                        elif dt.strptime(l[4], "%b %d, %Y") > drug.properties['Latest_Patent_Date']:
                            drug.properties['Latest_Patent_Date'] = dt.strptime(l[4], "%b %d, %Y")
        
        return drug_list

    @staticmethod
    def find_exclusive_drugs(drug_list,filename="exclusivity.txt"):
        '''receives a list of Drug dictionaries, then looks to see if the unique identifier for a particular drug can 
        be found in the exclusivity file. If so, modifies that Drug's Exclusivity_Agreement key to True and updates 
        Latest_Expiration_Date, otherwise sets it to False.'''
        with open(filename, 'r') as fh:
            header = fh.readline().strip().split('~')
            for line in fh:
                l = line.split('~') ## l[1] is appl_no, l[2] is prod_no, l[4] is Exclusivity_Date
                for drug in drug_list:
                    if drug.properties['Appl_No'] == l[1] and drug.properties['Product_No'] == l[2]:
                        drug.properties['Exclusivity_Agreement']=True
                        if drug.properties['Latest_Exclusivity_Date'] is None:
                            drug.properties['Latest_Exclusivity_Date']=dt.strptime(l[4].strip(), "%b %d, %Y")
                        elif dt.strptime(l[4], "%b %d, %Y") > drug.properties['Latest_Patent_Date']:
                            drug.properties['Latest_Exclusivity_Date'] = dt.strptime(l[4], "%b %d, %Y")

        return drug_list

    @staticmethod
    def clean_user_provided_drug_list(essential_drugs_list):
        return [drug.split('+') for drug in essential_drugs_list]

    @staticmethod
    def keep_only_essential_drugs(drug_list,clean_essential_drugs_list):
        '''receives a list of drug dictionaries and removes those entries that aren't in essential_drugs_list.
        This would benefit from some serious code-review!'''

        for drug in drug_list: ## These are Drug objects from the products.txt file
            for component in drug.properties['Ingredient']:
                for essential_drug in clean_essential_drugs_list:
                    if len(essential_drug)==len(drug.properties['Ingredient']):
                        for elem in essential_drug:
                            if elem not in drug.properties['Ingredient']:
                                break
                            else:
                                drug.properties['FDA_Approved'] = True

        return [drug for drug in drug_list if drug.properties['FDA_Approved']]

    @staticmethod
    def write_drugs_to_file(drug_list,filename="output.csv"):
        '''outputs Drug objects in drug_list to a file. Should be changed to reflect need.'''
        with open(filename,'w') as fh:
            csvwriter = csv.writer(fh)
            csvwriter.writerow(["Ingredient","DF_Route","Trade_Name","Strength","Approval_Date","Type","Applicant_Full_Name","Under_Patent","Latest_Patent_Date","Exclusivity_Agreement","Latest_Exclusivity_Date","Generic_Forms"])
            for drug in drug_list:
                csvwriter.writerow(\
                    [drug.properties["Ingredient"],\
                    drug.properties["DF_Route"],\
                    drug.properties["Trade_Name"],\
                    drug.properties["Strength"],\
                    drug.properties["Approval_Date"],\
                    drug.properties["Type"],\
                    drug.properties["Applicant_Full_Name"],\
                    drug.properties["Under_Patent"],\
                    drug.properties["Latest_Patent_Date"],\
                    drug.properties["Exclusivity_Agreement"],\
                    drug.properties["Latest_Exclusivity_Date"],\
                    drug.properties["Generic_Forms"]]\
                )


essential_drugs_list = ['abacavir','abacavir+lamivudine','acyclovir','albendazole','amikacin','amodiaquine',\
                        'amodiaquine+sulfadoxine+pyrimethamine','amoxicillin','amoxicillin+clavulanate','amphotericin B',\
                        'ampicillin','artemether','artemether+lumefantrine','artesunate+amodiaquine','artesunate+mefloquine'\
                        'artesunate+pyronaridine tetraphosphate','atazanavir','azithromycin']



drug_list = Drug.get_drugs_from_products_file('products.txt')
essential_drugs = Drug.clean_user_provided_drug_list(essential_drugs_list)
essential_drugs = Drug.keep_only_essential_drugs(drug_list,essential_drugs)
essential_drugs = Drug.find_drugs_under_patent(essential_drugs,'patent.txt')
essential_drugs = Drug.find_exclusive_drugs(essential_drugs,'exclusivity.txt')
essential_drugs = Drug.condense_generics(essential_drugs)
Drug.write_drugs_to_file(essential_drugs,'output.csv')


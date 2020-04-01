import Functions as Func
import pandas as pd
import math
'''
Die Klasse Model dient zur Simulation. 

__init__
Der Kinstruktor übergibt alle relevabteb Datensätze und erstellt eine Logdatei. In der Logdateil sollen während der
Simulation alle werde berechnet werden und direkt die Logdatei als DF manipuliert werden.

run
Die run Methode soll verwendet werden um die Simulation durchzuführen.

updatecapacityusedbypv
update das dataframe mit dem input pvleistung und lastprofil im bezug auf verwendeten speicher
'''


class Model:
    def __init__(self, dataloadprofiles, listoflastprofiles, pvdata, numberofhouseswithpv, capacityofpvs,
                 capacityofenergystorage):
        self.dataloadprofiles = Func.kumuliereprofile(dataloadprofiles, listoflastprofiles)
        # Lastprofile in Auflösung Minutentakt und W/s <<< umrechnung auf KWH
        self.dataloadprofiles['Summe'] = self.dataloadprofiles['Summe'] * 60 / 3600000
        # PV daten in KW auf 1 KW Peak ursprünglich stündlich Auflösung <<< umrechung auf KWH
        pvdata['pvpower'] = pvdata['electricity'] * numberofhouseswithpv * capacityofpvs * 900 / 3600
        self.pvdata = pvdata
        self.capacityofenergystorage = capacityofenergystorage
        indexlogdata = dataloadprofiles.index
        collumslogdata = ['chargecapacity', 'netenergydemand', 'drawfromgrid', 'feedingrid', 'chargecapacityusedbypv']
        self.logdata = pd.DataFrame(columns=collumslogdata)
        self.logdata['timestamp'] = indexlogdata
        self.logdata = self.logdata.set_index('timestamp')
        self.logdata['netenergydemand'] = self.dataloadprofiles['Summe'] - self.pvdata['pvpower']
        self.logdata['chargecapacity'] = 0
        self.logdata['chargecapacityusedbypv'] = 0


    def run(self):
        # reindex zu besseren ansprechung über .loc am Ende zurück
        self.logdata = self.logdata.reset_index()

        # Berrechung für PV-Leistung
        self.updatecapacityusedbypv()

        # setzte Index
        self.logdata = self.logdata.set_index('timestamp')


    def updatecapacityusedbypv(self):
        # Fall unterscheidung pv größer Bedarf vs kleiner >> Anpassung Speicher und +- Grid
        for i in range(0, len(self.logdata)):
            if self.logdata.iloc[i]['netenergydemand'] > 0:
                self.logdata.loc[i, 'drawfromgrid'] = max(
                    self.logdata.iloc[i]['netenergydemand'] - self.logdata.iloc[i - 1]['chargecapacityusedbypv'], 0)
                self.logdata.loc[i, 'chargecapacityusedbypv'] = max(
                    self.logdata.iloc[i - 1]['chargecapacityusedbypv'] - self.logdata.iloc[i]['netenergydemand'], 0)
                self.logdata.loc[i, 'feedingrid'] = 0
            else:
                self.logdata.loc[i, 'feedingrid'] = max(abs(self.logdata.iloc[i]['netenergydemand']) - (
                        self.capacityofenergystorage - self.logdata.iloc[i - 1]['chargecapacity']), 0)
                self.logdata.loc[i, 'chargecapacityusedbypv'] = min(max(
                    self.logdata.iloc[i - 1]['chargecapacityusedbypv'] + abs(self.logdata.iloc[i]['netenergydemand']),
                    0), self.capacityofenergystorage)
                self.logdata.loc[i, 'drawfromgrid'] = 0
            # Summen bildung einzelner Task für gesamt Verwendung vllt auslagern als callabel funktion
            self.logdata.loc[i, 'chargecapacity'] = self.logdata.loc[i, 'chargecapacityusedbypv']
import Functions as Func
import pandas as pd

'''
Die Klasse Model dient zur Simulation. 

__init__
Der Kinstruktor übergibt alle relevabteb Datensätze und erstellt eine Logdatei. In der Logdateil sollen während der
Simulation alle Werte berechnet werden und direkt die Logdatei als DF manipuliert werden.

run
Die run Methode soll verwendet werden um die Simulation durchzuführen.

updatecapacityusedbypv
update das dataframe mit dem input pvleistung und lastprofil im bezug auf verwendeten speicher

setdecisionpoint
schreibt in logdatei decisionpoint und typeofdecision

decisionhandler
erhält Antwort von Agent und führt sie auf logdatei aus
'''


class Model:
    def __init__(self, dataloadprofiles, listoflastprofiles, pvdata, numberofhouseswithpv, capacityofpvs,
                 capacityofenergystorage, agent):
        self.agent = agent
        self.dataloadprofiles = Func.kumuliereprofile(dataloadprofiles, listoflastprofiles)
        # Lastprofile in Auflösung Minutentakt und W/s <<< umrechnung auf KWH
        self.dataloadprofiles['Summe'] = self.dataloadprofiles['Summe'] * 60 / 3600000
        # PV daten in KW auf 1 KW Peak ursprünglich stündlich Auflösung <<< umrechung auf KWH
        pvdata['pvpower'] = pvdata['electricity'] * numberofhouseswithpv * capacityofpvs * 900 / 3600
        # setzen von start parameter
        self.pvdata = pvdata
        self.capacityofenergystorage = capacityofenergystorage
        indexlogdata = dataloadprofiles.index
        collumslogdata = ['chargecapacity', 'netenergydemand', 'drawfromgrid', 'feedingrid', 'chargecapacityusedbypv',
                          'chargecapacityusedbycontrolenergysrl', 'chargecapacityusedbycontrolenergyprl',
                          'decisionpoint', 'typeofdecision']
        self.logdata = pd.DataFrame(columns=collumslogdata)
        self.logdata['timestamp'] = indexlogdata
        self.logdata['decisionpoint'] = False
        self.logdata['chargecapacity'] = 0
        self.logdata['chargecapacityusedbypv'] = 0
        self.logdata['chargecapacityusedbycontrolenergysrl'] = 0
        self.logdata['chargecapacityusedbycontrolenergyprl'] = 0
        self.setdecisionpoint()
        self.logdata = self.logdata.set_index('timestamp')
        self.logdata['netenergydemand'] = self.dataloadprofiles['Summe'] - self.pvdata['pvpower']

    def run(self):
        # reindex zu besseren ansprechung über .loc am Ende zurück
        self.logdata = self.logdata.reset_index()

        # Berrechung für PV-Leistung
        self.updatecapacityusedbypv()
        # self.updatechargecapacity()
        # Agenten
        for i in range(0, len(self.logdata)):
            if self.logdata.loc[i, 'decisionpoint']:
                # self.agent.getdecision(i, str(self.logdata[i, 'typeofdecision']))
                self.decisionhandler(i, self.logdata.loc[i, 'typeofdecision'],
                                     self.agent.getdecision(index=i, typeofdecision=self.logdata.loc[i, 'typeofdecision'],
                                                            logdata=self.logdata))
        # neu Berrechnung für PV
        # self.updatechargecapacity()
        self.updatecapacityusedbypv()
        self.updatechargecapacity()
        # setzte Index
        self.logdata = self.logdata.set_index('timestamp')

    def updatecapacityusedbypv(self):
        # Fall unterscheidung pv größer Bedarf vs kleiner >> Anpassung Speicher und +- Grid
        self.logdata['chargecapacityusedbypv'] = 0
        self.logdata['drawfromgrid'] = 0
        self.logdata['feedingrid'] = 0
        for i in range(0, len(self.logdata)):
            if self.logdata.iloc[i]['netenergydemand'] > 0:
                self.logdata.loc[i, 'drawfromgrid'] = max(
                    self.logdata.iloc[i]['netenergydemand'] - self.logdata.iloc[i - 1]['chargecapacityusedbypv'], 0)
                self.logdata.loc[i, 'chargecapacityusedbypv'] = max(
                    self.logdata.iloc[i - 1]['chargecapacityusedbypv'] - self.logdata.iloc[i]['netenergydemand'], 0)
                self.logdata.loc[i, 'feedingrid'] = 0
                if self.logdata.loc[i, 'chargecapacityusedbypv'] + self.logdata.loc[
                    i, 'chargecapacityusedbycontrolenergyprl'] + self.logdata.loc[
                    i, 'chargecapacityusedbycontrolenergysrl'] > self.capacityofenergystorage:
                    excess = self.logdata.loc[i, 'chargecapacityusedbypv'] + self.logdata.loc[
                        i, 'chargecapacityusedbycontrolenergyprl'] + self.logdata.loc[
                                 i, 'chargecapacityusedbycontrolenergysrl'] - self.capacityofenergystorage
                    self.logdata.loc[i, 'chargecapacityusedbypv'] = self.logdata.loc[
                                                                        i, 'chargecapacityusedbypv'] - excess
                    self.logdata.loc[i, 'feedingrid'] = excess - self.logdata.loc[i, 'drawfromgrid']
                    self.logdata.loc[i, 'drawfromgrid'] = 0

            else:
                self.logdata.loc[i, 'feedingrid'] = max(abs(self.logdata.iloc[i]['netenergydemand']) - (
                        self.capacityofenergystorage - self.logdata.loc[i - 1, 'chargecapacityusedbypv'] -
                        self.logdata.loc[i, 'chargecapacityusedbycontrolenergyprl'] -
                        self.logdata.loc[i, 'chargecapacityusedbycontrolenergysrl']), 0)
                self.logdata.loc[i, 'chargecapacityusedbypv'] = min(
                    self.logdata.iloc[i - 1]['chargecapacityusedbypv'] + abs(self.logdata.iloc[i]['netenergydemand']),
                    self.capacityofenergystorage - self.logdata.loc[i, 'chargecapacityusedbycontrolenergysrl'] -
                    self.logdata.loc[i, 'chargecapacityusedbycontrolenergyprl'])
                self.logdata.loc[i, 'drawfromgrid'] = 0

    def updatechargecapacity(self):
        # der Wert Chargecapacity findet im Model keine Verwendung, lediglich zu späteren Auswertung.
        self.logdata['chargecapacity'] = self.logdata['chargecapacityusedbypv'] + self.logdata[
            'chargecapacityusedbycontrolenergyprl'] + self.logdata['chargecapacityusedbycontrolenergysrl']

    def setdecisionpoint(self):
        nextsrl, nextprlmon, nextprltue, nextprlwed, nextprlthu, nextprlfri = 32, 60, 156, 252, 348, 444
        for i in range(0, len(self.logdata)):
            if i == nextsrl:
                self.logdata.loc[i, 'decisionpoint'] = True
                self.logdata.loc[i, 'typeofdecision'] = "SRL"
                nextsrl = nextsrl + 96
            if i == nextprlmon:
                self.logdata.loc[i, 'decisionpoint'] = True
                self.logdata.loc[i, 'typeofdecision'] = "PRL1"
                nextprlmon = nextprlmon + 672
            if i == nextprltue:
                self.logdata.loc[i, 'decisionpoint'] = True
                self.logdata.loc[i, 'typeofdecision'] = "PRL1"
                nextprltue = nextprltue + 672
            if i == nextprlwed:
                self.logdata.loc[i, 'decisionpoint'] = True
                self.logdata.loc[i, 'typeofdecision'] = "PRL1"
                nextprlwed = nextprlwed + 672
            if i == nextprlthu:
                self.logdata.loc[i, 'decisionpoint'] = True
                self.logdata.loc[i, 'typeofdecision'] = "PRL2"
                nextprlthu = nextprlthu + 672
            if i == nextprlfri:
                self.logdata.loc[i, 'decisionpoint'] = True
                self.logdata.loc[i, 'typeofdecision'] = "PRL3"
                nextprlfri = nextprlfri + 672

    def decisionhandler(self, index, decisiontype, reply):
        if decisiontype == 'SRL':
            if index + 80 < len(self.logdata):
                for i in range(index + 64, index + 80):
                    self.logdata.loc[i, 'chargecapacityusedbycontrolenergysrl'] = reply[0]
            if index + 96 < len(self.logdata):
                for i in range(index + 80, index + 96):
                    self.logdata.loc[i, 'chargecapacityusedbycontrolenergysrl'] = reply[1]
            if index + 112 < len(self.logdata):
                for i in range(index + 96, index + 112):
                    self.logdata.loc[i, 'chargecapacityusedbycontrolenergysrl'] = reply[2]
            if index + 128 < len(self.logdata):
                for i in range(index + 112, index + 128):
                    self.logdata.loc[i, 'chargecapacityusedbycontrolenergysrl'] = reply[3]
            if index + 144 < len(self.logdata):
                for i in range(index + 128, index + 144):
                    self.logdata.loc[i, 'chargecapacityusedbycontrolenergysrl'] = reply[4]
            if index + 160 < len(self.logdata):
                for i in range(index + 144, index + 160):
                    self.logdata.loc[i, 'chargecapacityusedbycontrolenergysrl'] = reply[5]
        if decisiontype == 'PRL1':
            if index + 228 < len(self.logdata):
                for i in range(index + 132, index + 228):
                    self.logdata.loc[i, 'chargecapacityusedbycontrolenergyprl'] = reply[0]
        if decisiontype == 'PRL2':
            if index + 228 < len(self.logdata):
                for i in range(index + 132, index + 228):
                    self.logdata.loc[i, 'chargecapacityusedbycontrolenergyprl'] = reply[0]
            if index + 324 < len(self.logdata):
                for i in range(index + 228, index + 324):
                    self.logdata.loc[i, 'chargecapacityusedbycontrolenergyprl'] = reply[1]
        if decisiontype == 'PRL3':
            if index + 324 < len(self.logdata):
                for i in range(index + 228, index + 324):
                    self.logdata.loc[i, 'chargecapacityusedbycontrolenergyprl'] = reply[0]
            if index + 420 < len(self.logdata):
                for i in range(index + 324, index + 420):
                    self.logdata.loc[i, 'chargecapacityusedbycontrolenergyprl'] = reply[1]

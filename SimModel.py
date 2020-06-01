import Functions as Func
import pandas as pd
import numpy as np
import copy
import noise
import random

'''
Die Klasse Model dient zur Simulation. 

__init__
Der Kinstruktor übergibt alle relevante Datensätze und erstellt eine Logdatei. In der Logdateil sollen während der
Simulation alle Werte berechnet werden und direkt die Logdatei geschrieben werden.

run
Die run Methode soll verwendet werden um die Simulation durchzuführen.

updatecapacityusedbypv
update das dataframe mit dem input pvleistung und lastprofil im bezug auf verwendeten speicher

updatechargecapacity
berechnet die Chargecapacity

setdecisionpoint
schreibt in logdatei decisionpoint und typeofdecision

decisionhandler
erhält Antwort von Agent und führt sie auf logdatei aus

cutlogdatei
kürzt die Logdatei und optional auch die Strompreise

evaluaterevenuestream
bewertet die logdatei nach selfconsumotion, endladestand der Baterie, feed in grid, Srl, PRL, Trading

def noise
added noise - gaussian oder perlin - Parameter für kurze und lange vorraussage

add trading
füge nach Simulation Trading in die Lücken, im code änderbare Trading strategie - perfekte vorraussicht

Spalten der Logdatei:

timestamp - Datum + Uhrzeit
chargecapacity - Auslastung Speicher
netenergydemand 
drawfromgrid
feedingrid
chargecapacityusedbypv
chargecapacityusedbycontrolenergysrl
chargecapacityusedbycontrolenergyprl
decisionpoint - Wird an diesem Zeitpunkt eine Entscheidung getriggert
typeofdecision - Was für eine Art von Entscheidung
chargecapacityusedbytrading
pvpower - Leistung PV Anlage
energydemandnopv - Verbrauch der Haushalte
errorpvlong - Error Faktor mit EW 0
errorpvshort - Error Faktor mit EW 
errorlastlong - Error Faktor mit EW 
errorlastshort - Error Faktor mit EW 
tradingperfect - Error Faktor mit EW 
drawfromgridcumsum - kumulierte summe
feedingridcumsum - kumulierte summe


'''


class Model:
    def __init__(self, dataloadprofiles, listoflastprofiles, dataafrr, datafcr, pricedata, pvdata, numberofhouseswithpv, capacityofpvs,
                 capacityofenergystorage, agent):
        self.pricedata = pricedata
        self.agent = agent
        self.listoflastprofiles = listoflastprofiles
        self.dataloadprofiles = Func.kumuliereprofile(dataloadprofiles, listoflastprofiles)
        # Lastprofile in Auflösung Minutentakt und W/s <<< umrechnung auf KWH
        self.dataloadprofiles['Summe'] = self.dataloadprofiles['Summe'] * 60 / 3600000
        # PV daten in KW auf 1 KW Peak ursprünglich stündlich Auflösung <<< umrechung auf KWH
        pvdata['pvpower'] = pvdata['electricity'] * numberofhouseswithpv * capacityofpvs * 900 / 3600
        # setzen von start daten
        self.dataafrr = dataafrr
        self.datafcr = datafcr
        self.pvdata = pvdata
        self.capacityofenergystorage = capacityofenergystorage
        self.valuedata = 0

        #Erstellen der LogData
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
        self.logdata['chargecapacityusedbytrading'] = 0

        # setzen der Entscheidungen in der LogData
        self.setdecisionpoint()

        self.logdata = self.logdata.set_index('timestamp')
        self.logdata['netenergydemand'] = self.dataloadprofiles['Summe'] - self.pvdata['pvpower']
        self.logdata['pvpower'] = self.pvdata['pvpower']
        self.logdata['energydemandnopv'] = self.dataloadprofiles['Summe']
        self.logdata = self.logdata.reset_index()


    def run(self, ignoreprldecision=False, ignoresrldecision=False, showprogress=False, runwithtrading=False, runwithnoise=False):

        # Berrechung für PV-Leistung und erstellen einer Copy zur übergabe
        self.updatecapacityusedbypv()
        modelcopy = copy.deepcopy(self)
        # self.updatechargecapacity()
        # Simulation über die Zeit - Online durch For-Schleife
        for i in range(0, len(self.logdata)):
        #for i in range(len(self.logdata) - 1, -1, -1):
            if self.logdata.loc[i, 'decisionpoint']:

                # Falls die Simulation mit Noise durchgeführt wird, wird dieser vor der Entscheidung in die Logdata eingefügt und übergeben
                if runwithnoise:
                    logdatacopy = copy.copy(self.logdata)
                    if self.logdata.loc[i, 'typeofdecision'] == "SRL" or self.logdata.loc[i, 'typeofdecision'] == "PRL1":
                        logdatacopy['pvpower'] = logdatacopy['pvpower'] * (logdatacopy['errorpvshort'] + 1)
                        logdatacopy['energydemandnopv'] = logdatacopy['energydemandnopv'] * (logdatacopy['errorlastshort'] + 1)
                        logdatacopy['netenergydemand'] = logdatacopy['energydemandnopv'] - logdatacopy['pvpower']

                        # neuberechnung der Capacity im CopyModel zur übergabe
                        modelcopy.logdata = logdatacopy
                        modelcopy.updatecapacityusedbypv()
                        logdatacopy = modelcopy.logdata
                    if self.logdata.loc[i, 'typeofdecision'] == "PRL2" or self.logdata.loc[i, 'typeofdecision'] == "PRL3":
                        logdatacopy['pvpower'] = logdatacopy['pvpower'] * (logdatacopy['errorpvlong'] + 1)
                        logdatacopy['energydemandnopv'] = logdatacopy['energydemandnopv'] * (logdatacopy['errorlastlong'] + 1)
                        logdatacopy['netenergydemand'] = logdatacopy['energydemandnopv'] - logdatacopy['pvpower']

                        # neuberechnung der Capacity im CopyModel zur übergabe
                        modelcopy.logdata = logdatacopy
                        modelcopy.updatecapacityusedbypv()
                        logdatacopy = modelcopy.logdata
                else:
                    logdatacopy = copy.copy(self.logdata)
            # PRL Entscheidungen
            # Fragt den Agenden nach seiner Antwort und ruft den Decissionhandler auf
            if self.logdata.loc[i, 'decisionpoint'] and self.logdata.loc[i, 'typeofdecision'][:3] == 'PRL' and not ignoreprldecision:
                self.decisionhandler(i, self.logdata.loc[i, 'typeofdecision'],
                                     self.agent.get_decision(index=i, typeofdecision=self.logdata.loc[i, 'typeofdecision'],
                                                             logdata=logdatacopy, copymodel=copy.deepcopy(self)))
                self.updatecapacityusedbypv()
            # SRL Entscheidungen
            # Fragt den Agenden nach seiner Antwort und ruft den Decissionhandler auf
            if self.logdata.loc[i, 'decisionpoint'] and self.logdata.loc[i, 'typeofdecision'][:3] == 'SRL' and not ignoresrldecision:
                self.decisionhandler(i, self.logdata.loc[i, 'typeofdecision'],
                                     self.agent.get_decision(index=i, typeofdecision=self.logdata.loc[i, 'typeofdecision'],
                                                             logdata=logdatacopy, copymodel=copy.deepcopy(self)))

            # Print Progress
            if i % (len(self.logdata) // 10) == 0 and showprogress:
                print("Progress: " + str(int(i / len(self.logdata) * 100)) + "%")

        # Update
        self.updatecapacityusedbypv()
        self.updatechargecapacity()

        # optionales trading
        if runwithtrading:
            self.addtrading()
        self.updatechargecapacity()


    def updatecapacityusedbypv(self):
        self.logdata['chargecapacityusedbypv'] = 0
        self.logdata['drawfromgrid'] = 0
        self.logdata['feedingrid'] = 0

        # Fall unterscheidung pv größer Bedarf vs kleiner >> Anpassung Speicher und +- Grid
        for i in range(0, len(self.logdata)):

            # Positiver Netenergydemand
            # Energie wird vom Speicher bezogen
            # Falls Speicher nicht mehr voll wird der Strom vom Netz bezogen
            # Ist der Speicher voller als die Kapazitätsgrenze, entlade Speicher ins Netz (feed in grid)
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
            # Negativer Netenergydemand
            # Speicher so viel wie möglich in Speicher
            # Ist der Speicher voll, übergib überflüssige Energie in Netz
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
        # addiere einzelne Task zur Chargecapacity auf
        self.logdata['chargecapacity'] = self.logdata['chargecapacityusedbypv'] + self.logdata[
            'chargecapacityusedbycontrolenergyprl'] + self.logdata['chargecapacityusedbycontrolenergysrl'] + self.logdata['chargecapacityusedbytrading']

    def setdecisionpoint(self):
        # Setzen der Entscheidungspunkte in Logdata
        # einzelne Steplängen 96 für Tag 672 für Woche
        # 32, 60, 156 .... Zeitpunkt der ersten Entscheidung
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
        # Bekommt die Antwort des Agenten und trägt sie in die Logdatei ein.
        # bei jeder Antwort wird geprüft ob das Ende des relavnten Zeitraums noch in der Logdatei enthalten ist.
        # Anschließend wird der Wert in die Logdatei geschrieben.
        # Die Grenzen entsprechen immer den Start sowie den Endzeitpunkt des relevanten Bereichs
        # Bsp: PRL1 Entscheidungen sind für einen Zeitraum der 132 Simulationsschritte in der Zukunft liegt und nach 24h vorbei ist
        # 24h* 4 (viertel stunden) = 96             132 + 96 = 228
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

    def cutlogdatei(self, start=192, end=289, includepricedatafortrading=False):
        self.logdata = self.logdata.loc[start:len(self.logdata) - end]
        if includepricedatafortrading:
            self.pricedata = self.pricedata.loc[start:len(self.pricedata) - end]

    def evaluaterevenuestream(self):
        self.logdata = self.logdata.reset_index(drop=True)
        self.pricedata = self.pricedata.reset_index(drop=True)
    # Simple berechnung für SelfConsumption, feedingrid, chargecapacity
    # kumulierte Summen werden gewichtet
        self.logdata['drawfromgridcumsum'] = self.logdata['drawfromgrid'].cumsum()
        self.logdata['feedingridcumsum'] = self.logdata['feedingrid'].cumsum()
        totalenergydemand = self.logdata['energydemandnopv'].sum()
        # Gewichtung 0.30 Euro / kwh
        valueselfconsumption = (totalenergydemand - self.logdata['drawfromgrid'].sum()) * 0.30
        # Gewichtung 0.10 Euro / kwh
        valuefeedingrid = self.logdata['feedingrid'].sum() * 0.10
        # Gewichtung 0.30 Euro / kwh
        valuechargecapacity = self.logdata.loc[len(self.logdata) - 1]['chargecapacityusedbypv'] * 0.30

        valuesrlcontrolenergy = 0
        productsneg = ['NEG_00_04', 'NEG_04_08', 'NEG_08_12', 'NEG_12_16', 'NEG_16_20', 'NEG_20_24']

        # Schleife mit Step 4*4 = 16 ( 4 Stunden - eine SRL Zeitscheibe) läuft über Simulation und multipliziert bereitgestellte SRL
        # mit deren Preis
        # Manipulierung des timestamps falls Preisdaten nicht aus selben Jahr wie timestamp der Simulatuion
        for counter, i in enumerate(range(0, len(self.logdata), 16)):
            timestamp = self.logdata.loc[i, 'timestamp']
            # ANSPASSUNG: Hier wird die Jahreszahl des Zeittempels manipuliert. Nicht notwendig falls Daten aus selben Jahr.
            # Aktueller Datensatz Preise von 2019.
            timestamp = '2019' + timestamp[4:10]
            product = productsneg[counter % 6]
            valuesrlcontrolenergy = valuesrlcontrolenergy + self.dataafrr.loc[timestamp, product][
                'TOTAL_AVERAGE_CAPACITY_PRICE_[EUR/MW]'] / 250 * self.logdata.loc[i, 'chargecapacityusedbycontrolenergysrl']

        valueprlcontrolenergy = 0

        # Schleife mit Step 4 * 24  ( 24 Stunden - eine PRL Zeitscheibe) läuft über Simulation und multipliziert bereitgestellte PRL
        # mit deren Preis
        # Manipulierung des timestamps falls Preisdaten nicht aus selben Jahr wie timestamp der Simulatuion
        for counter, i in enumerate(range(0, len(self.logdata), 4 * 24)):
            timestamp = self.logdata.loc[i, 'timestamp']
            # ANSPASSUNG: Hier wird die Jahreszahl des Zeittempels manipuliert. Nicht notwendig falls Daten aus selben Jahr.
            # Aktueller Datensatz Preise von 2019.
            timestamp = '2019' + timestamp[4:10]
            valueprlcontrolenergy = valueprlcontrolenergy + self.datafcr.loc[timestamp]['DE_SETTLEMENTCAPACITY_PRICE_[EUR/MW]'] / 250 / 2 * \
                                    self.logdata.loc[i, 'chargecapacityusedbycontrolenergyprl']

        valuetrading = 0
        # Kumulierte Summe, falls Energie gehalten wird - multipliziert mit Return auf viertelstunden basis
        if self.logdata['chargecapacityusedbytrading'].sum() > 0:
            for i in range(len(self.logdata)):
                valuetrading = valuetrading + self.logdata.loc[i, 'chargecapacityusedbytrading'] * self.pricedata.loc[i, 'pricediff'] / 1000 # umrechnung in kwh

        valuesumme = valueprlcontrolenergy + valuesrlcontrolenergy + valuefeedingrid + valuechargecapacity + valueselfconsumption + valuetrading
        self.valuedata = [valueselfconsumption, valuechargecapacity, valuefeedingrid, valuesrlcontrolenergy, valueprlcontrolenergy, valuetrading, valuesumme]


        return [valueselfconsumption, valuechargecapacity, valuefeedingrid, valuesrlcontrolenergy, valueprlcontrolenergy, valuetrading, valuesumme]

    def def_noise(self, typeofnoice, stdlongpv, stdshortpv, stdlonglast, stdshortlast, logdata):

        # Langer Fehler muss größer sein als kurzer
        #
        # Setze Perlin Noise mit übergebenen Fehler
        if typeofnoice == "perlin":
            base = random.randrange(1, 10000, 100)
            octaves = 5
            points = len(logdata)
            span = 15
            df = pd.DataFrame({'A': [np.nan]})

            logdata['errorpvlong'] = 0
            logdata['errorpvshort'] = 0

            for i in range(len(logdata)):
                x = float(i) * span / (points) - 0.5 * span
                y = noise.pnoise1(x + base, octaves) / 20 * stdlongpv * 100
                df = df.append({'A': y}, ignore_index=True)
            logdata['errorpvlong'] = df['A']
            logdata['errorpvshort'] = df['A'] / stdlongpv * stdshortpv
            base = random.randrange(1, 10000, 100)
            logdata['errorlastlong'] = 0
            logdata['errorlastshort'] = 0

            df = pd.DataFrame({'B': [np.nan]})

            for i in range(len(logdata)):
                x = float(i) * span / (points) - 0.5 * span
                y = noise.pnoise1(x + base, octaves) / 20 * stdlonglast * 100
                df = df.append({'B': y}, ignore_index=True)
            logdata['errorlastlong'] = df['B']
            logdata['errorlastshort'] = df['B'] / stdlonglast * stdshortlast
            logdata.loc[0, 'errorpvlong'] = 0
            logdata.loc[0, 'errorlastlong'] = 0
            logdata.loc[0, 'errorpvshort'] = 0
            logdata.loc[0, 'errorlastshort'] = 0

        # setze Gaussian Noise
        if typeofnoice == "gaussian":
            df = pd.DataFrame(np.random.normal(0, stdlongpv, len(logdata)))
            logdata['errorpvlong'] = df[0]
            logdata['errorpvshort'] = df[0] / stdlongpv * stdshortpv

            df = pd.DataFrame(np.random.normal(0, stdlonglast, len(logdata)))
            logdata['errorlastlong'] = df[0]
            logdata['errorlastshort'] = df[0] / stdlonglast * stdshortlast

        if stdlonglast == 0:
            logdata['errorlastlong'] = 0
        if stdlongpv == 0:
            logdata['errorpvlong'] = 0
        if stdshortlast == 0:
            logdata['errorlastshort'] = 0
        if stdshortpv == 0:
            logdata['errorpvshort'] = 0


    def addtrading(self):
        pricedata = self.pricedata.reset_index()
        pricedata['pricediff'] = pricedata['price'] - pricedata['price'].shift(1)
        pricedata['direction'] = [1 if pricedata['pricediff'].loc[i] > 0 else 0 for i in pricedata.index]
        pricedata['signalbasedbuy'] = [1 if pricedata.loc[i, 'ma0.5'] < pricedata.loc[i, 'ma2'] else 0 for i in pricedata.index]

        pricedata['profitperfect'] = [pricedata.loc[i, 'pricediff'] if pricedata.loc[i, 'direction'] == 1 else 0 for i in pricedata.index]
        pricedata['profitsignal'] = [pricedata.loc[i, 'pricediff'] if pricedata.loc[i, 'signalbasedbuy'] == 1 else 0 for i in
                                     pricedata.index]
        pricedata['profitsimpel'] = pricedata['pricediff']
        self.pricedata = pricedata
        # Setzte Tradingperfect auf True falls ein perfekter Händler Strom halten würde
        self.logdata['tradingperfect'] = [True if pricedata['direction'].loc[i] == 1 else False for i in pricedata.index]
        # Freie Kapazitäten werden verwendet falls ein perfekter Händler Strom halten würde
        self.logdata['chargecapacityusedbytrading'] = [self.capacityofenergystorage - self.logdata.loc[i, 'chargecapacity'] if self.logdata.loc[i, 'tradingperfect'] else 0 for i in self.logdata.index]
        self.logdata['chargecapacity'] = [self.capacityofenergystorage if self.logdata.loc[i, 'tradingperfect'] else self.logdata.loc[i, 'chargecapacity'] for i in self.logdata.index]


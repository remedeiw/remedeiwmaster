import math
import SimModel

# Jeder Agent erbt von Superagent und hat die selben Parameter für die get_decision
class Superagent():
    def get_decision(self, index, typeofdecision, logdata, copymodel: SimModel.Model):
        pass


class Agentonlypv(Superagent):
    # Agent onlypv gibt immer 0 zurück
    def get_decision(self, index, typeofdecision, logdata, copymodel):
        if typeofdecision == "SRL":
            decision = [0, 0, 0, 0, 0, 0]
        if typeofdecision == "PRL1":
            decision = [0]
        if typeofdecision == "PRL2":
            decision = [0, 0]
        if typeofdecision == "PRL3":
            decision = [0, 0]
        return decision


class Agent_manualinput(Superagent):
    # Agent manualinput ermöglicht einen manuellen Input für jede Entscheidung während der Laufzeit
    def get_decision(self, index, typeofdecision, logdata, copymodel):
        if typeofdecision == "SRL":
            eingabe1 = int(input(str(index) + " 00_04 " + str(typeofdecision)))
            eingabe2 = int(input(str(index) + " 04_08 " + str(typeofdecision)))
            eingabe3 = int(input(str(index) + " 08_12 " + str(typeofdecision)))
            eingabe4 = int(input(str(index) + " 12_16 " + str(typeofdecision)))
            eingabe5 = int(input(str(index) + " 16_20 " + str(typeofdecision)))
            eingabe6 = int(input(str(index) + " 20_24 " + str(typeofdecision)))

            decision = [eingabe1, eingabe2, eingabe3, eingabe4, eingabe5, eingabe6]
        if typeofdecision == "PRL1":
            eingabe1 = int(input(str(index) + " 00_24 " + str(typeofdecision)))
            decision = [eingabe1]
        if typeofdecision == "PRL2":
            eingabe1 = int(input(str(index) + " 00_24 Sat " + str(typeofdecision)))
            eingabe2 = int(input(str(index) + " 00_24 Sun " + str(typeofdecision)))
            decision = [eingabe1, eingabe2]
        if typeofdecision == "PRL3":
            eingabe1 = int(input(str(index) + " 00_24 Mon " + str(typeofdecision)))
            eingabe2 = int(input(str(index) + " 00_24 Tue " + str(typeofdecision)))
            decision = [eingabe1, eingabe2]
        return decision


class Agent_Fillforoccupancyrate(Superagent):
    # Füllt freie Kapzitäten auf
    #
    def __init__(self):
        self.capacityofenergystorage = 0
        # Steps von Entscheidungspunkt zu SRL Zeitscheiben
        self.srlsteps = [64, 80, 96, 112, 128, 144, 160]
        # Steps von Entscheidungspunkt zu PRL Zeitscheiben
        self.prlsteps = [132, 228, 324, 420]


    def get_decision(self, index, typeofdecision, logdata, copymodel: SimModel.Model):
        # Zieht maximalen Ladestand im Entscheidungszeitraum von der Speicherkapazität ab und gibt die minimale freie Kapazität zurück
        self.capacityofenergystorage = copymodel.capacityofenergystorage
        if typeofdecision == "SRL" and index + self.srlsteps[6] < len(logdata):
            decision = [0, 0, 0, 0, 0, 0]
            for i in range(0, 6):
                data = logdata.iloc[index + self.srlsteps[i]: index + self.srlsteps[i + 1]]
                decision[i] = max(self.capacityofenergystorage - math.ceil(
                    data['chargecapacityusedbypv'].max() + data['chargecapacityusedbycontrolenergyprl'].max()), 0)
        else:
            decision = [0, 0, 0, 0, 0, 0]

        if typeofdecision == "PRL1":
            decision = [0, 0]
            if index + self.prlsteps[1] < len(logdata):
                data = logdata.iloc[index + self.prlsteps[0]: index + self.prlsteps[1]]
                decision[0] = self.capacityofenergystorage - math.ceil(data['chargecapacityusedbypv'].max())

        if typeofdecision == "PRL2":
            decision = [0, 0]
            if index + self.prlsteps[1] < len(logdata):
                data = logdata.iloc[index + self.prlsteps[0]: index + self.prlsteps[1]]
                decision[0] = self.capacityofenergystorage - math.ceil(data['chargecapacityusedbypv'].max())
            if index + self.prlsteps[2] < len(logdata):
                data = logdata.iloc[index + self.prlsteps[1]: index + self.prlsteps[2]]
                decision[1] = self.capacityofenergystorage - math.ceil(data['chargecapacityusedbypv'].max())

        if typeofdecision == "PRL3":
            decision = [0, 0]
            if index + self.prlsteps[2] < len(logdata):
                data = logdata.iloc[index + self.prlsteps[1]: index + self.prlsteps[2]]
                decision[0] = self.capacityofenergystorage - math.ceil(data['chargecapacityusedbypv'].max())
            if index + self.prlsteps[3] < len(logdata):
                data = logdata.iloc[index + self.prlsteps[2]: index + self.prlsteps[3]]
                decision[1] = self.capacityofenergystorage - math.ceil(data['chargecapacityusedbypv'].max())

        return decision


class Agent_Outlook(Superagent):
    def __init__(self, storagetime):
        self.occagent = Agent_Fillforoccupancyrate()
        # Steps von Entscheidungspunkt zu SRL Zeitscheiben
        self.srlsteps = [64, 80, 96, 112, 128, 144, 160]
        # Steps von Entscheidungspunkt zu PRL Zeitscheiben
        self.prlsteps = [132, 228, 324, 420]
        # Tage die neben dem Entscheidungszeitraum mit betrachtet werden sollen
        self.storagetime = storagetime

    def get_decision(self, index, typeofdecision, logdata, copymodel: SimModel.Model):
        # Agent begrenzt die Ladekapazität für PV durch hörere Zuteilung zu PRL
        # Es soll nur so viel PV geladen werden, dass es gerade aufgebraucht wird bis zum nächsten Sonnenaufgang
        # Über den Parameter "Storagetime" kann festgelegt werden wie viele Tage voraus geschaut werden soll.
        decision = self.occagent.get_decision(index, typeofdecision, logdata, copymodel)
        if typeofdecision == "PRL1":
            if index + self.prlsteps[1] + 192 < len(logdata):
                data = logdata.iloc[index + self.prlsteps[0] + 48: self.find_next_sunrise(index + self.prlsteps[0] + 96 * self.storagetime, logdata)]
                decision[0] = decision[0] + math.floor(data['chargecapacityusedbypv'].min())

        if typeofdecision == "PRL2":
            if index + self.prlsteps[1] + 192 < len(logdata):
                data = logdata.iloc[index + self.prlsteps[0] + 48: self.find_next_sunrise(index + self.prlsteps[0] + 96 * self.storagetime, logdata)]
                decision[0] = decision[0] + math.floor(data['chargecapacityusedbypv'].min())

            if index + self.prlsteps[2] + 192 < len(logdata):
                data = logdata.iloc[index + self.prlsteps[1] + 48: self.find_next_sunrise(index + self.prlsteps[1] + 96 * self.storagetime, logdata)]
                decision[1] = decision[1] + math.floor(data['chargecapacityusedbypv'].min())

        if typeofdecision == "PRL3":
            if index + self.prlsteps[2] + 192 < len(logdata):
                data = logdata.iloc[index + self.prlsteps[1] + 48: self.find_next_sunrise(index + self.prlsteps[1] + 96 * self.storagetime, logdata)]
                decision[0] = decision[0] + math.floor(data['chargecapacityusedbypv'].min())

            if index + self.prlsteps[3] + 192 < len(logdata):
                data = logdata.iloc[index + self.prlsteps[2] + 48: self.find_next_sunrise(index + self.prlsteps[2] + 96 * self.storagetime, logdata)]
                decision[1] = decision[1] + math.floor(data['chargecapacityusedbypv'].min())
        return decision

    def find_next_sunrise(self, start, logdata):
        while logdata.loc[start, 'pvpower'] <= 0:
            start = start + 1
        return start


class Agent(Superagent):
    def __init__(self):
        self.srlsteps = [64, 80, 96, 112, 128, 144, 160]
        self.prlsteps = [132, 228, 324, 420]

    def get_decision(self, index, typeofdecision, logdata, copymodel: SimModel.Model):
        #
        # Agent überprüft den Tag nach dem Entscheidungszeitraum.
        # Ist es kein sonniger Tag, so wird die Storagetime für den vorherigen erhöht.
        #
        agent = Agent_Outlook(1)
        decision = agent.get_decision(index, typeofdecision, logdata, copymodel)
        if typeofdecision == "PRL1":
            if index + self.prlsteps[1] + 192 < len(logdata):
                if self.is_sunny_day(self.find_next_sunrise(index + self.prlsteps[1], logdata), self.find_next_sunrise(index + self.prlsteps[1] + 96, logdata), logdata):
                    agent.storagetime = 1
                else:
                    agent.storagetime = 2
            decision = agent.get_decision(index, typeofdecision, logdata, copymodel)

        if typeofdecision == "PRL2":
            if index + self.prlsteps[1] + 192 < len(logdata):
                if self.is_sunny_day(self.find_next_sunrise(index + self.prlsteps[1], logdata), self.find_next_sunrise(index + self.prlsteps[1] + 96, logdata), logdata):
                    agent.storagetime = 1
                else:
                    agent.storagetime = 2
            decision1 = agent.get_decision(index, typeofdecision, logdata, copymodel)
            if index + self.prlsteps[2] + 192 < len(logdata):
                if self.is_sunny_day(self.find_next_sunrise(index + self.prlsteps[2], logdata), self.find_next_sunrise(index + self.prlsteps[2] + 96, logdata), logdata):
                    agent.storagetime = 1
                else:
                    agent.storagetime = 2
            decision2 = agent.get_decision(index, typeofdecision, logdata, copymodel)
            decision = decision1
            decision[1] = decision2[1]
        if typeofdecision == "PRL3":
            if index + self.prlsteps[2] + 192 < len(logdata):
                if self.is_sunny_day(self.find_next_sunrise(index + self.prlsteps[2], logdata), self.find_next_sunrise(index + self.prlsteps[2] + 96, logdata), logdata):
                    agent.storagetime = 1
                else:
                    agent.storagetime = 2
            decision1 = agent.get_decision(index, typeofdecision, logdata, copymodel)
            if index + self.prlsteps[3] + 192 < len(logdata):
                if self.is_sunny_day(self.find_next_sunrise(index + self.prlsteps[3], logdata), self.find_next_sunrise(index + self.prlsteps[3] + 96, logdata), logdata):
                    agent.storagetime = 1
                else:
                    agent.storagetime = 2
            decision2 = agent.get_decision(index, typeofdecision, logdata, copymodel)
            decision = decision1
            decision[1] = decision2[1]




        return decision

    def is_sunny_day(self, start, end, logdata):
        data = logdata.iloc[start:end]
        if data['netenergydemand'].sum() < 0:
            result = True
        else:
            result = False
        return result

    def find_next_sunrise(self, start, logdata):
        while logdata.loc[start, 'pvpower'] <= 0:
            start = start + 1
        return start




class Agentoptimizebypricesignal(Superagent):
    def __init__(self, step=1):
        self.step = step

    # Experimental
    # Preissensitiver Agent erhöht die PRL Entscheidung so lange wie es den Value des Entscheidungsraums erhöht.
    # Startet mit Agent Fillforoccunpancyrate Decision
    def get_decision(self, index, typeofdecision, logdata, copymodel: SimModel.Model):
        modelagent = Agent_Fillforoccupancyrate()
        self.copymodel = copymodel
        self.copymodel.agent = modelagent
        if typeofdecision[:3] == "PRL":
            decision = modelagent.get_decision(index, typeofdecision, logdata, copymodel)
            self.copymodel.decisionhandler(index, typeofdecision, decision)
            self.copymodel.run(ignoreprldecision=True)
            value = self.copymodel.evaluaterevenuestream()[5]
            lastvalue = -100
            for i in range(0, len(decision)):
            #for i in range(len(decision) - 1, -1, -1):
                # while value > lastvalue:
                while value - lastvalue > 0.005 * self.step:
                    # print(value)
                    lastvalue = value
                    decision[i] = min(decision[i] + self.step, copymodel.capacityofenergystorage)
                    # print(decision[i])
                    self.copymodel.decisionhandler(index, typeofdecision, decision)
                    self.copymodel.run(ignoreprldecision=True)
                    data = self.copymodel.evaluaterevenuestream()
                    value = data[6] + data[0] * 10

                decision[i] = max(decision[i] - self.step, 0)

        if typeofdecision == "SRL":
            decision = modelagent.get_decision(index, typeofdecision, logdata, copymodel)

        return decision
import math
class agentnopv():
    def getdecision(self, index, typeofdecision, logdata):
        if typeofdecision == "SRL":
            decision = [0, 0, 0, 0, 0, 0]
        if typeofdecision == "PRL1":
            decision = [0]
        if typeofdecision == "PRL2":
            decision = [0, 0]
        if typeofdecision == "PRL3":
            decision = [0, 0]
        return decision


class agentmanualinput():
    def getdecision(self, index, typeofdecision, logdata):
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


class agentoccupancyrate():
    def __init__(self, capacityofenergystorage):
        self.capacityofenergystorage = capacityofenergystorage
        self.srlsteps = [64, 80, 96, 112, 128, 144, 160]
        self.prlsteps = [132, 228, 324, 420]


    def getdecision(self, index, typeofdecision, logdata):
        if typeofdecision == "SRL" and index + self.srlsteps[6] < len(logdata):
            decision = [0, 0, 0, 0, 0, 0]
            for i in range(0,6):
                data = logdata.iloc[index + self.srlsteps[i]: index + self.srlsteps[i + 1]]
                decision[i] = self.capacityofenergystorage - math.ceil(data['chargecapacityusedbypv'].max() + data['chargecapacityusedbycontrolenergyprl'].max())
        else:
            decision = [0, 0, 0, 0, 0, 0]

        if typeofdecision == "PRL1":
            decision = [0]
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


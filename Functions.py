import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def plotdataframecontrolenergy(dataframe, posorneg):
    dataframegroup = dataframe.groupby('PRODUCT')
    plt.figure(figsize=(12, 5))
    for product, group in dataframegroup:
        if product[:3] == posorneg:
            group['TOTAL_AVERAGE_CAPACITY_PRICE_[EUR/MW]'].plot()
    legend = plt.legend(loc='upper left', frameon=False)
    legend.get_texts()[0].set_text(posorneg + '_00_04')
    legend.get_texts()[1].set_text(posorneg + '_04_08')
    legend.get_texts()[2].set_text(posorneg + '_08_12')
    legend.get_texts()[3].set_text(posorneg + '_12_16')
    legend.get_texts()[4].set_text(posorneg + '_16_20')
    legend.get_texts()[5].set_text(posorneg + '_20_24')
    plt.xticks(rotation=45)


def plotpvdata(pvdata):
    plt.figure(figsize=(12, 5))
    pvdata['electricity'].plot(color="orange")
    plt.xticks(rotation=45)


def plotlastprofiledata(lastprofile, profilenumbers):
    plt.figure(figsize=(12, 5))
    for profilenum in profilenumbers:
        profil = 'Profil ' + str(profilenum)
        lastprofile[profil].plot()
    plt.xticks(rotation=45)
    legend = plt.legend(loc='upper left', frameon=False)



def plotpricedata(pricedata):
    plt.figure(figsize=(12, 5))
    pricedata['Deutschland/Luxemburg[Euro/MWh]'].plot(color="pink")
    plt.xticks(rotation=45)


def plotprimecontroldata(data):
    plt.figure(figsize=(12, 5))
    data['CROSSBORDER_SETTLEMENTCAPACITY_PRICE_[EUR/MW]'].plot()
    plt.xticks(rotation=45)


#def kumulierelastprofildaten(dataframe, timestampsdf):
#    clmn = list(dataframe)
#    for column in clmn:
#        dataframe[column] = dataframe[column].rolling(15).sum()
#    dataframe = dataframe.join(timestampsdf)

#    # dataframe = dataframe[dataframe.index % 15 == 0]
#    return dataframe'


def viertelstundentakt(dataframe):
    dataframe = dataframe[dataframe.index % 15 == 0]
    return dataframe


def getdata(timestart, timeende):
    datafcr = pd.read_csv('Data/datafcr2019.csv', index_col='DATE_TO')
    dataafrr = pd.read_csv('Data/dataafrr2019.csv')
    datamfrr = pd.read_csv('Data/datamfrr2019.csv', index_col='DATE_TO')
    datalastprofile = pd.read_csv('Data/lastprofile.csv', index_col='time')
    pvdata = pd.read_csv('Data/pvdata.csv', index_col='timestamp')
    dataprice = pd.read_csv('Data/Gro_handelspreise_2019.csv', index_col='timestamp')

    dataafrr = dataafrr.set_index(['DATE_TO', 'PRODUCT'])

    datafcr = datafcr.loc['2019-' + timestart:'2019-' + timeende]
    dataafrr = dataafrr.loc['2019-' + timestart:'2019-' + timeende]
    datamfrr = datamfrr.loc['2019-' + timestart:'2019-' + timeende]
    datalastprofile = datalastprofile.loc['2014-' + timestart:'2014-' + timeende]
    pvdata = pvdata.loc['2014-' + timestart:'2014-' + timeende]
    dataprice = dataprice.loc['2019-' + timestart:'2019-' + timeende]


    return datafcr, dataafrr, datamfrr, datalastprofile, pvdata, dataprice


def kumuliereprofile(dataframe, profilenumbers):
    dataframe['Summe'] = 0
    for profilenum in profilenumbers:
        profil = 'Profil ' + str(profilenum)
        dataframe['Summe'] = dataframe['Summe'] + dataframe[profil]

    return dataframe


def plotchargecapacity(model):
    # X Achse 2. Plot neu beschriften
    plt.figure(figsize=(16, 5))
    model.logdata['chargecapacity'].plot(color='red')
    model.logdata['chargecapacityusedbypv'].plot(color='blue')
    model.logdata['chargecapacityusedbycontrolenergyprl'].plot(color='orange')
    model.logdata['chargecapacityusedbycontrolenergysrl'].plot(color='green')
    legend = plt.legend(loc='upper left', frameon=False)
    plt.axhline(y=0, color='pink')
    plt.axhline(y=model.capacityofenergystorage, color='pink')
    plt.xticks(rotation=15)
    plt.ylabel('Charge Capacity')
    plt.figure(figsize=(16, 5))
    plt.stackplot(model.logdata.index, model.logdata['chargecapacityusedbypv'],
    model.logdata['chargecapacityusedbycontrolenergyprl'],
    model.logdata['chargecapacityusedbycontrolenergysrl'], labels=['PV', 'PRL', 'SRL'],
            baseline="zero")
    # plt.stackplot(model.logdata.index ,model.logdata['chargecapacityusedbycontrolenergyprl'], model.logdata['chargecapacityusedbycontrolenergysrl'], model.logdata['chargecapacityusedbypv'], labels=['PRL','SRL','PV'], baseline="zero")
    plt.axhline(y=0, color='pink')
    plt.axhline(y=model.capacityofenergystorage, color='pink')
    plt.xticks(np.arange(1, len(model.logdata.index), step=100), [], rotation=15)
    legend = plt.legend(loc='upper left', frameon=False)
    plt.ylabel('Charge Capacity')
    #plt.xticks(locs,labels, rotation=15)
    #locs, labels = plt.xticks()



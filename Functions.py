import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import copy


def plot_secondcontrolenergy(model, posorneg="NEG"):
    dataframe = model.dataafrr
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
    plt.ylabel("price in Euro/MWh")


def plot_pvdata(model):
    plt.figure(figsize=(12, 5))
    model.pvdata['electricity'].plot(color="#2CBDFE")
    plt.xticks(rotation=45)
    plt.ylabel('kwh')


def plot_lastprofiledata(model):
    plt.figure(figsize=(12, 5))
    for profilenum in model.listoflastprofiles:
        profil = 'Profil ' + str(profilenum)
        model.dataloadprofiles[profil].plot()
    plt.xticks(rotation=45)
    legend = plt.legend(loc='upper left', frameon=False)
    plt.ylabel('last')



def plot_primecontroldata(model):
    plt.figure(figsize=(12, 5))
    model.datafcr['CROSSBORDER_SETTLEMENTCAPACITY_PRICE_[EUR/MW]'].plot(color='#2CBDFE')
    plt.xticks(rotation=45)
    plt.ylabel("price in Euro/MWh")


#def kumulierelastprofildaten(dataframe, timestampsdf):
#    clmn = list(dataframe)
#    for column in clmn:
#        dataframe[column] = dataframe[column].rolling(15).sum()
#    dataframe = dataframe.join(timestampsdf)

#    # dataframe = dataframe[dataframe.index % 15 == 0]
#    return dataframe'


#def viertelstundentakt(dataframe):
#    dataframe = dataframe[dataframe.index % 15 == 0]
#    return dataframe


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


def plot_realchargestate(model, SRLFaktor=0.5, includetrading = False):
    if includetrading:
        model.logdata['realchargecapacity'] = model.logdata['chargecapacityusedbypv'] + model.logdata['chargecapacityusedbycontrolenergyprl'] * 0.5 + model.logdata['chargecapacityusedbycontrolenergysrl'] * SRLFaktor + model.logdata['chargecapacityusedbytrading']
    else:
        model.logdata['realchargecapacity'] = model.logdata['chargecapacityusedbypv'] + model.logdata[
            'chargecapacityusedbycontrolenergyprl'] * 0.5 + model.logdata['chargecapacityusedbycontrolenergysrl'] * SRLFaktor
    # X Achse 2. Plot neu beschriften
    plt.figure(figsize=( 16, 5))
    model.logdata['chargecapacity'].plot(color='purple')
    model.logdata['chargecapacityusedbypv'].plot(color='blue')
    model.logdata['chargecapacityusedbycontrolenergyprl'].plot(color='orange')
    model.logdata['chargecapacityusedbycontrolenergysrl'].plot(color='green')
    model.logdata['chargecapacityusedbytrading'].plot(color='red')
    model.logdata['realchargecapacity'].plot(color='black')
    #legend = plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    legend = plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.2),
               ncol=3)
    plt.axhline(y=0, color='pink')
    plt.axhline(y=model.capacityofenergystorage, color='pink')
    plt.xticks(rotation=15)
    plt.ylabel('Charge Capacity in kwh')
    locs, labels = plt.xticks()
    labels = labels[1:]

    load = 0
    for i in range(0, len(model.logdata)):
        if model.logdata.iloc[i-1]['realchargecapacity'] < model.logdata.iloc[i]['realchargecapacity']:
            load = load + model.logdata.iloc[i]['realchargecapacity'] - model.logdata.iloc[i-1]['realchargecapacity']
    #print(load)
    print(load/model.capacityofenergystorage)


def plot_chargecapacity(model):
    # X Achse 2. Plot neu beschriften
    plt.figure(figsize=( 16, 5))
    model.logdata['chargecapacity'].plot(color='purple')
    model.logdata['chargecapacityusedbypv'].plot(color='blue')
    model.logdata['chargecapacityusedbycontrolenergyprl'].plot(color='orange')
    model.logdata['chargecapacityusedbycontrolenergysrl'].plot(color='green')
    model.logdata['chargecapacityusedbytrading'].plot(color='red')
    #legend = plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    legend = plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.2),
               ncol=3)
    plt.axhline(y=0, color='pink')
    plt.axhline(y=model.capacityofenergystorage, color='pink')
    plt.xticks(rotation=15)
    plt.ylabel('Charge Capacity in kwh')
    locs, labels = plt.xticks()
    labels = labels[1:]

    plt.figure(figsize=(16, 5))
    plt.stackplot(model.logdata.index, model.logdata['chargecapacityusedbypv'],
    model.logdata['chargecapacityusedbycontrolenergyprl'],
    model.logdata['chargecapacityusedbycontrolenergysrl'], model.logdata['chargecapacityusedbytrading'], labels=['PV', 'PRL', 'SRL', 'Trading'],
            baseline="zero")
    # plt.stackplot(model.logdata.index ,model.logdata['chargecapacityusedbycontrolenergyprl'], model.logdata['chargecapacityusedbycontrolenergysrl'], model.logdata['chargecapacityusedbypv'], labels=['PRL','SRL','PV'], baseline="zero")
    plt.axhline(y=0, color='pink')
    plt.axhline(y=model.capacityofenergystorage, color='pink')
    plt.xticks(np.arange(1, len(model.logdata.index), step=200),labels , rotation=15)
    legend = plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.2),
          ncol=3)
    plt.ylabel('Charge Capacity in kwh')
    plt.xlabel('timestamp')
    #plt.xticks(locs,labels, rotation=15)



def plot_error(model):
    logdata = copy.copy(model.logdata)
    plt.figure(figsize=(12, 5))
    logdata['netenergydemand'].plot()
    logdata['netenergydemandshorterror'] = logdata['energydemandnopv'] * (logdata['errorlastshort'] + 1) - logdata['pvpower'] * (
                logdata['errorpvshort'] + 1)
    logdata['netenergydemandshorterror'].plot()
    logdata['netenergydemandlongerror'] = logdata['energydemandnopv'] * (logdata['errorlastlong'] + 1) - logdata['pvpower'] * (
                logdata['errorpvlong'] + 1)
    logdata['netenergydemandlongerror'].plot()
    legend = plt.legend(loc='upper right', frameon=False)
    plt.xticks(rotation=15)
    plt.ylabel('net energy demand in kwh')
    plt.xlabel('time')



def plot_revenuestreams(model):
    fig = plt.figure()
    ax = fig.add_axes([0, 0, 1, 1])
    langs = ['value selfconsumption', 'value chargecapacity', 'value feed in grid', 'value SRL controlenergy', 'value PRL controlenergy',
             'value trading', 'value summe']
    data = model.valuedata
    ax.bar(langs, data, color=['#2CBDFE', '#9D2EC5', 'yellow', '#47DBCD', '#F5b14C', 'red', 'darksalmon'])
    plt.xticks(rotation=20)
    plt.axhline(y=data[6], color='darksalmon')
    plt.ylabel("Revenue Points")
    plt.show()



def plot_pricedata(model):
    plt.figure(figsize=(12, 5))
    model.pricedata['price'].plot(label='price', color='#2CBDFE')
    model.pricedata['ma2'].plot(label='ma2')
    model.pricedata['ma0.5'].plot(label='ma0.5')
    plt.xticks(rotation=20)
    plt.ylabel("price in Euro/MWh")
    plt.legend()
    plt.show()


def plot_capacityusedbypie(model):
    usedbypv = np.trapz(model.logdata['chargecapacityusedbypv']) / (model.capacityofenergystorage * len(model.logdata))
    usedbysrl = np.trapz(model.logdata['chargecapacityusedbycontrolenergysrl']) / (model.capacityofenergystorage * len(model.logdata))
    usedbyprl = np.trapz(model.logdata['chargecapacityusedbycontrolenergyprl']) / (model.capacityofenergystorage * len(model.logdata))
    usedbytrading = np.trapz(model.logdata['chargecapacityusedbytrading']) / (model.capacityofenergystorage * len(model.logdata))

    explode = (0.1, 0, 0, 0)
    datapiechart = [usedbypv, usedbyprl, usedbysrl, usedbytrading]
    labels = ['PV', 'PRL', 'SRL', 'Trading']

    plt.pie(datapiechart, labels=labels, autopct='%1.1f%%', pctdistance=1.3, labeldistance=1.5, explode=explode)
    plt.show()
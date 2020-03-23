import pandas as pd
import matplotlib.pyplot as plt


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


def plotlastprofiledata(lastprofile, profilenumber):
    plt.figure(figsize=(12, 5))
    profil = 'Profil '+ str(profilenumber)
    lastprofile[profil].plot()
    plt.xticks(rotation=45)

def kumulierelastprofildaten(dataframe, timestampsdf):
    clmn = list(dataframe)
    for column in clmn:
        dataframe[column] = dataframe[column].rolling(15).sum()
    dataframe = dataframe.join(timestampsdf)
    # dataframe = dataframe[dataframe.index % 15 == 0]
    return dataframe


def viertelstundentakt(dataframe):
    dataframe = dataframe[dataframe.index % 15 == 0]
    return dataframe


def getdata(timestart, timeende):
    datafcr = pd.read_csv('Data/datafcr2019.csv', index_col='DATE_TO')
    dataafrr = pd.read_csv('Data/dataafrr2019.csv', index_col='DATE_TO')
    datamfrr = pd.read_csv('Data/datamfrr2019.csv', index_col='DATE_TO')
    datalastprofile = pd.read_csv('Data/lastprofile.csv', index_col='time')
    pvdata = pd.read_csv('Data/pvdata.csv', index_col='timestamp')

    datafcr = datafcr.loc['2019-' + timestart:'2019-' + timeende]
    dataafrr = dataafrr.loc['2019-' + timestart:'2019-' + timeende]
    datamfrr = datamfrr.loc['2019-' + timestart:'2019-' + timeende]
    datalastprofile = datalastprofile.loc['2014-' + timestart:'2014-' + timeende]
    pvdata = pvdata.loc['2014-' + timestart:'2014-' + timeende]

    return datafcr, dataafrr, datamfrr, datalastprofile, pvdata

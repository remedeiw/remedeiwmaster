import pandas as pd
import matplotlib.pyplot as plt

def plotDataFrameControlEnergy(dataframe,posorneg):
    dataframegroup = dataframe.groupby('PRODUCT')
    plt.figure(figsize = (12, 5))
    for product, group in dataframegroup:
        if product[:3] == posorneg:
            group['TOTAL_AVERAGE_CAPACITY_PRICE_[EUR/MW]'].plot()
    legend = plt.legend(loc='upper left', frameon=False)
    legend.get_texts()[0].set_text(posorneg + '_00_04')
    legend.get_texts()[1].set_text(posorneg +'_04_08')
    legend.get_texts()[2].set_text(posorneg +'_08_12')
    legend.get_texts()[3].set_text(posorneg +'_12_16')
    legend.get_texts()[4].set_text(posorneg +'_16_20')
    legend.get_texts()[5].set_text(posorneg +'_20_24')
    plt.xticks(rotation=45)

def kumuliereLastprofilDaten(dataframe,timestampsdf):
    clmn = list(dataframe)
    for column in clmn:
        dataframe[column] = dataframe[column].rolling(15).sum()
    dataframe = dataframe.join(timestampsdf)
    #dataframe = dataframe[dataframe.index % 15 == 0]
    return dataframe

def viertelstundentakt(dataframe):
    dataframe = dataframe[dataframe.index % 15 == 0]
    return dataframe


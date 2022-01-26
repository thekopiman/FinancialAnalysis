from ast import Return
from shutil import SameFileError
from yahoo_fin.stock_info import get_data
import pandas as pd
import numpy as np
from datetime import datetime
import os
import math

from modules import StockAnalysis, CrossReferencing


class ReturnsAnalysis:
    def __init__(self, dataset=None, excel_file=None) -> None:
        '''
        dataset: A dataframe of the following columns - date, XX_adjclose,
        YY_adjclose, ZZ_adjclose, etc
        excel_file: Send the path of the excel file to read it as a DataFrame
        '''
        try:
            if dataset != None:
                pass
            elif excel_file != None:
                self.rawdataset = pd.read_excel(excel_file)
        except ValueError:
            self.rawdataset = dataset

        self.dataset = {'raw': self.rawdataset}
        self.tickers = self.obtain_ticker()
        # self.dataset['summary'] = pd.DataFrame(
        #     columns=[["Index name"] + self.tickers])

        # Remember to update the index names subsequently -> Create a method to do this automatically :D
        self.dataset['summary'] = pd.DataFrame(
            columns=[self.tickers], index=[
                'mean_returns',
                'annual_returns',
                'standard_deviation',
                'variance',
                'annual_std'])

    def obtain_ticker(self):
        headers = list(self.dataset['raw'].columns)[1:]
        tickers = []
        for header in headers:
            if header != "date":
                tickers.append(str(header).split("_")[0])
        return tickers

    def get_rawdataset(self):
        return self.dataset['raw']

    def get_returnsdataset(self):
        try:
            return self.dataset['returns']
        except KeyError:
            self.update_returns()
            return self.dataset['returns']

    def get_summarydataset(self):
        try:
            return self.dataset['summary']
        except KeyError:
            self.update_expectedreturns()
            return self.dataset['summary']

    def get_r_minus_er(self):
        try:
            return self.dataset['r_minus_er']
        except KeyError:
            self.update_r_minus_er()
            return self.dataset['r_minus_er']

    def get_r_minus_er_squared(self):
        try:
            return self.dataset['r_minus_er2']
        except KeyError:
            self.update_r_minus_er_squared()
            return self.dataset['r_minus_er2']

    def update_returns(self):
        '''
        Update the dict self.dataset to have returns in a new element
        Its header would be r_XXX_adjclose
        '''
        headers = list(self.dataset['raw'].columns)[
            1:]  # Ignore the date column

        for header in headers:
            r = [None]
            for i in range(len(self.dataset['raw'][header])):
                if i == 0:  # Ignore the date column
                    continue
                else:
                    r.append(self.dataset['raw'][header][i] /
                             self.dataset['raw'][header][i-1] - 1)
            try:
                self.dataset['returns'] = pd.concat([self.dataset['returns'], pd.DataFrame(
                    r, columns=[f"r_{str(header)}"])], axis=1)
            except KeyError:
                self.dataset['returns'] = pd.DataFrame(
                    r, columns=[f"r_{str(header)}"])

    def update_expectedreturns(self):
        '''
        Updates the summary dataframe to include the E(r) of the stock.
        That note that it's using the Mean Method
        ### MEAN METHOD ###
        '''
        try:
            returns = self.dataset['returns']  # returns is a dataframe
        except KeyError:
            print("Run the update_returns() method to obtain the returns first")
            exit()

        headers = list(returns.columns)
        expected_returns = []
        for header in headers:
            mean = returns[header].mean()
            expected_returns.append(mean)
        self.dataset['summary'].loc['mean_returns'] = expected_returns

    def update_r_minus_er(self):
        '''
        Update the dict self.dataset to have (r-E(r)) in a new element
        Its header would be r_minus_er_XXX
        '''
        headers = list(self.dataset['returns'].columns)
        for header in headers:
            r = []

            for i in self.dataset['returns'][header]:
                # print(f"out {header}")
                if pd.notna(i):
                    ticker = str(header).split('_')[1]
                    r.append(i - self.dataset['summary']
                             [(ticker,)]['mean_returns'])
                else:
                    continue
            try:
                self.dataset['r_minus_er'] = pd.concat([self.dataset['r_minus_er'], pd.DataFrame(
                    r, columns=[f"r_minus_er_{str(header).split('_')[1]}"])], axis=1)
            except KeyError:
                self.dataset['r_minus_er'] = pd.DataFrame(
                    r, columns=[f"r_minus_er_{str(header).split('_')[1]}"])

    def update_r_minus_er_squared(self):
        '''
        Update the dict self.dataset to have (r-E(r))^2 in a new element
        Its header would be r_minus_er2_XXX
        '''
        headers = list(self.dataset['returns'].columns)
        for header in headers:
            r = []

            for i in self.dataset['returns'][header]:
                # print(f"out {header}")
                if pd.notna(i):
                    ticker = str(header).split('_')[1]
                    r.append((i - self.dataset['summary']
                             [(ticker,)]['mean_returns'])**2)
                else:
                    continue
            try:
                self.dataset['r_minus_er2'] = pd.concat([self.dataset['r_minus_er2'], pd.DataFrame(
                    r, columns=[f"r_minus_er2_{str(header).split('_')[1]}"])], axis=1)
            except KeyError:
                self.dataset['r_minus_er2'] = pd.DataFrame(
                    r, columns=[f"r_minus_er2_{str(header).split('_')[1]}"])

    def update_annual_returns(self):
        '''
        Updates the summary dataframe to include the Annual E(r) of the stock.
        That note that it's using the Compound Interest Method
        ### Compound Interest Method ###
        '''

        mean_returns = self.dataset['summary'].loc[['mean_returns']]

        headers = list(mean_returns.columns)
        annual_return = []
        for header in headers:
            annual_return.append(
                (1 + mean_returns[header]['mean_returns'])**250 - 1)

        self.dataset['summary'].loc['annual_returns'] = annual_return

    def update_standard_deviation(self):
        '''
        Updates the summary dataframe to include the standard deviation of the stock.
        Take note that Variance will also be updated here.
        '''
        headers = list(self.dataset['returns'].columns)
        standard_deviation = []
        variance = []
        for header in headers:
            standard_deviation.append(self.dataset['returns'][header].std())
            variance.append(
                (self.dataset['returns'][header].std())**2)

        self.dataset['summary'].loc['standard_deviation'] = standard_deviation
        self.dataset['summary'].loc['variance'] = variance

    def update_annual_std(self):
        '''
        Updates the summary dataframe to include the Annual std of the stock.
        That note that it's just multiplying by sqrt(250)
        ### Compound Interest Method ###
        '''
        headers = list(self.dataset['returns'].columns)
        annual_std = []
        for header in headers:
            annual_std.append(
                self.dataset['returns'][header].std()*math.sqrt(250))

        self.dataset['summary'].loc['annual_std'] = annual_std


if __name__ == '__main__':

    Sample1 = ReturnsAnalysis(
        excel_file=r"SAMPLE PATH FILE")

    # Commands to run for analysis
    Sample1.update_returns()  # Create the returns dataframe in the dataset
    # Updates/Create the summary dataframe -> Only creates the mean row
    Sample1.update_expectedreturns()
    Sample1.update_r_minus_er()  # Create the (r-E(r)) dataframe in the dataset
    # Create the (r-E(r))^2 dataframe in the dataset
    Sample1.update_r_minus_er_squared()

    # Using Compound interest, calculates the annual returns from the mean_returns
    Sample1.update_annual_returns()

    # Using Sample populace (1/n-1) to calculate the standard deviation of the stock
    Sample1.update_standard_deviation()

    # Calculate the annual std by multiple std by sqrt(250)
    Sample1.update_annual_std()

    # print(Sample1.get_rawdataset())
    # print(Sample1.get_returnsdataset())
    print(Sample1.get_summarydataset())
    # print(Sample1.get_r_minus_er())
    # print(Sample1.get_r_minus_er_squared())

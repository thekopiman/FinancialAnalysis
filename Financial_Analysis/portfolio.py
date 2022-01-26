from ast import Return
from shutil import SameFileError
from yahoo_fin.stock_info import get_data
import pandas as pd
import numpy as np
from datetime import datetime
import os
import math

from modules import StockAnalysis, CrossReferencing
from analysis import ReturnsAnalysis


class Portfolio(CrossReferencing):
    def __init__(self, ticker, start_date=None, end_date=None):
        super().__init__(ticker, start_date, end_date)

        self.database = ReturnsAnalysis(dataset=self.merged_df)

        #### Commands to run for analysis ####

        self.database.update_returns()  # Create the returns dataframe in the dataset
        # Updates/Create the summary dataframe -> Only creates the mean row
        self.database.update_expectedreturns()
        self.database.update_r_minus_er()  # Create the (r-E(r)) dataframe in the dataset
        # Create the (r-E(r))^2 dataframe in the dataset
        self.database.update_r_minus_er_squared()

        # Using Compound interest, calculates the annual returns from the mean_returns
        self.database.update_annual_returns()

        # Using Sample populace (1/n-1) to calculate the standard deviation of the stock
        self.database.update_standard_deviation()

        # Calculate the annual std by multiple std by sqrt(250)
        self.database.update_annual_std()


if __name__ == '__main__':
    portfolio1 = Portfolio(["^N225", "M44U.SI", "^STI", "AMZN"],
                           start_date="12/04/2012", end_date="12/04/2019")

    print(portfolio1.merged_df)
    print(portfolio1.database.get_summarydataset())

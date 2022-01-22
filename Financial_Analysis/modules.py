from yahoo_fin.stock_info import get_data
import pandas as pd
import numpy as np
from datetime import datetime
import os
import itertools


class StockAnalysis():
    def __init__(self, ticker, start_date=None, end_date=None, index_as_date=False, interval="1d"):
        '''
        ticker = Stock ticker name
        start_date = in mm/dd/yyyy
        end_date = in mm/dd/yyyy
        index_as_date = Bool
        interval = Interval must be "1d", "1wk", "1mo", or "1m" for daily, weekly, monthly, or minute data. Intraday minute data is limited to 7 days.
        '''
        self.stock = get_data(ticker, start_date, end_date,
                              index_as_date, interval)
        # print(self.stock)
        self.stock = self.stock[self.stock['close'].notna()]
        self.stock_ticker = ticker

    def get_stock_data(self):
        return self.stock

    def filter_stock_data(self, filter):
        '''
        Filter needs to be in a list (multiple) or a string (singular)
        Headers include: date, open, high, low, close ,adjclose, volume, ticker
        '''
        if type(filter) == str:
            filter = [filter]
        return self.stock.filter(items=filter)

    def get_dates(self, datatype="set", date_layout='%Y-%m-%d'):
        '''
        datatype: set, dataframe, list
        date_layout: Configure %Y-%m-%d %H:%M:%S as much as you want

        Recommand using set for for intersections

        returns a set/dataframe/list of the dates
        '''
        if datatype == "dataframe":
            return self.filter_stock_data("date")
        elif datatype == "list":
            return [datetime.utcfromtimestamp(int(unix[0])/1000000000).strftime(date_layout) for unix in self.filter_stock_data("date").filter(items=["date"]).values.tolist()]
        elif datatype == "set":
            return set([datetime.utcfromtimestamp(int(unix[0])/1000000000).strftime(date_layout) for unix in self.filter_stock_data("date").filter(items=["date"]).values.tolist()])

    def get_returns(self, dataframe=None):
        if dataframe == None:
            dataframe = self.stock

        # Not completed Refer to jupyter-notebook for reference

    def filter_common_dates(self, common_dates, update=False) -> pd.DataFrame:
        '''
        Returns the Dataframe with the dates mentioned
        '''
        new_df = self.stock[self.stock.date.isin(common_dates)]

        if update == True:
            self.stock = new_df

        return new_df


class CrossReferencing:
    def __init__(self, tickers, start_date, end_date) -> None:
        '''
        ticker = Stock ticker name (Put the tinkers in a list eg. ["amzn","googl","^GSPC"])
        start_date = in mm/dd/yyyy
        end_date = in mm/dd/yyyy
        Setting index_as_date=False, interval="1d" as default. Unable to change.
        '''
        self.all_df = {}
        for ticker in tickers:
            self.all_df[ticker] = StockAnalysis(ticker, start_date=start_date,
                                                end_date=end_date, index_as_date=False, interval="1d")

        # print(self.all_df)
        self.common_dates = self.dates_intersect(
            [df.get_dates(datatype="set") for df in self.all_df.values()])

        self.merged_df = self.merge_data(self.all_df, self.common_dates)

    @classmethod
    def dates_intersect(self, list_of_dates) -> set:
        '''
        list_of_dates: a list of sets of dates eg. [{'2009-12-08', '2009-12-04', '2009-12-07', '2009-12-09'}, {'2009-12-04', '2009-12-09', '2009-12-08', '2009-12-07'}]

        Returns a set of dates that these dates are common.
        '''

        return sorted(set.intersection(*list_of_dates))

    @classmethod
    def merge_data(self, data, common_dates, filter_to_adjclose=True) -> pd.DataFrame:
        '''
        data: Needs to be a dict with the key (ticker) and value (dataframe)
        common_dates: set/list/tuple of dates
        filter_to_adjclose: Bool -> Filter each dataframe to its adjclose value only.

        Merge the Dataframes according to their common dates.
        Take note that the return Dataframes will have their headers edited to their corresponding column name based on its ticker. Eg ("amzn_adjclose", "googl_adjclose")

        Return Dataframe
        '''
        # print(data)
        # print(len(common_dates))
        for df_name in data:
            df = data[df_name].filter_common_dates(common_dates, update=True)
            # print(df.count())

            # df.to_excel(f"{os.getcwd()}\{df_name}.xlsx",
            #             index=False, header=True)
            if filter_to_adjclose:
                df = df.filter(items=["adjclose"])
            for header in list(df.columns):
                # print(f"{df_name}_{header}")
                df.rename(columns={header: str(
                    f"{df_name}_{header}")}, inplace=True)
            data[df_name] = df  # Update the dataframe into the data
        # print(pd.DataFrame(common_dates))
        # for x in data.values():
        #     print(x.shape)

        return self.merging_error_solver(common_dates, data.values())

    @classmethod
    def merging_error_solver(self, common_dates, dataframes):
        '''
        For some reason, for a certain combination of stocks, merging is not always successful.
        '''

        # Basic Concat Function
        final_df = pd.concat([pd.DataFrame(common_dates, columns=[
                             "date"])] + [x for x in dataframes], axis=1)

        if final_df.shape[0] == list(dataframes)[0].shape[0]:
            return final_df
        else:
            # Convert DataFrames into Numpy Arrays First
            print("Dataframe to Array conversion has occured")
            headers = [list(x.columns)[0] for x in dataframes]

            arrays = np.concatenate([dataframe.to_numpy()
                                    for dataframe in dataframes], axis=1)
            # print(arrays)
            return pd.concat([pd.DataFrame(common_dates, columns=[
                             "date"]), pd.DataFrame(arrays, columns=headers)], axis=1)


if __name__ == '__main__':
    portfolio = CrossReferencing(
        ["^N225", "M44U.SI", "^STI", "AMZN"], start_date="12/04/2012", end_date="12/04/2019")

    print(portfolio.merged_df.shape)
    # print(portfolio.merged_df)
    # print(os.getcwd())
    portfolio.merged_df.to_excel(
        f"{os.getcwd()}\Everything.xlsx", index=False, header=True)

    print("End")

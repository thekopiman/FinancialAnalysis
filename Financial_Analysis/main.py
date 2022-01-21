from yahoo_fin.stock_info import get_data
import pandas as pd
import numpy as np
from datetime import datetime
from modules import StockAnalysis


def main():
    amazon_daily = StockAnalysis("amzn", start_date="12/04/2009",
                                 end_date="12/10/2009", index_as_date=False, interval="1d")

    print(amazon_daily.get_dates(datatype="set"))


if __name__ == '__main__':
    main()

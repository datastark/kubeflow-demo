import numpy as np
import pandas as pd
from elasticsearch import exceptions as expf
from elasticsearch import Elasticsearch

def load_data(tickers, es_address, year_cutoff=2010):
  """Load stock market data (close values for each day) for given tickers.
  Args:
    tickers (list): list of tickers
  Returns:
    pandas.dataframe: dataframe with close values of tickers
  """
  query = {
    "query": {
        "range" : {
            "Date" : {
                "gte": year_cutoff,
            }
        }
    }
}
  # get the data
  es = Elasticsearch( [es_address], port=9200 )
  res_source = {}
  for ticker in tickers:
    res_source[ticker] = [hit["_source"] 
                          for hit in es.search(index=ticker, 
                                               body=query, 
                                               size=2000, 
                                               _source=["Date", "Close"]
                                               )['hits']['hits']] 
  results = {}
  for ticker in tickers:
    results[ticker] = pd.DataFrame(res_source[ticker]).set_index('Date')

  # sort and fill blanks
  closing_data = pd.DataFrame()
  for ticker in tickers:
    closing_data['{}_close'.format(ticker)] = results[ticker]['Close']
    closing_data['{}_close'.format(ticker)] = pd.to_numeric(closing_data['{}_close'.format(ticker)],errors='coerce')
  closing_data.sort_index(inplace=True)
  closing_data.index = pd.to_datetime(closing_data.index, format='%Y-%m-%d', 
                                        errors='coerce')                                        
  closing_data = closing_data.fillna(method='ffill')

  return closing_data

def preprocess_data(closing_data):
  """Preprocesses data into time series.
  Args:
    closing_data (pandas.dataframe):  dataframe with close values of tickers
  Returns:
    pandas.dataframe: dataframe with time series
  """
  # transform into log return
  log_return_data = pd.DataFrame()
  tickers = [column_header.split("_")[0] for column_header in closing_data.columns.values]
  for ticker in tickers:
    log_return_data['{}_log_return'.format(ticker)] = np.log(
        closing_data['{}_close'.format(ticker)] /
        closing_data['{}_close'.format(ticker)].shift())

  log_return_data['snp_log_return_positive'] = 0
  log_return_data.ix[log_return_data['snp_log_return'] >= 0, 'snp_log_return_positive'] = 1
  log_return_data['snp_log_return_negative'] = 0
  log_return_data.ix[log_return_data['snp_log_return'] < 0, 'snp_log_return_negative'] = 1

  # create dataframe
  training_test_data = pd.DataFrame(
      columns=[
          'snp_log_return_positive', 'snp_log_return_negative',
          'snp_log_return_1', 'snp_log_return_2', 'snp_log_return_3',
          'nyse_log_return_1', 'nyse_log_return_2', 'nyse_log_return_3',
          'djia_log_return_1', 'djia_log_return_2', 'djia_log_return_3',
          'nikkei_log_return_0', 'nikkei_log_return_1', 'nikkei_log_return_2',
          'hangseng_log_return_0', 'hangseng_log_return_1', 'hangseng_log_return_2',
          'ftse_log_return_0', 'ftse_log_return_1', 'ftse_log_return_2',
          'dax_log_return_0', 'dax_log_return_1', 'dax_log_return_2',
          'aord_log_return_0', 'aord_log_return_1', 'aord_log_return_2'])

  # fill dataframe with time series
  for i in range(7, len(log_return_data)):
    training_test_data = training_test_data.append(
      {'snp_log_return_positive': log_return_data['snp_log_return_positive'].ix[i],
       'snp_log_return_negative': log_return_data['snp_log_return_negative'].ix[i],
       'snp_log_return_1': log_return_data['snp_log_return'].ix[i - 1],
       'snp_log_return_2': log_return_data['snp_log_return'].ix[i - 2],
       'snp_log_return_3': log_return_data['snp_log_return'].ix[i - 3],
       'nyse_log_return_1': log_return_data['nyse_log_return'].ix[i - 1],
       'nyse_log_return_2': log_return_data['nyse_log_return'].ix[i - 2],
       'nyse_log_return_3': log_return_data['nyse_log_return'].ix[i - 3],
       'djia_log_return_1': log_return_data['djia_log_return'].ix[i - 1],
       'djia_log_return_2': log_return_data['djia_log_return'].ix[i - 2],
       'djia_log_return_3': log_return_data['djia_log_return'].ix[i - 3],
       'nikkei_log_return_0': log_return_data['nikkei_log_return'].ix[i],
       'nikkei_log_return_1': log_return_data['nikkei_log_return'].ix[i - 1],
       'nikkei_log_return_2': log_return_data['nikkei_log_return'].ix[i - 2],
       'hangseng_log_return_0': log_return_data['hangseng_log_return'].ix[i],
       'hangseng_log_return_1': log_return_data['hangseng_log_return'].ix[i - 1],
       'hangseng_log_return_2': log_return_data['hangseng_log_return'].ix[i - 2],
       'ftse_log_return_0': log_return_data['ftse_log_return'].ix[i],
       'ftse_log_return_1': log_return_data['ftse_log_return'].ix[i - 1],
       'ftse_log_return_2': log_return_data['ftse_log_return'].ix[i - 2],
       'dax_log_return_0': log_return_data['dax_log_return'].ix[i],
       'dax_log_return_1': log_return_data['dax_log_return'].ix[i - 1],
       'dax_log_return_2': log_return_data['dax_log_return'].ix[i - 2],
       'aord_log_return_0': log_return_data['aord_log_return'].ix[i],
       'aord_log_return_1': log_return_data['aord_log_return'].ix[i - 1],
       'aord_log_return_2': log_return_data['aord_log_return'].ix[i - 2]},
      ignore_index=True)

  return training_test_data

import os
import pandas as pd


def get_output_directory():
    return '{0:s}/Data/Realmly'.format(os.environ['HOME'])


def get_value_by_key(df,key=None, key_col=None, val_col=None):
    """
    find value by key
    :param df: pandas.DataFrame
    :param key: the key to be searched
    :param key_col: [optional] default 0, string or integer, by location or by name
    :param val_col: [optional] default 0, they location of the value
    :return: the cell value to the right of the key
    """
    if key is None:
        return None
    if not( isinstance(df, pd.DataFrame)):
        raise TypeError('Wrong Type: DataFrame expected')

    if key_col is None:
        key_col_index = 0
    else:
        if isinstance(key_col,int):
            key_col_index = key_col
        else:
            key_col_index = df.columns.get_loc(key_col)

    if val_col is None:
        val_col_index = key_col_index + 1
    else:
        if isinstance(val_col,int):
            val_col_index = val_col
        else:
            val_col_index = df.columns.get_loc(val_col)

    s = df.iloc[:,key_col_index]
    row_index = s[s==key].index.tolist()
    if row_index is not None:
        return df.iloc[row_index,val_col_index].values
    else:
        return None


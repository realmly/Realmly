# -*- coding: utf-8 -*-
"""
financial projection/calculations:
    mortgage 
    loan calcluations


"""

import numpy as np
import numbers
import pandas as pd
import sys
import os
import Realmly.util.utilities as util


def amortize(loan_amount,rate, number_of_payments = 360, payment_per_year=12, prepayment=None,begin_or_end='end'):
    '''
    amortize(loan_amount, rate, number_of_payments = 360, payment_per_year=12, prepayment=[], begin_or_end = 'end')
    
    loan_amount: dollar amount of the loan balance at on
    rate       : annual interest rates in decimal
    number_of_payments: default 360, for monthly 30 year
    payment_per_year : 12, rate compounding periods per year
    prepaymen  : empty, even or arbitrary 
    begin_or_end:default "end", payment in arrears    
    
    '''
    
    if number_of_payments <= 0:
        raise Exception('Number of Payments should be a positive number')
    if rate < 0:
        raise Exception('Interest rate should be a positive number')

#   interest rate per payment period
    rate_per_period = rate / payment_per_year
    
#    pre-payments
    if prepayment is None or not(prepayment):
        additional_payments = np.zeros(number_of_payments)
    elif type(prepayment) is not np.ndarray:
        additional_payments = np.ones((number_of_payments,1))*prepayment
    else:
        additional_payments = np.copy(prepayment)
        
    if len(additional_payments) != number_of_payments:
        if len( additional_payments) == 0 :
            additional_payments = np.zeros(number_of_payments)
        elif len(additional_payments) == 1:
            additional_payments = np.ones(number_of_payments) * additional_payments
        else:
            raise Exception( 'Prepayment vector shorter than number of payments')
    additional_payments = additional_payments.round(2)
            
#   fixed rate mortgage payment per perriod
    payment = round(-np.pmt(rate_per_period, number_of_payments, loan_amount, 0, begin_or_end),2)

#   build amortization table    
    balance = np.ones(2)*round(loan_amount, 2)
    balances = np.zeros((number_of_payments,2))
    interests = np.zeros((number_of_payments,2))
    principal_payments = np.zeros((number_of_payments,2))
    total_payments = np.zeros((number_of_payments,2))

    prepaying = sum( abs( additional_payments)) > 0
    
# iterate through payment periods    
    for i in range(number_of_payments):
        interests[i,0] = round( balance[0] * rate_per_period, 2)
        interests[i,1] = round( balance[1] * rate_per_period, 2)
        principal_payments[i,0] = min( balance[0], payment - interests[i,0])
        principal_payments[i,1] = min( balance[1], payment - interests[i,1]+additional_payments[i])
        balance[0] -= principal_payments[i,0]
        balance[1] -= principal_payments[i,1]
        balances[i,0] = balance[0]
        balances[i,1]=balance[1]
        total_payments[i,0]=interests[i,0]+principal_payments[i,0]
        total_payments[i,1]=interests[i,1]+principal_payments[i,1]
        
    if prepaying:
        print( "Prepayments reduced pay periods from %d to %d" %(number_of_payments,np.count_nonzero(total_payments[:,1])))
        print( "Total interests payment changed from %.0f to %.0f"%(sum(interests[:,0]),sum(interests[:,1])))
    else:    
        total_payments = total_payments[:,0]
        interests = interests[:,0]
        principal_payments = principal_payments[:,0]
        balances = balances[:,0]
            

    return total_payments, interests, principal_payments, balances

    
# financial projection for real estate investments
# predicated

def investment_projection( years, purchase, loan, income, operation, sale, tax, info=None, print_flag=False, output_location=None):
    if years is None or not (isinstance( years, numbers.Number)) or years <= 0:
        years = 5
        print( "Invalid number of years of projection ", years, " years assumed")
    
    is_columns = [
                  'Net Incomes',
                  'Net Operating Incomes',
                  'Total Revenues',
                  'Rents', 'Other Incomes',
                  'Maintenance', 'Utilities',
                  'Turnover Costs',
                  'Realm Fees',
                  'Property Management Fees',
                  'Property Taxes', 'Other taxes',
                  'Insurances',
                  'Interests',
                  'Principal Repayments',
                  'Debt Service',
                  'Depreciations',
                  'Utilities',
                  'Operating Expenses',
                  'Other Expenses',
                  'Total Expenses'
                  ]
    bs_columns = [ 'Total Assets', 'Equity', 'Total Debt',
                  'Cumulative Depreciations', 'Tax Basis' ]
                  
    cf_columns = [ 'Cash Flow From Operation', 'Cash Flow From Financing',
                  'Cash Flow From Investing', 'Net Cash Flows',
                  'Capital Expeditures' ]
                  
    ratio_columns = [ 'Capitalization Rates', 'Return On Investments',
                     'Cash On Cash Returns', 'Gross Rent Multiplier',
                     'Loan To Value Ratios', 'Leverage',
                     'Debt Coverage Ratios', 'Operating Ratios',
                     'Total Expense Ratios'
                      ]
                     
    is_projection = pd.DataFrame( np.zeros((years+1,len(is_columns))), columns = is_columns)
    bs_projection = pd.DataFrame( np.zeros((years+1,len(bs_columns))), columns = bs_columns)
    cf_projection = pd.DataFrame( np.zeros((years+1,len(cf_columns))), columns = cf_columns)
    ratios        = pd.DataFrame( np.zeros((years+1,len(ratio_columns))), columns = ratio_columns)
    
    ratios.index.name = 'Year'
    cf_projection.index.name = 'Year'
    is_projection.index.name = 'Year'
    bs_projection.index.name = 'Year'

    
    initial_equity = purchase['price']+purchase['buying costs']-loan['loan']    
    initial_loan   = loan['loan']
    interest_rate  = loan['rate']
    
    # get loan amortization schedules
    amortizing_years = loan['amortization period']
    payments_per_year = loan['payments per year']
    number_of_payments = amortizing_years * payments_per_year
    mortgage_payments,interest_expenses,principal_payments,loan_balances = amortize(initial_loan,interest_rate,number_of_payments,payments_per_year)
    annual_loan_payments = mortgage_payments.reshape((amortizing_years,payments_per_year))
    annual_loan_payments = np.round(np.sum(annual_loan_payments,1),0)
    annual_interest_expenses = interest_expenses.reshape((amortizing_years,payments_per_year))
    annual_interest_expenses = np.round(np.sum(annual_interest_expenses,1),0)
    annual_principal_payments = principal_payments.reshape((amortizing_years,payments_per_year))
    annual_principal_payments = np.round(np.sum(annual_principal_payments,1),0)
    annual_loan_balances = loan_balances.reshape((amortizing_years,payments_per_year))
    annual_loan_balances = np.round(annual_loan_balances[:,-1],0)

    bs_projection['Total Debt'][0]=initial_loan
    bs_projection['Total Debt'][1:]=annual_loan_balances[:years]
    is_projection['Interests'][0]=0
    is_projection['Interests'][1:]=annual_interest_expenses[:years]
    is_projection['Principal Repayments'][0]=0
    is_projection['Principal Repayments'][1:]=annual_principal_payments[:years]
    is_projection['Debt Service'][1:] = annual_loan_payments[:years]
    cf_projection['Cash Flow From Financing'][1:]+=annual_principal_payments[:years]
    
    # get income projection
    rent_inflation = income['rent inflation']
    rent_per_period = income['rent']
    rent_per_year = rent_per_period * income['payments per year']
    rent_per_year = rent_per_year * (1-income['vacancy'])
    annual_rents = np.round( rent_per_year * np.exp(np.array(range(years))*np.log(1+rent_inflation)))
    is_projection['Rents'][1:]=annual_rents
    is_projection['Total Revenues']=is_projection['Rents']+is_projection['Other Incomes']

    # get utility projection
    util_inflation = income['Utility Inflation']
    utility = income['Utilities']
    annual_utilities = utility * np.round( np.exp(np.array(range(years))*np.log(1+util_inflation)))
    is_projection['Utilities'][1:]=annual_utilities

    # asset price
    asset_values = np.round( purchase['price']*np.exp((np.array(range(years+1)))*np.log(sale['appreciation']+1)), 0)
    
    bs_projection['Total Assets']=asset_values.round(0)
    bs_projection['Total Assets'][0] += purchase['buying costs']
    bs_projection['Equity'] = bs_projection['Total Assets'] - bs_projection['Total Debt']
    # operating cost
    annual_property_management_fees = operation['property management fee'] * annual_rents
    annual_realm_fees = operation['realm fee']*annual_rents
    annual_turnover_costs = operation['tenant turnover cost']*np.ones(years)
    annual_insurance_costs = operation['insurance']*asset_values[0]*(np.exp(np.arange(years)*np.log(1+operation['insurance inflation'])))
    annual_maintenance_costs = asset_values[0]*operation['maintenance']*np.exp(np.arange(years)*np.log(1+operation['maintenance inflation']))
    annual_operating_costs = annual_property_management_fees + annual_turnover_costs + annual_insurance_costs + annual_utilities
    annual_operating_costs += annual_maintenance_costs    
    
    is_projection['Insurances'][1:]= np.round(annual_insurance_costs, 0)
    is_projection['Maintenance'][1:]=annual_maintenance_costs.round(0)
    is_projection['Turnover Costs'][1:]=annual_turnover_costs.round(0)
    is_projection['Property Management Fees'][1:]=annual_property_management_fees.round(0)
    is_projection['Realm Fees'][1:]=annual_realm_fees.round(0)
    is_projection['Operating Expenses']=is_projection['Insurances']+is_projection['Maintenance']+\
        is_projection['Realm Fees'] + is_projection['Property Management Fees']+\
        is_projection['Turnover Costs']

    # taxes
    annual_property_taxes = tax['property tax']*(np.exp(np.array(range(years))*np.log(1+tax['property tax inflation'])))
    is_projection['Property Taxes'][1:]= np.round( annual_property_taxes, 0)    
    
    # operating income
    annual_operating_incomes = annual_rents - annual_operating_costs - annual_property_taxes - annual_utilities
    is_projection['Net Operating Incomes']=is_projection['Total Revenues']-is_projection['Operating Expenses']-is_projection['Property Taxes'] -is_projection['Utilities']
    
    # total costs
    annual_total_expenses  = annual_operating_costs + annual_property_taxes + annual_interest_expenses[:years]
    is_projection['Total Expenses'][1:] = np.round( annual_total_expenses,0)
    
    #depreciation charge and tax basis
    annual_depreciations = np.round((purchase['price']-tax['land value'])/27.5*np.ones(years), 0)
    cumulative_depreciations = np.cumsum( annual_depreciations)
    tax_basis = np.ones(years)*purchase['price']-cumulative_depreciations
    
    bs_projection['Cumulative Depreciations'][0]=0
    bs_projection['Cumulative Depreciations'][1:]=cumulative_depreciations.round(0)
    bs_projection['Tax Basis'][0]=bs_projection['Total Assets'][0]
    bs_projection['Tax Basis'][1:]=tax_basis.round(0)
    is_projection['Depreciations'][1:]=annual_depreciations
    
    #net income
    annual_net_incomes = annual_operating_incomes - annual_interest_expenses[:years] - annual_depreciations
    taxes = annual_net_incomes * tax['income tax']
    is_projection['Net Incomes']=is_projection['Net Operating Incomes']-is_projection['Interests']-is_projection['Depreciations']
    
    #cash flow
    annual_before_tax_cash_flows = np.round( annual_operating_incomes - annual_loan_payments[:years], 2)
    annual_after_tax_cash_flows = np.round( annual_operating_incomes - annual_loan_payments[:years] - taxes, 2)
    
    cf_projection['Cash Flow From Financing']=-is_projection['Debt Service']
    cf_projection['Cash Flow From Operation']= is_projection['Net Operating Incomes']
    cf_projection['Net Cash Flows'][1:]=np.round( annual_operating_incomes - annual_loan_payments[:years], 2)
    
    # net sale
    net_sales = asset_values[-1]*(1-sale['broker commissions'])

    disposal = {}    
    disposal.update({'Gross Sales': asset_values[-1]})
    disposal.update({'Sales Comissions': round( asset_values[-1]*sale['broker commissions'],0)})
    disposal.update({'Net Sales Before Tax': net_sales.round(0) })
    disposal.update({'Tax Basis': tax_basis[-1].round(0)})

    #taxes related to sales
    pnl = net_sales - tax_basis[-1]    
    if pnl > 0:
        long_term_gain = round( max( 0, net_sales - bs_projection['Total Assets'][0]),0)
        depreciation_recapture = round( min( pnl, cumulative_depreciations[-1]),0)
        short_term_gain = 0
    else: 
        depreciation_recapture = 0
        long_term_gain = 0
        short_term_gain = pnl

    long_term_gain_tax = round(long_term_gain * tax[ 'capital gain tax' ],0)
    short_term_gain_tax = round(short_term_gain * tax[ 'income tax' ],0)
    recapture_tax = round( depreciation_recapture * tax[ 'depreciation recapture tax' ],0)
    tax_upon_sales = round( recapture_tax + long_term_gain_tax + short_term_gain_tax,0)

    disposal.update({'Capital Gain': round(pnl,0)})
    disposal.update({'Long Term Gain': long_term_gain })
    disposal.update({'Long Term Gain Tax': long_term_gain_tax })
    disposal.update({'Short Term Gain': short_term_gain })
    disposal.update({'Short Term Gain Tax': short_term_gain_tax})
    disposal.update({'Depreciation Recapture': depreciation_recapture})
    disposal.update({'Depreciation Recapture Tax': recapture_tax })
    disposal.update({'Total Taxes':tax_upon_sales})
    disposal.update({'Net Sales After Tax': round( net_sales - tax_upon_sales)})
    disposal.update({'Total Gain Before Tax': round(is_projection['Net Incomes'].sum() + pnl)})
    disposal.update({'Total Gain After Tax': round( is_projection['Net Incomes'].sum()-taxes.sum()+pnl-tax_upon_sales)})
    disposal.update({'Total Return Before Tax': round( disposal['Total Gain Before Tax']/bs_projection['Equity'][0], 3)})
    disposal.update({'Total Return After Tax': round( disposal['Total Gain After Tax']/bs_projection['Equity'][0],3)})
    disposal.update({'Number Of Years': years })
    disposal.update({'Capital Gain Tax Rate': tax['capital gain tax']})
    disposal.update({'Income Tax Rate': tax['income tax']})
    disposal.update({'Depreciation Recapture Tax Rate': tax['depreciation recapture tax']})
    
    #IRR - internal rate of returns: after tax
    ivec = np.zeros( years + 1)
    ivec[0] = -initial_equity
    ivec[1:] = annual_after_tax_cash_flows
    ivec[-1] += net_sales - annual_loan_balances[years-1] - tax_upon_sales    
    irr = round(np.irr(ivec),3)
    disposal.update({'IRR After Tax': irr})
    
    #IRR - internal rate of returns: before tax
    itvec = np.zeros( years + 1)
    itvec[0] = -initial_equity
    itvec[1:] = annual_before_tax_cash_flows
    itvec[-1] += net_sales - annual_loan_balances[years-1]    
    irr_pre_tax = round(np.irr(itvec),3)
    disposal.update({'IRR Before Tax': irr_pre_tax })

    is_projection['Total Revenues']=is_projection['Rents']+is_projection['Other Incomes']
    
    # return metrics
    ratios['Capitalization Rates']=is_projection['Net Operating Incomes']/bs_projection['Total Assets'].shift(1)
    ratios['Debt Coverage Ratios']=is_projection['Net Operating Incomes']/is_projection['Debt Service']
    ratios['Loan To Value Ratios']=bs_projection['Total Debt']/bs_projection['Total Assets']
    ratios['Operating Ratios']=is_projection['Operating Expenses']/is_projection['Total Revenues']
    ratios['Total Expense Ratios']=is_projection['Total Expenses']/is_projection['Total Revenues']
    #ratios['Return On Investments']= is_projection['Net Incomes']/bs_projection['Equity']
    roi = (is_projection['Net Incomes']+bs_projection['Equity'])/bs_projection['Equity'].shift(1) - 1
    ratios['Return On Investments'] = roi
    ratios['Leverage'] = bs_projection['Total Assets']/bs_projection['Equity']
    ratios['Gross Rent Multiplier']=np.round(bs_projection['Total Assets']/is_projection['Rents'],1)
    ratios['Gross Rent Multiplier'][0] = 0
    ratios['Cash On Cash Returns']=cf_projection['Net Cash Flows']/(bs_projection['Equity'][0])
    
    s = { 'bs': bs_projection,
         'is': is_projection,
         'ratios': ratios,
         'disposal':disposal,
         'cf': cf_projection,
         'info': info,
         'annual loan': annual_loan_payments,
         'annual interests': annual_interest_expenses,
         'annual principal payments': annual_principal_payments }
    
    if print_flag:
        output_projection( s, output_location)
    return s


def output_projection(result, output_location=None):
    if not output_location or output_location is None:
        output_location = util.get_output_directory()
    output_location = output_location.strip()
    info = result['info']
    bs = result['bs']
    cf = result['cf']
    inc = result['is']
    disp = result['disposal']
    ratios = result['ratios']
    scenario = result['scenario']
    investor = result['investor']

    scenario_name = scenario['Scenario Name']

    cstr = "_"
    estr = " "
    address = str(info['Street Number'])+estr+info['Street Prefix']+estr+\
              info['Street Name']+estr+info['Street Suffix']+estr+\
              info['City']+estr+info['State']

    address_str = address.replace(estr, cstr)
    sc_str = scenario_name.replace(estr,cstr)

    file = os.path.join(output_location, 'PROJECTION_{0:s}_{1:s}.xlsx'.format(address_str, sc_str))
    try:
        writer = pd.ExcelWriter( file)
        book = writer.book
    
        # formats
        bold = book.add_format({'bold': True})
        bold_red = book.add_format({'bold': True, 'font_color': 'red'})
        bold_blue = book.add_format({'bold': True, 'font_color': 'blue'})
        dollar = book.add_format({'num_format': '$#,##0'})
        float1 = book.add_format({'num_format': '#.0'})
        percent0 = book.add_format({'num_format': '0%'})
        percent1 = book.add_format({'num_format': '0.0%'})

        # scenario page
        sheet = book.add_worksheet("Assumptions")
        row = 0
        col = 0
        sheet.set_column('A:A', 30)
        sheet.set_column('B:B', 20)
        sheet.set_column('C:C', 20)
        # scenario: header
        sheet.write(row, col, 'Senario', bold)
        sheet.write(row, col + 1, scenario['Scenario Name'])
        row += 2

        # scenario: acquisition
        sheet.write(row, col, 'Acquisition', bold_red)
        row += 1
        sheet.write(row, col, 'Purchase Price', bold)
        sheet.write(row, col+1, scenario['Purchase Price'], dollar)
        row += 1
        sheet.write(row, col, 'Purchase Costs', bold)
        sheet.write(row, col + 1, scenario['Purchase Costs'], dollar)
        row += 2

        # scenario: disposal
        sheet.write(row, col, 'Disposal', bold_red)
        row += 1
        sheet.write(row, col, 'Years', bold)
        sheet.write(row, col + 1, scenario['Years'])
        row += 1
        sheet.write(row, col, 'Price Appreciation', bold)
        sheet.write(row, col + 1, scenario['Price Appreciation'], percent1)
        row += 1
        sheet.write(row, col, 'Selling Price (Gross)', bold)
        sheet.write(row, col + 1, disp['Gross Sales'], dollar)
        row += 1
        sheet.write(row, col, 'Selling Commissions', bold)
        sheet.write(row, col + 1, scenario['Selling Commissions'], percent1)
        sheet.write(row, col + 2, disp['Gross Sales'] * scenario['Selling Commissions'], dollar)
        row += 1
        sheet.write(row, col, 'Other Selling Costs', bold)
        sheet.write(row, col + 1, scenario['Other Selling Costs'], dollar)
        row += 2

        # scenario: financing
        sheet.write(row, col, 'Financing', bold_red)
        row += 1
        sheet.write(row, col, 'Loan Rate', bold)
        sheet.write(row, col + 1, scenario['Rate'], percent1)
        row += 1
        sheet.write(row, col, 'Loan to Purchase', bold)
        sheet.write(row, col + 1, scenario['Loan'], percent0)
        sheet.write(row, col + 2, scenario['Purchase Price'] * scenario['Loan'], dollar)
        row += 1
        sheet.write(row, col, 'Amortization Period (Years)', bold)
        sheet.write(row, col + 1, scenario['Amortization Period'])
        row += 1
        sheet.write(row, col, 'Payments Per Year', bold)
        sheet.write(row, col + 1, scenario['Payments Per Year'])
        row += 2

        # scenario: investor assumption
        sheet.write(row, col, 'Investor', bold_red)
        row += 1
        sheet.write(row, col, 'Income Tax Rate', bold)
        sheet.write(row, col + 1, scenario['Income Tax'], percent1)
        row += 1
        sheet.write(row, col, 'Long Term Gain Tax', bold)
        sheet.write(row, col + 1, scenario['Capital Gain Tax'], percent1)
        row += 1
        sheet.write(row, col, 'Depreciation Recapture', bold)
        sheet.write(row, col + 1, scenario['Depreciation Recapture Tax'], percent1)
        row += 2

        # scenario: management
        sheet.write(row, col, 'Property Management', bold_blue)
        row += 1
        sheet.write(row, col, 'Rent', bold)
        sheet.write(row, col + 1, scenario['Rent'], dollar)
        row += 1
        sheet.write(row, col, 'Rent Per Year', bold)
        sheet.write(row, col + 1, scenario['Rent Payments Per Year'])
        row += 1
        sheet.write(row, col, 'Rent Increase', bold)
        sheet.write(row, col + 1, scenario['Rent Inflation'], percent1)
        row += 1
        sheet.write(row, col, 'Other Income', bold)
        sheet.write(row, col + 1, scenario['Other Income'], dollar)
        row += 1
        sheet.write(row, col, 'Vacancy', bold)
        sheet.write(row, col + 1, scenario['Vacancy'], percent0)
        row += 1
        sheet.write(row, col, 'Property Tax', bold)
        sheet.write(row, col + 1, scenario['Property Tax'], dollar)
        row += 1
        sheet.write(row, col, 'Property Tax Increase', bold)
        sheet.write(row, col + 1, scenario['Property Tax Inflation'], percent1)
        row += 1
        sheet.write(row, col, 'Insurance', bold)
        sheet.write(row, col + 1, scenario['Insurance'], dollar)
        row += 1
        sheet.write(row, col, 'Insurance Increase', bold)
        sheet.write(row, col + 1, scenario['Insurance Inflation'], percent1)
        row += 1
        sheet.write(row, col, 'Realms Fee', bold)
        sheet.write(row, col + 1, scenario['Realmly Fee'], percent1)
        sheet.write(row, col + 2, (1 - scenario['Vacancy']) * scenario['Rent' ]
                    * scenario['Rent Payments Per Year'] * scenario['Realmly Fee'], dollar)
        row += 1
        sheet.write(row, col, 'Tenant Turnover Costs', bold)
        sheet.write(row, col + 1, scenario['Tenant Turnover Costs'], dollar)
        row += 1
        sheet.write(row, col, 'Utilities', bold)
        sheet.write(row, col + 1, scenario['Utilities'], dollar)
        row += 1
        sheet.write(row, col, 'Utilities Increase (per year, %)', bold)
        sheet.write(row, col + 1, scenario['Utility Inflation'], percent1)
        row += 1
        sheet.write(row, col, 'Maintenance', bold)
        sheet.write(row, col + 1, scenario['Maintenance'], dollar)
        row += 1
        sheet.write(row, col, 'Maintenance Increase', bold)
        sheet.write(row, col + 1, scenario['Maintenance Inflation'], percent1)
        row += 1
        sheet.write(row, col, 'Other Management Fees', bold)
        sheet.write(row, col + 1, scenario['Property Management Fee'], percent1)


        # summary page
        sheet = book.add_worksheet('Summary')
        row = 0
        col = 0
        sheet.write(row, col, 'Name', bold)
        sheet.write(row, col+1, scenario_name)
        row += 1
        sheet.write(row, col, 'Address', bold)
        sheet.write(row, col+1,address)
        row += 1
        sheet.write(row, col+2, 'Taxes')
        row += 1
        sheet.write(row, col, 'Number of Years', bold)
        sheet.write(row, col+1, disp['Number Of Years'])
        row += 1
        sheet.write(row, col, 'List Price', bold)
        sheet.write(row, col+1, info['List Price'], dollar)
        row += 1
        sheet.write(row, col, 'Purchase Price', bold)
        sheet.write(row, col+1, bs['Total Assets'][0], dollar)
                
        row += 1
        sheet.write(row, col, 'Gross Selling Price', bold)
        sheet.write(row, col+1, disp['Gross Sales'], dollar)
        row += 1
        sheet.write(row, col, '  Selling Fees', bold)
        sheet.write(row, col+1, -disp['Sales Comissions'], dollar)
        row += 1
        sheet.write(row, col, 'Net Proceeds', bold)
        sheet.write(row, col+1, disp['Net Sales Before Tax'], dollar)
        row += 1
        sheet.write(row, col, 'Total Gain', bold)
        sheet.write(row, col+1, disp['Total Gain Before Tax'], dollar)
        row += 1
        sheet.write(row, col, '  Distribution', bold)
        sheet.write(row, col+1, disp['Total Gain Before Tax']-disp['Capital Gain'], dollar)
        row += 1
        sheet.write(row, col, '  Capital Gain', bold)
        sheet.write(row, col+1, disp['Capital Gain'], dollar)
        sheet.write(row, col+2, -disp['Total Taxes'], dollar)
        row += 1
        sheet.write(row, col, '    Long Term Gain', bold)
        sheet.write(row, col+1, disp['Long Term Gain'], dollar)
        sheet.write(row, col+2, -disp['Long Term Gain Tax'], dollar)
        row += 1
        sheet.write(row, col, '    Short Term Gain', bold)
        sheet.write(row, col+1, disp['Short Term Gain'], dollar)
        sheet.write(row, col+2, -disp['Short Term Gain Tax'], dollar)
        row += 1
        sheet.write(row, col, '    Depreciation Recapture', bold)
        sheet.write(row, col+1, disp['Depreciation Recapture'], dollar)
        sheet.write(row, col+2, -disp['Depreciation Recapture Tax'], dollar)

        row += 2
        sheet.write(row, col, 'P & L', bold)
        sheet.write(row, col+1, 'Pre Tax', bold)
        sheet.write(row, col+2, 'After Tax', bold)
        sheet.write(row, col+4, 'Income Tax Rate')
        sheet.write(row, col+5, 'Capital Gain Tax Rate')
        sheet.write(row, col+6, 'Depreciation Recapture Tax Rate')
        
        row += 1
        sheet.write(row, col, 'Annual Return', bold_blue)
        sheet.write(row, col+1, disp['IRR Before Tax'], percent1)
        sheet.write(row, col+2, disp['IRR After Tax' ], percent1)
        sheet.write(row, col+4, disp['Income Tax Rate'], percent0)
        sheet.write(row, col+5, disp['Capital Gain Tax Rate'],percent0)
        sheet.write(row, col+6, disp['Depreciation Recapture Tax Rate'], percent0)
        row += 1
        sheet.write(row, col, 'Income', bold_blue)
        sheet.write(row, col + 1, disp['Income Before Tax'], percent1)
        sheet.write(row, col + 2, disp['Income After Tax'], percent1)
        row += 1
        sheet.write(row, col, 'Appreciation', bold_blue)
        sheet.write(row, col + 1, disp['Capital Appreciation Before Tax'], percent1)
        sheet.write(row, col + 2, disp['Capital Appreciation After Tax'], percent1)
        row += 1
        sheet.write(row, col, 'Period Total Return', bold)
        sheet.write(row, col+1, disp['Total Return Before Tax'], percent1)
        sheet.write(row, col+2, disp['Total Return After Tax' ], percent1)
        sheet.set_column('A:A',30)

        # growth of $10,000
        investor.to_excel(writer, sheet_name = 'Growth of $10,000')
        sheet = writer.sheets['Growth of $10,000']
        sheet.set_column('B:ZZ', 20, dollar)

        # income
        inc.to_excel(writer, sheet_name = 'Income')
        sheet = writer.sheets['Income']
        sheet.set_column('B:ZZ', 20, dollar)
        # cash flow
        cf.to_excel(writer, sheet_name = 'Cash Flow')
        sheet = writer.sheets['Cash Flow']
        sheet.set_column('B:ZZ', 20, dollar)
        # balance sheet
        bs.to_excel(writer, sheet_name = 'Balance Sheet')
        sheet = writer.sheets['Balance Sheet']
        sheet.set_column('B:ZZ', 20, dollar)
        
        # balance sheet
        ratios.to_excel(writer, sheet_name = 'Financial Ratios')
        sheet = writer.sheets['Financial Ratios']
        sheet.set_column('B:D', 20, percent1)
        sheet.set_column('E:E', 20, float1)
        sheet.set_column('F:K', 20, percent0)
        
        writer.save()
        writer.close()
        print( 'Successfully output projection to ', file)
    except Exception as err:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print('Error: ', type( err), err)
        print(exc_type, fname, exc_tb.tb_lineno)
        writer.close()
    else:
        writer.close()


def investment_scenario(deal, scenario, print_flag=False,
                        output_location=None):
    if deal is None:
        raise Exception('No deal info')
    if scenario is None:
        raise Exception('No scenario info')
    years = int(scenario['Years'])
    print("{0:d} years projection".format(years))

    if years is None or not (isinstance(years, numbers.Number)) or years <= 0:
        years = 5
        print("Invalid number of years of projection ", years, " years assumed")

    is_columns = [
        'Net Incomes',
        'Net Operating Incomes',
        'Total Revenues',
        'Rents', 'Other Incomes',
        'Maintenance', 'Utilities',
        'Turnover Costs',
        'Advertising',
        'Administrative',
        'Realm Fees',
        'Property Management Fees',
        'Property Taxes', 'Other taxes',
        'Insurances',
        'Interests',
        'Principal Repayments',
        'Debt Service',
        'Depreciations',
        'Operating Expenses',
        'Other Expenses',
        'Total Expenses',
        'Income Before Depreciation'
    ]
    bs_columns = ['Total Assets', 'Equity', 'Total Debt',
                  'Cumulative Depreciations', 'Tax Basis']

    cf_columns = ['Cash Flow From Operation', 'Cash Flow From Financing',
                  'Cash Flow From Investing', 'Net Cash Flows',
                  'Capital Expeditures']

    ratio_columns = ['Capitalization Rates', 'Return On Investments',
                     'Cash On Cash Returns', 'Gross Rent Multiplier',
                     'Loan To Value Ratios', 'Leverage',
                     'Debt Coverage Ratios', 'Operating Ratios',
                     'Total Expense Ratios'
                     ]

    is_projection = pd.DataFrame(np.zeros((years + 1, len(is_columns))), columns=is_columns)
    bs_projection = pd.DataFrame(np.zeros((years + 1, len(bs_columns))), columns=bs_columns)
    cf_projection = pd.DataFrame(np.zeros((years + 1, len(cf_columns))), columns=cf_columns)
    ratios = pd.DataFrame(np.zeros((years + 1, len(ratio_columns))), columns=ratio_columns)

    ratios.index.name = 'Year'
    cf_projection.index.name = 'Year'
    is_projection.index.name = 'Year'
    bs_projection.index.name = 'Year'

    initial_loan = scenario['Loan'] * scenario['Purchase Price']
    initial_equity = scenario['Purchase Price'] + scenario['Purchase Costs'] - initial_loan
    interest_rate = scenario['Rate']

    # get loan amortization schedules
    amortizing_years = int(scenario['Amortization Period'])
    payments_per_year = int(scenario['Payments Per Year'])
    number_of_payments = amortizing_years * payments_per_year
    mortgage_payments, interest_expenses, principal_payments, loan_balances = amortize(initial_loan, interest_rate,
                                                                                       number_of_payments,
                                                                                       payments_per_year)
    annual_loan_payments = mortgage_payments.reshape((amortizing_years, payments_per_year))
    annual_loan_payments = np.round(np.sum(annual_loan_payments, 1), 0)
    annual_interest_expenses = interest_expenses.reshape((amortizing_years, payments_per_year))
    annual_interest_expenses = np.round(np.sum(annual_interest_expenses, 1), 0)
    annual_principal_payments = principal_payments.reshape((amortizing_years, payments_per_year))
    annual_principal_payments = np.round(np.sum(annual_principal_payments, 1), 0)
    annual_loan_balances = loan_balances.reshape((amortizing_years, payments_per_year))
    annual_loan_balances = np.round(annual_loan_balances[:, -1], 0)

    bs_projection['Total Debt'][0] = initial_loan
    bs_projection['Total Debt'][1:] = annual_loan_balances[:years]
    is_projection['Interests'][0] = 0
    is_projection['Interests'][1:] = annual_interest_expenses[:years]
    is_projection['Principal Repayments'][0] = 0
    is_projection['Principal Repayments'][1:] = annual_principal_payments[:years]
    is_projection['Debt Service'][1:] = annual_loan_payments[:years]
    cf_projection['Cash Flow From Financing'][1:] += annual_principal_payments[:years]

    # get income projection
    rent_inflation = scenario['Rent Inflation']
    rent_per_period = scenario['Rent']
    rent_per_year = rent_per_period * scenario['Rent Payments Per Year']
    rent_per_year = rent_per_year * (1 - scenario['Vacancy'])
    annual_rents = np.round(rent_per_year * np.exp(np.array(range(years)) * np.log(1 + rent_inflation)))
    is_projection['Rents'][1:] = annual_rents
    is_projection['Total Revenues'] = is_projection['Rents'] + is_projection['Other Incomes']
    # asset price
    asset_values = np.round(scenario['Purchase Price'] * np.exp((np.array(range(years + 1))) * np.log(scenario['Price Appreciation'] + 1)), 0)

    bs_projection['Total Assets'] = asset_values.round(0)
    bs_projection['Total Assets'][0] += scenario['Purchase Costs']
    bs_projection['Equity'] = bs_projection['Total Assets'] - bs_projection['Total Debt']
    # operating cost
    annual_property_management_fees = scenario['Property Management Fee'] * annual_rents
    annual_realm_fees = scenario['Realmly Fee'] * annual_rents
    annual_turnover_costs = scenario['Tenant Turnover Costs'] * np.ones(years)
    annual_advertising = scenario['Advertising'] * np.ones(years)
    annual_administrative = scenario['Administrative'] * np.ones(years)
    annual_insurance_costs = scenario['Insurance']*(np.exp(np.arange(years) *
        np.log(1 + scenario['Insurance Inflation'])))
    annual_utility_costs = scenario['Utilities'] * (np.exp(np.arange(years) *
        np.log(1 + scenario['Utility Inflation'])))
    annual_maintenance_costs = scenario['Maintenance'] * np.exp(
        np.arange(years) * np.log(1 + scenario['Maintenance Inflation']))
    is_projection['Utilities'][1:] = annual_utility_costs
    annual_operating_costs = annual_property_management_fees + annual_turnover_costs + annual_insurance_costs
    annual_operating_costs += annual_maintenance_costs
    annual_operating_costs += annual_utility_costs

    is_projection['Insurances'][1:] = np.round(annual_insurance_costs, 0)
    is_projection['Maintenance'][1:] = annual_maintenance_costs.round(0)
    is_projection['Turnover Costs'][1:] = annual_turnover_costs.round(0)
    is_projection['Advertising'][1:] = annual_advertising.round(0)
    is_projection['Administrative'][1:] = annual_administrative.round(0)
    is_projection['Property Management Fees'][1:] = annual_property_management_fees.round(0)
    is_projection['Realm Fees'][1:] = annual_realm_fees.round(0)
    is_projection['Operating Expenses'] = is_projection['Insurances'] + is_projection['Maintenance'] + \
                                          is_projection['Realm Fees'] + is_projection['Property Management Fees'] + \
                                          is_projection['Turnover Costs'] + is_projection['Utilities'] + \
                                          is_projection['Advertising'] + is_projection['Administrative']

    # taxes
    annual_property_taxes = scenario['Property Tax'] * (
    np.exp(np.array(range(years)) * np.log(1 + scenario['Property Tax Inflation'])))
    is_projection['Property Taxes'][1:] = np.round(annual_property_taxes, 0)

    # operating income
    annual_operating_incomes = annual_rents - annual_operating_costs - annual_property_taxes
    is_projection['Net Operating Incomes'] = is_projection['Total Revenues'] - is_projection['Operating Expenses'] - \
                                             is_projection['Property Taxes']

    # total costs
    annual_total_expenses = annual_operating_costs + annual_property_taxes + annual_interest_expenses[:years]
    is_projection['Total Expenses'][1:] = np.round(annual_total_expenses, 0)

    # depreciation charge and tax basis
    dep_period = 27.5 if deal['Class'] == 'Residential' else 39
    annual_depreciations = np.round((scenario['Purchase Price'] + scenario['Purchase Costs']- deal['Land Value']) / dep_period * np.ones(years), 0)
    cumulative_depreciations = np.cumsum(annual_depreciations)
    tax_basis = np.ones(years) * scenario['Purchase Price'] + scenario['Purchase Costs']- cumulative_depreciations

    bs_projection['Cumulative Depreciations'][0] = 0
    bs_projection['Cumulative Depreciations'][1:] = cumulative_depreciations.round(0)
    bs_projection['Tax Basis'][0] = bs_projection['Total Assets'][0]
    bs_projection['Tax Basis'][1:] = tax_basis.round(0)
    is_projection['Depreciations'][1:] = annual_depreciations

    # net income
    annual_net_incomes = annual_operating_incomes - annual_interest_expenses[:years] - annual_depreciations
    taxes = annual_net_incomes * scenario['Income Tax']
    is_projection['Net Incomes'] = is_projection['Net Operating Incomes'] - is_projection['Interests'] - is_projection[
        'Depreciations']
    is_projection['Income Before Depreciation'] = is_projection['Net Incomes'] + is_projection['Depreciations']

    # cash flow
    annual_before_tax_cash_flows = np.round(annual_operating_incomes - annual_loan_payments[:years], 2)
    annual_after_tax_cash_flows = np.round(annual_operating_incomes - annual_loan_payments[:years] - taxes, 2)

    cf_projection['Cash Flow From Financing'] = -is_projection['Debt Service']
    cf_projection['Cash Flow From Operation'] = is_projection['Net Operating Incomes']
    cf_projection['Net Cash Flows'][1:] = np.round(annual_operating_incomes - annual_loan_payments[:years], 2)


    # net sale
    net_sales = asset_values[-1] * (1 - scenario['Selling Commissions'])

    disposal = {}
    disposal.update({'Gross Sales': asset_values[-1]})
    disposal.update({'Sales Comissions': round(asset_values[-1] * scenario['Selling Commissions'], 0)})
    disposal.update({'Net Sales Before Tax': net_sales.round(0)})
    disposal.update({'Tax Basis': tax_basis[-1].round(0)})

    # taxes related to sales
    pnl = net_sales - tax_basis[-1]
    if pnl > 0:
        long_term_gain = round(max(0, net_sales - bs_projection['Total Assets'][0]), 0)
        depreciation_recapture = round(min(pnl, cumulative_depreciations[-1]), 0)
        short_term_gain = 0
    else:
        depreciation_recapture = 0
        long_term_gain = 0
        short_term_gain = pnl

    long_term_gain_tax = round(long_term_gain * scenario['Capital Gain Tax'], 0)
    short_term_gain_tax = round(short_term_gain * scenario['Income Tax'], 0)
    recapture_tax = round(depreciation_recapture * scenario['Depreciation Recapture Tax'], 0)
    tax_upon_sales = round(recapture_tax + long_term_gain_tax + short_term_gain_tax, 0)

    disposal.update({'Capital Gain': round(pnl, 0)})
    disposal.update({'Long Term Gain': long_term_gain})
    disposal.update({'Long Term Gain Tax': long_term_gain_tax})
    disposal.update({'Short Term Gain': short_term_gain})
    disposal.update({'Short Term Gain Tax': short_term_gain_tax})
    disposal.update({'Depreciation Recapture': depreciation_recapture})
    disposal.update({'Depreciation Recapture Tax': recapture_tax})
    disposal.update({'Total Taxes': tax_upon_sales})
    disposal.update({'Net Sales After Tax': round(net_sales - tax_upon_sales)})
    disposal.update({'Total Gain Before Tax': round(is_projection['Net Incomes'].sum() + pnl)})
    disposal.update(
        {'Total Gain After Tax': round(is_projection['Net Incomes'].sum() - taxes.sum() + pnl - tax_upon_sales)})
    disposal.update(
        {'Total Return Before Tax': round(disposal['Total Gain Before Tax'] / bs_projection['Equity'][0], 3)})
    disposal.update({'Total Return After Tax': round(disposal['Total Gain After Tax'] / bs_projection['Equity'][0], 3)})
    disposal.update({'Number Of Years': years})
    disposal.update({'Capital Gain Tax Rate': scenario['Capital Gain Tax']})
    disposal.update({'Income Tax Rate': scenario['Income Tax']})
    disposal.update({'Depreciation Recapture Tax Rate': scenario['Depreciation Recapture Tax']})

    # IRR - internal rate of returns: after tax
    ivec = np.zeros(years + 1)
    ivec[0] = -initial_equity
    ivec[1:] = annual_after_tax_cash_flows
    ivec[-1] += net_sales - annual_loan_balances[years - 1] - tax_upon_sales
    irr_after_tax = round(np.irr(ivec), 3)
    disposal.update({'IRR After Tax': irr_after_tax})

    # IRR - internal rate of returns: before tax
    itvec = np.zeros(years + 1)
    itvec[0] = -initial_equity
    itvec[1:] = annual_before_tax_cash_flows
    itvec[-1] += net_sales - annual_loan_balances[years - 1]
    irr_pre_tax = round(np.irr(itvec), 3)
    disposal.update({'IRR Before Tax': irr_pre_tax})

    # dividend
    dvec = np.zeros(years + 1)
    dvec[0] = -initial_equity
    dvec[1:] = annual_before_tax_cash_flows + is_projection['Principal Repayments'][1:]
    dvec[-1] += initial_equity
    dirr = round( np.irr(dvec), 3)
    disposal.update({'Income Before Tax': dirr})
    #disposal.update({'Capital Appreciation Before Tax': irr_pre_tax - dirr})

    # cap gain before tax
    dvec = np.zeros(years + 1)
    dvec[0] = -initial_equity
    dvec[1:] = -is_projection['Principal Repayments'][1:]
    dvec[-1] += net_sales - annual_loan_balances[years - 1]
    dirr = round( np.irr(dvec), 3)
    disposal.update({'Capital Appreciation Before Tax': dirr})


    # dividend after tax
    dtvec = np.zeros(years + 1)
    dtvec[0] = -initial_equity
    dtvec[1:] = annual_after_tax_cash_flows + is_projection['Principal Repayments'][1:]
    dtvec[-1] += initial_equity
    dtirr = round(np.irr(dtvec), 3)
    disposal.update({'Income After Tax': dtirr})
    #disposal.update({'Capital Appreciation After Tax': irr_after_tax - dtirr})

    # cap gain after tax
    dvec = np.zeros(years + 1)
    dvec[0] = -initial_equity
    dvec[1:] = -is_projection['Principal Repayments'][1:]
    dvec[-1] += net_sales - annual_loan_balances[years - 1] - tax_upon_sales
    dirr = round(np.irr(dvec), 3)
    disposal.update({'Capital Appreciation After Tax': dirr})

    is_projection['Total Revenues'] = is_projection['Rents'] + is_projection['Other Incomes']

    # return metrics
    ratios['Capitalization Rates'] = is_projection['Net Operating Incomes'] / bs_projection['Total Assets'].shift(1)
    ratios['Debt Coverage Ratios'] = is_projection['Net Operating Incomes'] / is_projection['Debt Service']
    ratios['Loan To Value Ratios'] = bs_projection['Total Debt'] / bs_projection['Total Assets']
    ratios['Operating Ratios'] = is_projection['Operating Expenses'] / is_projection['Total Revenues']
    ratios['Total Expense Ratios'] = is_projection['Total Expenses'] / is_projection['Total Revenues']
    # ratios['Return On Investments']= is_projection['Net Incomes']/bs_projection['Equity']
    roi = (is_projection['Net Incomes'] + bs_projection['Equity']) / bs_projection['Equity'].shift(1) - 1
    ratios['Return On Investments'] = roi
    ratios['Leverage'] = bs_projection['Total Assets'] / bs_projection['Equity']
    ratios['Gross Rent Multiplier'] = np.round(bs_projection['Total Assets'] / is_projection['Rents'], 1)
    ratios['Gross Rent Multiplier'][0] = 0
    ratios['Cash On Cash Returns'] = cf_projection['Net Cash Flows'] / (bs_projection['Equity'][0])

    # growth of $10,000
    investor = pd.DataFrame(None, index=bs_projection.index, columns=['Principal', 'Income', 'Total'])
    investor.iloc[1:, 0] = 10000*bs_projection['Equity'][1:]/bs_projection['Equity'][0]
    investor.iloc[0, 0] = 10000
    investor.iloc[1:, 1] = 10000*cf_projection['Net Cash Flows']/bs_projection['Equity'][0]
    investor.iloc[0, 1] = 0
    investor.loc[:, 'Total'] = investor.loc[:, 'Principal'] + investor.loc[:, 'Income']

    s = {'bs': bs_projection,
         'is': is_projection,
         'ratios': ratios,
         'disposal': disposal,
         'cf': cf_projection,
         'info': deal,
         'scenario':scenario,
         'investor': investor,
         'annual loan': annual_loan_payments,
         'annual interests': annual_interest_expenses,
         'annual principal payments': annual_principal_payments,
         }

    if print_flag:
        output_projection(s, output_location)

    return s


def parse(file):
    """

    :param file:
    :return: deal, scenarios, dict objects
    """
    if not(os.path.exists(file)):
        alt_file = '{0:s}/Projects/{1:s}'.format(util.get_output_directory(),file)
        if not(os.path.exists(alt_file)):
            raise FileNotFoundError(file,alt_file)
    else:
        alt_file = file

    xls = pd.ExcelFile(alt_file)
    dsheet = xls.parse('Deal',header=0)
    dkeys = ('Unit','Street Number','Street Prefix','Street Suffix',
             'Street Name','City','State','Country','Zip Code',
             'Type','Number of Units','List Price','Property Tax',
             'Land Value','Class','Type') # deal keys
    skeys = ('Purchase Price', 'Purchase Costs',
             'Loan','Rate','Amortization Period','Payments Per Year',
             'Rent','Rent Inflation', 'Rent Payments Per Year', 'Vacancy','Other Income',
             'Property Tax', 'Property Tax Inflation',
             'Insurance', 'Insurance Inflation',
             'Utilities', 'Utility Inflation', 'Maintenance','Maintenance Inflation',
             'Tenant Turnover Costs','Advertising','Administrative',
             'Realmly Fee', 'Property Management Fee',
             'Years','Selling Commissions','Other Selling Costs',
             'Price Appreciation',
             'Capital Gain Tax','Income Tax','Depreciation Recapture Tax'
             ) # scenario keys
    int_keys = ('Number of Units','Years',
                'Rent Payment Per Year','Payments Per Year')
    deal = {}
    for key in dkeys:
        val = util.get_value_by_key(dsheet,key,'Key','Value')
        if isinstance(val, np.ndarray) and val.size == 1:
            val = val[0]
            if key in int_keys:
                val = int(val)
            if val is np.nan:
                val = ''
        deal.update({key:val})
    scenario_sheets = [s for s in xls.sheet_names if "SCENARIO" in s.upper()]
    scenarios = []
    for sheet_name in scenario_sheets:
        sheet = xls.parse(sheet_name,header=0)
        scenario = {}
        print("Sheet: {0:s}".format(sheet_name.title()))
        try:
            for key in skeys:
                val = util.get_value_by_key(sheet, key, 'Key', 'Value')
                if isinstance(val,np.ndarray) and val.size == 1:
                    val = val[0]
                    if key in int_keys:
                        val = int(val)
                scenario.update({key: val})
            if scenario:
                scenario.update({'Scenario Name': sheet_name.title()})
                scenarios.append(scenario)
        except Exception as e:
            print(e)
            raise e
    return deal, scenarios


def project(file, print_flag=False, output_location=None):
    """

    :param file:
    :param print_flag: default False
    :return:
    """

    if not os.path.exists(file):
        print("No file found {0:s}".format(file))
        raise FileNotFoundError

    if output_location is None:
        output_location = os.path.dirname(file)
        print(output_location)
    deal, scenarios = parse(file)
    projections = [None]*len(scenarios)
    for i, s in enumerate(scenarios):
        projections[i] = investment_scenario(deal, s, print_flag, output_location)
    print(output_location)
    return deal, scenarios, projections

    
        
        
    
    
    
    
    
    
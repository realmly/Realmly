# -*- coding: utf-8 -*-
"""
financial projection/calculations:
    mortgage 
    loan calcluations


"""

import numpy as np
import numbers
import pandas as pd

def amortize(loan_amount,rate, number_of_payments = 360, payment_per_year=12, prepayment=[],begin_or_end='end' ):
    '''
    amortize(loan_amount, rate, number_of_payments = 360, payment_per_year=12, prepayment=[], begin_or_end = 'end' )
    
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
        raise Exception('Interest rate should be a positive number' )

#   interest rate per payment period
    rate_per_period = rate / payment_per_year;
    
#    pre-payments
    if prepayment is None or not(prepayment):
        additional_payments = np.zeros(number_of_payments)
    elif type(prepayment) is not np.ndarray:
        additional_payments = np.ones((number_of_payments,1))*prepayment
    else:
        additional_payments = np.copy(prepayment)
        
    if len(additional_payments) != number_of_payments:
        if len( additional_payments ) == 0 :
            additional_payments = np.zeros(number_of_payments)
        elif len(additional_payments) == 1:
            additional_payments = np.ones(number_of_payments) * additional_payments
        else:
            raise Exception( 'Prepayment vector shorter than number of payments' )
    additional_payments = additional_payments.round(2)
            
#   fixed rate mortgage payment per perriod
    payment = round(-np.pmt(rate_per_period, number_of_payments, loan_amount, 0, begin_or_end ),2)

#   build amortization table    
    balance = np.ones(2)*round(loan_amount, 2)
    balances = np.zeros((number_of_payments,2))
    interests = np.zeros((number_of_payments,2))
    principal_payments = np.zeros((number_of_payments,2))
    total_payments = np.zeros((number_of_payments,2))

    prepaying = sum( abs( additional_payments ) ) > 0
    
# iterate through payment periods    
    for i in range(number_of_payments):
        interests[i,0] = round( balance[0] * rate_per_period, 2)
        interests[i,1] = round( balance[1] * rate_per_period, 2)
        principal_payments[i,0] = min( balance[0], payment - interests[i,0] )
        principal_payments[i,1] = min( balance[1], payment - interests[i,1]+additional_payments[i] )
        balance[0] -= principal_payments[i,0]
        balance[1] -= principal_payments[i,1]
        balances[i,0] = balance[0]
        balances[i,1]=balance[1]
        total_payments[i,0]=interests[i,0]+principal_payments[i,0]
        total_payments[i,1]=interests[i,1]+principal_payments[i,1]
        
    if prepaying:
        print( "Prepayments reduced pay periods from %d to %d" %(number_of_payments,np.count_nonzero(total_payments[:,1]) ) )
        print( "Total interests payment changed from %.0f to %.0f"%(sum(interests[:,0]),sum(interests[:,1])))
    else:    
        total_payments = total_payments[:,0];
        interests = interests[:,0];
        principal_payments = principal_payments[:,0];
        balances = balances[:,0];
            

    return total_payments, interests, principal_payments, balances

    
# financial projection for real estate investments

def investment_projection( years, purchase, loan, income, operation, sale, tax ):
    if years is None or not (isinstance( years, numbers.Number)) or years <= 0:
        years = 5
        print( "Invalid number of years of projection ", years, " years assumed" )
    
    is_columns = [ 'Rents', 'Other Incomes', \
               'Maintenance', 'Utilities', \
               'Property Taxes', 'Other taxes',\
               'Insurances',\
               'Interests', \
               'Depreciations',\
               'Realm Fees',\
               'Property Management Fees',\
               'Turnover Costs',\
               'Total Revenues',\
               'Operating Costs',\
               'Net Incomes',\
               'Operating Incomes',\
               'Other Costs',\
               'Total Expenses'\
               ];
    bs_columns = [ 'Total Assets', 'Equity', 'Total Debt',\
                  'Cumulative Depreciations', 'Tax Basis' ];
    cf_columns = [ 'Cash Flow From Operation', 'Cash Flow From Financing',\
                  'Cash Flow From Investing', 'Operating Cash Flows',\
                  'Capital Expediture' ];
    ratio_columns = [ 'Capitalization Rates', 'Leverage', 'Rent Multiples',\
                     'Return On Investments', 'Return On Equity' ];
    is_projection = pd.DataFrame( np.zeros((years+1,len(is_columns))), columns = is_columns );
    bs_projection = pd.DataFrame( np.zeros((years+1,len(bs_columns))), columns = bs_columns );
    cf_projection = pd.DataFrame( np.zeros((years+1,len(cf_columns))), columns = cf_columns );
    ratios        = pd.DataFrame( np.zeros((years+1,len(ratio_columns))), columns = ratio_columns );

    
    initial_equity = purchase['price']+purchase['buying costs']-loan['loan']    
    initial_loan   = loan['loan']
    interest_rate  = loan['rate']
    
    # get loan amortization schedules
    amortizing_years = loan['amortization period'];
    payments_per_year = loan['payments per year'];
    number_of_payments = amortizing_years * payments_per_year;
    mortgage_payments,interest_expenses,principal_payments,loan_balances = amortize(initial_loan,interest_rate,number_of_payments,payments_per_year)
    annual_loan_payments = mortgage_payments.reshape((amortizing_years,payments_per_year));
    annual_loan_payments = np.round(np.sum(annual_loan_payments,1));
    annual_interest_expenses = interest_expenses.reshape((amortizing_years,payments_per_year));
    annual_interest_expenses = np.round(np.sum(annual_interest_expenses,1),2);
    annual_principal_payments = principal_payments.reshape((amortizing_years,payments_per_year));
    annual_principal_payments = np.round(np.sum(annual_principal_payments,1),2);
    annual_loan_balances = loan_balances.reshape((amortizing_years,payments_per_year));
    annual_loan_balances = np.round(annual_loan_balances[:,-1],2);

    bs_projection['Total Debt'][0]=initial_loan;
    bs_projection['Total Debt'][1:]=annual_loan_balances[:years];
    is_projection['Interests'][0]=0;
    is_projection['Interests'][1:]=annual_interest_expenses[:years];
    cf_projection['Cash Flow From Financing'][1:]+=annual_principal_payments[:years];
    
    # get income projection
    rent_inflation = income['rent inflation'];
    rent_per_period = income['rent'];
    rent_per_year = rent_per_period * income['payments per year'];
    rent_per_year = rent_per_year * (1-income['vacancy']);
    annual_rents = np.round( rent_per_year * np.exp(np.array(range(years))*np.log(1+rent_inflation)) );
    is_projection['Rents'][1:]=annual_rents;
    is_projection['Total Revenues']=is_projection['Rents']+is_projection['Other Incomes'];    
    # asset price
    asset_values = purchase['price']*np.exp((np.array(range(years+1)))*np.log(sale['appreciation']+1));
    
    bs_projection['Total Assets']=asset_values.round(0);
    bs_projection['Equity'] = bs_projection['Total Assets'] - bs_projection['Total Debt'];
    # operating cost
    annual_property_management_fees = operation['property management fee'] * annual_rents;
    annual_realm_fees = operation['realm fee']*annual_rents;
    annual_turnover_costs = operation['tenant turnover cost']*np.ones(years);
    annual_insurance_costs = operation['insurance']*asset_values[:-1];
    annual_maintenance_costs = asset_values[0]*operation['maintenance']*np.exp(np.arange(years)*np.log(1+operation['maintenance inflation']));
    annual_operating_costs = annual_property_management_fees + annual_turnover_costs + annual_insurance_costs;
    annual_operating_costs += annual_maintenance_costs;    
    
    is_projection['Insurances'][1:]=annual_insurance_costs.round(0);
    is_projection['Maintenance'][1:]=annual_maintenance_costs.round(0);
    is_projection['Turnover Costs'][1:]=annual_turnover_costs.round(0);
    is_projection['Property Management Fees'][1:]=annual_property_management_fees.round(0);
    is_projection['Realm Fees'][1:]=annual_realm_fees.round(0);
    is_projection['Operating Costs']=is_projection['Insurances']+is_projection['Maintenance']+\
        is_projection['Realm Fees'] + is_projection['Property Management Fees']+\
        is_projection['Turnover Costs']

    # taxes
    annual_property_taxes = tax['property tax']*(np.exp(np.array(range(years))*np.log(1+tax['property tax inflation'])) );
    is_projection['Property Taxes'][1:]=annual_property_taxes.round(0);    
    
    # operating income
    annual_operating_incomes = annual_rents - annual_operating_costs - annual_property_taxes;
    is_projection['Operating Incomes']=is_projection['Total Revenues']-is_projection['Operating Costs']-is_projection['Property Taxes'];
    
    # total costs
    annual_total_expenses  = annual_operating_costs + annual_property_taxes + annual_interest_expenses[:years];
    is_projection['Total Expenses'][1:] = annual_total_expenses;
    
    #depreciation charge and tax basis
    annual_depreciations = (purchase['price']-tax['land value'])/27.5*np.ones(years);
    cumulative_depreciations = np.cumsum( annual_depreciations );
    tax_basis = np.ones(years)*purchase['price']-cumulative_depreciations
    
    bs_projection['Cumulative Depreciations'][0]=0;
    bs_projection['Cumulative Depreciations'][1:]=cumulative_depreciations.round(0);
    bs_projection['Tax Basis'][0]=bs_projection['Total Assets'][0];
    bs_projection['Tax Basis'][1:]=tax_basis.round(0);
    is_projection['Depreciations'][1:]=annual_depreciations;
    
    #net income
    annual_net_incomes = annual_operating_incomes - annual_interest_expenses[:years] - annual_depreciations;
    taxes = annual_net_incomes * tax['income tax'];
    is_projection['Net Incomes']=is_projection['Operating Incomes']-is_projection['Interests']-is_projection['Depreciations'];
    
    #cash flow
    annual_cash_flows = np.round( annual_operating_incomes - annual_loan_payments[:years] - taxes, 2 );
    
    # net sale
    net_sales = asset_values[-1]*(1-sale['broker commissions']);

    disposal = {};    
    disposal.update({'Gross Sales': asset_values[-1]});
    disposal.update({'Sales Comissions': asset_values[-1]*sale['broker commissions']});
    disposal.update({'Net Sales Before Tax': net_sales.round(0) });
    disposal.update({'Tax Basis': tax_basis[-1].round(0)});

    #taxes related to sales
    pnl = net_sales - tax_basis[-1];    
    if pnl > 0:
        long_term_gain = round( max( 0, net_sales - asset_values[0] ),0 );
        depreciation_recapture = round( min( pnl, cumulative_depreciations[-1]),0);
        short_term_gain = 0;
    else: 
        depreciation_recapture = 0;
        long_term_gain = 0;
        short_term_gain = pnl;

    long_term_gain_tax = round(long_term_gain * tax[ 'capital gain tax' ],0);
    short_term_gain_tax = round(short_term_gain * tax[ 'income tax' ],0);
    recapture_tax = round( depreciation_recapture * tax[ 'depreciation recapture tax' ],0);
    tax_upon_sales = round( recapture_tax + long_term_gain_tax + short_term_gain_tax,0);

    disposal.update({'Capital Gain': round(pnl,0)});
    disposal.update({'Long Term Gain': long_term_gain });
    disposal.update({'Long Term Gain Tax': long_term_gain_tax });
    disposal.update({'Short Term Gain': short_term_gain });
    disposal.update({'Short Term Gain Tax': short_term_gain_tax});
    disposal.update({'Depreciation Recapture': depreciation_recapture});
    disposal.update({'Depreciation Recapture Tax': recapture_tax } );
    disposal.update( {'Total Taxes':tax_upon_sales});
    disposal.update( {'Net Sales After Tax': round( net_sales - tax_upon_sales )});
    disposal.update({'Total Gain Before Tax': round(is_projection['Net Incomes'].sum() + pnl )})
    disposal.update({'Total Gain After Tax': round( is_projection['Net Incomes'].sum()-taxes.sum()+pnl-tax_upon_sales)})
    
    #IRR - internal rate of returns: after tax
    ivec = np.zeros( years + 1 );
    ivec[0] = -initial_equity;
    ivec[1:] = annual_cash_flows;
    ivec[-1] += net_sales - annual_loan_balances[years-1] - tax_upon_sales;    
    irr = np.irr(ivec);
    
    #IRR - internal rate of returns: before tax
    itvec = np.zeros( years + 1 );
    itvec[0] = -initial_equity;
    itvec[1:] = annual_cash_flows + taxes;
    itvec[-1] += net_sales - annual_loan_balances[years-1];    
    irr_pre_tax = np.irr(itvec);

    is_projection['Total Revenues']=is_projection['Rents']+is_projection['Other Incomes'];
    ratios['Capitalization Rates']=is_projection['Operating Incomes']/bs_projection['Total Assets'];
    ratios['Return On Equity'] = is_projection['Net Incomes']/bs_projection['Equity'];
    ratios['Leverage'] = bs_projection['Total Debt']/bs_projection['Equity'];
    is_projection['Rents'][0]=is_projection['Rents'][1];
    ratios['Rent Multiples']=bs_projection['Total Assets']/is_projection['Rents'];
    
    s = { 'cash flows': annual_cash_flows,\
         'cash vector': ivec,\
         'cash vector after tax': itvec,\
         'principal payments': annual_principal_payments, \
         'irr after tax': irr,\
         'irr before tax': irr_pre_tax,\
         'disposal': disposal,\
         'taxes': taxes, \
         'bs': bs_projection,\
         'is': is_projection,\
         'ratios': ratios,\
         'cf': cf_projection }
    
    return s
        
        
        
    
    
    
    
    
    
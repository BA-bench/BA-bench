INTRODUCTION
 
You work at a bank and have been asked to prepare a spreadsheet that can generate loan schedules for 
personal loans taken out by the bank’s customers. The loan details are as follows: 
    • The loan duration can be for any number of months up to 72 months.
    • Drawdowns occur as a single drawdown for the full balance at the beginning of the loan.
    • The drawdown can occur on any Business Day. A Business Day is defined as a weekday
    (Monday to Friday) that is not a Holiday. The list of Holidays has been provided to you.
    • The Actual Payment Date shall be based on the Regular Payment Date, but adjusted to be a
    Business Day as described below.
    • Loan payments are made monthly in arrears, on the Actual Payment Date each month, with the
    first payment one month after drawdown.
    • The Regular Payment Date each month will be the same DAY of the month as the loan drawdown
    (for example, if the drawdown was the 8th of October, then the Regular Payment Date will be the
    8th of each month).
    • The Actual Payment Date will equal the Regular Payment Date, subject to the following three
    conditions:
 
HINT: For Questions 1-4, you can ignore conditions 2 and 3, as they will not be relevant. 
 
Condition 1:  If the Regular Payment Date is not a Business Day, then the Actual Payment 
Date will be made on the first Business Day after the regular payment date, 
except where that Business Day would be in a new calendar month. 
 
HINT: For Questions 5-8, your model will need to also incorporate conditions 2 and 3. 
 
Condition 2: 
If Condition 1 results in a new calendar month, the Actual Payment Date shall be 
the last Business Day of the calendar month (which, by definition, will be before 
the Regular Payment Date) 
Condition 3: 
If the Regular Payment Date is the 29th, 30th or 31st of the month then, where a 
month has fewer days (e.g. February), the Actual Payment Date will be the last 
Business Day of the calendar month. 
 
• The Monthly Payment Amount shall be the same for each period, and include both an interest
portion and a principal portion. Therefore, the split between interest and principal will change from 
period to period. 
• Interest due shall be calculated on an Actual / 365 basis based on the number of days between
successive Actual Payment Dates. 
• Do not round any of your calculations.
 
Your manager has also given you the following advice for preparing your model: 
• It is expected you will need to use Excel’s Goal Seek tool or equivalent functionality in order to
find the Monthly Payment Amount.  Due to the interest periods having a different number of days 
from month to month, you will not be able to solve this problem with the PMT, PPMT or IPMT 
functions.

HOLIDAY SCHEDULE 
 
Your model should accommodate the following fixed schedule of holidays. 
 
A list of these Holidays is included in the provided workbook. 
 
3 April 2015 
6 April 2015 
25 October 2015 
25 March 2016 
28 March 2016 
24 October 2016 
14 April 2017 
17 April 2017 
30 October 2017 
30 March 2018 
2 April 2018 
19 October 2018 
19 April 2019 
22 April 2019 
14 October 2019 
10 April 2020 
13 April 2020 
19 October 2020 
 
HINT: It may be convenient to construct a static list next to the Holiday List, either through 
formulas or manual entry, of the Actual Payment Date that corresponds to each Holiday. 
 
Questions 1-4 relate to Loan 1 with the following terms: 
Loan amount: $250,000 
Loan duration: 72 months 
Drawdown date: 19 January 2015 
Interest Rate: 5.20% per annum 
 
Questions 5-8 relate to Loan 2 with the following terms: 
Loan amount: $100,000 
Loan duration: 48 months 
Drawdown date: 30 June 2015 
Interest Rate: 7.00% per annum
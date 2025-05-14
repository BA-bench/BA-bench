INTRODUCTION
You are an analyst helping your company prepare its purchase bid for the 30-year concession of a State-
owned infrastructure asset that has been put up for sale.  You have been provided the outline of a 
financing model which includes 10 scenarios of Inputs, and 10 scenarios of Operating Cash Flow taken 
from a colleague’s forecast operations model. 
For each of the Input scenarios, most assumption values have been provided, but one or two from each 
scenario will need to be solved for to find the optimal value, subject to the other values provided. 
The values that may need to be solved for are: 
• First Debt Repayment Date
• Sculpted DSCR
• Debt Drawdown amount
• Equity Investment amount
• Required Rate of Return (also known as the Equity IRR)
Your task will be to build the necessary additions to the model so that it can identify the Optimal missing 
values for the selected scenario. 
For the 1st and 2nd dot point items, Optimal values are defined as: 
i) If solving for First repayment date, the latest possible date; or
ii) If solving for the Sculpted DSCR, the largest possible DSCR
That still allows the debt to be repaid by the Latest allowed Debt Maturity Date, without the DSCR ever 
falling below the Sculpted DSCR value in any given quarter. 
 
For the 3rd, 4th and 5th dot point items, Optimal values are defined as: 
i) If not provided with the Required Rate of Return, the values that maximise the Equity IRR, which
will then become the Required Rate of Return 
ii) If provided with the Required Rate of Return, the values that maximise the Purchase Price whilst
ensuring that the Equity IRR is not less than the Required Rate of Return. 
Build your model adhering to the included Details, and then answer the Questions. 
Further conditions (“Requirements of a Solved Model”) are listed at the bottom of the Inputs worksheet. 
QUESTION SUMMARY 
Questions 1 to 20 are based on the provided input scenarios. 
Questions 21 to 23 may require you to change some of the existing user-variable input values from certain 
scenarios in order to answer. 
 
Precision of Answers: 
If submitting a dollar value, give your answer rounded to the nearest thousand dollar  
(i.e. 0 decimal places when working in units of [$’000] ). There is no need to write “k” or “,000” at the end. 
If submitting a DSCR value, give your answer to 3 decimal places 
If submitting a percentage rate, give your answer as a percentage to 3 decimal places (e.g. 11.543%) 
If submitting a date, give your answer rounded to the nearest day. (That’s a joke…) 

DETAILS 
1. Purchase Date Cash Flows 
On the Purchase Date, the debt facility is drawn with a single drawdown and a single equity 
investment is made (there are no other equity investments at any time).  The sum of these two 
amounts equals the Purchase Price which immediately goes to the State.  In other words, net cash 
flow for the Purchase Date is zero. 
2. Interest Calculations 
Interest is calculated on the last day of each quarter as  
(Opening Balance in Quarter) * (Rate % p.a.) * (Days in Qtr) / 365 
This applies to both the interest owed on the Debt, and the interest earned / (owed) on any positive / 
(negative) cash account balance. 
3. Refinancing Calculations 
The debt is refinanced at three points throughout the term.  The refinanced amount is the outstanding 
debt balance immediately after principal repayment on the refinancing date. A fee is charged on the 
refinanced amount, and this fee is capitalised into the debt balance.  For clarity, there is no fee 
payable on the fee itself.  The fee is only charged on the old balance that is being refinanced. 
4. Debt Interest Payments 
Interest owed is always paid in full at the end of each quarter for the entire life of the debt facility. 
5. Debt Principal Repayments 
Debt is repaid on the last day of each quarter, commencing on the First Debt Repayment Date, 
continuing every quarter until the facility is fully repaid.  All debt must be paid off on or before the 
Latest Allowed Debt Maturity Date.  The amount of each repayment must be sculpted so that the 
DSCR is constant for all quarters during the repayment term.  The only exception to this is the final 
repayment quarter, which can have a higher DSCR.  The repayment amount in any quarter cannot 
exceed the quarterly opening balance of the facility.  Redraws are not permitted. 
6. DSCR 
The DSCR is defined only for quarters where the principal repayment amount is not zero.  It is equal 
each quarter to the quarterly value of CFADS / (Net Interest Expense + Principal Repayments) 
7. CFADS 
CFADS (Cash Flow Available for Debt Service) is provided by the ‘Operations’ worksheet for each 
quarter.  For clarity, the definition of CFADS does not include any carryover opening balance. 
Hint:  Assumptions have been set so that CFADS will be relatively smooth and healthy, and will 
always be at least as large as Net Interest Expense * Sculpted DSCR 
8. Net Interest Expense 
Defined as: For each quarter, interest owed on Debt plus interest owed on cash account overdraft 
balance (if any) less interest earned on cash account positive balance (if any).  
9. Cash Flow Waterfall 
The Cash Flow Waterfall should include only the following items: 
(1) CFADS; (2) Interest Revenue/(Overdraft Expense) on Cash Balance; (3) Interest Expense 
on Debt; (4) Principal Repayments; (5) Equity Distributions 
All cashflows are assumed to occur on the final day of each quarter. 
10. Equity Distributions 
Distributions occur on the last day of each quarter every June during the Asset life, and at the Asset 
Expiration Date.  All available cash (including the carry over opening balance) is distributed each 
distribution date, so long as the cash balance is positive immediately prior to distributions. 
11. Equity IRR 
The Equity IRR should be calculated using the XIRR function, and consider the cashflows to/from 
equity between the Purchase Date and the Asset Expiration Date inclusive. 
 

# spencer
A Monzo API Expense Script

## What?
A simple script that downloads your Monzo Transactions between two set dates, downloads your receipts giving them sensible file names,
and creates one or more Excel sheets with a summary. The summary contains a description field that should give all the details you need,
so you can just copy that over and then from there fill in the rest of your expense form.

Note: the description is based on a very simple heuristic, so you should always check it.

## What you need to do
### Once
Get monzo. Use [my sign-up link](https://join.monzo.com/r/m8iilb2) if you'd like to give back (we both get £5).

### Day to day
* Snap a picture of your receipt in the Monzo app every time you pay for an expense. This will then get downloaded.
* Make sure that the transaction category is correct. Ideally, you reserve one category for your expenses (the Expenses category fits).
* Add tags if you wish to. The script will write a separate Excel file for each tag it finds. 

### When you do expenses
Log into [the Monzo API](https://developers.monzo.com/) and copy your details into the script variables. You'll need to update the access
key every time. Working on that. Also update the other variables to reflect your personal details (start date, end date, 
expense category, base path, ...)


## Getting started
You don't need much:
* Install Python
* Download this repo (download as zip, or git clone)
* Log into the Monzo API
* Edit the variables in the script (Notepad will do, but if you're planning on developing, I recommend Pycharm).
* Run it.
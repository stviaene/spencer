import requests
import datetime
import pandas as pd
import urllib
import os
import re

# Get these from the Monzo API login page
user_id = "user_xxxxxxxxxxxxxxxxxxxxx"
acc_id = "acc_xxxxxxxxxxxxxxxxxxxxx"
token = "xxxxxxxxxxxxxxxxxxxxxxxxx"

# Where you want the receipts to end up
base_folder = os.path.join(r"my_path")
# The format of the excel filename (only use the placeholders provided, or code to add others in)
excel_name_template = "{start}_{end}_summary{{tag}}.xlsx"
# Format of dates in filenames
date_format_file = '%Y%m%d'
# Which category do you reserve for expenses?
expense_category = "expenses"
# Set to False to not download all receipts (handy for debugging)
download_receipts = True

# The start date. Inclusive
start_date = datetime.date(year=2019, month=7, day=1)
# End date, inclusive.
end_date = datetime.date(year=2019, month=8, day=4)

# The excel filename gets formatted here.
excel_name = excel_name_template.format(start=start_date.strftime(date_format_file),
                                        end=end_date.strftime(date_format_file))


def guess_reason(row):
    """
    Guess what the transaction was for. Very much a heuristic.
    """
    if "air" in row.merchant.lower() or "aer" in row.merchant.lower():
        return "Flights"
    elif "hotel" in row.merchant.lower() and row.amount > 100:
        return "Hotel"
    elif "bus" in row.merchant.lower() and row.merchant_cat == "transport":
        if row.created.hour > 15 and row.local_currency == "GBP":
            return "Bus home"
        else:
            return "Bus"
    elif row.merchant_cat == "transport":
        if row.created.hour < 12 and row.local_currency == "GBP":
            return "Taxi to airport"
        elif row.created.hour < 12 and row.local_currency == "EUR":
            return "Taxi to work"
        elif row.created.hour > 15 and row.local_currency == "EUR":
            return "Taxi to DUB airport"
        elif row.created.hour > 15 and row.local_currency == "GBP":
            return "Taxi home"
        else:
            return "Taxi"
    elif 7 <= row.created.hour < 11:
        return "Breakfast"
    elif 11 <= row.created.hour < 15:
        return "Lunch"
    elif row.created.hour >= 15:
        return "Dinner"
    else:
        return ""


def get_full_desc(row):
    if pd.notnull(row.local_amt):
        return "{date} {purpose}, {merchant}, €{local_amt}, £{amt}, €1=£{rate:.4f}".format(
            date=row.created.date().strftime('%d/%m'),
            purpose=row.purpose,
            merchant=row.merchant,
            local_amt=row.local_amt,
            amt=row.amount,
            rate=row.rate
        )
    else:
        return "{date} {purpose}, {merchant}, £{amt}".format(
            date=row.created.date().strftime('%d/%m'),
            purpose=row.purpose,
            merchant=row.merchant,
            amt=row.amount
        )


def get_filename(row: pd.Series):
    """
    Get the file name as which the receipts will be saved. A index will be added if there's more than 1 receipt.
    """
    parts = []
    parts.append(row.created.strftime(date_format_file))
    parts.append(row.purpose)
    if pd.notnull(row.local_amt):
        parts.append('{:.2f}{}'.format(row.local_amt, row.local_currency))
    parts.append('{:.2f}{}'.format(row.amount, row.currency))
    return '_'.join(parts)


def dl_receipts(row: pd.Series):
    """
    Download the receipts.
    """
    row = row.copy()
    if 'attachments' in row.json:
        tots = len(row.json['attachments'])
        for i, receipt in enumerate(row.json['attachments']):
            if tots > 1:
                dest = os.path.join(base_folder, row.filename+'_{}'.format(i+1))
            else:
                dest = os.path.join(base_folder, row.filename)
            loc, resp = urllib.request.urlretrieve(receipt['file_url'], dest)
            newdest = dest + '.' + resp.get_content_subtype()
            os.rename(dest, newdest)
            row['receipt_{}'.format(i)] = newdest
    return row


if __name__ == "__main__":
    # Main method

    url = 'https://api.monzo.com/transactions'
    headers = {
        "Authorization": "Bearer {}".format(token)
    }
    data = {
        "account_id": acc_id,
        "expand[]": "merchant",
        "since": start_date.isoformat(),
        "before": (end_date + datetime.timedelta(days=1)).isoformat()
    }
    print('Fetching transactions')
    response = requests.get(url, data=data, headers=headers)
    print('Processing')
    trans = response.json()['transactions']
    expenses = [t for t in trans if t['category'] == expense_category]
    df = pd.DataFrame({'json': expenses})
    df = df.assign(
        created=pd.to_datetime(df.json.apply(lambda x: x['created'])),
        merchant=df.json.apply(lambda x: x['merchant']['name']),
        merchant_cat=df.json.apply(lambda x: x['merchant']['category']),
        amount=df.json.apply(lambda x: x['amount']).astype(float).abs()/100,
        currency=df.json.apply(lambda x: x['currency']),
        local_amt=df.json.apply(lambda x: x['local_amount'] if x['local_currency'] != 'GBP' else None)
                      .astype(float).abs()/100,
        local_currency=df.json.apply(lambda x: x['local_currency']),
        tag=df.json.apply(lambda x: x['notes']).str.strip().str.strip('#')
    ).assign(
        rate=lambda x: (x.amount/x.local_amt),
        purpose=lambda x: x.apply(guess_reason, axis=1),
        create_dt=lambda x: x.created.dt.date
    ).assign(
        full_description=lambda x: x.apply(get_full_desc, axis=1),
        filename=lambda x: x.apply(get_filename, axis=1)
    )
    print('Downloading receipts')
    if download_receipts:
        dldf = df.apply(dl_receipts, axis=1)
        receipt_cols = [c for c in dldf.columns if re.match('\Areceipt_\d+\Z', c)]
    else:
        dldf = df
        receipt_cols = []
    print('Writing to Excel')
    for tag in dldf.tag.unique():
        dldf.query('tag == @tag')\
            [['create_dt', 'full_description', 'local_amt', 'local_currency', 'amount', 'currency', 'rate'] +
                receipt_cols]\
            .assign(rate=lambda x: x.rate.round(4))\
            .to_excel(os.path.join(base_folder, excel_name.format(tag="_" + tag if tag else '')), index=False)
    print('Done.')
    print("Generated {} expenses, worth {}.".format(len(dldf), dldf.amount.sum()))


import pdfplumber
import pandas as pd
import requests
import os

def clean_mensaplan_df(weekplan_pdf_df, mensa_location):
    """function to clean the mensaplan dataframe 

    1. Cleans the columns and rows
    2. Adds a price column after each lane
    3. Repairs parse errors
    4. Returns the cleaned dataframe


    Args:
        weekplan_pdf_df (pandas.DataFrame): the dataframe extracted from the pdf
        mensa_location (str): the location of the mensa. (Choice between "hsg" and "fhs")

    Returns:
        pandas.DataFrame: the cleaned dataframe
    """

    # switch case if mensa hsg or fhs
    if mensa_location == "hsg":
        # drop first row
        weekplan_pdf_df = weekplan_pdf_df.drop(0)

        

        # join columns 6 and 7 to one column and drop the original columns
        weekplan_pdf_df[6] = weekplan_pdf_df[6] + " " + weekplan_pdf_df[7]

        # drop columns 
        columns_to_drop = [1,3,5,7,8]
        weekplan_pdf_df = weekplan_pdf_df.drop(columns_to_drop, axis=1)

        # drop tagessuppe column
        weekplan_pdf_df = weekplan_pdf_df.drop(0, axis=1)
    elif mensa_location == "fhs":
        # drop column 1,2,4,5,7 
        columns_to_drop = [1,2,4,5,7]
        weekplan_pdf_df = weekplan_pdf_df.drop(columns_to_drop, axis=1)
    else:
        print("Mensa location not found")
        return None
    
    # cleanup and rename columns and rows
    weekplan_pdf_df.columns = ["Fast Lane", "Daily Favourites", "Lifestyle"]
    weekplan_pdf_df = weekplan_pdf_df.reset_index(drop=True)


    # add price column after each lane
    weekplan_pdf_df.insert(1, "Fast Lane Price", "")
    weekplan_pdf_df.insert(3, "Daily Favourites Price", "")
    weekplan_pdf_df.insert(5, "Lifestyle Price", "")

    # split at CHF and move CHF and rest to price column
    weekplan_pdf_df["Fast Lane Price"] = weekplan_pdf_df["Fast Lane"].str.extract(r'(CHF.*)')
    weekplan_pdf_df["Daily Favourites Price"] = weekplan_pdf_df["Daily Favourites"].str.extract(r'(CHF.*)')
    weekplan_pdf_df["Lifestyle Price"] = weekplan_pdf_df["Lifestyle"].str.extract(r'(CHF.*)')

    # remove price from each lane
    weekplan_pdf_df["Fast Lane"] = weekplan_pdf_df["Fast Lane"].str.replace(r'(CHF.*)', '', regex=True)
    weekplan_pdf_df["Daily Favourites"] = weekplan_pdf_df["Daily Favourites"].str.replace(r'(CHF.*)', '', regex=True)
    weekplan_pdf_df["Lifestyle"] = weekplan_pdf_df["Lifestyle"].str.replace(r'(CHF.*)', '', regex=True)

    # if \n is at the end, delete it, otherwise replace it with a space
    weekplan_pdf_df["Fast Lane"] = weekplan_pdf_df["Fast Lane"].str.replace(r'\n$', '', regex=True)
    weekplan_pdf_df["Daily Favourites"] = weekplan_pdf_df["Daily Favourites"].str.replace(r'\n$', '', regex=True)
    weekplan_pdf_df["Lifestyle"] = weekplan_pdf_df["Lifestyle"].str.replace(r'\n$', '', regex=True)

    weekplan_pdf_df["Fast Lane"] = weekplan_pdf_df["Fast Lane"].str.replace(r'\n', ' ', regex=True)
    weekplan_pdf_df["Daily Favourites"] = weekplan_pdf_df["Daily Favourites"].str.replace(r'\n', ' ', regex=True)
    weekplan_pdf_df["Lifestyle"] = weekplan_pdf_df["Lifestyle"].str.replace(r'\n', ' ', regex=True)


    ## Repair Parse errors

    # add space in front of every capital letter that has a lowercase letter in front of it
    weekplan_pdf_df["Fast Lane"] = weekplan_pdf_df["Fast Lane"].str.replace(r'(?<=[a-z])(?=[A-Z])', ' ', regex=True)
    weekplan_pdf_df["Daily Favourites"] = weekplan_pdf_df["Daily Favourites"].str.replace(r'(?<=[a-z])(?=[A-Z])', ' ', regex=True)
    weekplan_pdf_df["Lifestyle"] = weekplan_pdf_df["Lifestyle"].str.replace(r'(?<=[a-z])(?=[A-Z])', ' ', regex=True)

    # add space after each comma
    weekplan_pdf_df["Fast Lane"] = weekplan_pdf_df["Fast Lane"].str.replace(r',', ', ', regex=True)
    weekplan_pdf_df["Daily Favourites"] = weekplan_pdf_df["Daily Favourites"].str.replace(r',', ', ', regex=True)
    weekplan_pdf_df["Lifestyle"] = weekplan_pdf_df["Lifestyle"].str.replace(r',', ', ', regex=True)
    
    ## If errors occured, feel free to add more cleaning steps here ## 

    return weekplan_pdf_df
   

def get_mensaplan(week=1, mensa_location="hsg", path="mensaplan.pdf", get_pdf=True):
    """function to get the pdf of the mensaplan and return it as a pandas dataframe

    1. Downloads the pdf from the migros website utilizing a get request
    2. Extracts the table from the pdf utilizing pdfplumber
    3. Converts the table to a pandas dataframe
    4. Cleans the dataframe utilizing the clean_mensaplan_df function
    5. Returns the cleaned dataframe


    Args:
        week (int, optional): the week number. Defaults to 1. (1 is the current week and 2 is the next week)
        mensa_location (str, optional): the location of the mensa. Defaults to "hsg". (Choice between "hsg" and "fhs")
        save_file (bool, optional): if True, the pdf will be saved to the path specified in the path argument. Defaults to False.
        path (str, optional): the path where the pdf will be saved. Defaults to "mensaplan.pdf".
    """

    # spelling of pfd name is different for hsg and fhs
    if mensa_location == "hsg":
        name_wochenmenu = "Wochenmenu"
    elif mensa_location == "fhs":
        name_wochenmenu = "wochenmenu"

    # got the url and header informations from the network tab in the browser
    url = f'https://migros-ostschweiz.ch/wochenmenue/{mensa_location}/{name_wochenmenu}_{week}.pdf'

    headers = {
        # 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:134.0) Gecko/20100101 Firefox/134.0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Referer': 'https://gastro.migros.ch/',
        'DNT': '1',
        'Sec-GPC': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'cross-site',
        'Priority': 'u=0, i',
    }

    # Send a GET request to the URL
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Save the PDF as .file 
        with open("."+ path, "wb") as file:
            file.write(response.content)
        
        with pdfplumber.open("."+ path) as pdf:
            # get information from the first page and extract the table
            page = pdf.pages[0]
            table = page.extract_table()
        
        # convert the table to a pandas dataframe
        weekplan_pdf_df = pd.DataFrame(table)

        # clean the dataframe
        weekplan_pdf_df = clean_mensaplan_df(weekplan_pdf_df, mensa_location)


        # delete the saved pdf if the pdf should not be saved
        if not get_pdf:
            try:
                os.remove("."+ path)
            except:
                print("Failed to delete the pdf")

        
        return weekplan_pdf_df

        
    else:
        print(f"Failed to download the PDF. Status code: {response.status_code}")
        return None
    

    
    

import requests
import json
import os
import sys
import pandas as pd
from collections import defaultdict

# Constants
INF = 2000000000
AT = '@'    # Prefix before every name
HEADER_TEXT = 'Yet another round has ended and here are the results:'
FOOTER_TEXT = "If you're eligible for the standings list(s) " \
"but have not been tagged, leave a comment with your " \
"handle."

# File specific paths
HANDLES_DIR = 'CF Handles'
SEP_DIR = 'CF Handles\\Separate Lists'
OUTPUT_FILE = 'Output.txt'

# Options
LISTS = ['Overall', 'Rated', 'Summer Group']
LIST_LENGTH = {'Overall': 10, 'Rated': 10, 'Summer Group': 5}
OVERALL_LEN_IF_S = 5        # Length of overall list if 's'
ONLY_OFFICIAL_RANKS_FOR_RATED = False
FIELDS = ['handle', 'name', 'rating', 'maxrank']
RANKS = ['urank', 'orank']

"""
CSV file format:=
handle,name,rating,maxrank
the_hyp0cr1t3,Hriday,2024,candidate master
.
.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Input format:= 
Contest_ID options Contest_ID options...

Single space separated list of arguements.
'Options' include single character 's' and/or 'o'
    'o' => to also display [official rank]
    's' => to also display rated participants list
    '-c or -commit' => to commit changes/updates to files
    '-{handle}' => to exclude particular handles
Options may or may not be specified.

Eg: 1220 o 1340 s 1332 234 s o -the_hyp0cr1t3 -commit

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Output Format:=
Writes to OUTPUT_FILE_PATH (Output.txt)

HEADER_TEXT

CONTEST_1 NAME
Overall standings list
1. @name (handle) (unofficial rank) [official rank]
2. @name (handle) (unofficial rank) [official rank]
.
.

Rated standings list
1. @name (handle) (unofficial rank) [official rank]
.
.

{Separate category 1} standings list
1. @name (handle) (unofficial rank) [official rank]
.
.

CONTEST_2 NAME
.
.
.

Congratulations to @name on becoming Expert!
Congratulations to @name, @name and @name on becoming Master!

FOOTER_TEXT

"""

class Contest_info:
    def __init__(self, IDno):
        self.ID = IDno
        self.isofficial = False
        self.rated_sep = False
        self.name = 'uninit'

# Output write methods
def write_header():
    # Clear and write header text
    with open(OUTPUT_FILE, 'w') as file:
        file.write(HEADER_TEXT + '\n')

def write_lists(contest, standings, df):
    # Write each LIST to file in appropriate format
    with open(OUTPUT_FILE, 'a') as file:
        # Contest name
        file.write(contest.name+'\n')

        for category in LISTS:
            # Skip if category is RATED and 's' is not specified
            if category == 'Rated' and not contest.rated_sep: continue

            if len(standings[category]):
                # List name
                file.write(category+' Standings\n')

                for handle in standings[category]:
                    # 1. @name (handle) (unofficial rank) [official rank]
                    # 2. @name (handle) (unofficial rank) [official rank]
                    file.write(f'{df.loc[handle, category]}.'\
                            f" {AT}{df.loc[handle, 'name']} ({handle}) ")
                    df.loc[handle, category] = True

                    if not ONLY_OFFICIAL_RANKS_FOR_RATED:
                        file.write(f"({df.loc[handle, 'urank']}) ")

                    if contest.isofficial or category == 'Rated':
                        if df.loc[handle, 'orank'] == INF: df.loc[handle, 'orank'] = '-'
                        file.write(f"[{df.loc[handle, 'orank']}]")

                    file.write('\n')

                file.write('\n')

    return df

def write_congrats(congo):
    # Write congratulatory text
    # for all those who increased their maxrank (eg: specialist -> expert).
    with open(OUTPUT_FILE, 'a') as file:
        for rank in congo:
            file.write(f'Congratulations to {AT}')
            if len(congo[rank]) >= 2:
                file.write(f'{f", {AT}".join(congo[rank][:-1])} and {AT}')
            file.write(f'{congo[rank][-1]} on reaching {rank}!\n\n')

def write_footer():
    # Write footer text
    with open(OUTPUT_FILE, 'a') as file:
        file.write(FOOTER_TEXT + '\n')

# File read methods
def new_row(df_row):
    # {handle}, {name}..., {Overall:T/F}, ...LISTS
    row = [df_row[x] for x in FIELDS] + [False] * len(LISTS)
    return row[1:]

def add_folder(category, path, df):
    # Add all csv files in a folder (path)
    for year in os.listdir(path):
        if year[-4:] == '.csv':
            df1 = pd.read_csv(path+'\\'+year)

            for i, row in df1.iterrows():
                if row['handle'] not in df.index:
                    df.loc[row['handle']] = new_row(row)
            
                df.loc[row.handle, category] = True

    return df

def load_handles():
    # df columns = handles(key), FIELDS.., LISTS..., RANKS... 
    df = pd.DataFrame(columns=FIELDS+LISTS)
    df.set_index('handle', inplace=True)

    df = add_folder('Overall', HANDLES_DIR, df)
    
    for category in os.listdir(SEP_DIR):            
        df = add_folder(category, SEP_DIR+'\\'+category, df)
    
    df['Overall'] = True
    return df

# File write and update methods
def update_folder(path, df):
    # Update all csv files in a folder with corresponding updated data from df
    for year in os.listdir(path):
        if year[-4:] == '.csv':
            df1 = pd.read_csv(path+'\\'+year)
            df1['rating'] = 0
            df1['maxrank'] = 'uninit'
            df1.set_index('handle', inplace=True)

            for handle, row in df1.iterrows():      # updating each row
                df1.loc[handle, df1.columns] = df.loc[handle, df1.columns]
            
            df1 = df1.fillna(0)        # Some NaN complaints when casting to int32
            df1.astype({'rating': 'int32'}).dtypes
            df1.to_csv(path+'\\'+year)

def update_all_files(df):
    # Write df to each file in appropriate locations
    update_folder(HANDLES_DIR, df)
    for category in os.listdir(SEP_DIR):
        update_folder(SEP_DIR+'\\'+category, df)

# CF API query and response methods
def query_cfAPI(url, df):
    # Append handles and send a HTTP request to the CF API
    # return json response
    for handle, row in df.iterrows():
        url += handle + ';'

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        print('Timeout')
        sys.exit(1)
    except requests.exceptions.TooManyRedirects:
        print('Too many redirects')
        sys.exit(1)
    except requests.exceptions.RequestException as err:
        print(err)
        sys.exit(1)
    except requests.exceptions.HTTPError as err:
        print(err)
        sys.exit(1)

    return json.loads(response.text)

def update_ranks(df, json_response, isofficial):
    # update df RANKS with the json response
    for user in json_response['result']['rows']: 
        handle = user['party']['members'][0]['handle']
        participant_type = user['party']['participantType']
        
        good = (handle in df.index
                and participant_type != "PRACTICE"
                and participant_type != "VIRTUAL")
        if good:
            df.loc[handle, 'orank' if isofficial else 'urank'] = int(user['rank'])

    return df

def update_df(df, json_response):
    # Update df with user.info from the query as well as
    # check for mismatches between maxrank in file (i.e. df) and maxrank from query
    # All such mismatches populated in congo
    congo = defaultdict(list)      # congo[rank] = [names..]

    for user in json_response['result']: 
        handle = user['handle']
        try:
            rating = user['rating']     # unrated user.info json objects do not have "rating" field
            maxrank = user['maxRank']
        except:
            rating = 0
            maxrank = 'unrated'
        
        if df.loc[handle, 'maxrank'] != maxrank:
            congo[maxrank].append(df.loc[handle, 'name'])

        df.loc[handle, ['rating', 'maxrank']] = [rating, maxrank]

    return congo, df

# Standings extraction methods
def select(column, df, list_len):
    # Pick the top {list_len} handles from the sorted df
    standings_list = []     # List of handles
    local_rank = 0          # Rank within this list
    previous_rank = -1

    for handle, row in df.iterrows():
        # Only if True
        if row[column] == False: continue
        # Official rank or unofficial ranlk
        rank = row['orank'] if column == 'Rated' else row['urank']
        # Break if length exceeds and there is no tie for last place
        if len(standings_list) >= list_len and rank > previous_rank: break
        # Skip if rank does not exist
        if rank == INF: continue
        # If not a tie, advance local rank
        if rank != previous_rank:
            local_rank += 1
        # Update cell from True to local rank
        df.loc[handle, column] = local_rank
        # Append handle to list
        standings_list.append(handle)
        previous_rank = rank

    return df, standings_list

def get_standings(contest, df):
    # get CF API contest.standings (unofficial)
    url = 'https://codeforces.com/api/contest.standings?'\
        f'contestId={contest.ID}&showUnofficial=true&handles='

    json_response = query_cfAPI(url, df)
    df = update_ranks(df, json_response, False)

    # get CF API contest.standings (official)
    url = 'https://codeforces.com/api/contest.standings?'\
        f'contestId={contest.ID}&showUnofficial=false&handles='

    json_response = query_cfAPI(url, df)
    df = update_ranks(df, json_response, True)

    # Rated is true only if official rank exists
    df['Rated'] = [(False if val == INF else True) for val in df['orank']]

    # Sort by unofficial, official ranks
    df.sort_values(by=RANKS, inplace=True)

    standings = {}  # standings['Overall'] = list of handles, etc

    for column in df.columns:
        # for each standings list, retrieve top x handles (specified by LIST_LENGTH)
        # and update df[handle, this list] with the local rank in this list
        if column not in FIELDS and column not in RANKS:
            list_len = (OVERALL_LEN_IF_S 
                        if column == 'Overall' and contest.rated_sep
                        else LIST_LENGTH[column])
            df, standings[column] = select(column, df, list_len)
        
    contest.name = json_response['result']['contest']['name']
    df = write_lists(contest, standings, df)
    print(contest.name)
    return df

def main():
    contests = []   # List of Contest_info objects
    exclude = []    # Handles to exclude
    commit = False
    inp = input()

    for field in inp.split():
        # contest ID
        if field.isnumeric():
            contests.append(Contest_info(field))
        # commit
        elif field == '-c' or field == '-commit':
            commit = True
        # exclude
        elif field[0] == '-':
            exclude.append(field[1:])
        # display official ranks
        elif len(contests) and field == 'o':
            contests[-1].isofficial = True
        # display rated list separately
        elif len(contests) and field == 's':
            contests[-1].rated_sep = True

    # load handles from all files into a DataFrame
    df = load_handles()

    for handle in exclude:
        df.drop(handle, inplace=True)

    # CF API accepts upto 10000 handles in a single request
    assert(len(df) <= 10000), "Handle limit exceeded"

    for column in df.columns:
            assert(column in FIELDS
                    or column in LISTS
                    or column in RANKS), f'{column} not found'

    if len(contests): write_header()
    
    for contest in contests:
        for field in RANKS: df[field] = INF     # Reset ranks to INF
        df = get_standings(contest, df)

    # query CF API for user info of all handles
    url = 'https://codeforces.com/api/user.info?handles='
    json_response = query_cfAPI(url, df)

    # Update df and get the congo (congrats) list
    congo, df = update_df(df, json_response)

    if len(contests):
        write_congrats(congo)   # Congratulatory messages
        write_footer()

    if commit: 
        update_all_files(df)
        print('committed')

    print('Success')
    return

if __name__ == "__main__":
    main()

import requests
import json
import os
import sys
import csv

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
OUTPUT_FILE_PATH = 'Output.txt'

# Options
# LIST_LENGTHS specifies desired the length of each standings list
    # LIST_LENGTHS[0] = length of Overall standings list
    # LIST_LENGTHS[1] = length of Rated participants standings list
    # Index 2 onwards correspond to spearate lists
LIST_LENGTHS = [10, 10, 5]
OVERALL_LEN_IF_S = 5        # Length of overall list if 's'
ONLY_OFFICIAL_RANKS_FOR_RATED = False

"""
Input format:= 
Contest_ID options Contest_ID options...

Single space separated list of arguements.
'Options' include single character 's' and/or 'o'
    'o' => to also display [official rank]
    's' => to also display rated participants list
    '-{handle}' => exclude particular handles
Options may or may not be specified.

Eg: 1220 o 1340 s 1332 234 s o -the_hyp0cr1t3

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

FOOTER_TEXT

"""

class User:
    def __init__(self, _handle, _name, _ranksz):
        self.handle = _handle
        self.name = _name
        self.mask = 1
        self.ranksz = _ranksz
        self.reset()

    def trace(self):
        print(self.handle, self.urank, self.orank, self.mask)
        print(self.ranklists)

    def reset(self):
        self.urank = INF
        self.orank = INF
        self.ranklists = [INF for i in range(self.ranksz)]


class Contest_info:
    def __init__(self, IDno):
        self.ID = IDno
        self.isofficial = False
        self.rated_sep = False
        self.name = 'uninit'


def load_handles():
    # List of User objects
    handles = []
    # Dict with key = handle, val = index of handle in list of handles
    handle_ID = {}

    sep_categories = os.listdir(SEP_DIR)        # read all files in SEP dir
    rank_count = len(sep_categories) + 2

    years = os.listdir(HANDLES_DIR)     # read all files in HANDLES dir
    for year in years:                  # and add to handles
        if year[-4:] == '.csv':
            with open(HANDLES_DIR+'\\'+year, 'r') as file:
                reader = csv.reader(file, delimiter=',')
                for row in reader:
                    handle_ID[row[0]] = len(handles)
                    handles.append(User(row[0], row[1], rank_count))

    for category in sep_categories:             # add each SEP handle under
        years = os.listdir(SEP_DIR+'\\'+category)      # respective category
        temp = {}
        for year in years:
            if year[-4:] == '.csv':
                with open(SEP_DIR+'\\'+category+'\\'+year, 'r') as file:
                    reader = csv.reader(file, delimiter=',')
                    for row in reader:
                        if row[0] not in handle_ID:
                            handle_ID[row[0]] = len(handles)
                            handles.append(User(row[0], row[1], rank_count))
                        handles[handle_ID[row[0]]].mask |= (1<<(sep_categories.index(category)+1))

    return handles, sep_categories, rank_count


def query_handles(contest_id, handles, opt):
    # Read handles of all users from file,
    # concatenate with url request string,
    # send request to CF API
    # and finally return json response as a dict
    url = 'https://codeforces.com/api/contest.standings?'\
        f'contestId={contest_id}&showUnofficial={opt}&handles='

    for handle in handles:
        url += handle.handle + ';'

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


def update(handles, handle_ID, json_response, isofficial):
    for user in json_response['result']['rows']: 
        handle = user['party']['members'][0]['handle']
        participant_type = user['party']['participantType']
        
        if (handle not in handle_ID or
                participant_type == "PRACTICE" or
                participant_type == "VIRTUAL"):
            continue

        if isofficial:
            handles[handle_ID[handle]].orank = int(user['rank'])
        else:
            handles[handle_ID[handle]].urank = int(user['rank'])

    return handles


def select(handles, mask, rank_no, list_len):
    standings_list = []
    previous_rank = -1
    current_rank = 0
    for handle in handles:
        rank = handle.orank if rank_no == 1 else handle.urank
        if len(standings_list) >= list_len and rank > previous_rank: break
        if rank == INF: continue
        if handle.mask & mask == 0: continue
        if rank != previous_rank:
            current_rank += 1
        handle.ranklists[rank_no] = current_rank
        standings_list.append(handle)
        previous_rank = rank

    return standings_list


def write_tofile(contest, standings):
    with open(OUTPUT_FILE_PATH, 'a') as file:
        file.write(contest.name+'\n')        
        rank_no = 0

        for category in standings:
            if len(standings[category]):
                file.write(category+' Standings\n')

                for handle in standings[category]:
                    file.write(f'{handle.ranklists[rank_no]}.'\
                            f' {AT}{handle.name} ({handle.handle}) ')

                    if not ONLY_OFFICIAL_RANKS_FOR_RATED:
                        file.write(f'({handle.urank}) ')

                    if contest.isofficial or category == 'Rated':
                        if handle.orank == INF: handle.orank = '-'
                        file.write(f'[{handle.orank}]')

                    file.write('\n')

                file.write('\n')

            rank_no += 1

    return


def run(contest, handles, handle_ID, sep_categories):
    json_response = query_handles(contest.ID, handles, 'true')
    handles = update(handles, handle_ID, json_response, False)

    json_response = query_handles(contest.ID, handles, 'false')
    handles = update(handles, handle_ID, json_response, True)

    handles.sort(key = lambda x: x.urank)

    standings = {}
    
    rank_no = 0
    list_len = OVERALL_LEN_IF_S if contest.rated_sep else LIST_LENGTHS[rank_no]

    standings['Overall'] = select(handles, 1, rank_no, list_len)

    rank_no += 1

    if contest.rated_sep:
        standings['Rated'] = select(handles, 1, rank_no, LIST_LENGTHS[rank_no])
    else:
        standings['Rated'] = []

    for category in sep_categories:
        rank_no += 1
        mask = (1<<(rank_no-1))
        standings[category] = select(handles, mask, rank_no, LIST_LENGTHS[rank_no])
    
    contest.name = json_response['result']['contest']['name']

    write_tofile(contest, standings)

    print(contest.name)
    return


def write_header():
    with open(OUTPUT_FILE_PATH, 'w') as file:
        file.write(HEADER_TEXT + '\n')
    

def write_footer():
    with open(OUTPUT_FILE_PATH, 'a') as file:
        file.write(FOOTER_TEXT + '\n')


def main():
    # List of Contest_info objects
    contests = []

    # Handles to exclude
    exclude = []

    # Input string is space separated, terminated by newline
    inp = input()

    for field in inp.split():
        # Each number is taken as a separate contest object
        # optional parameters 'o' for official and 's' 
        # for ranked separately are scanned for until the next
        # contest number or new line
        if field.isnumeric():
            contests.append(Contest_info(field))
        elif field[0] == '-':
            exclude.append(field[1:])
        elif len(contests) and field == 'o':
            contests[-1].isofficial = True
        elif len(contests) and field == 's':
            contests[-1].rated_sep = True

    if len(contests) == 0:
        exit('No IDs found')

    handles, sep_categories, rank_count = load_handles()

    for handle in exclude:
        toremove = None
        for user in handles:
            if user.handle == handle:
                toremove = user
                break
        if toremove is None:
            print(f'{handle} not found')
        else:
            handles.remove(toremove)

    # CF API accepts upto 10000 handles in a single request
    assert(len(handles) <= 10000), "Handle limit exceeded"

    # List of list-lengths should be valid
    assert(len(LIST_LENGTHS) == rank_count), "LIST_LENGTHS do not match"

    write_header()
    
    for contest in contests:
        idx = 0
        handle_ID = {}
        for handle in handles: 
            handle.reset()
            handle_ID[handle.handle] = idx
            idx += 1
        run(contest, handles, handle_ID, sep_categories)

    write_footer()

    print("Success")
    return


if __name__ == "__main__":
    main()

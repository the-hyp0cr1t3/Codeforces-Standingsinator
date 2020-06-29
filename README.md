# Codeforces-Standingsinator
Generates a custom standings list from handles stored in csv files using the Codeforces API. Features an Overall standings list as well as other separate list(s) which include some subset of handles.

### Set up

* Download ```Gen.py``` and set up your directories as shown below.
* Create your csv files in the same format as [sample.csv](https://github.com/the-hyp0cr1t3/Codeforces-Standingsinator/blob/master/sample.csv) and save them under ```CF Handles``` for them to appear in the overall standings list. You may create special list folders such as, say "New to CC", and save them there instead if you want those handles to appear in the "New to CC standings list" as well. 
* Modify respective list lengths in ```Gen.py``` as per your needs. For each new special list append its respective desired length to ```LIST_LENGTHS```.
```
Codeforces Standingsinator
├── Gen.py
└── CF HANDLES
    ├── Separate Lists
    |        ├── Special list 1
    |        │   ├── some_special_handles_1.csv
    |        │   └──  some_special_handles_2.csv
    |        │    
    |        └── Special list 2
    |            ├── some_special_handles_1.csv
    |            └──  some_special_handles_2.csv
    ├── some_handles_1.csv
    └── some_other_handles_2.csv

```

All csv files within a particular 'Special List' will be considered for its corresponding standings list, as well as the overall standings list. Duplicates are not required, but may be present.

Note that the folders ```CF HANDLES``` and ```Separate Lists``` can be named anything. Modify the file-specific paths in ```Gen.py``` accordingly.

### Usage
Run ```Gen.py```
* Enter Contest ID, not Round number
* Enter a single line with one or more contest ID numbers, separated by spaces
* Following each contest ID, you may optionally enter 'o' (to also show official ranks) and/or 's' (to show rated standings separately)

**Eg**: 1220 o 1340 s 1332 234 s o

**Output**:\
Codeforces Round #586 (Div. 1 + Div. 2)\
Codeforces Round #637 (Div. 1) - Thanks, Ivan Belonogov!\
Codeforces Round #630 (Div. 2)\
Codeforces Round #145 (Div. 2, ACM-ICPC Rules)\
Success


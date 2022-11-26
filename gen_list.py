#!/usr/bin/env python3
"""
Generate random Kris Kringle assignemnts
"""

"""
TODO: TAKE OUT
Goal: Generate random Kris Kringle assignemnts

Process
1. read CSV input config file
2. for each record, randomly select another to be assigned. Follow these rules:
  a. Cannot be in same family group
  b. Prefer to weight proximity in selection
  c. prefer to weight previous associations (either side)
3. Store selections in DataFrame or dict

Quirks:
Pre-Assign must have at least two potentials (can be duplicated to force a single option)
"""
import os
import errno
import json
from datetime import datetime as dt
import argparse
from random import choice, choices, seed
from pandas import read_csv, read_excel, Series, DataFrame, concat

from tkinter import Tk, font, filedialog, StringVar, LEFT, RIGHT, TOP, BOTTOM, DISABLED, Button as SButton
from tkinter.ttk import Style, Frame, Button, Label, LabelFrame, Entry

DEFAULT_FILE='kk-list.xlsx'
DEFAULT_OUT_NAME=f'kk_{dt.now().strftime("%Y")}'
DEFAULT_OUT_DIR=os.getcwd()


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-f', '--file', help=f"name of input Excel file")
    parser.add_argument('-o', '--out', default=DEFAULT_OUT_NAME, help=f"name of file prefix for output (default: '{DEFAULT_OUT_NAME}')")
    parser.add_argument('-d', '--dir', default=DEFAULT_OUT_DIR, help=f"directory for output (default: '{DEFAULT_OUT_DIR}')")
    parser.add_argument('-s', '--seed', type=int, help=f"Set the seed for the random generator")
    parser.add_argument('-g', '--gui', action='store_true', help=f"Set the seed for the random generator")
    args = parser.parse_args()
    return args


def make_dir(path_name):
    if not os.path.exists(os.path.join(path_name)):
        try:
            # logger.info(f'(I): Creating dir: "{path_name}"')
            os.makedirs(os.path.join(path_name))
        except OSError as err: # Guard against race condition
            if err.errno != errno.EEXIST:
               raise


class ZeroPossibilities(ValueError):
    def __init__(self, *args, idx:str, sender_name:str, n_excludes:int, n_possible:int, n_assigns:int, n_total:int):
        self.idx = idx
        self.sender_name = sender_name
        self.n_excludes = n_excludes
        self.n_possible = n_possible
        self.n_assigns = n_assigns
        self.n_total = n_total
        super().__init__(*args)
    
    # def __repr__(self):
    #     return f"ZeroPossibilities Error for {self.sender_name} (excludes: {self.n_excludes}, possible: {self.n_possible})"

    def __str__(self):
        return f"Zero possibilities found for {self.sender_name} [{self.idx}] (excludes: {self.n_excludes}, possible: {self.n_possible}). Assigned {self.n_assigns} of {self.n_total}."


class App(Tk):
    def __init__(self, in_fname, out_dir, out_prefix_name, seed=None):
        Tk.__init__(self)
        self.in_file = StringVar()
        self.out_dir = StringVar()
        self.out_prefix = StringVar()
        self.in_file.set(in_fname if in_fname else "")
        self.out_dir.set(out_dir if out_dir else "")
        self.out_prefix.set(out_prefix_name if out_prefix_name else "")
        self.seed = seed
        self.title("Gemerate KK Assignments")
        self.__init_style()
        self.__add_widgets()


    def __init_style(self):
        self.paddings = {'padx': 5, 'pady': 5}
        self.frame_paddings = {'padx': 10, 'pady': 10, 'ipadx': 5, 'ipady': 5}
        self.button_paddings = {'padx': 10, 'pady': 10, 'ipadx': 20, 'ipady': 11 } # h(20, ratio)}
        
        ratio = 16/9
        width = 900
        h = lambda w,r: round(w*(1/r))
        size = lambda w, r: f"{w}x{h(w,r)}"
        self.geometry(f'{size(width, ratio)}')
        style = Style(self)
        style.theme_use('aqua')
        # NOTE: In order to customize any button colors, you need to set "style.theme_use()"
        style.configure('.', font=('Helvetica', 18))
        style.configure('TLabelFrame', font=('Helvetica', 14))
        # style.configure('TLabelFrame', font=('Helvetica', 14))
        style.configure('err.TLabel', font=('Helvetica', 18), foreground='#ffb3b8')
        style.configure('H1.TLabel', font=('Helvetica', 18))
        style.configure('body.TLabel', font=('Helvetica', 11))
        # style.configure('mono.TLabel', font=('IBM Plex Mono', 14))
        style.configure('mono.TLabel', font=('Courier', 14))
        style.configure('TLabel', font=('Helvetica', 14))
        style.configure('TButton', font=('Helvetica', 14))
        style.configure('primary.TButton', background = 'red', foreground = 'white', font=('Helvetica', 14))
        style.map('TButton', background=[('active','red')])


    def __add_widgets(self):
        files_frame = LabelFrame(self, text="Select files")
        ff1 = Frame(files_frame)
        Label( ff1, text='Input File:', style='H1.TLabel').pack(side=LEFT, **self.paddings)
        Label( ff1, textvariable=self.in_file, style='mono.TLabel').pack(side=LEFT, fill='x', **self.paddings)
        in_dir = os.path.dirname(self.in_file.get()) if self.in_file.get() else os.getcwd()
        Button( ff1, text = "Open...", command = self.cfgFiledialog(self.in_file, 'Select Input File', dir=in_dir)).pack(side=RIGHT, **self.paddings)
        ff2 = Frame(files_frame)
        Label( ff2, text='Output Folder:', style='H1.TLabel' ).pack(side=LEFT, **self.paddings)
        Label( ff2, textvariable=self.out_dir, style='mono.TLabel' ).pack(side=LEFT, fill='x', **self.paddings)
        Button( ff2, text = "Open...", command = self.cfgDirdialog(self.out_dir, 'Select Output Folder', dir=self.out_dir.get()) ).pack(side=RIGHT, **self.paddings)
        ff1.pack(fill='x')
        ff2.pack(fill='x')
        files_frame.pack(side=TOP, **self.frame_paddings, fill='x')
        F1 = Frame(self)
        L1 = Label(F1, text="Prefix")
        L1.pack(side = LEFT)
        E1 = Entry(F1, textvariable=self.out_prefix)
        E1.pack(side = RIGHT)
        F1.pack()

        self.F2 = Frame(self)
        self.err_label = Label(self.F2, text="Inputs are required.", style='err.TLabel') #, state = DISABLED)
        self.gen_label = Label(self.F2, text="")  # "About to start generating data"
        self.gen_label.pack(side=TOP)
        Button( self.F2, text = "Generate Assignments", style='primary.TButton', command = self.gen_assignments ).pack(**self.button_paddings)  #.pack(side=BOTTOM, expand=True, **button_paddings)
        self.F2.pack(expand=True, fill='both')

        F3 = Frame(self)
        self.results_label = Label(F3)
        F3.pack(expand=True, fill='both')


    def show(self):
        self.mainloop()


    def cfgFiledialog(self, s_var, title, dir="."):
        def opendialog():
            filename = filedialog.askopenfilename(initialdir=dir, title=title, filetypes=(("Excel files","*.xlsx"),("all files","*.*")))
            s_var.set(filename)
        return opendialog


    def cfgDirdialog(self, s_var, title, dir="."):
        def opendialog():
            filename = filedialog.askdirectory(initialdir=dir, title=title)
            s_var.set(filename)
        return opendialog


    def gen_assignments(self):
        # if err_label:  err_label.pack_forget()
        self.gen_label.configure(text="")
        self.err_label.pack_forget()
        self.results_label.configure(text="")
        self.results_label.pack_forget()
        if not self.in_file.get() or not self.out_dir.get() or not self.out_prefix.get():
            self.err_label.configure(text="Inputs are required.").pack(side=TOP)
            return
        else:
            self.err_label.pack_forget()
        # gen_label = Label(self.F2, text="About to start generating data")
        # gen_label.pack(side=TOP)
        self.gen_label.configure(text="About to start generating data")
        try:
            assigns_df = gen_assignments(self.in_file.get(), self.out_dir.get(), self.out_prefix.get(), self.seed)
            self.gen_label.configure(text=f'Finished generating assignments for "{self.out_prefix.get()}" see file "{self.out_dir.get()}".')
            self.results_label.configure(text=assigns_df.to_string(index=False))
            self.results_label.pack(side=BOTTOM)
        except ZeroPossibilities as zpe:
            print(f'(E): {zpe}')
            self.err_label.configure(text=f"{zpe}. Please try again.")
            self.err_label.pack(side=TOP)


def gen_assignments(in_fname:str, out_dir:str, out_prefix_name:str, seed:int=None):
    """
    Generate Assignments based on Excel file input.
    
    Arguments:
    in_fname -- Name of input file to read
    out_dir  -- Path to output directory
    out_prefix_name -- Prefix used for output files
    seed -- Seed to use for random number generator 
    FIXME: DOES SEED ACTUALLY WORK??
    """
    out_name = os.path.join(out_dir, out_prefix_name)
    assign = dict()
    try:
        family_wb = read_excel(in_fname, sheet_name=None)
    except:
        print(f'(E): Unable to read input Excel file "{in_fname}".')
        return
    names_d = family_wb['Active Members']
    pref_assigns = family_wb['Preferred Assign']
    # pref_assigns = DataFrame({'KK Giver': [], 'Vlookup (invalid)': []})
    past_assigns = family_wb['Past Assignments']
    sender_options = list()

    print('(I): Applying random preferred assignments.')
    for sender_name, pref_receive_g in pref_assigns.groupby('KK Giver'):
        if sender_name[0] == '#': continue
        if sender_name in assign.keys():
            print(f'(I): Sender "{sender_name}" already assigned')
            continue
        if len(pref_receive_g) < 1:
            print(f'(I): Sender "{sender_name}" does not have enough assignees to choose from for pre-assign')
            continue
        if len(pref_receive_g) == 1:
            receiver = pref_receive_g.iloc[0]['KK Receiver']
            assign[sender_name] = receiver
            print(f'(D): {sender_name} assigned to {receiver}')
            continue
        sender_past_assigns = past_assigns[past_assigns['KK Giver'] == sender_name]\
            .drop(['KK Giver', 'Vlookup (invalid)'], axis=1)\
            .dropna(axis=1)
        excludes = list(sender_past_assigns.iloc[0]) + [*assign.values()]
        possible = sorted(set(pref_receive_g['KK Receiver']) - set(excludes))
        if len(possible) == 0:
            print('(W): No possible pre-assign matches for sender: ', sender_name)
            continue
        receiver = choice(possible)
        assign[sender_name] = receiver
        sender_options.append({'Name': sender_name, 'Except': len(excludes), 'Possible': len(possible),})
        print(f'(D): {sender_name} assigned to {receiver}')
    
    print('(I): Applying random regular assignments.')
    ran_names_d = names_d.sample(frac=1, random_state=seed).reset_index(drop=True)
    regular_senders_d = names_d[~names_d['Name'].isin(assign.keys())].sample(frac=1, random_state=seed).reset_index(drop=True)
    for index, sender_row in regular_senders_d.iterrows():
        sender_name = sender_row['Name']
        if sender_name[0] == '#': print(f'(D): skipping {sender_name}'); continue
        if sender_name in assign:
            print(f'(I): {sender_row["Name"]} already assigned')
            continue
        sender_past_assigns = past_assigns[past_assigns['KK Giver'] == sender_name]\
            .drop(['KK Giver', 'Vlookup (invalid)'], axis=1)\
            .dropna(axis=1)
        excludes = set(
            [sender_name] +\
            list(ran_names_d[ran_names_d['Exclude Group 1'] == sender_row['Exclude Group 1']]['Name']) +\
            list(ran_names_d[ran_names_d['Exclude Group 2'] == sender_row['Exclude Group 2']]['Name']) +\
            list(sender_past_assigns.iloc[0] if len(sender_past_assigns) > 0 else [])+\
            [*assign.values()]
        )
        possible = sorted(list(set(ran_names_d['Name']) - excludes))  #WHY SORTED??
        print(f'(D): Sender: {sender_name}')
        print(f'(D): excludes: {len(excludes)}, possibles: {len(possible)} --')
        # print(excludes)
        # print(f'(D): Possibles ({len(possible)}):')
        print(possible)
        if sender_name in possible:
            print(f'(D): {sender_name} can be assiend to themselves!')
        possible_d = ran_names_d[ran_names_d['Name'].isin(possible)]
        if len(possible_d) == 0:
            print(f'(D): Unable to find option for sender: {sender_row["Name"]}')
            print(possible_d)
            assign_d = DataFrame(list(assign.items()), columns=['KK Giver', 'KK Receiver'])
            left_justify = {COL:'{{:<{}s}}'.format(assign_d[COL].str.len().max()).format for COL in assign_d}
            assign_d.to_string(f'{out_name}.err.txt', index=False, justify='left', formatters=left_justify)
            raise ZeroPossibilities(idx=index, sender_name=sender_name, n_excludes=len(excludes), n_possible=len(possible), n_assigns=len(assign.keys()), n_total=len(names_d))
            # raise ValueError(f'Zero possibilities for "{sender_row["Name"]}"')
        select = choices(list(possible_d['Name']))[0]
        sender_options.append({'Name': sender_name, 'Except': len(excludes), 'Possible': len(possible),})
        assign[sender_row['Name']] = select
        print(f'(D): {sender_name} assigned to {select}')
    assign_d = DataFrame(list(assign.items()), columns=['KK Giver', 'KK Receiver'])

    print(f'(I): Writing {len(assign)} Assignments...')
    DataFrame(sender_options).to_string(f'{out_name}.debug.txt', index=False)
    left_justify = {COL:'{{:<{}s}}'.format(assign_d[COL].str.len().max()).format for COL in assign_d}
    assign_d.to_string(f'{out_name}.txt', index=False, justify='left', formatters=left_justify)
    print(f'(I): Finished writing {out_name}')
    return assign_d


if __name__ == "__main__":
    args = parse_args()
    if args.seed:
        seed(args.seed)
    if args.dir:
        args.dir = os.path.abspath(args.dir)
    if args.file:
        args.file = os.path.abspath(args.file)
        make_dir(args.dir)
    if args.gui:
        App(args.file, args.dir, args.out).show()
    else:
        try:
            gen_assignments(args.file, args.dir, args.out, args.seed)
        except ZeroPossibilities as zpe:
            print('(E): ', zpe)
            exit(1)


"""
EXAMPLES:
"""
    # print('(D): ', names_d.columns)
    # print('(D): pre-assign: ', pre_assign)

    # names_g = names_d.groupby('Family Group')
    # print(names_g)

    # for receiver_name, send_g in pre_assign.groupby('KK Receiver'):
    #     # print('(D): receiver: ', receiver_name)
    #     if receiver_name in assign.values():  
    #         print(f'(I): Receiver "{receiver_name}" already assigned')
    #         continue
    #     if len(send_g) <= 1:
    #         print(f'(I): Receiver "{receiver_name}" does not have enough assignees to choose from for pre-assign')
    #         continue
    #     # print(list(send_g['Sender']))
    #     excludes = assign.keys()
    #     possible = sorted(set(send_g['KK Giver']) - set(excludes))
    #     if len(possible) == 0:
    #         print('(I): No possible pre-assign matches for receiver: ', receiver_name)
    #         continue
    #     sender = choice(possible)
    #     assign[sender] = receiver_name
        # print(f'(D): {sender} assigned to {receiver_name}')
    # print(assign)


    # Apply Weights:
    # w = [1]*len(possible_d)  # Unity weights
    # w = possible_d['Group2'].apply(lambda v: 1 if v == geo_zone else 5)  # Apply Weights. Use for past_assigns
    # select = choices(list(possible_d['Name']), weights=w)[0]

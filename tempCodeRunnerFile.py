genderChoice = tk.StringVar(value="")  # Domyślnie brak wyboru

genderLabel = tk.Label(dataFrame,text="Płeć:")
genderLabel.grid(row=3,column=0,padx=5)

maleRadio = tk.Radiobutton(dataFrame, text="Mężczyzna", variable=genderChoice, value="Mężczyzna")
maleRadio.grid(row=3, column=1, padx=5, sticky='w')

femaleRadio = tk.Radiobutton(dataFrame, text="Kobieta", variable=genderChoice, value="Kobieta")
femaleRadio.grid(row=3, column=1, padx=5, sticky='e')
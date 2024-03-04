# pandas to xlsx python

from openpyxl import load_workbook
import io
day_extenso = {
    'SEG': 'SEGUNDA-FEIRA',
    'TER': 'TERÇA-FEIRA',
    'QUA': 'QUARTA-FEIRA',
    'QUI': 'QUINTA-FEIAR',
    'SEX': 'SEXTA-FEIRA',
    'SAB': 'SÁBADO',
    'DOM': 'DOMINGO'
}
    



def pandas_to_xlsx(df, day):
    wb = load_workbook(filename='hora.xlsx')
    sheet_ranges = wb['hora']
    sheet_ranges['A1'] = f'{day_extenso[day]}'.replace('1', '1°').replace('2', '2°').replace('3', '3°')
    for j, row in enumerate(df.iterrows()):
        valores = row[1].tolist()
        index = row[0]
        sheet_ranges[f'A{j+3}'] = index
        for i, valor in enumerate(valores):
            sheet_ranges[f'{chr(65+i+1)}{j+3}'] = valor
    # save as stream
    stream = io.BytesIO()
    wb.save(stream)
    return stream.getvalue()




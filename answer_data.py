import pandas as pd
from model import model_predict
import matplotlib.pyplot as plt


def make_plot(data_arr):
    fig, ax = plt.subplots()
    ax.plot(data_arr, 'tab:purple')

    ax.set(xlabel='Кол-во значений',
           ylabel='Объём добычи нефти (м³)',
           title='Динамика добычи нефти')
    ax.grid()

    path = "test.png"
    fig.savefig(path)

    return path


def answer(csv_file):
    predictions = model_predict(csv_file)
    result_hm = {}

    df = csv_file

    # Переименовываем столбцы с добавлением единиц измерения
    new_columns = {
        df.columns[0]: df.columns[0] + ", бар",
        df.columns[1]: df.columns[1] + ", градусы цельсия",
        df.columns[2]: df.columns[2] + ", бар",
        df.columns[3]: df.columns[3] + ", %",
        df.columns[4]: df.columns[4] + ", бар",
        df.columns[5]: df.columns[5] + ", градусы цельсия",
        df.columns[6]: df.columns[6] + ", бар"
    }
    df = df.rename(columns=new_columns)

    # Добавляем столбец с предсказаниями и правильной единицей измерения
    df['Объем добычи нефти, м³'] = predictions

    csv_path, xlsx_path = 'result_csv.csv', 'result_xls.xlsx'

    df.to_csv(csv_path, index=False)
    df.to_excel(xlsx_path, index=False)

    week_cnt = len(df) // 7
    month_cnt = len(df) // 30

    # Сокращенная обработка недель и месяцев
    if week_cnt >= 2:
        week1 = df.iloc[:7]
        week2 = df.iloc[7:14]

        result_hm['week1_avg'] = float(week1['Объем добычи нефти, м³'].mean())
        result_hm['week1_min'] = float(week1['Объем добычи нефти, м³'].min())
        result_hm['week1_max'] = float(week1['Объем добычи нефти, м³'].max())

        result_hm['week2_avg'] = float(week2['Объем добычи нефти, м³'].mean())
        result_hm['week2_min'] = float(week2['Объем добычи нефти, м³'].min())
        result_hm['week2_max'] = float(week2['Объем добычи нефти, м³'].max())

    if month_cnt >= 1:
        month1 = df.iloc[:30]

        result_hm['month1_avg'] = float(month1['Объем добычи нефти, м³'].mean())
        result_hm['month1_min'] = float(month1['Объем добычи нефти, м³'].min())
        result_hm['month1_max'] = float(month1['Объем добычи нефти, м³'].max())

    plot_path = make_plot(predictions)

    return csv_path, xlsx_path, plot_path, result_hm

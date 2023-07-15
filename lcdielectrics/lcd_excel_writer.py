import pandas as pd
import xlsxwriter

# TODO remove pandas dependency


def make_excel_2(results: dict, output: str, single_volt: bool) -> None:
    workbook = xlsxwriter.Workbook(output.split(".json")[0] + ".xlsx")

    if single_volt:
        pass

    else:
        for key in results.keys():
            worksheet = workbook.add_worksheet(name = key)
            for i, freq in enumerate(results[key].keys()):
                print(results[key][freq].keys())
                col_headings = list(results[key][freq].keys())
                start_row = len(results[key][freq][col_headings[0]]) + 3
                worksheet.write(start_row * i, 0, "Frequency (Hz): ")
                worksheet.write(start_row * i, 1, float(freq))
                worksheet.write_row((start_row) * i  + 1, 0, col_headings)

                for j, heading in enumerate(col_headings):
                    worksheet.write_column(start_row * i + 2, j, results[key][freq][heading])

                # df = pd.DataFrame(results[key][freq])
                # cols = list(df.columns.values)
                # cols.insert(0, cols.pop(cols.index("volt")))
                # df = df[cols]
                # df.to_excel(
                #     writer,
                #     sheet_name=str(key),
                #     index=False,
                #     startrow=((len(df.index) + 3) * i) + 1,
                #     startcol=0,
                # )
                # worksheet = writer.sheets[str(key)]
                # worksheet.write((len(df.index) + 3) * i, 0, "Frequency (Hz): ")
                # worksheet.write((len(df.index) + 3) * i, 1, float(freq))
    workbook.close()


def make_excel(results: dict, output: str, single_volt: bool) -> None:
    with pd.ExcelWriter(output.split(".json")[0] + ".xlsx") as writer:
        if single_volt:
            for key in results.keys():
                for i, freq in enumerate(results[key].keys()):
                    df = pd.DataFrame(results[key][freq])
                    df["freq"] = freq
                    volt = results[key][freq]["volt"]
                    df = df.drop(columns="volt")

                    cols = list(df.columns.values)
                    cols.insert(0, cols.pop(cols.index("freq")))
                    df = df[cols]
                    if i == 0:
                        df.to_excel(
                            writer,
                            sheet_name=str(key),
                            index=False,
                            startrow=i + 1,
                            startcol=0,
                        )
                    else:
                        df.to_excel(
                            writer,
                            sheet_name=str(key),
                            header=False,
                            index=False,
                            startrow=i + 2,
                            startcol=0,
                        )

                    worksheet = writer.sheets[str(key)]
                    worksheet.write(0, 0, "Voltage (V): ")
                    worksheet.write(0, 1, float(volt[0]))

        else:
            for key in results.keys():
                for i, freq in enumerate(results[key].keys()):
                    df = pd.DataFrame(results[key][freq])
                    cols = list(df.columns.values)
                    cols.insert(0, cols.pop(cols.index("volt")))
                    df = df[cols]
                    df.to_excel(
                        writer,
                        sheet_name=str(key),
                        index=False,
                        startrow=((len(df.index) + 3) * i) + 1,
                        startcol=0,
                    )
                    worksheet = writer.sheets[str(key)]
                    worksheet.write((len(df.index) + 3) * i, 0, "Frequency (Hz): ")
                    worksheet.write((len(df.index) + 3) * i, 1, float(freq))

import xlsxwriter


def make_excel_2(results: dict, output: str, single_volt: bool) -> None:
    workbook = xlsxwriter.Workbook(output.split(".json")[0] + ".xlsx")

    for T in results.keys():
        worksheet = workbook.add_worksheet(name=T)
        if single_volt:
            col_headings = list(results[T][list(results[T].keys())[0]].keys())
            col_headings.remove("volt")
            volt = results[T][list(results[T].keys())[0]]["volt"]
            worksheet.write(0, 0, "Voltage (V): ")
            worksheet.write(0, 1, float(volt[0]))
            worksheet.write(1, 0, "Freq (Hz)")
            worksheet.write_row(1, 1, col_headings)

            for i, freq in enumerate(results[T].keys()):
                worksheet.write(2 + i, 0, freq)
                for j, heading in enumerate(col_headings):
                    worksheet.write_column(2, j + 1, results[T][freq][heading])

        else:
            for i, freq in enumerate(results[T].keys()):
                col_headings = list(results[T][freq].keys())
                start_row = len(results[T][freq][col_headings[0]]) + 3
                worksheet.write(start_row * i, 0, "Frequency (Hz): ")
                worksheet.write(start_row * i, 1, float(freq))
                worksheet.write_row((start_row) * i + 1, 0, col_headings)

                for j, heading in enumerate(col_headings):
                    worksheet.write_column(
                        start_row * i + 2, j, results[T][freq][heading]
                    )

    workbook.close()



import xlsxwriter
from lcdielectrics.lcd_dataclasses import OutputType

def make_excel(results: dict, output: str, output_type: OutputType) -> None:
    workbook = xlsxwriter.Workbook(output.split(".json")[0] + ".xlsx")

    for T in results.keys():
        worksheet = workbook.add_worksheet(name=str(T))
        if output_type == OutputType.SINGLE_VOLT:
            for i, freq in enumerate(results[T].keys()):
                col_headings = list(results[T][freq].keys())
                col_headings.remove("volt")
                volt = results[T][freq]["volt"][0]
                worksheet.write(0, 0, "Voltage (V)")
                worksheet.write(0, 1, float(volt))
                worksheet.write(1, 0, "Freq (Hz)")
                worksheet.write_row(1, 1, col_headings)

                worksheet.write(2+i, 0, freq)
                for j, heading in enumerate(col_headings):
                    worksheet.write_row(
                        i + 2, j+1, results[T][freq][heading]
                    )
        elif output_type == OutputType.SINGLE_FREQ:
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

        elif output_type == OutputType.SINGLE_VOLT_FREQ:
            pass

    workbook.close()

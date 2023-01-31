import pandas as pd


def make_excel(results: dict, output: str, v_list: bool) -> None:

    with pd.ExcelWriter(output.split(".json")[0] + ".xlsx") as writer:

        if v_list:
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
        else:
            for key in results.keys():
                if key != "volt":
                    df = pd.DataFrame(results[key])
                    cols = list(df.columns.values)
                    cols.insert(0, cols.pop(cols.index("freq")))
                    df = df[cols]
                    df.to_excel(
                        writer, sheet_name=str(key), index=False, startrow=1, startcol=0
                    )

import pandas as pd


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

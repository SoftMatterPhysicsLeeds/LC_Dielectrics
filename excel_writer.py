import pandas as pd

def make_excel(results: dict, output: str, v_list: bool) -> None:

    with pd.ExcelWriter(output.split(".json")[0] + ".xlsx") as writer:
        
        if v_list:
            for key in results.keys():
                              
                for i,freq in enumerate(results[key].keys()):
                    df = pd.DataFrame(results[key][freq])
                    df.to_excel(writer, sheet_name=str(key), index=False, startrow= 1, startcol = i*2+i )
                    worksheet = writer.sheets[str(key)]
                    worksheet.write(0,0,"Frequency (Hz): ")  
                    worksheet.write(0, i*2+i+1, float(freq))
        else:
            for key in results.keys():
                if key != "volt":
                    df = pd.DataFrame(results[key])
                    df.to_excel(writer, sheet_name=str(key), index=False)
                   






import pandas as pd

def make_excel(results: dict, output: str) -> None:

    depth = finddepth(results)
    
    with pd.ExcelWriter(output.split(".")[0] + ".xlsx") as writer:
        
        if depth == 2:
            for key in results.keys():
                if key != "volt":
                    df = pd.DataFrame(results[key])
                    df.to_excel(writer, sheet_name=key, index=False)
        elif depth == 3:
            for key in results.keys():
                              
                for i,freq in enumerate(results[key].keys()):
                    df = pd.DataFrame(results[key][freq])
                    df.to_excel(writer, sheet_name=key, index=False, startrow= 1, startcol = i*2+i )
                    worksheet = writer.sheets[key]
                    worksheet.write(0,0,"Frequency (Hz): ")  
                    worksheet.write(0, i*2+i+1, float(freq))
                   

def finddepth(dictA: dict) -> int:
    if isinstance(dictA, dict):
        return 1 + (max(map(finddepth, dictA.values()))
                    if dictA else 0)
    return 0



